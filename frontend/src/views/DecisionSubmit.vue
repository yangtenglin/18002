<template>
  <div class="page-container">
    <div class="page-header">
      <h2>提交经营决策 - 第{{ game.current_round }}回合</h2>
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <el-alert
      v-if="game.status !== 'running'"
      title="当前模拟未在运行中，无法提交决策"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-alert
      v-if="existingDecision?.is_submitted"
      title="本回合已提交决策"
      type="success"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header><span>定价策略</span></template>
          <el-form :model="form" label-width="120px" :disabled="game.status !== 'running' || existingDecision?.is_submitted">
            <el-form-item label="标准间房价">
              <el-input-number v-model="form.room_rate_standard" :min="100" :max="2000" :step="50" />
              <span class="unit">元/晚</span>
            </el-form-item>
            <el-form-item label="豪华间房价">
              <el-input-number v-model="form.room_rate_deluxe" :min="200" :max="3000" :step="50" />
              <span class="unit">元/晚</span>
            </el-form-item>
            <el-form-item label="套房房价">
              <el-input-number v-model="form.room_rate_suite" :min="500" :max="5000" :step="100" />
              <span class="unit">元/晚</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header><span>预算分配</span></template>
          <el-form :model="form" label-width="120px" :disabled="game.status !== 'running' || existingDecision?.is_submitted">
            <el-form-item label="餐饮预算">
              <el-input-number v-model="form.food_budget" :min="0" :max="500000" :step="5000" />
              <span class="unit">元</span>
            </el-form-item>
            <el-form-item label="营销预算">
              <el-input-number v-model="form.marketing_budget" :min="0" :max="500000" :step="5000" />
              <span class="unit">元</span>
            </el-form-item>
            <el-form-item label="员工培训预算">
              <el-input-number v-model="form.staff_training_budget" :min="0" :max="300000" :step="5000" />
              <span class="unit">元</span>
            </el-form-item>
            <el-form-item label="装修改造预算">
              <el-input-number v-model="form.renovation_budget" :min="0" :max="300000" :step="5000" />
              <span class="unit">元</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header><span>服务质量目标</span></template>
          <el-form :model="form" label-width="120px" :disabled="game.status !== 'running' || existingDecision?.is_submitted">
            <el-form-item label="服务质量评分">
              <el-slider v-model="form.service_quality_target" :min="1" :max="10" :step="0.5" show-stops show-input />
            </el-form-item>
          </el-form>
        </el-card>

        <div style="margin-top: 20px; text-align: center">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="game.status !== 'running' || existingDecision?.is_submitted"
            @click="handleSubmit"
          >
            <el-icon><Check /></el-icon> 提交决策
          </el-button>
        </div>
      </el-col>

      <el-col :span="10">
        <el-card>
          <template #header><span>决策摘要</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="标准间">{{ form.room_rate_standard }} 元/晚</el-descriptions-item>
            <el-descriptions-item label="豪华间">{{ form.room_rate_deluxe }} 元/晚</el-descriptions-item>
            <el-descriptions-item label="套房">{{ form.room_rate_suite }} 元/晚</el-descriptions-item>
            <el-descriptions-item label="餐饮预算">{{ formatMoney(form.food_budget) }}</el-descriptions-item>
            <el-descriptions-item label="营销预算">{{ formatMoney(form.marketing_budget) }}</el-descriptions-item>
            <el-descriptions-item label="培训预算">{{ formatMoney(form.staff_training_budget) }}</el-descriptions-item>
            <el-descriptions-item label="装修预算">{{ formatMoney(form.renovation_budget) }}</el-descriptions-item>
            <el-descriptions-item label="服务目标">{{ form.service_quality_target }} 分</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header><span>总预算</span></template>
          <div class="total-budget">
            <div class="budget-item">
              <span>经营预算合计</span>
              <span class="amount">{{ formatMoney(totalBudget) }}</span>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header><span>决策提示</span></template>
          <el-text type="info" size="small">
            <ul>
              <li>定价过高会降低入住率，过低影响利润</li>
              <li>营销投入可提升入住率，但注意投入产出比</li>
              <li>餐饮预算影响客人均消费和满意度</li>
              <li>培训投入提升服务质量，装修提升客户体验</li>
              <li>服务质量目标越高运营成本越大</li>
            </ul>
          </el-text>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { gameApi, decisionApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const gameId = route.params.id

const game = ref({ current_round: 0, status: 'draft' })
const existingDecision = ref(null)
const submitting = ref(false)

const form = reactive({
  team: null,
  room_rate_standard: 500,
  room_rate_deluxe: 800,
  room_rate_suite: 1500,
  food_budget: 50000,
  marketing_budget: 30000,
  staff_training_budget: 20000,
  renovation_budget: 10000,
  service_quality_target: 7.0,
})

const totalBudget = computed(() =>
  form.food_budget + form.marketing_budget + form.staff_training_budget + form.renovation_budget
)

const formatMoney = (val) => {
  if (!val) return '¥0'
  return '¥' + val.toLocaleString()
}

const fetchGame = async () => {
  game.value = await gameApi.get(gameId)
}

const fetchMyDecision = async () => {
  try {
    const data = await decisionApi.myDecision(gameId)
    existingDecision.value = data
    if (data.team) {
      form.team = data.team
    }
    form.room_rate_standard = data.room_rate_standard || 500
    form.room_rate_deluxe = data.room_rate_deluxe || 800
    form.room_rate_suite = data.room_rate_suite || 1500
    form.food_budget = data.food_budget || 50000
    form.marketing_budget = data.marketing_budget || 30000
    form.staff_training_budget = data.staff_training_budget || 20000
    form.renovation_budget = data.renovation_budget || 10000
    form.service_quality_target = data.service_quality_target || 7.0
  } catch (err) {
    if (err?.response?.data?.team_id) {
      form.team = err.response.data.team_id
    }
  }
}

const handleSubmit = async () => {
  await ElMessageBox.confirm('确定提交本回合经营决策吗？提交后不可修改。', '确认提交', { type: 'warning' })
  submitting.value = true
  try {
    await decisionApi.submit(gameId, form)
    ElMessage.success('决策已提交')
    fetchMyDecision()
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchGame(), fetchMyDecision()])
})
</script>

<style scoped>
.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}
.total-budget {
  padding: 10px 0;
}
.budget-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
.budget-item .amount {
  font-size: 20px;
  font-weight: 600;
  color: #e6a23c;
}
ul {
  padding-left: 18px;
  margin: 0;
}
li {
  margin-bottom: 6px;
  line-height: 1.6;
}
</style>
