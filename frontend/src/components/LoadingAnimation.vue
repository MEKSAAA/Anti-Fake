<template>
  <div class="loading-container" :class="{ 'container-mode': containerMode }" v-if="visible">
    <div class="pacman-container">
      <div class="pacman">
        <div class="pacman-top"></div>
        <div class="pacman-bottom"></div>
        <div class="feed"></div>
      </div>
    </div>
    <div class="progress-container">
      <el-progress :percentage="Math.floor(percentage)" :stroke-width="20" :show-text="false" />
      <div class="progress-text">{{ Math.floor(percentage) }}%</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  percentage: {
    type: Number,
    default: 0
  },
  containerMode: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.loading-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(1px);
}

.loading-container.container-mode {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(1px);
  z-index: 10;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.pacman-container {
  margin-bottom: 20px;
}

.pacman {
  width: 60px;
  height: 60px;
  position: relative;
  margin-top: 20px;
}

.pacman-top {
  width: 60px;
  height: 30px;
  background: #54bcbd;
  border-radius: 60px 60px 0 0;
  animation: spin1 0.5s linear infinite;
  transform-origin: center bottom;
  position: absolute;
  top: 0;
}

.pacman-bottom {
  width: 60px;
  height: 30px;
  background: #54bcbd;
  border-radius: 0 0 60px 60px;
  animation: spin2 0.5s linear infinite;
  transform-origin: center top;
  position: absolute;
  bottom: 0;
}

.feed {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #54bcbd;
  border-radius: 50%;
  top: 25px;
  left: 70px;
  animation: feed 0.5s linear infinite;
}

@keyframes spin1 {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(-45deg);
  }
}

@keyframes spin2 {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(45deg);
  }
}

@keyframes feed {
  0% {
    transform: translateX(0);
    opacity: 1;
  }
  100% {
    transform: translateX(-60px);
    opacity: 0;
  }
}

.progress-container {
  width: 200px;
  position: relative;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  color: #54bcbd;
  font-size: 14px;
  font-weight: bold;
}

:deep(.el-progress-bar__inner) {
  background-color: #54bcbd !important;
}
</style>
