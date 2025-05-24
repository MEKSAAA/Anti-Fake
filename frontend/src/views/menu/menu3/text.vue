<template>
  <div class="text-optimizer-container">
    <div class="page-title">文本优化</div>
    <div class="page-subtitle">上传文本或直接输入文段进行优化</div>

    <!-- 输入方式选择 -->
    <div class="input-methods">
      <div class="method method-one" :class="{ active: activeMethod === 'input' }" @click="setActiveMethod('input')">
        <div class="method-label">方式一：直接输入</div>
      </div>
      <div class="method method-two" :class="{ active: activeMethod === 'upload' }" @click="setActiveMethod('upload')">
        <div class="method-label">方式二：文件上传</div>
      </div>
    </div>

    <!-- 文本输入区域 -->
    <div class="input-container" v-if="activeMethod === 'input'">
      <div class="input-area" style="display: flex; align-items: flex-start; gap: 12px">
        <el-input v-model="form.text" type="textarea" :rows="8" placeholder="鼠标点击直接输入文字" style="flex: 1" />
        <el-button v-if="form.text" type="danger" @click="clearAll" style="height: 32px; margin-top: 4px">清空</el-button>
      </div>
    </div>

    <!-- 文件上传区域 -->
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
            <el-button type="danger" size="small" @click.stop="clearAll" style="margin-left: 8px">清空</el-button>
          </div>
        </div>
      </el-upload>
    </div>

    <!-- 风格选择区域 -->
    <div class="style-selection" style="position: relative">
      <LoadingAnimation :visible="isGenerating" :percentage="loadingPercentage" :container-mode="true" />
      <div class="style-title">选择优化风格：</div>
      <div class="style-buttons">
        <el-button
          v-for="style in textStyles"
          :key="style.value"
          :type="selectedStyle === style.value ? 'primary' : 'default'"
          @click="selectStyle(style.value)"
        >
          {{ style.label }}
        </el-button>
      </div>
      <div class="generate-button" style="margin-top: 24px; display: flex; justify-content: flex-end">
        <el-button type="primary" @click="optimizeText" :loading="isGenerating" :disabled="!form.text || !selectedStyle">
          优化文本
        </el-button>
      </div>
    </div>

    <!-- 结果展示区域 -->
    <div class="result-container" v-if="generatedContent">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">优化结果</span>
      </div>
      <div class="result-content">
        <div class="result-text">{{ generatedContent }}</div>
        <div class="copy-button">
          <el-button type="success" @click="copyToClipboard">复制内容</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LoadingAnimation from "@/components/LoadingAnimation.vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import mammoth from "mammoth";
import * as pdfjsLib from "pdfjs-dist";
import { onMounted, reactive, ref } from "vue";

// 设置 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

// 创建axios实例
const api = axios.create({
  baseURL: "http://localhost:6006",
  timeout: 100000,
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`
  }
});

const userInfoStore = useUserInfoStore();

// 状态变量
const activeMethod = ref("input");
const selectedStyle = ref("");
const isGenerating = ref(false);
const generatedContent = ref("");
const uploadFile = ref<File | null>(null);
const stylesLoading = ref(false);
const loadingPercentage = ref(0);
let loadingInterval;

// 文本优化风格
const textStyles = ref<
  Array<{
    label: string;
    value: string;
    description: string;
  }>
>([]);

// 表单数据
const form = reactive({
  text: ""
});

// 获取文本风格列表
const fetchTextStyles = async () => {
  stylesLoading.value = true;
  try {
    const response = await api.get("/text_optimization/styles");
    if (response.data.success) {
      textStyles.value = response.data.data.map((item: any) => ({
        label: item.description,
        value: item.value,
        description: item.description
      }));
    } else {
      ElMessage.error(response.data.message || "获取文本风格失败");
    }
  } catch (error) {
    console.error("获取文本风格失败:", error);
    ElMessage.error("获取文本风格失败，请重试");
  } finally {
    stylesLoading.value = false;
  }
};

// 组件挂载时获取文本风格
onMounted(() => {
  fetchTextStyles();
});

const setActiveMethod = (method: string) => {
  activeMethod.value = method;
  form.text = "";
  uploadFile.value = null;
};

const selectStyle = (style: string) => {
  selectedStyle.value = style;
  generatedContent.value = "";
};

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    uploadFile.value = file.raw;
  }
};

// 解析PDF文件
const parsePDF = async (file: File): Promise<string> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = "";

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map((item: any) => item.str).join(" ");
      fullText += pageText + "\n";
    }

    return fullText;
  } catch (error) {
    console.error("PDF解析错误:", error);
    throw new Error("PDF文件解析失败");
  }
};

// 解析Word文件
const parseWord = async (file: File): Promise<string> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value;
  } catch (error) {
    console.error("Word解析错误:", error);
    throw new Error("Word文件解析失败");
  }
};

const submitUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  try {
    if (uploadFile.value.type === "text/plain") {
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        if (!e.target?.result) return;
        form.text = e.target.result as string;
        ElMessage.success("文件上传成功");
      };
      reader.readAsText(uploadFile.value);
    } else if (uploadFile.value.type === "application/pdf") {
      try {
        const text = await parsePDF(uploadFile.value);
        form.text = text;
        ElMessage.success("PDF文件解析成功");
      } catch (error) {
        ElMessage.error("PDF文件解析失败，请重试");
        clearAll();
      }
    } else if (
      uploadFile.value.type === "application/msword" ||
      uploadFile.value.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ) {
      try {
        const text = await parseWord(uploadFile.value);
        form.text = text;
        ElMessage.success("Word文件解析成功");
      } catch (error) {
        ElMessage.error("Word文件解析失败，请重试");
        clearAll();
      }
    } else {
      ElMessage.warning("请上传txt、PDF或Word格式的文件");
      clearAll();
    }
  } catch (error) {
    ElMessage.error("文件上传失败，请重试");
    console.error("上传文件错误:", error);
  }
};

const clearAll = () => {
  form.text = "";
  selectedStyle.value = "";
  generatedContent.value = "";
  uploadFile.value = null;
};

const optimizeText = async () => {
  if (!form.text) {
    ElMessage.warning("请先输入或上传文本");
    return;
  }
  if (!selectedStyle.value) {
    ElMessage.warning("请选择优化风格");
    return;
  }

  isGenerating.value = true;
  loadingPercentage.value = 0;

  // 启动进度条动画
  loadingInterval = setInterval(() => {
    if (loadingPercentage.value < 90) {
      loadingPercentage.value += Math.random() * 10;
    }
  }, 500);

  try {
    const formData = new FormData();
    formData.append("user_id", userInfoStore.user_id);
    formData.append("text", form.text);
    formData.append("style", selectedStyle.value);

    const response = await api.post("/text_optimization/optimize", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });

    if (response.data.success) {
      loadingPercentage.value = 100;
      generatedContent.value = response.data.data.optimized_text;
      ElMessage.success("文本优化成功");
    } else {
      ElMessage.error(response.data.message || "文本优化失败");
    }
  } catch (error) {
    console.error("优化错误:", error);
    ElMessage.error("优化失败，请重试");
  } finally {
    clearInterval(loadingInterval);
    isGenerating.value = false;
  }
};

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(generatedContent.value);
    ElMessage.success("复制成功");
  } catch (error) {
    ElMessage.error("复制失败，请手动复制");
  }
};
</script>

<style scoped>
@font-face {
  font-family: "MiSans";
  src: url("@/assets/fonts/MiSans-Regular.ttf") format("truetype");
}

.text-optimizer-container {
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

.method.active {
  background-color: #e0f3f3;
}

.method.active .method-label {
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

.style-selection {
  margin: 20px 0;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.style-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #333;
}

.style-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.result-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-top: 20px;
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
  padding: 15px;
}

.result-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.copy-button {
  display: flex;
  justify-content: flex-end;
}
</style>
