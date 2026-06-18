<template>
  <div class="page-container">
    <div class="page-header">
      <h2>班级管理</h2>
      <el-button v-if="userStore.isTeacher" type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建班级
      </el-button>
    </div>

    <el-table :data="classrooms" v-loading="loading" stripe>
      <el-table-column prop="name" label="班级名称" />
      <el-table-column prop="code" label="班级代码" width="120" />
      <el-table-column prop="teams_count" label="团队数" width="100" />
      <el-table-column prop="students_count" label="学生数" width="100" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '活跃' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/classrooms/${row.id}`)">详情</el-button>
          <el-button v-if="userStore.isTeacher" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" title="创建班级" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="班级描述（选填）" />
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
import { classroomApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const classrooms = ref([])
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref()

const createForm = reactive({ name: '', description: '' })
const createRules = {
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchClassrooms = async () => {
  loading.value = true
  try {
    classrooms.value = await classroomApi.list()
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  await createFormRef.value.validate()
  createLoading.value = true
  try {
    await classroomApi.create(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    fetchClassrooms()
  } finally {
    createLoading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除班级"${row.name}"吗？`, '确认删除', { type: 'warning' })
  await classroomApi.delete(row.id)
  ElMessage.success('已删除')
  fetchClassrooms()
}

onMounted(fetchClassrooms)
</script>
