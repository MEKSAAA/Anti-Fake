<template>
  <div class="history-wrapper">
    <h2>历史记录</h2>
    <div class="method-tabs">
      <div class="method method-one" :class="{ active: activeMethod === 'all' }" @click="setActiveMethod('all')">
        <div class="method-label">全部历史</div>
      </div>
      <div class="method method-two" :class="{ active: activeMethod === 'text' }" @click="setActiveMethod('text')">
        <div class="method-label">文本检测历史</div>
      </div>
      <div class="method method-three" :class="{ active: activeMethod === 'image' }" @click="setActiveMethod('image')">
        <div class="method-label">图片检测历史</div>
      </div>
    </div>

    <el-table :data="paginatedData" v-loading="loading" border style="width: 100%" class="table">
      <el-table-column type="index" label="编号" width="60" align="center" />
      <el-table-column prop="source" label="检测来源" min-width="90" align="center" :show-overflow-tooltip="true" />
      <el-table-column prop="content" label="内容" min-width="300" align="center" :show-overflow-tooltip="true" />

      <el-table-column label="附件" min-width="120" align="center">
        <template #default="{ row }">
          <el-button
            v-if="row.detection_type === 'image' && row.detect_image_path"
            type="primary"
            size="small"
            @click="showImage(row.image_path)"
          >
            查看图片
          </el-button>
          <span v-else style="color: #ccc">无</span>
        </template>
      </el-table-column>

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

    <!-- 图片预览弹窗 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="50%">
      <el-image style="width: 100%" :src="previewImageUrl" fit="contain" :preview-src-list="[previewImageUrl]" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import dayjs from "dayjs";

// 当前选中的检测类型
const activeMethod = ref<"all" | "text" | "image">("all");
const setActiveMethod = (method: "all" | "text" | "image") => {
  activeMethod.value = method;
  currentPage.value = 1;
  getHistory(); // 每次切换类型重新获取记录
};

// 用户信息
const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

// 历史记录
const historyList = ref([]);
const loading = ref(false);

// 分页逻辑
const currentPage = ref(1);
const pageSize = 15;
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return historyList.value.slice(start, start + pageSize);
});
const handlePageChange = (page: number) => {
  currentPage.value = page;
};

// 时间格式化
const formatDate = (_: any, __: any, cellValue: string) => {
  return dayjs(cellValue).format("YYYY-MM-DD");
};

// 图片预览相关
const previewVisible = ref(false);
const previewImageUrl = ref("");
const showImage = (url: string) => {
  previewImageUrl.value = `http://localhost:6006${url}`;
  previewVisible.value = true;
};

// 获取历史记录
const getHistory = async () => {
  if (!userId) {
    console.warn("用户未登录，无法获取历史记录！");
    return;
  }

  try {
    loading.value = true;

    let url = `http://localhost:6006/news_detection/history/${userId}`;
    if (activeMethod.value === "text") {
      url += "?type=text";
    } else if (activeMethod.value === "image") {
      url += "?type=image";
    }

    const { data } = await axios.get(url);
    console.log(data);
    historyList.value = data?.data || [];
  } catch (err) {
    console.error("获取历史记录失败：", err);
  } finally {
    loading.value = false;
  }
};

// 初次加载全部历史
onMounted(() => {
  getHistory();
});
</script>

<style scoped lang="scss">
.history-wrapper {
  margin-left: 20px;
  margin-right: 20px;
}

.method-tabs {
  display: flex;
  gap: 12px;
  margin: 10px 0 20px;
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

.method-one.active,
.method-two.active,
.method-three.active {
  background-color: #e0f3f3;
}

.method-one.active .method-label,
.method-two.active .method-label,
.method-three.active .method-label {
  color: #54bcbd;
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
