<template>
  <div class="multimodal-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>多模态检测</span>
        </div>
      </template>
      <div class="content">
        <el-form :model="form" label-width="120px">
          <el-form-item label="文本内容">
            <el-input v-model="form.text" type="textarea" :rows="4" placeholder="请输入文本内容" />
          </el-form-item>
          <el-form-item label="图片上传">
            <el-upload class="upload-demo" action="#" :auto-upload="false" :on-change="handleImageChange">
              <el-button type="primary">点击上传</el-button>
              <template #tip>
                <div class="el-upload__tip">支持jpg/png文件，且不超过5MB</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSubmit">开始检测</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from "vue";

const form = reactive({
  text: "",
  image: null
});

const handleImageChange = file => {
  form.image = file.raw;
};

const handleSubmit = () => {
  // TODO: 实现多模态检测逻辑
  console.log("提交的文本:", form.text);
  console.log("提交的图片:", form.image);
};

const handleReset = () => {
  form.text = "";
  form.image = null;
};
</script>

<style scoped>
.multimodal-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.content {
  margin-top: 20px;
}
.upload-demo {
  margin-bottom: 10px;
}
</style>
