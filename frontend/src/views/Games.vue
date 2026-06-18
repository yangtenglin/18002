<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模拟经营</h2>
      <el-button v-if="userStore.isTeacher" type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建模拟
      </el-button>
    </div>

    <el-table :data="games" v-loading="loading" stripe>
      <el-table-column prop="name" label="模拟名称" min-width="150" />
      <el-table-column prop="class_room_name" label="所属班级" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="回合" width="100">
        <template #default="{ row }">{{ row.current_round }} / {{ row.total_rounds }}</template>
      </el-table-column>
      <el-table-column prop="teams_count" label="团队数" width="80" />
      <el-table-column label="提交情况" width="120">
        <template #default="{ row }">
          <span v-if="row.current_round > 0">{{ row.submitted_count }} / {{ row.teams_count }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/games/${row.id}`)">详情</el-button>
          <el-button size="small" type="success" @click="$router.push(`/games/${row.id}/dashboard`)">看板</el-button>
          <el-button size="small" type="warning" @click="$router.push(`/games/${row.id}/ranking`)">排名</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" title="创建模拟" width="600px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="模拟名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入模拟名称" />
        </el-form-item>
        <el-form-item label="所属班级" prop="class_room">
          <el-select v-model="createForm.class_room" placeholder="选择班级" style="width: 100%">
            <el-option v-for="c in myClassrooms" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总回合数" prop="total_rounds">
          <el-input-number v-model="createForm.total_rounds" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { gameApi, classroomApi } from '../api'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const games = ref([])
const myClassrooms = ref([])
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref()

const createForm = reactive({ name: '', class_room: '', total_rounds: 8, description: '' })
const createRules = {
  name: [{ required: true, message: '请输入模拟名称', trigger: 'blur' }],
  class_room: [{ required: true, message: '请选择班级', trigger: 'change' }],
  total_rounds: [{ required: true, message: '请设置回合数', trigger: 'change' }],
}

const statusType = (s) => ({ draft: 'info', running: 'success', paused: 'warning', finished: 'danger' }[s] || 'info')
const statusLabel = (s) => ({ draft: '草稿', running: '进行中', paused: '暂停', finished: '已结束' }[s] || s)

const fetchGames = async () => {
  loading.value = true
  try {
    games.value = await gameApi.list()
  } finally {
    loading.value = false
  }
}

const fetchClassrooms = async () => {
  if (userStore.isTeacher) {
    myClassrooms.value = await classroomApi.list()
  }
}

const handleCreate = async () => {
  await createFormRef.value.validate()
  createLoading.value = true
  try {
    await gameApi.create(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.class_room = ''
    createForm.total_rounds = 8
    createForm.description = ''
    fetchGames()
  } finally {
    createLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchGames(), fetchClassrooms()])
})
</script>
