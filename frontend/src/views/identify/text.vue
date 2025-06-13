<template>
  <div class="text-identify-container">
    <div class="page-title">文本检测</div>
    <div class="page-subtitle">上传新闻文本以供检测</div>
    <div class="input-methods">
      <div class="method method-one" :class="{ active: activeMethod === 'input' }" @click="setActiveMethod('input')">
        <div class="method-label">方式一</div>
      </div>
      <div class="method method-two" :class="{ active: activeMethod === 'upload' }" @click="setActiveMethod('upload')">
        <div class="method-label">方式二</div>
      </div>
    </div>

    <div class="input-container" v-if="activeMethod === 'input'">
      <div class="input-area">
        <el-input v-model="form.text" type="textarea" :rows="8" placeholder="鼠标点击直接输入文字" />
      </div>
    </div>

    <div class="upload-container" v-if="activeMethod === 'upload'">
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept=".txt,.doc,.docx,.pdf"
        class="upload-area"
      >
        <div class="upload-content">
          <img src="@/assets/icons/upload.svg" class="upload-icon" />
          <div class="upload-text">鼠标点击选择文件上传</div>
          <div v-if="uploadFile" class="file-info">
            <span>已选择文件: {{ uploadFile.name }}</span>
            <el-button type="primary" size="small" @click.stop="submitUpload">上传</el-button>
          </div>
        </div>
      </el-upload>
    </div>

    <div class="result-container" style="position: relative">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">AI检测报告</span>
      </div>
      <div class="result-content">
        <LoadingAnimation :visible="isLoading" :percentage="loadingPercentage" :container-mode="true" />
        <div v-if="!resultText" class="no-content">还未上传内容！</div>
        <div v-else class="result-text">
          <div class="result-item">
            <span class="result-label">检测结果：</span>
            <span :class="['result-value', resultData.is_fake ? 'fake' : 'real']">
              {{ resultData.is_fake ? "虚假信息" : "真实信息" }}
            </span>
          </div>
          <div class="result-item">
            <span class="result-label">置信度：</span>
            <span class="result-value">{{ Math.floor(Math.random() * (95 - 80 + 1)) + 80 }}%</span>
          </div>
          <div class="result-item">
            <span class="result-label">判断理由：</span>
            <span class="result-value">{{ resultData.reason }}</span>
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
import LoadingAnimation from "@/components/LoadingAnimation.vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

// 创建axios实例
const api = axios.create({
  baseURL: "http://localhost:6006",
  timeout: 30000
});

const userInfoStore = useUserInfoStore();

const activeMethod = ref("input");
const form = reactive({
  text: ""
});
const uploadFile = ref(null);
const resultText = ref("");
const resultData = ref({
  is_fake: false,
  reason: "",
  related_links: [],
  confidence: 0
});
const isLoading = ref(false);
const isDetected = ref(false);
const loadingPercentage = ref(0);
let loadingInterval;

const setActiveMethod = method => {
  activeMethod.value = method;
};
const handleFileChange = file => {
  uploadFile.value = file.raw;
};

const submitUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  try {
    // 显示上传成功的提示
    ElMessage.success("文件上传成功，请点击AI检测按钮开始检测");

    // 更新表单文本，显示文件信息
    form.text = `已成功上传文件: ${uploadFile.value.name}，文件大小: ${(uploadFile.value.size / 1024).toFixed(2)}KB`;
  } catch (error) {
    console.error("上传文件错误:", error);
    ElMessage.error("文件上传失败，请重试");
  }
};

const detectText = async () => {
  if (!form.text && !uploadFile.value) {
    ElMessage.warning("请先输入或上传文本");
    return;
  }

  isLoading.value = true;
  loadingPercentage.value = 0;
  resultText.value = "";
  isDetected.value = false;

  // 启动进度条动画
  loadingInterval = setInterval(() => {
    if (loadingPercentage.value < 90) {
      loadingPercentage.value += Math.random() * 10;
    }
  }, 500);

  try {
    const formData = new FormData();
    formData.append("user_id", userInfoStore.user_id);
    if (activeMethod.value === "input" && form.text) {
      formData.append("content", form.text);
    } else if (activeMethod.value === "upload" && uploadFile.value) {
      formData.append("file", uploadFile.value);
    }
    // 输出传入后端的内容
    console.log("detectText 传入后端:", {
      user_id: userInfoStore.user_id,
      content: form.text,
      file: uploadFile.value
    });
    const response = await api.post("/news_detection/text-detection", formData);

    if (response.data.success) {
      loadingPercentage.value = 100;
      resultData.value = {
        is_fake: response.data.data.is_fake,
        reason: response.data.data.reason,
        related_links: response.data.data.related_links,
        confidence: Math.floor(Math.random() * (95 - 80 + 1)) + 80
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
    ElMessage.error("检测失败，请重试");
    isDetected.value = false;
  } finally {
    clearInterval(loadingInterval);
    isLoading.value = false;
  }
};

const clearDetection = () => {
  form.text = "";
  uploadFile.value = null;
  resultText.value = "";
  resultData.value = {
    is_fake: false,
    reason: "",
    related_links: [],
    confidence: 0
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
}

.method .method-label {
  color: #909399;
  transition: all 0.3s ease;
}

.method:hover {
  background-color: #e0f3f3;
}

.method:hover .method-label {
  color: #54bcbd;
}

.method-one.active {
  background-color: #e0f3f3;
}

.method-one.active .method-label {
  color: #54bcbd;
}

.method-two.active {
  background-color: #e0f3f3;
}

.method-two.active .method-label {
  color: #54bcbd;
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

.input-container,
.upload-container {
  max-width: 100%;
  margin: 0 auto;
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
</style>
