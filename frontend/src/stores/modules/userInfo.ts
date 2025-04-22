import { defineStore } from "pinia";

export const useUserInfoStore = defineStore("userInfo", {
  state: () => ({
    email: "",
    user_id: "",
    username: ""
  }),
  actions: {
    setUserInfo(payload: { email: string; user_id: string; username: string }) {
      this.email = payload.email;
      this.user_id = payload.user_id;
      this.username = payload.username;
    },
    clearUserInfo() {
      this.email = "";
      this.user_id = "";
      this.username = "";
    }
  }
});
