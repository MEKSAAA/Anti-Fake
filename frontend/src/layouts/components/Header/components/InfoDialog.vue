<template>
  <el-dialog class="dialg" v-model="dialogVisible" title="个人信息" width="500px" draggable>
    <div class="avatar-section">
      <img :src="avatarUrl" alt="默认头像" class="avatar-image" />
      <el-upload class="upload-avatar" :show-file-list="false" :before-upload="handleAvatarChange" accept="image/*">
        <el-button type="primary" size="default">更换头像</el-button>
      </el-upload>
    </div>
    <el-form label-width="100px" class="custom-form">
      <el-form-item label="用户ID">
        <div class="info-text">{{ userId }}</div>
      </el-form-item>
      <el-form-item label="邮箱">
        <div class="info-text">{{ email }}</div>
      </el-form-item>
      <el-form-item label="用户名">
        <template v-if="!isEditing">
          <div class="info-text">{{ username }}</div>
        </template>
        <template v-else>
          <el-input v-model="username" />
        </template>
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
import { ElMessage } from "element-plus";
import { useUserInfoStore } from "@/stores/modules/userInfo";

const dialogVisible = ref(false);
const isEditing = ref(false);
const email = ref("");
const username = ref("");
const userId = ref("");
const avatarUrl = ref("");

const userInfoStore = useUserInfoStore();

// 打开弹窗并加载用户数据
const openDialog = () => {
  const { email: e, username: u, user_id: id, avatar: a } = userInfoStore;
  email.value = e;
  username.value = u;
  userId.value = id.toString();
  avatarUrl.value = a;
  isEditing.value = false;
  dialogVisible.value = true;
};

defineExpose({ openDialog });

// 更新头像信息
const updateAvatar = async () => {
  try {
    const response = await fetch(`http://localhost:6006/auth/get_avatar/${userId.value}`);
    const data = await response.json();
    console.log(data);
    if (data.success) {
      // avatarUrl.value = data.data.avatar;
      // userInfoStore.setAvatar({ avatar: avatarUrl.value });
      avatarUrl.value = `${data.data.avatar}?t=${Date.now()}`; // 加时间戳防缓存
      userInfoStore.setAvatar({ avatar: avatarUrl.value });
    } else {
      ElMessage.error("获取头像失败");
    }
  } catch (error) {
    console.error("Error fetching avatar:", error);
    ElMessage.error("获取头像时出错");
  }
};

// 上传头像
const handleAvatarChange = async (file: File) => {
  const isImage = file.type.startsWith("image/");
  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }

  const formData = new FormData();
  formData.append("avatar", file); // 直接传递文件对象
  formData.append("user_id", userId.value); // 传入 user_id

  try {
    const uploadResponse = await fetch("http://localhost:6006/auth/update/avatar", {
      method: "POST",
      body: formData
    });

    // 调试输出响应状态码
    console.log("Upload response status:", uploadResponse.status);

    const uploadData = await uploadResponse.json();
    console.log("Upload response data:", uploadData); // 输出返回的数据，便于调试

    if (uploadData.success) {
      ElMessage.success("头像上传成功！");
      updateAvatar(); // 上传成功后，更新头像信息
    } else {
      ElMessage.error("头像上传失败");
    }
  } catch (error) {
    console.error("Error during avatar upload:", error); // 输出错误信息
    ElMessage.error("上传头像时出错");
  }
  return false;
};

// 保存修改用户名
const confirmUpdate = async () => {
  if (username.value === userInfoStore.username) {
    isEditing.value = false;
    ElMessage.info("用户名未修改，无需保存~");
    return;
  }

  try {
    const response = await fetch("http://localhost:6006/auth/update/user_name", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        user_id: userId.value,
        new_user_name: username.value
      })
    });

    const result = await response.json();
    console.log("Update username response:", result);

    if (result.success) {
      // 更新本地的用户信息
      const { user } = result.data;
      userInfoStore.setUserInfo({
        email: user.email,
        username: user.username,
        user_id: user.user_id,
        avatar: user.avatar
      });

      ElMessage.success("用户名修改成功！");
      isEditing.value = false;
    } else {
      ElMessage.error(result.message || "用户名修改失败");
    }
  } catch (error) {
    console.error("Error updating username:", error);
    ElMessage.error("修改用户名时出错");
  }
};
</script>

<style scoped lang="scss">
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;

  .avatar-image {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    margin-bottom: 15px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }

  .upload-avatar {
    text-align: center;
  }
}

.custom-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: left;
  width: 80%;
}

.el-form-item {
  width: 60%; /* 可以调整此值来控制表单宽度 */
}

.info-text {
  margin-left: 15px;
}

.dialog-footer {
  text-align: right;
}
</style>
