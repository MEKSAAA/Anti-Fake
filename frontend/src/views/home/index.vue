<template>
  <div class="statistics-wrapper">
    <div class="grid-item">
      <v-chart class="chart" :option="userChartOption" autoresize />
    </div>
    <div class="grid-item">
      <v-chart class="chart" :option="globalChartOption" autoresize />
    </div>
    <div class="grid-item">
      <v-chart class="chart" :option="typeChartOption" autoresize />
    </div>
    <div class="grid-item">
      <v-chart class="chart" :option="trendChartOption" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import axios from "axios";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart, LineChart } from "echarts/charts";
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent } from "echarts/components";

use([CanvasRenderer, PieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent]);

const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

const globalFake = ref(0);
const globalReal = ref(0);
const userFake = ref(0);
const userReal = ref(0);
const trendData = ref<any[]>([]);
const detectionTypeData = ref({
  image: 0,
  text: 0
});

const fetchGlobalStats = async () => {
  const { data } = await axios.get("http://localhost:6006/statistics/global");
  globalFake.value = data.data.total_fake_count;
  globalReal.value = data.data.total_real_count;
};

const fetchUserStats = async () => {
  const { data } = await axios.get(`http://localhost:6006/statistics/user/${userId}`);
  userFake.value = data.data.total_fake_count;
  userReal.value = data.data.total_real_count;
};

const fetchTrendData = async () => {
  const { data } = await axios.get("http://localhost:6006/statistics/trend");
  trendData.value = data.data || [];
};

const fetchDetectionTypeData = async () => {
  const { data } = await axios.get("http://localhost:6006/statistics/detection-types");
  detectionTypeData.value.image = data.data.image_detection.total_count;
  detectionTypeData.value.text = data.data.text_detection.total_count;
};

const globalChartOption = computed(() => ({
  title: { text: "Anti-Fake检测新闻真伪比例", left: "center" },
  tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c} ({d}%)" },
  legend: { bottom: "10%", left: "center" },
  series: [
    {
      name: "Anti-Fake检测结果",
      type: "pie",
      radius: "50%",
      data: [
        { value: globalFake.value, name: "伪新闻" },
        { value: globalReal.value, name: "真实新闻" }
      ]
    }
  ]
}));

const userChartOption = computed(() => ({
  title: { text: "我的检测新闻真伪比例", left: "center" },
  tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c} ({d}%)" },
  legend: { bottom: "10%", left: "center" },
  series: [
    {
      name: "我的检测结果",
      type: "pie",
      radius: "50%",
      data: [
        { value: userFake.value, name: "伪新闻" },
        { value: userReal.value, name: "真实新闻" }
      ]
    }
  ]
}));

const trendChartOption = computed(() => {
  const dates = trendData.value.map(item => item.date.slice(5));
  const fakeCounts = trendData.value.map(item => Number(item.fake_count));
  const realCounts = trendData.value.map(item => Number(item.real_count));
  const totalCounts = trendData.value.map(item => Number(item.total_count));

  return {
    title: { text: "Anti-Fake新闻检测数量趋势", left: "center" },
    tooltip: { trigger: "axis" },
    legend: { bottom: "10%", left: "center" },
    grid: { left: "10%", right: "10%", bottom: "20%", containLabel: true },
    xAxis: { type: "category", boundaryGap: false, data: dates },
    yAxis: { type: "value" },
    series: [
      { name: "伪新闻数量", type: "line", data: fakeCounts },
      { name: "真实新闻数量", type: "line", data: realCounts },
      { name: "总检测数量", type: "line", data: totalCounts }
    ]
  };
});

const typeChartOption = computed(() => ({
  title: { text: "Anti-Fake新闻检测类型比例", left: "center" },
  tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c} ({d}%)" },
  legend: { bottom: "10%", left: "center" },
  series: [
    {
      name: "Anti-Fake检测类型",
      type: "pie",
      radius: "50%",
      data: [
        { value: detectionTypeData.value.image, name: "图像检测" },
        { value: detectionTypeData.value.text, name: "文本检测" }
      ]
    }
  ]
}));

onMounted(() => {
  fetchGlobalStats();
  fetchUserStats();
  fetchTrendData();
  fetchDetectionTypeData();
});
</script>

<style scoped lang="scss">
.statistics-wrapper {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-auto-rows: 1fr;
  gap: 12px;
  padding: 24px;
  box-sizing: border-box;
  height: calc(100vh - 150px);
  width: 100%;
}

.grid-item {
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
