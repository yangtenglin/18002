<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ game.name }}</h2>
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="label">当前状态</div>
        <div class="value" :class="statusClass">{{ statusLabel }}</div>
      </div>
      <div class="stat-card">
        <div class="label">当前回合</div>
        <div class="value primary">{{ game.current_round }} / {{ game.total_rounds }}</div>
      </div>
      <div class="stat-card">
        <div class="label">参与团队</div>
        <div class="value">{{ game.teams_count }}</div>
      </div>
      <div class="stat-card">
        <div class="label">已提交决策</div>
        <div class="value" :class="game.submitted_count === game.teams_count ? 'success' : 'warning'">
          {{ game.submitted_count || 0 }} / {{ game.teams_count }}
        </div>
      </div>
    </div>

    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>模拟控制</span></template>
          <div class="control-buttons">
            <el-button
              v-if="userStore.isTeacher"
              type="success"
              :disabled="game.status !== 'draft' && game.status !== 'paused'"
              @click="startGame"
            >
              <el-icon><VideoPlay /></el-icon> {{ game.status === 'draft' ? '启动模拟' : '继续模拟' }}
            </el-button>
            <el-button
              v-if="userStore.isTeacher && game.status === 'running'"
              type="warning"
              @click="pauseGame"
            >
              <el-icon><VideoPause /></el-icon> 暂停模拟
            </el-button>
            <el-button
              v-if="userStore.isTeacher && game.status === 'running'"
              type="danger"
              @click="advanceRound"
            >
              <el-icon><Right /></el-icon> 结算当前回合 & 推进
            </el-button>
            <el-button
              v-if="game.status === 'running'"
              type="primary"
              @click="$router.push(`/games/${game.id}/decision`)"
            >
              <el-icon><Edit /></el-icon> 提交决策
            </el-button>
            <el-button type="success" @click="$router.push(`/games/${game.id}/dashboard`)">
              <el-icon><DataAnalysis /></el-icon> 数据看板
            </el-button>
            <el-button type="warning" @click="$router.push(`/games/${game.id}/ranking`)">
              <el-icon><Trophy /></el-icon> 排名
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>模拟信息</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="所属班级">{{ game.class_room_name }}</el-descriptions-item>
            <el-descriptions-item label="总回合数">{{ game.total_rounds }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ game.description || '暂无' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="userStore.isTeacher">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>各回合参数配置</span>
        </div>
      </template>
      <el-table :data="game.parameters" stripe size="small" max-height="400">
        <el-table-column prop="round_number" label="回合" width="70" />
        <el-table-column prop="market_base_demand" label="基础需求" width="100" />
        <el-table-column prop="seasonal_factor" label="季节因子" width="100" />
        <el-table-column prop="economic_factor" label="经济因子" width="100" />
        <el-table-column prop="competition_intensity" label="竞争强度" width="100" />
        <el-table-column prop="cost_inflation_rate" label="通胀率" width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="editParameter(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showParamDialog" title="编辑回合参数" width="500px">
      <el-form :model="paramForm" label-width="100px" size="small">
        <el-form-item label="基础需求"><el-input-number v-model="paramForm.market_base_demand" :min="100" :step="100" /></el-form-item>
        <el-form-item label="季节因子"><el-input-number v-model="paramForm.seasonal_factor" :min="0.1" :max="3" :step="0.1" :precision="2" /></el-form-item>
        <el-form-item label="经济因子"><el-input-number v-model="paramForm.economic_factor" :min="0.1" :max="3" :step="0.1" :precision="2" /></el-form-item>
        <el-form-item label="竞争强度"><el-input-number v-model="paramForm.competition_intensity" :min="0" :max="1" :step="0.05" :precision="2" /></el-form-item>
        <el-form-item label="通胀率"><el-input-number v-model="paramForm.cost_inflation_rate" :min="0" :max="0.5" :step="0.01" :precision="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showParamDialog = false">取消</el-button>
        <el-button type="primary" @click="saveParameter">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { gameApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()
const gameId = route.params.id

const game = ref({ parameters: [] })
const showParamDialog = ref(false)
const paramForm = reactive({
  id: null, market_base_demand: 1000, seasonal_factor: 1.0,
  economic_factor: 1.0, competition_intensity: 0.5, cost_inflation_rate: 0.02,
})

const statusLabel = computed(() => {
  const map = { draft: '草稿', running: '进行中', paused: '暂停', finished: '已结束' }
  return map[game.value.status] || game.value.status
})
const statusClass = computed(() => ({
  draft: 'info', running: 'success', paused: 'warning', finished: 'danger',
}[game.value.status] || ''))

const fetchGame = async () => {
  game.value = await gameApi.get(gameId)
}

const startGame = async () => {
  await ElMessageBox.confirm('确定启动模拟吗？启动后将进入第1回合。', '确认', { type: 'info' })
  await gameApi.start(gameId)
  ElMessage.success('模拟已启动')
  fetchGame()
}

const pauseGame = async () => {
  await gameApi.pause(gameId)
  ElMessage.success('模拟已暂停')
  fetchGame()
}

const advanceRound = async () => {
  await ElMessageBox.confirm(
    `确定结算第${game.value.current_round}回合并推进吗？系统将自动计算经营结果。`,
    '确认结算',
    { type: 'warning' }
  )
  await gameApi.advanceRound(gameId)
  ElMessage.success('回合已结算')
  fetchGame()
}

const editParameter = (param) => {
  paramForm.id = param.id
  paramForm.market_base_demand = param.market_base_demand
  paramForm.seasonal_factor = param.seasonal_factor
  paramForm.economic_factor = param.economic_factor
  paramForm.competition_intensity = param.competition_intensity
  paramForm.cost_inflation_rate = param.cost_inflation_rate
  showParamDialog.value = true
}

const saveParameter = async () => {
  const { id, ...data } = paramForm
  await gameApi.updateParameter(gameId, id, data)
  ElMessage.success('参数已更新')
  showParamDialog.value = false
  fetchGame()
}

onMounted(fetchGame)
</script>

<style scoped>
.control-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
