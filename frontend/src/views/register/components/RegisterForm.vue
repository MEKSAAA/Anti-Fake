<template>
  <div class="logo-container">
    <img src="@/assets/images/logo_with_name.png" alt="Logo" class="logo-image" />
  </div>

  <div class="avatar-section">
    <img :src="avatarUrl" alt="默认头像" class="avatar-image" />
  </div>

  <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" size="large">
    <el-form-item prop="username">
      <el-input v-model="registerForm.username" placeholder="请输入用户名">
        <template #prefix>
          <el-icon><User /></el-icon>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item prop="email">
      <el-input v-model="registerForm.email" placeholder="请输入邮箱">
        <template #prefix>
          <el-icon><Message /></el-icon>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item prop="code">
      <el-input v-model="registerForm.code" placeholder="请输入验证码">
        <template #prefix>
          <el-icon><ChatDotRound /></el-icon>
        </template>
        <template #append>
          <el-button :disabled="countdown > 0" @click="sendCode">{{
            countdown > 0 ? countdown + "s 后重试" : "获取验证码"
          }}</el-button>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item prop="password">
      <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password>
        <template #prefix>
          <el-icon><Lock /></el-icon>
        </template>
      </el-input>
    </el-form-item>
  </el-form>

  <div class="buttons">
    <el-button :icon="Back" @click="goToLogin" round size="large" style="width: 180px">返回登录</el-button>
    <el-button
      :icon="Check"
      type="primary"
      :loading="loading"
      @click="register(registerForm)"
      round
      size="large"
      style="width: 180px"
    >
      注册
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import type { ElForm } from "element-plus";
import { User, Lock, Message, Check, Back } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import defaultAvatar from "@/assets/images/default_avatar.png";

const avatarUrl = ref<string>(defaultAvatar);

type FormInstance = InstanceType<typeof ElForm>;

const router = useRouter();
const loading = ref(false);
const registerFormRef = ref<FormInstance>();

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  code: ""
});

const registerRules = reactive({
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
});

const countdown = ref(0);
let timer: ReturnType<typeof setInterval>;

const sendCode = async () => {
  if (!registerForm.email) {
    ElMessage.warning("请先输入邮箱哦～📮");
    return;
  }

  try {
    const response = await fetch("http://localhost:6006/auth/send_code", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: registerForm.email })
    });

    const result = await response.json();

    if (result.success) {
      ElMessage.success(result.message || "验证码已发送！");

      countdown.value = 60;
      clearInterval(timer);
      timer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) clearInterval(timer);
      }, 1000);
    } else {
      ElMessage.error(result.message || "发送验证码失败！");
    }
  } catch (error) {
    console.error("发送验证码异常：", error);
    ElMessage.error("发送验证码失败，请检查网络或服务器状态！");
  }
};

const register = async (form: { username: string; email: string; password: string; code: string }) => {
  try {
    const response = await fetch("http://localhost:6006/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username: form.username,
        email: form.email,
        password: form.password,
        verification_code: form.code
      })
    });

    // 处理服务器响应
    const data = await response.json();

    if (response.ok) {
      // 注册成功
      ElMessage.success(data.message);
      console.log("注册成功", data.user);
      router.push("/login");
    } else {
      // 注册失败
      ElMessage.error(data.message || "注册失败，请重试！");
    }
  } catch (error) {
    ElMessage.error("网络错误，无法连接到服务器！");
    console.error("注册异常:", error);
  }
};

const goToLogin = () => {
  router.push("/login");
};
</script>

<style scoped lang="scss">
.logo-container {
  text-align: center;
  margin-top: -50px;
}

.logo-image {
  max-width: 280px;
}

.avatar-section {
  text-align: center;
}

.avatar-image {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #dcdfe6;
  margin-bottom: 10px;
}

.el-form {
  max-width: 400px;
  padding: 30px;
  justify-content: center;
}

.buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  width: 100%;
  margin-top: -20px;
}
</style>
