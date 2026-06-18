<template>
  <div class="page-container">
    <div class="page-header">
      <h2>积分排名</h2>
      <el-button @click="fetchRanking">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-card style="margin-bottom: 20px">
      <template #header><span>综合排名</span></template>
      <el-table :data="rankings" stripe>
        <el-table-column label="排名" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.rank === 1 ? 'danger' : row.rank === 2 ? 'warning' : row.rank === 3 ? 'success' : 'info'"
              size="large"
              round
            >
              {{ row.rank }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="team_name" label="团队" width="150" />
        <el-table-column label="已完成回合" width="120">
          <template #default="{ row }">{{ row.rounds_played }}</template>
        </el-table-column>
        <el-table-column label="总收入" width="140">
          <template #default="{ row }">¥{{ row.total_revenue?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="总成本" width="140">
          <template #default="{ row }">¥{{ row.total_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="总利润" width="140">
          <template #default="{ row }">
            <span :style="{ color: row.total_profit >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
              ¥{{ row.total_profit?.toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="平均满意度" width="120">
          <template #default="{ row }">{{ row.avg_satisfaction?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column label="平均市场份额" width="120">
          <template #default="{ row }">{{ (row.avg_market_share * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="综合评分" width="120">
          <template #default="{ row }">
            <span style="font-size: 18px; font-weight: 700; color: #409eff">
              {{ row.final_score?.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="rankings.length > 0">
      <template #header><span>评分对比图</span></template>
      <v-chart :option="chartOption" style="height: 400px" autoresize />
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
import { BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'

use([CanvasRenderer, BarChart, TitleComponent, TooltipComponent, GridComponent])

const route = useRoute()
const gameId = route.params.id
const rankings = ref([])

const chartOption = computed(() => {
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9b59b6']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['综合评分', '总利润(万)'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: rankings.value.map(r => r.team_name) },
    yAxis: [
      { type: 'value', name: '评分' },
      { type: 'value', name: '利润(万元)', axisLabel: { formatter: '{value}' } },
    ],
    series: [
      {
        name: '综合评分',
        type: 'bar',
        data: rankings.value.map(r => r.final_score?.toFixed(1)),
        itemStyle: { color: colors[0] },
      },
      {
        name: '总利润(万)',
        type: 'bar',
        yAxisIndex: 1,
        data: rankings.value.map(r => (r.total_profit / 10000)?.toFixed(1)),
        itemStyle: { color: colors[1] },
      },
    ],
  }
})

const fetchRanking = async () => {
  rankings.value = await dashboardApi.ranking(gameId)
}

onMounted(fetchRanking)
</script>
