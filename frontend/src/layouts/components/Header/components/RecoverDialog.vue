<template>
  <el-dialog v-model="dialogVisible" title="找回密码" width="500px" draggable>
    <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" disabled placeholder="系统自动填充邮箱">
          <template #prefix>
            <el-icon><Message /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="验证码" prop="verification_code">
        <el-input v-model="form.verification_code" placeholder="请输入验证码">
          <template #prefix>
            <el-icon><ChatDotRound /></el-icon>
          </template>
          <template #append>
            <el-button :disabled="countdown > 0" @click="sendCode">
              {{ countdown > 0 ? countdown + "s 后重试" : "获取验证码" }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password />
      </el-form-item>

      <el-form-item label="确认密码" prop="confirm_password">
        <el-input v-model="form.confirm_password" type="password" show-password />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpdate">确认</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import { Message, ChatDotRound } from "@element-plus/icons-vue";

const dialogVisible = ref(false);
const formRef = ref();
const userInfoStore = useUserInfoStore();

const form = ref({
  email: "",
  verification_code: "",
  new_password: "",
  confirm_password: ""
});

const rules = {
  email: [{ required: false, message: "邮箱不能为空", trigger: "blur" }],
  verification_code: [{ required: true, message: "请输入验证码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "新密码至少6位字符", trigger: "blur" }
  ],
  confirm_password: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (value !== form.value.new_password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

// 倒计时逻辑
const countdown = ref(0);
let timer: NodeJS.Timeout | null = null;

const sendCode = async () => {
  if (!form.value.email) {
    ElMessage.warning("邮箱为空，无法发送验证码！");
    return;
  }

  try {
    const response = await fetch("http://localhost:6006/auth/send_code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.value.email })
    });

    const result = await response.json();
    if (result.success) {
      ElMessage.success("验证码发送成功！");
      startCountdown();
    } else {
      ElMessage.error(result.message || "验证码发送失败！");
    }
  } catch (error) {
    ElMessage.error("验证码发送出错！");
  }
};

const startCountdown = () => {
  countdown.value = 60;
  timer && clearInterval(timer);
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(timer!);
      timer = null;
    }
  }, 1000);
};

// 打开弹窗并填充邮箱
const openDialog = () => {
  const { email } = userInfoStore;
  form.value = {
    email: email,
    verification_code: "",
    new_password: "",
    confirm_password: ""
  };
  dialogVisible.value = true;
};

defineExpose({ openDialog });

// 提交找回密码
const confirmUpdate = () => {
  formRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.error("请正确填写表单！");
      return;
    }

    try {
      const response = await fetch("http://localhost:6006/auth/find_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userInfoStore.user_id,
          email: form.value.email,
          verification_code: form.value.verification_code,
          new_password: form.value.new_password
        })
      });

      const result = await response.json();
      if (result.success) {
        ElMessage.success("密码找回成功！");
        dialogVisible.value = false;
      } else {
        ElMessage.error(result.message || "找回失败！");
      }
    } catch (error) {
      ElMessage.error("找回密码请求失败！");
    }
  });
};
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>
