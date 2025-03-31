<template>
  <div>
    <div class="card mb10">
      <h4 class="title">Anti-Fake</h4>
    </div>
    <div class="card mb10">
      <h4 class="title">项目信息</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Gitee" label-align="left">
          <el-link type="primary" href="https://github.com/MEKSAAA/Anti-Fake.git" target="_blank"> Gitee </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="Github" label-align="left">
          <el-link type="primary" href="https://github.com/MEKSAAA/Anti-Fake.git" target="_blank"> Github </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="文档地址" label-align="left">
          <el-link type="primary" href="https://github.com/MEKSAAA/Anti-Fake.git" target="_blank"> 文档地址 </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="预览地址" label-align="left">
          <el-link type="primary" href="https://github.com/MEKSAAA/Anti-Fake.git" target="_blank"> 预览地址 </el-link>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup lang="ts" name="about"></script>

<style lang="scss" scoped>
.card {
  .title {
    margin: 0 0 15px;
    font-size: 17px;
    font-weight: bold;
    color: var(--el-text-color-primary);
  }
  .text {
    font-size: 15px;
    line-height: 25px;
    color: var(--el-text-color-regular);
    .el-link {
      font-size: 15px;
    }
  }
}
</style>
