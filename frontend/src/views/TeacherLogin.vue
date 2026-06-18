<template>
  <div class="login-container teacher-bg">
    <div class="login-card">
      <div class="login-header">
        <div class="role-badge teacher-badge">教师</div>
        <el-icon :size="40" color="#f56c6c"><House /></el-icon>
        <h1>教师登录</h1>
        <p>酒店模拟经营教学平台</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" prefix-icon="User" placeholder="教师用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" prefix-icon="Lock" type="password" placeholder="密码" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="danger" :loading="loading" style="width: 100%" @click="handleLogin">教师登录</el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <router-link to="/login" class="back-link">
          <el-icon><ArrowLeft /></el-icon> 返回选择身份
        </router-link>
        <span>
          还没有账号？<router-link to="/register?role=teacher">立即注册</router-link>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入教师用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await userStore.login({ ...form, role: 'teacher' })
    if (data.user.role !== 'teacher') {
      ElMessage.error('该账号不是教师身份，请选择正确的登录入口')
      await userStore.logout()
      return
    }
    ElMessage.success('登录成功')
    router.push('/classrooms')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.teacher-bg {
  background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 50%, #fbc2eb 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.role-badge {
  display: inline-block;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
}
.teacher-badge {
  background: linear-gradient(135deg, #f56c6c, #e6404a);
  color: #fff;
}
.login-header h1 {
  font-size: 22px;
  color: #303133;
  margin: 12px 0 4px;
}
.login-header p {
  font-size: 14px;
  color: #909399;
}
.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #909399;
}
.login-footer a {
  color: #f56c6c;
  text-decoration: none;
}
.back-link {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
