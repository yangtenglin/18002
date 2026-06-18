<template>
  <div class="role-select-container">
    <div class="role-select-card">
      <div class="role-select-header">
        <el-icon :size="48" color="#409eff"><House /></el-icon>
        <h1>酒店模拟经营教学平台</h1>
        <p>管理类课程模拟实践教学系统</p>
      </div>
      <div class="role-select-body">
        <h3>请选择您的身份</h3>
        <div class="role-cards">
          <div class="role-card teacher" @click="goLogin('teacher')">
            <div class="role-icon">
              <el-icon :size="56"><UserFilled /></el-icon>
            </div>
            <div class="role-name">教师登录</div>
            <div class="role-desc">创建班级、管理团队、启动模拟经营</div>
          </div>
          <div class="role-card student" @click="goLogin('student')">
            <div class="role-icon">
              <el-icon :size="56"><User /></el-icon>
            </div>
            <div class="role-name">学生登录</div>
            <div class="role-desc">参与模拟经营、提交决策、查看排名</div>
          </div>
        </div>
      </div>
      <div class="role-select-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goLogin = (role) => {
  router.push(`/login/${role}`)
}
</script>

<style scoped>
.role-select-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.role-select-card {
  width: 600px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.role-select-header {
  text-align: center;
  margin-bottom: 36px;
}
.role-select-header h1 {
  font-size: 24px;
  color: #303133;
  margin: 12px 0 4px;
}
.role-select-header p {
  font-size: 14px;
  color: #909399;
}
.role-select-body {
  text-align: center;
}
.role-select-body h3 {
  font-size: 16px;
  color: #606266;
  margin-bottom: 24px;
}
.role-cards {
  display: flex;
  gap: 24px;
  justify-content: center;
}
.role-card {
  flex: 1;
  padding: 32px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}
.role-card.teacher {
  background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
  border-color: #f56c6c33;
}
.role-card.teacher:hover {
  border-color: #f56c6c;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(245, 108, 108, 0.25);
}
.role-card.student {
  background: linear-gradient(135deg, #f0f9ff 0%, #d9ecff 100%);
  border-color: #409eff33;
}
.role-card.student:hover {
  border-color: #409eff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.25);
}
.role-icon {
  margin-bottom: 12px;
}
.role-card.teacher .role-icon {
  color: #f56c6c;
}
.role-card.student .role-icon {
  color: #409eff;
}
.role-name {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.role-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}
.role-select-footer {
  text-align: center;
  font-size: 14px;
  color: #909399;
  margin-top: 32px;
}
.role-select-footer a {
  color: #409eff;
  text-decoration: none;
}
</style>
