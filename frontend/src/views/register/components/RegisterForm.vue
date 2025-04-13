<template>
  <div class="logo-container">
    <img src="@/assets/images/logo_with_name.png" alt="Logo" class="logo-image" />
  </div>

  <div class="avatar-section">
    <img :src="avatarUrl" alt="默认头像" class="avatar-image" />
    <el-upload class="upload-avatar" :show-file-list="false" :before-upload="handleAvatarChange">
      <el-button type="primary" size="default">更换头像</el-button>
    </el-upload>
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
          <el-icon><Message /></el-icon>
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
      @click="register(registerFormRef)"
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

// 上传头像处理
const handleAvatarChange = (file: File) => {
  const isImage = file.type.startsWith("image/");
  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }

  // 显示预览
  const reader = new FileReader();
  reader.onload = e => {
    avatarUrl.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);

  // 模拟上传成功
  ElMessage.success("头像上传成功！");
  return false; // 阻止自动上传，改为自定义处理
};

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

// 验证码倒计时
const countdown = ref(0);
let timer: ReturnType<typeof setInterval>; // 修正 timer 类型

const sendCode = () => {
  if (!registerForm.email) {
    ElMessage.warning("请先输入邮箱哦～📮");
    return;
  }

  // 模拟发送验证码
  ElMessage.success("验证码已发送！🎉（假的）");

  countdown.value = 60;
  clearInterval(timer); // 清除旧的定时器
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(timer);
    }
  }, 1000);
};

const register = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  formEl.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      // await registerApi({ ...registerForm, password: md5(registerForm.password) });
      ElMessage.success("注册成功！（假装成功了😎）");
      router.push("/login");
    } catch (err) {
      ElMessage.error("注册失败！");
    } finally {
      loading.value = false;
    }
  });
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

.upload-avatar .el-button {
  margin-top: 10px;
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
