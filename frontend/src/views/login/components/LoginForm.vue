<template>
  <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" size="large">
    <el-tabs v-model="loginMethod" type="card">
      <!-- 用户名登录 -->
      <el-tab-pane label="用户名登录" name="username">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名">
            <template #prefix>
              <el-icon class="el-input__icon"><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            autocomplete="new-password"
          >
            <template #prefix>
              <el-icon class="el-input__icon"><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-tab-pane>

      <!-- 邮箱登录 -->
      <el-tab-pane label="邮箱登录" name="email">
        <el-form-item prop="email">
          <el-input v-model="loginForm.email" placeholder="请输入邮箱">
            <template #prefix>
              <el-icon class="el-input__icon"><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="verification_code">
          <el-input v-model="loginForm.verification_code" placeholder="请输入验证码">
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
      </el-tab-pane>
    </el-tabs>
  </el-form>

  <div class="login-btn">
    <el-button :icon="CirclePlus" round size="large" @click="goToRegister">注册</el-button>
    <el-button :icon="UserFilled" round size="large" type="primary" :loading="loading" @click="handleLogin"> 登录 </el-button>
  </div>
</template>

<script setup lang="ts">
import { initDynamicRouter } from "@/routers/modules/dynamicRouter";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import { CirclePlus, Lock, Message, User, UserFilled } from "@element-plus/icons-vue";
import { ElForm, ElMessage } from "element-plus";
import { onBeforeUnmount, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loginFormRef = ref<InstanceType<typeof ElForm>>();
const loginMethod = ref<"username" | "email">("username");
const loading = ref(false);

const loginForm = reactive({
  username: "",
  password: "",
  email: "",
  verification_code: ""
});

const loginRules = reactive({
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }],
  verification_code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
});

const countdown = ref(0);
let timer: ReturnType<typeof setInterval>;

const sendCode = async () => {
  if (!loginForm.email) {
    ElMessage.warning("请先输入邮箱📮");
    return;
  }

  try {
    const response = await fetch("http://localhost:6006/auth/send_code", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: loginForm.email })
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

const handleLogin = async () => {
  const method = loginMethod.value;
  const form = loginForm;

  try {
    let response;

    if (method === "username") {
      response = await fetch("http://localhost:6006/auth/login/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: form.username, password: form.password })
      });
    } else {
      response = await fetch("http://localhost:6006/auth/login/code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, verification_code: form.verification_code })
      });
    }

    const data = await response.json();
    console.log("后端返回的数据:", data);

    if (response.ok) {
      await initDynamicRouter();
      ElMessage.success(data.message || "登录成功！");
      let { user_id, email, username, avatar } = data.data.user;

      // 如果 avatar 是 null 或者 "none"，就用默认头像
      if (!avatar || avatar === "none") {
        avatar = new URL("@/assets/images/default_avatar.png", import.meta.url).href;
      }

      const userData = { email, user_id, username, avatar };
      const userInfoStore = useUserInfoStore();
      userInfoStore.setUserInfo(userData);
      localStorage.setItem("user-info", JSON.stringify(userData));

      router.push("/layout");
    } else {
      ElMessage.error(data.message || "登录失败");
    }
  } catch (error) {
    ElMessage.error("网络错误");
    console.error("登录异常:", error);
  }
};

const goToRegister = () => {
  router.push("/register");
};

onBeforeUnmount(() => {
  document.onkeydown = null;
});
</script>

<style scoped lang="scss">
@import "../index.scss";

::v-deep(.el-tabs__nav) {
  width: 100%;
  display: flex;
}

::v-deep(.el-tabs__item) {
  flex: 1;
  text-align: center;
}
</style>
