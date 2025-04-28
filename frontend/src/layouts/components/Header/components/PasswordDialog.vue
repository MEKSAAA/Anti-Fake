<template>
  <el-dialog v-model="dialogVisible" title="修改密码" width="500px" draggable>
    <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
      <el-form-item label="当前密码" prop="currentPassword">
        <el-input v-model="form.currentPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model="form.newPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" show-password />
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

const dialogVisible = ref(false);
const formRef = ref();
const userInfoStore = useUserInfoStore();

// 表单数据
const form = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: ""
});

// 表单校验规则
const rules = {
  currentPassword: [{ required: true, message: "请输入当前密码", trigger: "blur" }],
  newPassword: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "新密码至少6位字符", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (value !== form.value.newPassword) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

// 打开弹窗方法
const openDialog = () => {
  form.value.currentPassword = "";
  form.value.newPassword = "";
  form.value.confirmPassword = "";
  dialogVisible.value = true;
};

defineExpose({ openDialog });

// 确认修改密码
const confirmUpdate = () => {
  formRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.error("请正确填写表单!");
      return;
    }

    try {
      const response = await fetch("http://localhost:6006/auth/update/password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          user_id: userInfoStore.user_id,
          current_password: form.value.currentPassword,
          new_password: form.value.newPassword
        })
      });

      const result = await response.json();
      console.log("修改密码响应:", result);

      if (result.success) {
        ElMessage.success("密码修改成功!");
        dialogVisible.value = false;
      } else {
        ElMessage.error(result.message || "密码修改失败!");
      }
    } catch (error) {
      console.error("修改密码出错:", error);
      ElMessage.error("修改密码时发生了意料之外的小错误!");
    }
  });
};
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>
