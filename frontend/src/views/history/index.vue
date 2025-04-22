<template>
  <div class="history-wrapper">
    <h2>历史记录</h2>
    <el-table :data="historyList" style="width: 100%" v-loading="loading">
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="result" label="检测结果" />
      <el-table-column prop="create_time" label="检测时间" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios"; // 或使用你封装的 request 方法

const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

const historyList = ref([]);
const loading = ref(false);

const getHistory = async () => {
  if (!userId) {
    console.warn("用户未登录，无法获取历史记录！");
    return;
  }

  try {
    loading.value = true;
    const { data } = await axios.get(`http://localhost:6006/news_detection/history/${userId}`);
    console.log(data);
    historyList.value = data?.data || [];
  } catch (err) {
    console.error("获取历史记录失败：", err);
  } finally {
    loading.value = false;
  }
};

// 页面加载时获取历史
onMounted(() => {
  getHistory();
});
</script>

<style scoped lang="scss">
.history-wrapper {
  padding: 20px;
}
</style>
