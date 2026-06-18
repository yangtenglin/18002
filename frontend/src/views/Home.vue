<template>
  <div class="page-container">
    <div class="welcome-section">
      <h1>欢迎回来，{{ userStore.user?.username }}</h1>
      <p>{{ userStore.isTeacher ? '管理您的班级和模拟经营课程' : '参与酒店模拟经营实战学习' }}</p>
    </div>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="label">我的班级</div>
        <div class="value primary">{{ stats.classrooms }}</div>
      </div>
      <div class="stat-card">
        <div class="label">进行中的模拟</div>
        <div class="value success">{{ stats.runningGames }}</div>
      </div>
      <div class="stat-card">
        <div class="label">总模拟数</div>
        <div class="value">{{ stats.totalGames }}</div>
      </div>
      <div class="stat-card">
        <div class="label">角色</div>
        <div class="value" :class="userStore.isTeacher ? 'danger' : 'success'">
          {{ userStore.isTeacher ? '教师' : '学生' }}
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button v-if="userStore.isTeacher" type="primary" @click="$router.push('/classrooms')">
              <el-icon><School /></el-icon> 班级管理
            </el-button>
            <el-button type="success" @click="$router.push('/games')">
              <el-icon><Monitor /></el-icon> 模拟经营
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>平台说明</span>
          </template>
          <el-timeline>
            <el-timeline-item timestamp="第1步" placement="top" color="#409eff">
              教师创建班级并分组
            </el-timeline-item>
            <el-timeline-item timestamp="第2步" placement="top" color="#67c23a">
              教师启动模拟经营游戏
            </el-timeline-item>
            <el-timeline-item timestamp="第3步" placement="top" color="#e6a23c">
              学生团队提交经营决策
            </el-timeline-item>
            <el-timeline-item timestamp="第4步" placement="top" color="#f56c6c">
              系统自动计算经营结果与评分排名
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { classroomApi, gameApi } from '../api'

const userStore = useUserStore()

const stats = ref({
  classrooms: 0,
  runningGames: 0,
  totalGames: 0,
})

onMounted(async () => {
  try {
    const [classrooms, games] = await Promise.all([
      classroomApi.list(),
      gameApi.list(),
    ])
    stats.value.classrooms = classrooms.length || 0
    stats.value.totalGames = games.length || 0
    stats.value.runningGames = games.filter(g => g.status === 'running').length || 0
  } catch {
    // ignore
  }
})
</script>

<style scoped>
.welcome-section {
  margin-bottom: 24px;
}
.welcome-section h1 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 4px;
}
.welcome-section p {
  color: #909399;
  font-size: 14px;
}
.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
