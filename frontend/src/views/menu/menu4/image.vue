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
      <div class="options-area">
        <div class="option-group">
          <span class="option-label">图片风格：</span>
          <el-select v-model="form.style" placeholder="请选择图片风格" :loading="stylesLoading">
            <el-option v-for="style in styleOptions" :key="style.value" :label="style.name" :value="style.value">
              <span>{{ style.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">{{ style.description }}</span>
            </el-option>
          </el-select>
        </div>
        <div class="option-group">
          <span class="option-label">图片尺寸：</span>
          <el-input-number v-model="form.width" :min="256" :max="2048" :step="64" placeholder="宽度" />
          <span class="size-separator">×</span>
          <el-input-number v-model="form.height" :min="256" :max="2048" :step="64" placeholder="高度" />
        </div>
        <div class="option-group">
          <span class="option-label">生成数量：</span>
          <el-input-number v-model="form.count" :min="1" :max="4" :step="1" />
        </div>
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
      <div class="options-area">
        <div class="option-group">
          <span class="option-label">图片风格：</span>
          <el-select v-model="form.style" placeholder="请选择图片风格" :loading="stylesLoading">
            <el-option v-for="style in styleOptions" :key="style.value" :label="style.name" :value="style.value">
              <span>{{ style.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">{{ style.description }}</span>
            </el-option>
          </el-select>
        </div>
        <div class="option-group">
          <span class="option-label">图片尺寸：</span>
          <el-input-number v-model="form.width" :min="256" :max="2048" :step="64" placeholder="宽度" />
          <span class="size-separator">×</span>
          <el-input-number v-model="form.height" :min="256" :max="2048" :step="64" placeholder="高度" />
        </div>
        <div class="option-group">
          <span class="option-label">生成数量：</span>
          <el-input-number v-model="form.count" :min="1" :max="4" :step="1" />
        </div>
      </div>
    </div>

    <div class="result-container" style="position: relative">
      <LoadingAnimation :visible="isLoading" :percentage="loadingPercentage" :container-mode="true" />
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">AI生成结果</span>
      </div>
      <div class="result-content">
        <div v-if="!generatedImages.length" class="no-content">还未生成图片！</div>
        <div v-else class="images-grid">
          <div v-for="(image, index) in generatedImages" :key="index" class="image-item">
            <img :src="image.url" class="generated-image" />
            <div class="image-info">
              <p class="prompt-info"><strong>原始提示词:</strong> {{ image.orig_prompt }}</p>
              <p class="prompt-info"><strong>实际提示词:</strong> {{ image.actual_prompt }}</p>
            </div>
            <div class="image-actions">
              <el-button type="primary" @click="downloadImage(image, index)" size="small">下载图片</el-button>
            </div>
          </div>
        </div>
      </div>
      <div class="action-button">
        <el-button class="clear-btn" @click="clearAll" :disabled="isLoading">清空</el-button>
        <el-button class="generate-btn" @click="generateImage" :disabled="isLoading">
          {{ isLoading ? "正在生成中..." : "生成图片" }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="textToImage">
import LoadingAnimation from "@/components/LoadingAnimation.vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";

// 修改 axios 实例配置，移除 token 相关配置
const api = axios.create({
  baseURL: "http://localhost:6006",
  timeout: 100000
});

// 移除请求拦截器中的 token 配置
api.interceptors.request.use(config => {
  return config;
});

// 修改响应拦截器，简化错误处理
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 400:
          ElMessage.error("请求参数错误，请检查输入");
          break;
        default:
          ElMessage.error("生成失败，请重试");
      }
    } else {
      ElMessage.error("网络错误，请检查网络连接");
    }
    return Promise.reject(error);
  }
);

// 用户信息store
const userInfoStore = useUserInfoStore();

// 风格选项
const styleOptions = ref<Array<{ value: string; name: string; description: string }>>([]);
const stylesLoading = ref(false);

const activeMethod = ref("input");
const form = reactive({
  text: "",
  style: "realistic",
  width: 1024,
  height: 1024,
  count: 1
});
const uploadFile = ref<File | null>(null);
const generatedImages = ref<Array<{ url: string; orig_prompt: string; actual_prompt: string }>>([]);
const isLoading = ref(false);
const loadingPercentage = ref(0);
let loadingInterval;

// 获取风格选项
const fetchStyles = async () => {
  try {
    stylesLoading.value = true;
    const response = await api.get("/image_generation/styles");
    if (response.data.success) {
      styleOptions.value = response.data.data;
      // 如果当前选择的风格不在新的选项中，设置为第一个选项
      if (styleOptions.value.length > 0 && !styleOptions.value.find(s => s.value === form.style)) {
        form.style = styleOptions.value[0].value;
      }
    }
  } catch (error) {
    console.error("获取风格选项失败:", error);
    ElMessage.error("获取风格选项失败");
  } finally {
    stylesLoading.value = false;
  }
};

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
        // 上传成功后自动生成图片
        generateImage();
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
    ElMessage.warning("请输入图片描述文字");
    return;
  }

  if (!userInfoStore.user_id) {
    ElMessage.warning("请先登录");
    return;
  }

  isLoading.value = true;
  loadingPercentage.value = 0;
  generatedImages.value = [];

  // 启动进度条动画
  loadingInterval = setInterval(() => {
    if (loadingPercentage.value < 90) {
      loadingPercentage.value += Math.random() * 10;
    }
  }, 500);

  try {
    const formData = new FormData();
    formData.append("content", form.text);
    formData.append("user_id", userInfoStore.user_id);
    formData.append("size", `${form.width}*${form.height}`);
    formData.append("num_images", form.count.toString());
    formData.append("style", form.style);

    const response = await api.post("/image_generation/generate", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });

    if (response.data.success) {
      loadingPercentage.value = 100;
      generatedImages.value = response.data.data.images || [];
      ElMessage.success("图片生成成功");
    } else {
      ElMessage.error(response.data.message || "生成失败");
    }
  } catch (error: any) {
    console.error("生成图片错误:", error);
    if (error.response) {
      switch (error.response.status) {
        case 400:
          ElMessage.error("请求参数错误，请检查输入");
          break;
        default:
          ElMessage.error("生成失败，请重试");
      }
    } else {
      ElMessage.error("网络错误，请检查网络连接");
    }
  } finally {
    clearInterval(loadingInterval);
    isLoading.value = false;
  }
};

const downloadImage = (image: { url: string; orig_prompt: string; actual_prompt: string }, index: number) => {
  if (!image.url) return;

  const link = document.createElement("a");
  link.href = image.url;
  link.download = `generated-image-${index + 1}-${Date.now()}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const clearAll = () => {
  form.text = "";
  form.style = "realistic";
  form.width = 1024;
  form.height = 1024;
  form.count = 1;
  uploadFile.value = null;
  generatedImages.value = [];
  ElMessage.success("已清空所有内容");
};

// 组件挂载时获取风格选项
onMounted(() => {
  fetchStyles();
});
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

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  width: 100%;
}

.image-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.generated-image {
  width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.image-info {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin: 10px 0;

  .prompt-info {
    margin: 5px 0;
    font-size: 12px;
    color: #606266;
    word-break: break-all;

    strong {
      color: #303133;
    }
  }
}

.image-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}

.clear-btn {
  background-color: #f56c6c;
  color: white;
  padding: 12px 40px;
  border: none;
  border-radius: 4px;
  min-width: 120px;

  &:hover {
    background-color: #e64242;
  }

  &:disabled {
    background-color: #c0c4cc;
    color: #fff;
    cursor: not-allowed;
  }
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

.options-area {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.option-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;

  &:last-child {
    margin-bottom: 0;
  }
}

.option-label {
  width: 80px;
  color: #606266;
  font-size: 14px;
}

.size-separator {
  margin: 0 10px;
  color: #909399;
}
</style>
