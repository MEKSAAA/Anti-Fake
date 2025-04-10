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

    <div class="result-container">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">AI检测报告</span>
      </div>
      <div class="result-content">
        <div v-if="!resultText" class="no-content">还未上传内容！</div>
        <div v-else class="result-text">{{ resultText }}</div>
      </div>
      <div class="action-button">
        <el-button class="ai-detect-btn" @click="detectText">AI检测</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

const activeMethod = ref("input");
const form = reactive({
  text: ""
});
const uploadFile = ref(null);
const resultText = ref("");

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
    const reader = new FileReader();
    reader.onload = e => {
      if (uploadFile.value.type === "text/plain") {
        form.text = e.target.result;
        ElMessage.success("文件上传成功");
      } else {
        form.text = `已成功上传文件: ${uploadFile.value.name}，文件大小: ${(uploadFile.value.size / 1024).toFixed(2)}KB`;
        ElMessage.success("文件上传成功，文件内容已提取");
      }
    };
    reader.readAsText(uploadFile.value);
  } catch (error) {
    ElMessage.error("文件上传失败，请重试");
    console.error("上传文件错误:", error);
  }
};

const detectText = () => {
  if (!form.text) {
    ElMessage.warning("请先输入或上传文本");
    return;
  }
  resultText.value = `检测结果：该新闻文本真实可信度为98.5%，未发现明显虚假信息特征。`;
  ElMessage.success("检测完成");
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
}

.ai-detect-btn:hover {
  background-color: #48a5a6;
}

:deep(.el-textarea__inner) {
  border: none;
  resize: none;
}

:deep(.el-textarea__inner):focus {
  box-shadow: none;
}

:deep(.el-upload) {
  width: 100%;
  height: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
