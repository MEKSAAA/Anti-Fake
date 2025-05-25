<template>
  <div class="history-wrapper">
    <h2>历史记录</h2>
    <div class="method-tabs">
      <div class="method method-one" :class="{ active: activeMethod === 'title' }" @click="setActiveMethod('title')">
        <div class="method-label">标题生成历史</div>
      </div>
      <div class="method method-two" :class="{ active: activeMethod === 'summary' }" @click="setActiveMethod('summary')">
        <div class="method-label">概要生成历史</div>
      </div>
      <div class="method method-three" :class="{ active: activeMethod === 'image' }" @click="setActiveMethod('image')">
        <div class="method-label">图片生成历史</div>
      </div>
      <div class="method method-four" :class="{ active: activeMethod === 'text' }" @click="setActiveMethod('text')">
        <div class="method-label">文本优化历史</div>
      </div>
    </div>

    <el-table :data="paginatedData" v-loading="loading" border style="width: 100%" class="table">
      <el-table-column type="index" label="编号" width="60" align="center" />

      <!-- 根据不同类型，显示不同列 -->
      <template v-if="activeMethod === 'title'">
        <el-table-column prop="original_content" label="原始内容" min-width="300" align="center" :show-overflow-tooltip="true" />
        <el-table-column prop="title_style" label="标题风格" min-width="120" align="center" :formatter="formatTitleStyle" />
        <el-table-column prop="generated_title" label="生成标题" min-width="200" align="center" :show-overflow-tooltip="true" />
        <el-table-column prop="generation_date" label="生成时间" min-width="150" align="center" :formatter="formatDate" />
      </template>

      <template v-else-if="activeMethod === 'summary'">
        <el-table-column prop="original_content" label="原始内容" min-width="300" align="center" :show-overflow-tooltip="true" />
        <el-table-column prop="summary_type" label="概要风格" min-width="120" align="center" :formatter="formatSummaryType" />
        <el-table-column prop="summary_content" label="生成概要" min-width="300" align="center" :show-overflow-tooltip="true" />
        <el-table-column prop="summary_date" label="生成时间" min-width="150" align="center" :formatter="formatDate" />
      </template>

      <template v-else-if="activeMethod === 'image'">
        <el-table-column prop="prompt_text" label="原始内容" min-width="250" align="center" show-overflow-tooltip />
        <el-table-column prop="image_style" label="图片风格" min-width="120" align="center" :formatter="formatPictureType" />
        <el-table-column label="图片" min-width="120" align="center">
          <template #default="{ row }">
            <el-button v-if="row.image_paths" type="primary" size="small" @click="showImage(row.image_paths)">
              查看图片
            </el-button>
            <span v-else style="color: #ccc">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="generation_date" label="生成时间" min-width="160" align="center" :formatter="formatDate" />
      </template>

      <template v-else-if="activeMethod === 'text'">
        <el-table-column prop="original_text" label="原始文本" min-width="300" align="center" :show-overflow-tooltip="true" />
        <el-table-column
          prop="target_style"
          label="优化风格"
          min-width="120"
          align="center"
          :formatter="formatOptimizationType"
        />
        <el-table-column prop="optimized_text" label="优化文本" min-width="300" align="center" :show-overflow-tooltip="true" />
        <el-table-column prop="optimization_date" label="优化时间" min-width="150" align="center" :formatter="formatDate" />
      </template>
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
    <el-dialog v-model="previewVisible" title="图片预览" width="70%" top="5vh">
      <div style="text-align: center">
        <el-image :src="previewImageUrls[currentPreviewIndex]" fit="contain" style="max-width: 75vh; max-height: 75vh" />
        <div style="margin-top: 10px">
          <el-button :disabled="currentPreviewIndex === 0" @click="currentPreviewIndex--">上一张</el-button>
          <el-button :disabled="currentPreviewIndex === previewImageUrls.length - 1" @click="currentPreviewIndex++">
            下一张
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import axios from "axios";
import dayjs from "dayjs";

const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

const activeMethod = ref<"title" | "summary" | "image" | "text">("title");
const setActiveMethod = (method: typeof activeMethod.value) => {
  activeMethod.value = method;
  currentPage.value = 1;
  getHistory();
};

const historyList = ref<any[]>([]);
const loading = ref(false);

const currentPage = ref(1);
const pageSize = 10;
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return historyList.value.slice(start, start + pageSize);
});
const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const formatTitleStyle = (_: any, __: any, cellValue: string) => {
  switch (cellValue) {
    case "informative":
      return "信息型";
    case "attractive":
      return "吸睛型";
    case "questioning":
      return "疑问型";
    case "dramatic":
      return "情节型";
    case "neutral":
      return "客观型";
    case "concise":
      return "简洁型";
    case "emotional":
      return "情感型";
    default:
      return cellValue || "未知类型";
  }
};

const formatSummaryType = (_: any, __: any, cellValue: string) => {
  switch (cellValue) {
    case "brief":
      return "简洁型";
    case "detailed":
      return "详细型";
    case "key_points":
      return "要点型";
    case "analytical":
      return "分析型";
    case "news_flash":
      return "快讯型";
    default:
      return cellValue || "未知类型";
  }
};

const formatPictureType = (_: any, __: any, cellValue: string) => {
  switch (cellValue) {
    case "realistic":
      return "真实型";
    case "watercolor":
      return "水彩型";
    case "oil_painting":
      return "油画型";
    case "ink_painting":
      return "水墨画型";
    case "anime":
      return "二次元型";
    case "minimalist":
      return "极简型";
    case "tech":
      return "科技型";
    case "cartoon_3d":
      return "卡通型";
    case "abstract":
      return "抽象型";
    default:
      return cellValue || "未知类型";
  }
};

const formatOptimizationType = (_: any, __: any, cellValue: string) => {
  switch (cellValue) {
    case "formal":
      return "正式型";
    case "casual":
      return "日常型";
    case "academic":
      return "学术型";
    case "journalistic":
      return "客观型";
    case "narrative":
      return "故事型";
    case "persuasive":
      return "倡议型";
    case "concise":
      return "简洁型";
    case "elaborate":
      return "详细型";
    case "prodessional":
      return "专业型";
    default:
      return cellValue || "未知类型";
  }
};

const formatDate = (_: any, __: any, cellValue: string) => {
  return cellValue ? dayjs(cellValue).format("YYYY-MM-DD  HH:mm:ss") : "";
};

const previewImageUrls = ref<string[]>([]);
const previewVisible = ref(false);
const currentPreviewIndex = ref(0);

const showImage = (urls: string[]) => {
  const adjustedUrls = urls.map(url => url.replace(/^\/?root\/news_backend/, "http://localhost:6006"));
  previewImageUrls.value = adjustedUrls;
  currentPreviewIndex.value = 0;
  previewVisible.value = true;
};

const getHistory = async () => {
  if (!userId) {
    console.warn("用户未登录，无法获取历史记录！");
    return;
  }

  let url = "";
  switch (activeMethod.value) {
    case "title":
      url = `http://localhost:6006/news_title/history/${userId}`;
      break;
    case "summary":
      url = `http://localhost:6006/news_summary/history/${userId}`;
      break;
    case "image":
      url = `http://localhost:6006/image_generation/history/${userId}`;
      break;
    case "text":
      url = `http://localhost:6006/text_optimization/history/${userId}`;
      break;
  }

  try {
    loading.value = true;
    const { data } = await axios.get(url);
    historyList.value = data?.data || [];
    console.log(historyList.value);
  } catch (err) {
    console.error("获取历史记录失败：", err);
    historyList.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  getHistory();
});

// 监听切换，分页也要刷新当前页数据
watch([activeMethod, currentPage], () => {
  // 这里已经在 setActiveMethod 里请求过一次，所以分页换页时只更新数据
  if (currentPage.value !== 1) {
    getHistory();
  }
});
</script>

<style scoped lang="scss">
.history-wrapper {
  margin: 20px;
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
.method-three.active,
.method-four.active {
  background-color: #e0f3f3;
}

.method-one.active .method-label,
.method-two.active .method-label,
.method-three.active .method-label,
.method-four.active .method-label {
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
