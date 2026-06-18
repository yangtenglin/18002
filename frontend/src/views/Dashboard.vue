<template>
  <div class="page-container">
    <div class="page-header">
      <h2>数据看板 - {{ dashboard.game?.name }}</h2>
      <el-button @click="fetchDashboard">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <div v-if="dashboard.game" class="stat-cards">
      <div class="stat-card">
        <div class="label">当前回合</div>
        <div class="value primary">第 {{ dashboard.game.current_round }} 回合</div>
      </div>
      <div class="stat-card">
        <div class="label">参与团队</div>
        <div class="value">{{ dashboard.cumulative_results?.length || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="label">最高分</div>
        <div class="value success">{{ topScore }}</div>
      </div>
      <div class="stat-card">
        <div class="label">最高利润</div>
        <div class="value warning">{{ topProfit }}</div>
      </div>
    </div>

    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>各团队利润趋势</span></template>
          <v-chart :option="profitChartOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>各团队评分趋势</span></template>
          <v-chart :option="scoreChartOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>当前回合入住率</span></template>
          <v-chart :option="occupancyChartOption" style="height: 300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>市场份额分布</span></template>
          <v-chart :option="marketShareChartOption" style="height: 300px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header><span>当前回合详细数据</span></template>
      <el-table :data="dashboard.current_round_results" stripe>
        <el-table-column prop="team_name" label="团队" width="120" />
        <el-table-column label="入住率-标准" width="110">
          <template #default="{ row }">{{ (row.occupancy_rate_standard * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="入住率-豪华" width="110">
          <template #default="{ row }">{{ (row.occupancy_rate_deluxe * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="入住率-套房" width="110">
          <template #default="{ row }">{{ (row.occupancy_rate_suite * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="总收入" width="120">
          <template #default="{ row }">¥{{ row.revenue_total?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="总成本" width="120">
          <template #default="{ row }">¥{{ row.cost_total?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="利润" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.profit >= 0 ? '#67c23a' : '#f56c6c' }">
              ¥{{ row.profit?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="满意度" width="90">
          <template #default="{ row }">{{ row.customer_satisfaction?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column label="市场份额" width="100">
          <template #default="{ row }">{{ (row.market_share * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <el-tag :type="row.score >= 60 ? 'success' : row.score >= 30 ? 'warning' : 'danger'" size="small">
              {{ row.score?.toFixed(1) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { dashboardApi } from '../api'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent,
} from 'echarts/components'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const route = useRoute()
const gameId = route.params.id

const dashboard = ref({ game: {}, current_round_results: [], cumulative_results: [], round_history: [] })

const topScore = computed(() => {
  const results = dashboard.value.cumulative_results
  if (!results?.length) return '-'
  return results[0]?.final_score?.toFixed(1) || '-'
})

const topProfit = computed(() => {
  const results = dashboard.value.cumulative_results
  if (!results?.length) return '-'
  const max = Math.max(...results.map(r => r.total_profit))
  return '¥' + max.toLocaleString()
})

const getTeamColors = () => {
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6', '#1abc9c', '#e74c3c']
  return colors
}

const buildTeamSeriesData = (field) => {
  const history = dashboard.value.round_history || []
  const teamMap = {}
  history.forEach(r => {
    if (!teamMap[r.team_name]) teamMap[r.team_name] = {}
    teamMap[r.team_name][r.round_number] = r[field]
  })
  const teamNames = Object.keys(teamMap)
  const rounds = [...new Set(history.map(r => r.round_number))].sort((a, b) => a - b)
  const colors = getTeamColors()
  return {
    rounds,
    series: teamNames.map((name, i) => ({
      name,
      type: 'line',
      data: rounds.map(r => teamMap[name][r]?.toFixed(2) || null),
      smooth: true,
      itemStyle: { color: colors[i % colors.length] },
    })),
  }
}

const profitChartOption = computed(() => {
  const { rounds, series } = buildTeamSeriesData('profit')
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: rounds.map(r => `第${r}回合`) },
    yAxis: { type: 'value', name: '利润(元)' },
    series,
  }
})

const scoreChartOption = computed(() => {
  const { rounds, series } = buildTeamSeriesData('score')
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: rounds.map(r => `第${r}回合`) },
    yAxis: { type: 'value', name: '评分' },
    series,
  }
})

const occupancyChartOption = computed(() => {
  const results = dashboard.value.current_round_results || []
  const colors = getTeamColors()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['标准间', '豪华间', '套房'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: results.map(r => r.team_name) },
    yAxis: { type: 'value', name: '入住率', axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '标准间', type: 'bar', data: results.map(r => (r.occupancy_rate_standard * 100).toFixed(1)), itemStyle: { color: colors[0] } },
      { name: '豪华间', type: 'bar', data: results.map(r => (r.occupancy_rate_deluxe * 100).toFixed(1)), itemStyle: { color: colors[1] } },
      { name: '套房', type: 'bar', data: results.map(r => (r.occupancy_rate_suite * 100).toFixed(1)), itemStyle: { color: colors[2] } },
    ],
  }
})

const marketShareChartOption = computed(() => {
  const results = dashboard.value.current_round_results || []
  const colors = getTeamColors()
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: results.map((r, i) => ({
        name: r.team_name,
        value: (r.market_share * 100).toFixed(1),
        itemStyle: { color: colors[i % colors.length] },
      })),
    }],
  }
})

const fetchDashboard = async () => {
  dashboard.value = await dashboardApi.overview(gameId)
}

onMounted(fetchDashboard)
</script>
