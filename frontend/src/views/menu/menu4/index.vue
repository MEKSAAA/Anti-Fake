<template>
  <div class="text-to-image-container">
    <div class="page-title">文生图</div>
    <div class="page-subtitle">输入文字描述，AI将为您生成图片</div>

    <div class="input-methods">
      <div class="method method-one" :class="{ active: activeMethod === 'input' }" @click="setActiveMethod('input')">
        <div class="method-label">方式一：直接输入</div>
      </div>
      <div class="method method-two" :class="{ active: activeMethod === 'upload' }" @click="setActiveMethod('upload')">
        <div class="method-label">方式二：上传文件</div>
      </div>
    </div>

    <div class="input-container" v-if="activeMethod === 'input'">
      <div class="input-area">
        <el-input v-model="form.text" type="textarea" :rows="8" placeholder="请输入图片描述文字" />
      </div>
    </div>

    <div class="upload-container" v-if="activeMethod === 'upload'">
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept=".txt,.doc,.docx"
        class="upload-area"
      >
        <div class="upload-content">
          <img src="@/assets/icons/upload.svg" class="upload-icon" />
          <div class="upload-text">点击选择文件上传</div>
          <div v-if="uploadFile" class="file-info">
            <span>已选择文件: {{ uploadFile.name }}</span>
            <el-button type="primary" size="small" @click.stop="submitUpload">上传</el-button>
          </div>
        </div>
      </el-upload>
    </div>

    <div class="result-container">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">AI生成结果</span>
      </div>
      <div class="result-content">
        <div v-if="!generatedImage" class="no-content">还未生成图片！</div>
        <div v-else class="image-result">
          <img :src="generatedImage" class="generated-image" />
          <div class="image-actions">
            <el-button type="primary" @click="downloadImage" :disabled="!generatedImage">下载图片</el-button>
          </div>
        </div>
      </div>
      <div class="action-button">
        <el-button class="generate-btn" @click="generateImage" :disabled="isLoading">
          {{ isLoading ? "正在生成中..." : "生成图片" }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="textToImage">
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

// 模拟图片URL
const MOCK_IMAGE_URL = "https://picsum.photos/800/600";

const activeMethod = ref("input");
const form = reactive({
  text: ""
});
const uploadFile = ref<File | null>(null);
const generatedImage = ref("");
const isLoading = ref(false);

const setActiveMethod = (method: string) => {
  activeMethod.value = method;
};

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    uploadFile.value = file.raw;
  }
};

const submitUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  try {
    const reader = new FileReader();
    reader.onload = (e: ProgressEvent<FileReader>) => {
      const result = e.target?.result;
      if (typeof result === "string") {
        form.text = result;
        ElMessage.success("文件上传成功");
      }
    };
    reader.readAsText(uploadFile.value);
  } catch (error) {
    ElMessage.error("文件上传失败，请重试");
    console.error("上传文件错误:", error);
  }
};

const generateImage = async () => {
  if (!form.text) {
    ElMessage.warning("请先输入或上传文本");
    return;
  }

  isLoading.value = true;
  generatedImage.value = "";

  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 使用模拟图片URL
    generatedImage.value = MOCK_IMAGE_URL;
    ElMessage.success("图片生成成功");
  } catch (error) {
    console.error("生成图片错误:", error);
    ElMessage.error("生成失败，请重试");
  } finally {
    isLoading.value = false;
  }
};

const downloadImage = () => {
  if (!generatedImage.value) return;

  const link = document.createElement("a");
  link.href = generatedImage.value;
  link.download = `generated-image-${Date.now()}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
</script>

<style scoped lang="scss">
.text-to-image-container {
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

.input-methods {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.method {
  padding: 8px 20px;
  border-radius: 20px;
  cursor: pointer;
  background-color: #f5f5f5;
  transition: all 0.3s ease;

  .method-label {
    color: #909399;
    transition: all 0.3s ease;
  }

  &:hover {
    background-color: #e0f3f3;
    .method-label {
      color: #54bcbd;
    }
  }

  &.active {
    background-color: #e0f3f3;
    .method-label {
      color: #54bcbd;
    }
  }
}

.input-area,
.upload-area {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
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
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-content {
  color: #909399;
  font-size: 16px;
}

.image-result {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.generated-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.image-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.generate-btn {
  background-color: #54bcbd;
  color: white;
  padding: 12px 40px;
  border: none;
  border-radius: 4px;
  min-width: 120px;

  &:hover {
    background-color: #48a5a6;
  }

  &:disabled {
    background-color: #c0c4cc;
    color: #fff;
    cursor: not-allowed;
  }
}
</style>
