<template>
  <div class="history-wrapper">
    <h2>历史记录</h2>

    <el-table :data="paginatedData" v-loading="loading" border style="width: 100%" class="table">
      <el-table-column type="index" label="编号" width="60" align="center" />
      <el-table-column prop="source" label="检测来源" min-width="90" align="center" :show-overflow-tooltip="true" />
      <el-table-column prop="content" label="内容" min-width="300" align="center" :show-overflow-tooltip="true" />
      <el-table-column prop="detection_reason" label="检测结果" min-width="300" align="center" :show-overflow-tooltip="true" />
      <el-table-column prop="upload_date" label="检测时间" min-width="120" align="center" :formatter="formatDate" />
    </el-table>

    <!-- 分页器 -->
    <el-pagination
      class="pagination"
      background
      layout="prev, pager, next"
      :total="historyList.length"
      :page-size="pageSize"
      :current-page="currentPage"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import dayjs from "dayjs";

const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

const historyList = ref([]);
const loading = ref(false);

// 分页相关
const currentPage = ref(1);
const pageSize = 15;
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return historyList.value.slice(start, start + pageSize);
});

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

// 时间格式处理
const formatDate = (_: any, __: any, cellValue: string) => {
  return dayjs(cellValue).format("YYYY-MM-DD");
};

const getHistory = async () => {
  if (!userId) {
    console.warn("用户未登录，无法获取历史记录！");
    return;
  }

  try {
    loading.value = true;
    const { data } = await axios.get(`http://localhost:6006/news_detection/history/${userId}`);
    historyList.value = data?.data || [];
  } catch (err) {
    console.error("获取历史记录失败：", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  getHistory();
});
</script>

<style scoped lang="scss">
.history-wrapper {
  margin-left: 20px;
  margin-right: 20px;
}

.table {
  background-color: var(--el-bg-color);
  border-radius: 10px;
  box-shadow: 0 2px 10px 2px rgba(0, 0, 0, 0.1);
}

.el-table .cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>
