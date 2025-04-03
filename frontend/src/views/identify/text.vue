<template>
  <div class="text-identify-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>文本检测</span>
        </div>
      </template>
      <div class="content">
        <el-form :model="form" label-width="120px">
          <el-form-item label="输入文本">
            <el-input v-model="form.text" type="textarea" :rows="6" placeholder="请输入需要检测的文本内容" />
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
  text: "" //删除这里的逗号
});

const handleSubmit = () => {
  // TODO: 实现文本检测逻辑
  console.log("提交的文本:", form.text);
};

const handleReset = () => {
  form.text = "";
};
</script>

<style scoped>
.text-identify-container {
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
</style>
