<template>
  <div class="news-processor-container">
    <div class="page-title">新闻处理</div>
    <div class="page-subtitle">上传新闻文本或直接输入文段</div>

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

    <!-- 功能选择区域 -->
    <div class="function-selection">
      <div class="function-title">选择处理功能：</div>
      <div class="function-buttons">
        <el-button :type="activeFunction === 'summary' ? 'primary' : 'default'" @click="setActiveFunction('summary')">
          新闻概要生成
        </el-button>
        <el-button :type="activeFunction === 'title' ? 'primary' : 'default'" @click="setActiveFunction('title')">
          新闻标题生成
        </el-button>
      </div>
    </div>

    <!-- 风格选择区域 -->
    <div class="style-selection">
      <div class="style-title">选择生成风格：</div>
      <div class="style-buttons">
        <template v-if="activeFunction === 'summary'">
          <el-button
            v-for="style in summaryTypes"
            :key="style.value"
            :type="selectedStyle === style.value ? 'primary' : 'default'"
            @click="selectStyle(style.value)"
            :loading="summaryTypesLoading"
          >
            {{ style.label }}
          </el-button>
        </template>
        <template v-else>
          <el-button
            v-for="style in titleStyles"
            :key="style.value"
            :type="selectedStyle === style.value ? 'primary' : 'default'"
            @click="selectStyle(style.value)"
            :loading="titleStylesLoading"
          >
            {{ style.label }}
          </el-button>
        </template>
      </div>
      <div class="generate-button" style="margin-top: 24px; display: flex; justify-content: flex-end;">
        <el-button type="primary" @click="generateContent" :loading="isGenerating" :disabled="!form.text || !selectedStyle">
          {{ activeFunction === "summary" ? "生成概要" : "生成标题" }}
        </el-button>
      </div>
    </div>

    <!-- 结果展示区域 -->
    <div class="result-container" v-if="generatedContent">
      <div class="result-header">
        <img src="@/assets/icons/ai-report.svg" class="result-icon" />
        <span class="result-title">生成结果</span>
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

<script setup>
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

// 创建axios实例
const api = axios.create({
  baseURL: "http://localhost:6006",
  timeout: 100000
});

const userInfoStore = useUserInfoStore();

// 状态变量
const activeMethod = ref("input");
const activeFunction = ref("");
const selectedStyle = ref("");
const isGenerating = ref(false);
const generatedContent = ref("");
const uploadFile = ref(null);
const isGenerated = ref(false);

// 标题风格动态获取
const titleStyles = ref([]);
const titleStylesLoading = ref(false);

// 概要风格动态获取
const summaryTypes = ref([]);
const summaryTypesLoading = ref(false);

// 确保form对象在使用前被正确初始化
const form = reactive({
  text: ""
});

const setActiveMethod = method => {
  activeMethod.value = method;
  // 切换方法时清空文本
  form.text = "";
  uploadFile.value = null;
};

const setActiveFunction = async functionType => {
  activeFunction.value = functionType;
  selectedStyle.value = "";
  generatedContent.value = "";
  if (functionType === "title") {
    titleStylesLoading.value = true;
    try {
      const res = await api.get("/news_title/styles");
      console.log("标题风格后端返回：", res.data);
      if (res.data.success && Array.isArray(res.data.data)) {
        titleStyles.value = res.data.data.map(item => ({
          label: item.description,
          value: item.value,
          name: item.name
        }));
      } else {
        titleStyles.value = [];
        ElMessage.error(res.data.message || "获取标题风格失败");
      }
    } catch (e) {
      titleStyles.value = [];
      ElMessage.error("获取标题风格失败");
    } finally {
      titleStylesLoading.value = false;
    }
  } else if (functionType === "summary") {
    summaryTypesLoading.value = true;
    try {
      const res = await api.get("/news_summary/types");
      console.log("概要风格后端返回：", res.data);
      if (res.data.success && Array.isArray(res.data.data)) {
        summaryTypes.value = res.data.data.map(item => ({
          label: item.description,
          value: item.value,
          name: item.name
        }));
      } else {
        summaryTypes.value = [];
        ElMessage.error(res.data.message || "获取概要风格失败");
      }
    } catch (e) {
      summaryTypes.value = [];
      ElMessage.error("获取概要风格失败");
    } finally {
      summaryTypesLoading.value = false;
    }
  }
};

const selectStyle = style => {
  selectedStyle.value = style;
  generatedContent.value = "";
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

const clearAll = () => {
  form.text = "";
  selectedStyle.value = "";
  generatedContent.value = "";
  isGenerated.value = false;
  uploadFile.value = null;
};

const generateContent = async () => {
  if (!form.text) {
    ElMessage.warning("请先输入或上传文本");
    return;
  }
  if (!selectedStyle.value) {
    ElMessage.warning("请选择生成风格");
    return;
  }
  isGenerating.value = true;
  // 输出传入后端的内容
  if (activeFunction.value === "title") {
    console.log("generateContent 传入后端:", {
      user_id: userInfoStore.user_id,
      content: form.text,
      style: selectedStyle.value
    });
  } else if (activeFunction.value === "summary") {
    console.log("generateContent 传入后端:", {
      user_id: userInfoStore.user_id,
      content: form.text,
      summary_type: selectedStyle.value
    });
  }
  try {
    if (activeFunction.value === "title") {
      const formData = new FormData();
      formData.append("user_id", userInfoStore.user_id);
      formData.append("content", form.text);
      formData.append("style", selectedStyle.value);
      const response = await api.post("/news_title/generate", formData);
      if (response.data.success) {
        generatedContent.value = response.data.data.title;
        ElMessage.success("标题生成成功");
        isGenerated.value = true;
      } else {
        ElMessage.error(response.data.message || "标题生成失败");
      }
    } else if (activeFunction.value === "summary") {
      const formData = new FormData();
      formData.append("user_id", userInfoStore.user_id);
      formData.append("content", form.text);
      formData.append("summary_type", selectedStyle.value);
      const response = await api.post("/news_summary/summarize", formData);
      if (response.data.success) {
        generatedContent.value = response.data.data.summary;
        ElMessage.success("概要生成成功");
        isGenerated.value = true;
      } else {
        ElMessage.error(response.data.message || "概要生成失败");
      }
    }
  } catch (error) {
    console.error("生成错误:", error);
    ElMessage.error("生成失败，请重试");
  } finally {
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

.news-processor-container {
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

.function-selection,
.style-selection {
  margin: 20px 0;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.function-title,
.style-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #333;
}

.function-buttons,
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
