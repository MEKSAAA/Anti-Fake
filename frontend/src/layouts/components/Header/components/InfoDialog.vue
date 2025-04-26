<template>
  <el-dialog v-model="dialogVisible" title="个人信息" width="500px" draggable>
    <el-form label-width="80px">
      <el-form-item label="用户id">
        <el-input v-model="userId" disabled />
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="username" :disabled="!isEditing" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="email" :disabled="!isEditing" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="password" type="password" placeholder="******" :disabled="!isEditing" />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button v-if="!isEditing" type="primary" @click="isEditing = true">修改</el-button>
        <el-button v-else type="primary" @click="confirmUpdate">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useUserInfoStore } from "@/stores/modules/userInfo";
import { ElMessage } from "element-plus";

const dialogVisible = ref(false);
const isEditing = ref(false);
const email = ref("");
const username = ref("");
const userId = ref("");
const password = ref("");

const userInfoStore = useUserInfoStore();

// 打开弹窗并加载用户数据
const openDialog = () => {
  const { email: e, username: u, user_id: id } = userInfoStore;
  email.value = e;
  username.value = u;
  userId.value = id.toString();
  password.value = "123456"; // 这里暂时写死
  isEditing.value = false;
  dialogVisible.value = true;
};

defineExpose({ openDialog });

// 保存修改
const confirmUpdate = () => {
  userInfoStore.setUserInfo({
    email: email.value,
    username: username.value,
    user_id: userInfoStore.user_id
  });
  ElMessage.success("用户信息已更新！");
  isEditing.value = false;
};
</script>
