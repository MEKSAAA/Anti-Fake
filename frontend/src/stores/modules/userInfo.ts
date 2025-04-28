import { defineStore } from "pinia";

export const useUserInfoStore = defineStore("userInfo", {
  state: () => ({
    email: "",
    user_id: "",
    username: "",
    avatar: ""
  }),
  actions: {
    setUserInfo(payload: { email: string; user_id: string; username: string; avatar: string }) {
      this.email = payload.email;
      this.user_id = payload.user_id;
      this.username = payload.username;
      this.avatar = payload.avatar;
    },
    setAvatar(payload: { avatar: string }) {
      this.avatar = payload.avatar;
    },
    clearUserInfo() {
      this.email = "";
      this.user_id = "";
      this.username = "";
      this.avatar = "";
    }
  }
});
