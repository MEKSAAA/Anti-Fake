<template>
  <div class="tool-bar-ri">
    <div class="header-icon">
      <ThemeSetting id="themeSetting" />
      <Fullscreen id="fullscreen" />
    </div>
    <span class="username">{{ userInfoStore.username }}</span>
    <Avatar />
  </div>
</template>

<script setup lang="ts">
// import { computed } from "vue";
// import { useUserStore } from "@/stores/modules/user";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import ThemeSetting from "./components/ThemeSetting.vue";
import Fullscreen from "./components/Fullscreen.vue";
import Avatar from "./components/Avatar.vue";

// const userStore = useUserStore();
// const username = computed(() => userStore.userInfo.name);

const userInfoStore = useUserInfoStore();
</script>

<style scoped lang="scss">
.tool-bar-ri {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-right: 25px;
  .header-icon {
    display: flex;
    align-items: center;
    & > * {
      margin-left: 21px;
      color: var(--el-header-text-color);
    }
  }
  .username {
    margin: 0 20px;
    font-size: 15px;
    color: var(--el-header-text-color);
  }
}
</style>
