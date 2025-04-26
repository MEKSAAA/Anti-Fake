import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw
import yaml
from torchvision import transforms
from transformers import BertTokenizerFast
from dataset.utils import pre_caption
import numpy as np
import os
# 导入必要的模型文件
from models.HAMMER import HAMMER
from models.vit import interpolate_pos_embed
from models import box_ops

class DeepFakeDetector:
    def __init__(self, config_path, model_path, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        print("device:", self.device)
        self.config = yaml.load(open(config_path, 'r'), Loader=yaml.Loader)
        
        self.text_encoder = './bert/'
        # self.text_encoder = 'bert-base-uncased'
        self.tokenizer = BertTokenizerFast.from_pretrained(self.text_encoder)
        
        print("creating HAMMER...")
        self.model = HAMMER(
            args=None, 
            config=self.config, 
            text_encoder=self.text_encoder, 
            tokenizer=self.tokenizer, 
            init_deit=True
        )
        
        checkpoint = torch.load(model_path, map_location='cpu')
        state_dict = checkpoint['model']
        
        pos_embed_reshaped = interpolate_pos_embed(state_dict['visual_encoder.pos_embed'], self.model.visual_encoder)
        state_dict['visual_encoder.pos_embed'] = pos_embed_reshaped
        
        msg = self.model.load_state_dict(state_dict, strict=False)
        print('loading checkpoint:', model_path)
        print(msg)
        
        self.model.to(self.device)
        self.model.eval()
        # 图像预处理
        self.image_transform = transforms.Compose([
            transforms.Resize((self.config['image_res'], self.config['image_res']), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
        ])
        
    def load_image(self, image_path):
        print("loading image...")
        try:
            image = Image.open(image_path).convert("RGB")
        except Warning:
            raise ValueError("### Warning: fakenews Image.open")
        W, H = image.size
        image_tensor = self.image_transform(image).unsqueeze(0)  # Add batch dimension
        return W, H, image_tensor.to(self.device)

    def load_text(self, text):
        print("loading text...")
        text_token = self.tokenizer(
            [text],  #模仿批处理
            max_length=128, 
            truncation=True, 
            add_special_tokens=True, 
            return_attention_mask=True, 
            return_token_type_ids=False,
            # return_tensors='pt'
        )
        print("text_token:", text_token)
        text_input = self.text_input_adjust(text_token)
        print("text_input:", text_input)
        return text_input

    def text_input_adjust(self, text_input, fake_word_pos=None):
        # 输入ID适配
        print("text input adjust...")
        input_ids_remove_SEP = [x[:-1] for x in text_input.input_ids]
        maxlen = max([len(x) for x in text_input.input_ids])-1
        input_ids_remove_SEP_pad = [x + [0] * (maxlen - len(x)) for x in input_ids_remove_SEP]
        text_input.input_ids = torch.LongTensor(input_ids_remove_SEP_pad).to(self.device)
        
        # 注意力掩码适配
        attention_mask_remove_SEP = [x[:-1] for x in text_input.attention_mask]
        attention_mask_remove_SEP_pad = [x + [0] * (maxlen - len(x)) for x in attention_mask_remove_SEP]
        text_input.attention_mask = torch.LongTensor(attention_mask_remove_SEP_pad).to(self.device)
        
        return text_input
    
    @torch.no_grad()
    def predict(self, image_path, text):    
        print("predicting...")
        W, H, image = self.load_image(image_path)
        caption = pre_caption(text, self.config['max_words'])
        text_input = self.load_text(caption)
        
        fake_image_box = torch.zeros(1, 4).to(self.device)
        label = ['unknown']
        
        print("predicting...")
        logits_real_fake, logits_multicls, output_coord, logits_tok = self.model(
            image, label, text_input, fake_image_box, None, is_train=False
        )
        print("calculate probability...")
        prob_real_fake = F.softmax(logits_real_fake, dim=1)
        pred_real_fake = prob_real_fake.argmax(1).item() # 选择概率最大的类别
        fake_score = prob_real_fake[0, 1].item() #第一个样本中假新闻概率的分数
        
        # 处理多分类结果
        print("calculating multi-class results...")
        pred_classes = []
        for i, score in enumerate(logits_multicls[0]):
            if score >= 0:  # 大于0的视为阳性
                if i == 0:
                    pred_classes.append("face_swap")
                elif i == 1:
                    pred_classes.append("face_attribute")
                elif i == 2:
                    pred_classes.append("text_swap")
                elif i == 3:
                    pred_classes.append("text_attribute")
        
        # 处理边界框结果
        print("processing bounding box results...")
        boxes = box_ops.box_cxcywh_to_xyxy(output_coord)
        box_coordinates = boxes[0].tolist() #转为python列表
        
        # 处理文本标记结果
        print("processing text token results...")
        logits_tok_reshape = logits_tok.view(-1, 2)
        logits_tok_pred = logits_tok_reshape.argmax(1)
        token_pred = logits_tok_pred.view(text_input.attention_mask[:, 1:].shape)
        
        fake_tokens = []
        for i in range(token_pred.shape[1]):
            if token_pred[0, i] == 1:
                fake_tokens.append(i)
                
        word_ids = text_input.word_ids(0)
        fake_word_indices = set()
        for i in fake_tokens:
            token_idx = i + 1    # 加1是因为我们跳过了CLS token，所以需要调整索引
            if token_idx < len(word_ids) and word_ids[token_idx] is not None:
                fake_word_indices.add(word_ids[token_idx])        
        words = caption.split()
        fake_words = [words[i] for i in fake_word_indices if i < len(words)]
        # 返回结果
        print("returning results...")
        result = {
            "is_fake": bool(pred_real_fake),
            "fake_probability": fake_score,
            "manipulation_types": pred_classes, 
            "fake_image_box": {
                "x1": box_coordinates[0] * W,
                "y1": box_coordinates[1] * H,
                "x2": box_coordinates[2] * W,
                "y2": box_coordinates[3] * H
            },
            "fake_words": fake_words,
            "original_shape": (W, H)
        }
        if result['is_fake']:
            image = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(image)
            box = result['fake_image_box']
            draw.rectangle([box['x1'], box['y1'], box['x2'], box['y2']], outline="red", width=3)
            dir_path = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            file_name, file_ext = os.path.splitext(base_name)
            
            # 创建新文件名 filename_output.ext
            output_filename = f"{file_name}_output{file_ext}"
            output_path = os.path.join(dir_path, output_filename)
            image.save(output_path)
            result["detect_image_path"] = output_path
    
        return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='./configs/test.yaml')
    parser.add_argument('--model_path', default='HAMMER_checkpoint_best.pth')
    parser.add_argument('--image_path', required=True)
    parser.add_argument('--text', required=True)
    
    args = parser.parse_args()
    
    detector = DeepFakeDetector(args.config, args.model_path)
    result = detector.predict(args.image_path, args.text)
    
    print("Detection Result:")
    print(f"Is Fake: {result['is_fake']}")
    print(f"Fake Probability: {result['fake_probability']:.4f}")
    
    if result['is_fake']:
        print(f"Manipulation Types: {', '.join(result['manipulation_types'])}")
        print(f"Fake Image Box: {result['fake_image_box']}")
        if result['fake_words']:
            print(f"Fake Text Words: {result['fake_words']}") 