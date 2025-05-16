<template>
  <div class="text-identify-container">
    <div class="page-title">多模态检测</div>
    <div class="page-subtitle">上传新闻文本和图片以供检测</div>

    <div class="input-container">
      <div class="input-area left">
        <div class="input-title">文本输入</div>
        <el-input v-model="form.text" type="textarea" :rows="8" placeholder="请输入新闻文本内容" />
      </div>
      <div class="input-area right">
        <div class="input-title">图片上传</div>
        <el-upload
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          accept="image/*"
          class="upload-area"
        >
          <div class="upload-content">
            <template v-if="!imagePreview">
              <img src="@/assets/icons/upload.svg" class="upload-icon" />
              <div class="upload-text">点击或拖拽图片到此处上传</div>
            </template>
            <template v-else>
              <img :src="imagePreview" class="preview-image" />
            </template>
            <div v-if="uploadFile" class="file-info">
              <span>已选择文件: {{ uploadFile.name }}</span>
              <el-button type="primary" size="small" @click.stop="submitUpload">上传</el-button>
            </div>
          </div>
        </el-upload>
      </div>
    </div>

    <div class="result-container">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">AI检测报告</span>
      </div>
      <div class="result-content">
        <div v-if="!resultText" class="no-content">还未上传内容！</div>
        <div v-else class="result-text">
          <div class="result-item">
            <span class="result-label">检测结果：</span>
            <span :class="['result-value', resultData.is_fake ? 'fake' : 'real']">
              {{ resultData.is_fake ? "虚假信息" : "真实信息" }}
            </span>
          </div>
          <div v-if="resultData.is_fake" class="result-item">
            <span class="result-label">判断理由：</span>
            <span class="result-value">{{ resultData.reason }}</span>
          </div>
          <div v-if="resultData.fake_probability > 0" class="result-item">
            <span class="result-label">虚假概率：</span>
            <span class="result-value">{{ (resultData.fake_probability * 100).toFixed(2) }}%</span>
          </div>
          <div v-if="resultData.manipulation_types && resultData.manipulation_types.length > 0" class="result-item">
            <span class="result-label">篡改类型：</span>
            <span class="result-value">{{ resultData.manipulation_types.join(", ") }}</span>
          </div>
          <div v-if="resultData.fake_words && resultData.fake_words.length > 0" class="result-item">
            <span class="result-label">可疑词语：</span>
            <span class="result-value">{{ resultData.fake_words.join(", ") }}</span>
          </div>
          <div v-if="resultData.related_links && resultData.related_links.length > 0" class="result-item">
            <span class="result-label">相关链接：</span>
            <div class="related-links">
              <a v-for="(link, index) in resultData.related_links" :key="index" :href="link" target="_blank" class="link-item">
                {{ link }}
              </a>
            </div>
          </div>
        </div>
      </div>
      <div class="action-button">
        <el-button class="ai-detect-btn" @click="isDetected ? clearDetection() : detectText()" :disabled="isLoading">
          {{ isLoading ? "正在检测中..." : isDetected ? "清空检测结果以重新检测" : "AI检测" }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

// 创建axios实例
const api = axios.create({
  baseURL: "http://localhost:6006",
  timeout: 100000,
  headers: {
    "Content-Type": "multipart/form-data"
  }
});

const userInfoStore = useUserInfoStore();

const form = reactive({
  text: ""
});
const uploadFile = ref(null);
const imagePreview = ref(null);
const resultText = ref("");
const resultData = ref({
  is_fake: false,
  reason: "",
  related_links: [],
  detect_image_path: "",
  fake_image_box: {
    x1: 0,
    x2: 0,
    y1: 0,
    y2: 0
  },
  fake_probability: 0,
  fake_words: [],
  manipulation_types: [],
  original_shape: []
});
const isLoading = ref(false);
const isDetected = ref(false);

const handleFileChange = file => {
  uploadFile.value = file.raw;
  // 创建图片预览
  const reader = new FileReader();
  reader.onload = e => {
    imagePreview.value = e.target.result;
  };
  reader.readAsDataURL(file.raw);
};

const submitUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  if (!uploadFile.value.type.startsWith("image/")) {
    ElMessage.warning("请上传图片文件");
    uploadFile.value = null;
    return;
  }

  ElMessage.success("图片上传成功");
};

const detectText = async () => {
  if (!form.text) {
    ElMessage.warning("请输入新闻文本内容");
    return;
  }

  if (!uploadFile.value) {
    ElMessage.warning("请上传图片");
    return;
  }

  isLoading.value = true;
  resultText.value = "";
  isDetected.value = false;

  try {
    const formData = new FormData();
    formData.append("user_id", userInfoStore.user_id);
    formData.append("content", form.text);
    formData.append("image", uploadFile.value, uploadFile.value.name);

    // 输出传入后端的内容
    console.log("detectText 传入后端:", {
      user_id: userInfoStore.user_id,
      content: form.text,
      image: uploadFile.value
    });

    const response = await api.post("/news_detection/image-detection", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });

    if (response.data.success) {
      resultData.value = {
        is_fake: response.data.data.is_fake,
        reason: response.data.data.detection_reason || "",
        related_links: response.data.data.related_news_links || [],
        detect_image_path: response.data.data.detect_image_path || "",
        fake_image_box: response.data.data.fake_image_box || {
          x1: 0,
          x2: 0,
          y1: 0,
          y2: 0
        },
        fake_probability: response.data.data.fake_probability || 0,
        fake_words: response.data.data.fake_words || [],
        manipulation_types: response.data.data.manipulation_types || [],
        original_shape: response.data.data.original_shape || []
      };
      resultText.value = "检测完成";
      isDetected.value = true;
      ElMessage.success("检测完成");
    } else {
      ElMessage.error(response.data.message || "检测失败");
      isDetected.value = false;
    }
  } catch (error) {
    console.error("检测错误:", error);
    if (error.response) {
      console.error("错误响应:", error.response.data);
      ElMessage.error(`检测失败: ${error.response.data.message || "服务器内部错误"}`);
    } else if (error.request) {
      console.error("请求错误:", error.request);
      ElMessage.error("网络请求失败，请检查网络连接");
    } else {
      ElMessage.error("检测失败，请重试");
    }
    isDetected.value = false;
  } finally {
    isLoading.value = false;
  }
};

const clearDetection = () => {
  form.text = "";
  uploadFile.value = null;
  imagePreview.value = null;
  resultText.value = "";
  resultData.value = {
    is_fake: false,
    reason: "",
    related_links: [],
    detect_image_path: "",
    fake_image_box: {
      x1: 0,
      x2: 0,
      y1: 0,
      y2: 0
    },
    fake_probability: 0,
    fake_words: [],
    manipulation_types: [],
    original_shape: []
  };
  isDetected.value = false;
  ElMessage.success("已清空检测结果");
};
</script>

<style scoped>
@font-face {
  font-family: "MiSans";
  src: url("@/assets/fonts/MiSans-Regular.ttf") format("truetype");
}

.text-identify-container {
  padding: 20px;
  font-family: "MiSans", sans-serif;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.input-container {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.input-area {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.input-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  cursor: pointer;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.upload-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

.upload-text {
  color: #909399;
  margin-bottom: 10px;
}

.file-info {
  margin-top: 10px;
  text-align: center;
  color: #54bcbd;
}

.result-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.result-icon {
  width: 24px;
  height: 24px;
  margin-right: 8px;
}

.result-title {
  font-size: 18px;
  font-weight: bold;
}

.result-content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-content {
  color: #909399;
  font-size: 16px;
}

.result-text {
  padding: 15px;
  width: 100%;
  font-size: 14px;
  line-height: 1.6;
}

.action-button {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.ai-detect-btn {
  background-color: #54bcbd;
  color: white;
  padding: 12px 40px;
  border: none;
  border-radius: 4px;
  min-width: 120px;
}

.ai-detect-btn:hover {
  background-color: #48a5a6;
}

.ai-detect-btn:disabled {
  background-color: #c0c4cc;
  color: #fff;
  cursor: not-allowed;
}

.result-item {
  margin-bottom: 15px;
}

.result-label {
  font-weight: bold;
  color: #333;
  margin-right: 10px;
}

.result-value {
  color: #666;
}

.result-value.fake {
  color: #f56c6c;
}

.result-value.real {
  color: #67c23a;
}

.related-links {
  margin-top: 10px;
}

.link-item {
  display: block;
  color: #54bcbd;
  text-decoration: none;
  margin-bottom: 5px;
  word-break: break-all;
}

.link-item:hover {
  text-decoration: underline;
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  margin-bottom: 10px;
}
</style>
