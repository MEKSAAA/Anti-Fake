<template>
  <div class="logo-container">
    <img src="@/assets/images/logo_with_name.png" alt="Logo" class="logo-image" />
  </div>

  <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" size="large">
    <el-form-item prop="email">
      <el-input v-model="forgotForm.email" placeholder="请输入邮箱">
        <template #prefix>
          <el-icon><Message /></el-icon>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item prop="code">
      <el-input v-model="forgotForm.code" placeholder="请输入验证码">
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
      <el-input v-model="forgotForm.password" type="password" placeholder="请输入密码" show-password>
        <template #prefix>
          <el-icon><Lock /></el-icon>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item prop="confirmPassword">
      <el-input v-model="forgotForm.confirmPassword" type="password" placeholder="请确认密码" show-password>
        <template #prefix>
          <el-icon><Lock /></el-icon>
        </template>
      </el-input>
    </el-form-item>
  </el-form>

  <div class="buttons">
    <el-button :icon="Back" @click="goToLogin" round size="large" style="width: 180px">返回登录</el-button>
    <el-button :icon="Check" type="primary" :loading="loading" @click="forgot()" round size="large" style="width: 180px">
      找回
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import type { ElForm } from "element-plus";
import { Lock, Message, Check, Back } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

type FormInstance = InstanceType<typeof ElForm>;

const router = useRouter();
const loading = ref(false);
const forgotFormRef = ref<FormInstance>();

const forgotForm = reactive({
  email: "",
  password: "",
  confirmPassword: "",
  code: ""
});

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error("请确认密码")); // 为空
  } else if (value.length < 6) {
    callback(new Error("密码长度至少6位"));
  } else if (value !== forgotForm.password) {
    callback(new Error("两次输入的密码不一致！")); // 和密码不一样
  } else {
    callback(); // 成功
  }
};

const forgotRules = reactive({
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: "blur" }],
  code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
});

const countdown = ref(0);
let timer: ReturnType<typeof setInterval>;

const sendCode = async () => {
  if (!forgotForm.email) {
    ElMessage.warning("请先输入邮箱📮");
    return;
  }

  clearInterval(timer);

  try {
    const response = await fetch("http://localhost:6006/auth/send_code", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: forgotForm.email })
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

const forgot = async () => {
  if (!forgotFormRef.value) return;

  // 校验表单
  try {
    await forgotFormRef.value.validate();
  } catch (validationError) {
    ElMessage.warning("请完整填写表单信息🌟");
    return;
  }

  loading.value = true;

  try {
    const res = await fetch("http://localhost:6006/auth/find_password_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email: forgotForm.email,
        verification_code: forgotForm.code,
        new_password: forgotForm.password
      })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      ElMessage.success(data.message || "密码找回成功！");
      console.log("找回密码成功🎉", data);
      router.push("/login");
    } else {
      ElMessage.error(data.message || "找回失败，请稍后重试！");
    }
  } catch (error) {
    console.error("找回密码请求异常❌", error);
    ElMessage.error("网络连接失败，请检查你的网络或稍后再试！");
  } finally {
    loading.value = false;
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
