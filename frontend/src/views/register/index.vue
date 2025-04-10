<template>
  <div class="register-container flx-center">
    <div class="register-box">
      <SwitchDark class="dark" />
      <div class="register-form">
        <RegisterForm />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="login">
import RegisterForm from "./components/RegisterForm.vue";
import SwitchDark from "@/components/SwitchDark/index.vue";
</script>

<style scoped lang="scss">
@import "./index.scss";
</style>
