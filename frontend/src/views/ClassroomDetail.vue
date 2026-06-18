<template>
  <div class="page-container">
    <div class="page-header">
      <h2>班级详情 - {{ classroom.name }}</h2>
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <el-descriptions :column="3" border style="margin-bottom: 20px">
      <el-descriptions-item label="班级代码">{{ classroom.code }}</el-descriptions-item>
      <el-descriptions-item label="团队数">{{ classroom.teams_count }}</el-descriptions-item>
      <el-descriptions-item label="学生数">{{ classroom.students_count }}</el-descriptions-item>
      <el-descriptions-item label="描述" :span="3">{{ classroom.description || '暂无' }}</el-descriptions-item>
    </el-descriptions>

    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>团队列表</span>
          <el-button v-if="userStore.isTeacher" type="primary" size="small" @click="showTeamDialog = true">
            <el-icon><Plus /></el-icon> 创建团队
          </el-button>
        </div>
      </template>

      <el-table :data="teams" stripe>
        <el-table-column prop="name" label="团队名称" />
        <el-table-column label="队长" width="120">
          <template #default="{ row }">{{ row.captain_detail?.username || '-' }}</template>
        </el-table-column>
        <el-table-column label="成员数" width="100">
          <template #default="{ row }">{{ row.members_detail?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="成员" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="m in row.members_detail" :key="m.id" size="small" style="margin: 2px">
              {{ m.username }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="userStore.isTeacher" label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openMemberDialog(row)">管理成员</el-button>
            <el-button size="small" type="danger" @click="deleteTeam(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showTeamDialog" title="创建团队" width="400px">
      <el-form :model="teamForm" label-width="80px">
        <el-form-item label="团队名称">
          <el-input v-model="teamForm.name" placeholder="请输入团队名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTeamDialog = false">取消</el-button>
        <el-button type="primary" @click="createTeam">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showMemberDialog" title="管理团队成员" width="500px">
      <el-transfer
        v-model="selectedMembers"
        :data="allStudents"
        :titles="['可选学生', '团队成员']"
        :props="{ key: 'id', label: 'username' }"
      />
      <template #footer>
        <el-button @click="showMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMembers">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { classroomApi, userApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()
const classroomId = route.params.id

const classroom = ref({})
const teams = ref([])
const allStudents = ref([])
const showTeamDialog = ref(false)
const showMemberDialog = ref(false)
const teamForm = reactive({ name: '' })
const selectedMembers = ref([])
const currentTeam = ref(null)

const fetchClassroom = async () => {
  classroom.value = await classroomApi.get(classroomId)
}

const fetchTeams = async () => {
  teams.value = await classroomApi.teams(classroomId)
}

const fetchStudents = async () => {
  const data = await userApi.list({ role: 'student' })
  allStudents.value = data.map(s => ({ id: s.id, username: s.username, disabled: false }))
}

const createTeam = async () => {
  if (!teamForm.name) {
    ElMessage.warning('请输入团队名称')
    return
  }
  await classroomApi.createTeam(classroomId, teamForm)
  ElMessage.success('创建成功')
  showTeamDialog.value = false
  teamForm.name = ''
  fetchTeams()
}

const deleteTeam = async (row) => {
  await ElMessageBox.confirm(`确定删除团队"${row.name}"吗？`, '确认', { type: 'warning' })
  await classroomApi.deleteTeam(classroomId, row.id)
  ElMessage.success('已删除')
  fetchTeams()
}

const openMemberDialog = (team) => {
  currentTeam.value = team
  selectedMembers.value = team.members_detail?.map(m => m.id) || []
  showMemberDialog.value = true
}

const saveMembers = async () => {
  const team = currentTeam.value
  const existingIds = team.members_detail?.map(m => m.id) || []
  const toAdd = selectedMembers.value.filter(id => !existingIds.includes(id))
  const toRemove = existingIds.filter(id => !selectedMembers.value.includes(id))

  if (toAdd.length > 0) {
    await classroomApi.addMembers(classroomId, team.id, toAdd)
  }
  if (toRemove.length > 0) {
    await classroomApi.removeMembers(classroomId, team.id, toRemove)
  }

  ElMessage.success('成员已更新')
  showMemberDialog.value = false
  fetchTeams()
}

onMounted(async () => {
  await Promise.all([fetchClassroom(), fetchTeams(), fetchStudents()])
})
</script>
