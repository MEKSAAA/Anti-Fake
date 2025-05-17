<template>
  <div class="forgot-container flx-center">
    <div class="forgot-box">
      <SwitchDark class="dark" />
      <div class="forgot-form">
        <ForgotForm />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="login">
import SwitchDark from "@/components/SwitchDark/index.vue";
import ForgotForm from "./components/ForgotForm.vue";
</script>

<style scoped lang="scss">
@import "./index.scss";
</style>
