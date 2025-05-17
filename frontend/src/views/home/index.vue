<template>
  <div class="statistics-wrapper">
    <div class="chart-box">
      <div class="chart-container">
        <v-chart class="chart" :option="globalChartOption" autoresize />
      </div>
      <div class="chart-container">
        <v-chart class="chart" :option="userChartOption" autoresize />
      </div>
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
import { PieChart } from "echarts/charts";
import { TitleComponent, TooltipComponent, LegendComponent } from "echarts/components";

use([CanvasRenderer, PieChart, TitleComponent, TooltipComponent, LegendComponent]);

// 获取当前用户
const userInfoStore = useUserInfoStore();
const userId = userInfoStore.user_id;

// 全局统计数据
const globalFake = ref(0);
const globalReal = ref(0);

// 用户统计数据
const userFake = ref(0);
const userReal = ref(0);

// 获取全局数据
const fetchGlobalStats = async () => {
  try {
    const { data } = await axios.get("http://localhost:6006/statistics/global");
    globalFake.value = data.data.total_fake_count;
    globalReal.value = data.data.total_real_count;
  } catch (err) {
    console.error("获取全局统计失败", err);
  }
};

// 获取用户数据
const fetchUserStats = async () => {
  try {
    const { data } = await axios.get(`http://localhost:6006/statistics/user/${userId}`);
    userFake.value = data.data.total_fake_count;
    userReal.value = data.data.total_real_count;
  } catch (err) {
    console.error("获取用户统计失败", err);
  }
};

// 饼图配置：全局
const globalChartOption = computed(() => ({
  title: {
    text: "Anti-Fake检测新闻真伪比例",
    left: "center"
  },
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/>{b} : {c} ({d}%)"
  },
  legend: {
    bottom: "10%",
    left: "center"
  },
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

// 饼图配置：用户
const userChartOption = computed(() => ({
  title: {
    text: "我的检测新闻真伪比例",
    left: "center"
  },
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/>{b} : {c} ({d}%)"
  },
  legend: {
    bottom: "10%",
    left: "center"
  },
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

onMounted(() => {
  fetchGlobalStats();
  fetchUserStats();
});
</script>

<style scoped lang="scss">
.statistics-wrapper {
  padding: 20px;
}

.chart-box {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 40px;
}

.chart-container {
  flex: 1;
  min-width: 400px;
  max-width: 48%;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.chart {
  width: 100%;
  height: 300px;
}
</style>
