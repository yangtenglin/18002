# 酒店模拟经营教学平台 - 项目说明文档

## 一、项目概述

本项目是一个面向酒店管理或商科教学场景的**模拟经营教学平台**。教师可以创建班级、组建团队、发起多回合的酒店经营模拟；学生以团队为单位，通过制定定价、营销、餐饮、人员培训等经营决策参与模拟竞争；系统根据仿真引擎算法自动计算经营结果并排名。

### 核心目标
- 将课堂理论知识转化为实战决策训练
- 多团队竞争博弈，体验真实商业环境
- 数据可视化看板，辅助复盘分析

---

## 二、技术栈

| 模块 | 技术 | 版本/说明 |
|---|---|---|
| 前端 | Vue 3 + Vite | `<script setup>` SFC 语法 |
| UI 组件库 | Element Plus | v2.14.2 |
| 图表 | ECharts 6 + vue-echarts | 可视化数据看板 |
| 状态管理 | Pinia | v3.0.4 |
| 路由 | Vue Router 4 | 含角色路由守卫 |
| HTTP 客户端 | Axios | v1.18.0 |
| 后端 | Django 4+ | Python 3 |
| API 框架 | Django REST Framework | Session 认证 |
| 数据库 | SQLite 3 | `backend/db.sqlite3` |
| 跨域 | django-cors-headers | 开发环境全允许 |

---

## 三、项目结构

```
/Users/linyile/projects/new/2
├── backend/                          # Django 后端
│   ├── backend/                      # Django 项目配置
│   │   ├── settings.py               # 全局配置
│   │   ├── urls.py                   # 路由入口
│   │   └── ...
│   ├── users/                        # 用户模块（注册/登录/角色）
│   ├── classes/                      # 班级 & 团队
│   ├── simulation/                   # 模拟游戏 & 参数
│   │   └── engine.py                 # ★ 核心仿真引擎
│   ├── decisions/                    # 学生决策提交
│   ├── dashboard/                    # 结果看板 & 排名
│   ├── manage.py
│   └── setup_testdata.py             # 测试数据初始化脚本
└── frontend/                         # Vue 3 前端
    ├── src/
    │   ├── api/index.js              # Axios API 封装
    │   ├── router/index.js           # 路由配置（含角色守卫）
    │   ├── stores/user.js            # Pinia 用户状态
    │   ├── views/                    # 页面组件
    │   │   ├── Home.vue              # 首页 / 控制台
    │   │   ├── Register.vue          # 注册
    │   │   ├── StudentLogin.vue      # 学生登录
    │   │   ├── TeacherLogin.vue      # 教师登录
    │   │   ├── Classrooms.vue        # 班级列表（教师）
    │   │   ├── ClassroomDetail.vue   # 班级详情/团队管理（教师）
    │   │   ├── Games.vue             # 模拟列表
    │   │   ├── GameDetail.vue        # 模拟详情/控制（教师）
    │   │   ├── DecisionSubmit.vue    # ★ 提交经营决策（学生）
    │   │   ├── Dashboard.vue         # ★ 数据看板（图表）
    │   │   └── Ranking.vue           # 综合排名
    │   └── layout/MainLayout.vue     # 主布局（导航栏）
    └── package.json
```

---

## 四、启动与运行说明

### 4.1 环境要求
- Python ≥ 3.9
- Node.js ≥ 16
- npm 或 pnpm

### 4.2 后端启动

```bash
cd /Users/linyile/projects/new/2/backend

# 1. 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install django djangorestframework django-cors-headers

# 3. 初始化数据库（首次）
python manage.py makemigrations
python manage.py migrate

# 4. 创建超级管理员（可选，用于后台 /admin）
python manage.py createsuperuser

# 5. 启动服务
python manage.py runserver
# 后端将运行在 http://localhost:8000
```

### 4.3 前端启动

```bash
cd /Users/linyile/projects/new/2/frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
# 前端将运行在 http://localhost:5173
# Vite 已配置 /api 代理到 http://localhost:8000
```

### 4.4 快速初始化测试数据

项目提供了 `setup_testdata.py` 脚本，可一键生成班级、团队、模拟游戏及首回合决策数据：

```bash
cd backend
python setup_testdata.py
```

> 注意：运行脚本前需确保已存在用户 `teacher1` 和至少 4 名学生账号。可先通过注册页面创建，或通过 Django shell 创建。

---

## 五、数据模型（ER 关系）

| 模型 | 文件 | 核心字段 |
|---|---|---|
| **User** | [users/models.py](file:///Users/linyile/projects/new/2/backend/users/models.py#L5-L19) | username, password, role(teacher/student), student_id |
| **ClassRoom** | [classes/models.py](file:///Users/linyile/projects/new/2/backend/classes/models.py#L5-L18) | name, code, teacher(FK), is_active |
| **Team** | [classes/models.py](file:///Users/linyile/projects/new/2/backend/classes/models.py#L21-L34) | name, class_room(FK), members(M2M), captain(FK) |
| **Game** | [simulation/models.py](file:///Users/linyile/projects/new/2/backend/simulation/models.py#L5-L28) | name, class_room(FK), status, current_round, total_rounds |
| **GameParameter** | [simulation/models.py](file:///Users/linyile/projects/new/2/backend/simulation/models.py#L31-L47) | game, round_number, seasonal_factor, economic_factor, competition_intensity, cost_inflation_rate |
| **Decision** | [decisions/models.py](file:///Users/linyile/projects/new/2/backend/decisions/models.py#L7-L28) | team, game, round_number, 三类房价, 4项预算, service_quality_target, is_submitted |
| **RoundResult** | [dashboard/models.py](file:///Users/linyile/projects/new/2/backend/dashboard/models.py#L6-L33) | team, game, round_number, 入住率, 收入, 成本, 利润, 满意度, 市场份额, score |
| **CumulativeResult** | [dashboard/models.py](file:///Users/linyile/projects/new/2/backend/dashboard/models.py#L36-L55) | team, game, rounds_played, total_profit, final_score, rank |

---

## 六、核心仿真引擎算法分析

引擎核心代码位于 [simulation/engine.py](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L7-L197) 的 `SimulationEngine` 类。

### 6.1 常量参数
```python
ROOMS_STANDARD = 60    # 标准间数量
ROOMS_DELUXE = 30      # 豪华间数量
ROOMS_SUITE = 10       # 套房数量
BASE_OCCUPANCY = 0.65  # 基准入住率 65%
BASE_OPERATION_COST_PER_ROOM = 150  # 单房月运营成本
```

### 6.2 算法流程（`calculate_round`）

```
所有团队已提交决策
        ↓
读取该回合 GameParameter（季节/经济/竞争/通胀因子）
        ↓
计算全市场平均房价（三类房型各自的均价）
        ↓
对每个团队：
  ├─ 计算三类房型入住率 _calc_occupancy()
  ├─ 计算客房收入 = 房间数 × 入住率 × 30天 × 房价
  ├─ 计算餐饮收入 = 客人总数 × 200 × 餐饮质量因子 × 0.25
  ├─ 计算运营成本 = 总房间数 × 150 × 30 × (1+通胀率)^round
  ├─ 累加营销/培训/装修预算 → 总成本
  ├─ 利润 = 总收入 - 总成本
  └─ 计算客户满意度 _calc_satisfaction()
        ↓
按收入占比计算各团队市场份额
        ↓
归一化计算回合评分（利润40% + 收入25% + 满意度20% + 市场份额15%）
        ↓
写入 RoundResult，更新 CumulativeResult（含最终排名）
```

### 6.3 入住率计算公式（`_calc_occupancy`）

```python
occupancy = BASE_OCCUPANCY × (avg_rate / rate)
          × seasonal_factor × economic_factor
          + min(marketing_budget / 50000, 1.5) × 0.15
          + (1 - competition_intensity) × 0.1
```

含义拆解：
- **价格竞争力**：`avg_rate / rate`，本团队定价低于市场均价则入住率提升，反之下降
- **环境因子**：`seasonal_factor`（季节性）和 `economic_factor`（宏观经济）由教师配置
- **营销效果**：营销预算越高 → 入住率越高，5万元达到 15% 上限后边际收益归零
- **竞争效应**：市场竞争强度越低 → 入住率越高（常数项）

### 6.4 客户满意度计算公式（`_calc_satisfaction`）

满意度采用加权平均：
- **服务质量（权重30%）**：`service_quality_target / 10 × 3`
- **装修效果（权重20%）**：`min(renovation_budget / 50000, 1.5) × 2`
- **价格满意度（权重30%）**：`(market_avg / my_avg) × 3`
- **餐饮体验（权重20%）**：`min(food_budget / 50000, 1.5) × 2`

最后 `× 10 / 3` 映射到 0~10 分区间。

### 6.5 评分公式（`_calculate_scores`）

采用**相对归一化**（每个维度除以所有团队的最大值）：
```
profit_score        = (profit / max_profit)        × 40
revenue_score       = (revenue / max_revenue)      × 25
satisfaction_score  = (satisfaction / max_sat)     × 20
market_score        = market_share × 100 × 0.15    → 等于 market_share × 15
round_score = 四项之和，最低 0
```

### 6.6 综合最终得分（`_update_cumulative_results`）

```python
final_score = (round_score_sum / rounds_played) × (1 + total_profit / max(total_revenue, 1))
```

即：**平均回合得分 × (1 + 累计利润率)**，奖励长期盈利能力。

---

## 七、分角色功能讲解

### 7.1 教师端（Teacher）

| 功能 | 页面/API | 说明 |
|---|---|---|
| **账号注册登录** | [Register.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Register.vue) / `POST /api/auth/register/` | 注册时 role 选择 teacher |
| **班级管理** | [Classrooms.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Classrooms.vue) / `POST /api/classrooms/` | 创建班级，系统自动生成 8 位邀请码 |
| **团队组建** | [ClassroomDetail.vue](file:///Users/linyile/projects/new/2/frontend/src/views/ClassroomDetail.vue) / `POST /api/classrooms/{id}/teams/` | 手动创建团队、添加/移除学生成员 |
| **创建模拟** | [Games.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Games.vue) / `POST /api/games/` | 指定班级、总回合数（默认 8 回合），系统自动生成每回合参数 |
| **参数配置** | [GameDetail.vue](file:///Users/linyile/projects/new/2/frontend/src/views/GameDetail.vue#L86-L119) / `PUT /api/games/{gid}/parameters/{pid}/` | 调整每回合季节/经济/竞争/通胀因子 |
| **启动/暂停模拟** | [GameDetail.vue](file:///Users/linyile/projects/new/2/frontend/src/views/GameDetail.vue#L36-L57) / `POST /api/games/{id}/start/` | 控制模拟生命周期（draft→running→paused→finished） |
| **结算推进回合** | [GameDetail.vue](file:///Users/linyile/projects/new/2/frontend/src/views/GameDetail.vue#L52-L57) / `POST /api/games/{id}/advance-round/` | **调用引擎结算当前回合**，所有团队决策计算完毕后进入下一回合 |
| **数据看板** | [Dashboard.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Dashboard.vue) / `GET /api/games/{id}/dashboard/` | 利润趋势、评分趋势、入住率对比、市场份额饼图、详细数据表格 |
| **综合排名** | [Ranking.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Ranking.vue) / `GET /api/games/{id}/ranking/` | 按 `final_score` 排名展示累计成绩 |

### 7.2 学生端（Student）

| 功能 | 页面/API | 说明 |
|---|---|---|
| **账号注册登录** | [Register.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Register.vue) / `POST /api/auth/register/` | 注册时 role 选 student，可填写学号 |
| **加入团队** | 由教师分配 | 教师在班级详情中把学生加入某团队 |
| **查看模拟列表** | [Games.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Games.vue) / `GET /api/games/` | 仅显示自己所在团队的班级的模拟 |
| **提交经营决策** | [DecisionSubmit.vue](file:///Users/linyile/projects/new/2/frontend/src/views/DecisionSubmit.vue) / `POST /api/games/{id}/decisions/` | ★ 核心页面。每回合提交一次：三类房价、餐饮/营销/培训/装修预算、服务质量目标 |
| **查看决策结果** | [Dashboard.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Dashboard.vue) / `GET /api/games/{id}/dashboard/` | 教师结算回合后可查看本团队及全市场数据 |
| **查看排名** | [Ranking.vue](file:///Users/linyile/projects/new/2/frontend/src/views/Ranking.vue) | 查看累计成绩排名 |

### 7.3 业务流转时序

```
教师                      系统                        学生
 │                         │                           │
 ├─ 创建班级 ──────────────▶│                           │
 ├─ 创建团队并分配成员 ────▶│                           │
 ├─ 创建模拟游戏 ──────────▶│─ 生成 GameParameter ─────▶│
 ├─ 启动模拟（R1）────────▶│                           │
 │                         │◀───────── 提交 R1 决策 ───┤
 │                         │                           │
 ├─ 结算推进回合 ──────────▶│─ 调用 SimulationEngine ──▶│
 │                         │─ 写入 RoundResult ───────▶│
 │                         │─ 更新 CumulativeResult ──▶│
 │                         │◀───────── 提交 R2 决策 ───┤
 │                         │                           │
 │          ┌──────── 重复 N 回合 ────────┐            │
 │          └─────────────────────────────┘            │
 ├─ 查看 Dashboard / Ranking ◀─── 查询数据 ────────────┤
```

---

## 八、后端 API 接口一览

详见 [backend/urls.py](file:///Users/linyile/projects/new/2/backend/backend/urls.py#L22-L50)

### 认证
| Method | Path | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register/` | 公开 | 注册 |
| POST | `/api/auth/login/` | 公开 | 登录（需传 role 校验） |
| POST | `/api/auth/logout/` | 登录 | 登出 |
| GET | `/api/auth/me/` | 登录 | 当前用户信息 |

### 班级 & 团队
| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET/POST | `/api/classrooms/` | 教师可写 | 班级列表/创建 |
| GET/PUT/DELETE | `/api/classrooms/{id}/` | 教师 | 班级详情/修改/删除 |
| GET/POST | `/api/classrooms/{cid}/teams/` | 教师 | 团队列表/创建 |
| GET/PUT/DELETE | `/api/classrooms/{cid}/teams/{tid}/` | 教师 | 团队详情/修改/删除 |
| POST | `/api/classrooms/{cid}/teams/{tid}/add-members/` | 教师 | 批量添加成员 |
| POST | `/api/classrooms/{cid}/teams/{tid}/remove-members/` | 教师 | 批量移除成员 |

### 模拟游戏
| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET/POST | `/api/games/` | 教师可写 | 模拟列表/创建 |
| GET/PUT/DELETE | `/api/games/{id}/` | 教师 | 模拟详情/修改/删除 |
| POST | `/api/games/{id}/start/` | 教师 | 启动模拟 |
| POST | `/api/games/{id}/pause/` | 教师 | 暂停模拟 |
| POST | `/api/games/{id}/advance-round/` | 教师 | ★ 结算当前回合 + 推进 |
| GET | `/api/games/{gid}/parameters/` | 登录 | 获取回合参数列表 |
| PUT | `/api/games/{gid}/parameters/{pid}/` | 教师 | 修改回合参数 |

### 决策
| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET/POST | `/api/games/{gid}/decisions/` | 登录 | 决策列表/提交 |
| GET/PUT | `/api/games/{gid}/decisions/{did}/` | 登录 | 决策详情/修改（未提交时） |
| GET | `/api/games/{gid}/my-decision/` | 学生 | 我的当前回合决策 |

### 看板 & 排名
| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/games/{gid}/dashboard/` | 登录 | 综合看板数据 |
| GET | `/api/games/{gid}/ranking/` | 登录 | 累计排名 |
| GET | `/api/games/{gid}/results/{round}/` | 登录 | 单回合结果 |
| GET | `/api/games/{gid}/trend/{team_id}/` | 登录 | 单团队回合趋势 |

---

## 九、算法改进空间与优化建议

### 9.1 当前算法的局限性

#### 🔴 问题 1：入住率模型过于线性
当前 [_calc_occupancy](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L115-L123) 使用 `avg_rate / rate` 简单比值，极端定价会导致结果失真（如定价为均价 2 倍时入住率仅 32.5%，但现实中不会如此剧烈）。

**改进建议**：使用 Sigmoid 或对数函数平滑价格敏感度：
```python
# 推荐替换方案
price_ratio = avg_rate / max(rate, 1)
price_effect = 1 / (1 + math.exp(-(price_ratio - 1) * 3))  # Sigmoid，在 ratio=1 附近过渡平滑
occupancy = BASE_OCCUPANCY * (0.5 + price_effect)
```

#### 🔴 问题 2：满意度与实际决策变量弱耦合
`staff_training_budget`（员工培训预算）在满意度公式中**完全未使用**！见 [_calc_satisfaction](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L125-L138)。培训预算仅体现在成本中，对评分无正向贡献，会导致学生理性策略为培训预算=0。

**改进建议**：将培训预算纳入服务质量计算：
```python
training_effect = min(decision.staff_training_budget / 50000, 1.5)
service_score = (min(decision.service_quality_target / 10, 1.0) * 0.6 + training_effect * 0.4) * 3
```

#### 🔴 问题 3：餐饮收入计算逻辑混乱
[engine.py#L91-L97](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L91-L97) 中餐饮收入公式：
```
总客人 × 200 × 餐饮质量因子 × 0.25
```
其中 200 是硬编码的"基准餐饮消费"，0.25 是 `BASE_FOOD_REVENUE_RATIO`，但两者相乘后含义不清。且 `food_quality_factor` 在 budget=0 时取 0.3（意味着不投餐饮预算仍有 30% 质量），缺乏经济学依据。

**改进建议**：拆分为"餐饮转化率 × 人均消费"：
```python
conversion_rate = 0.4 + min(decision.food_budget / 50000, 1.0) * 0.4   # 40%~80%客人用餐
per_capita = 120 + min(decision.food_budget / 50000, 1.5) * 80         # 人均120~240元
result.revenue_food = total_rooms_occupied * 30 * conversion_rate * per_capita
```

#### 🟡 问题 4：评分的相对归一化导致"零和博弈"
[_calculate_scores](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L149-L162) 中所有维度都除以团队间最大值，这意味着某团队做得好会**压低其他团队的分数**。教学场景中更适合采用"绝对基准+相对排名"的混合方式。

**改进建议**：设置行业基准值，偏离基准扣分：
```python
# 示例：利润评分改为绝对值为主
industry_profit_per_room = 50000  # 单房月利润行业基准
benchmark_profit = total_rooms * 30 * industry_profit_per_room
profit_score = min(r.profit / benchmark_profit, 1.0) * 40
```

#### 🟡 问题 5：缺少跨回合的持续性变量
- 装修预算是"当期花当期受益"，但现实中装修应持续受益 3~5 回合，效果递减
- 客户满意度应具有滞后效应（上一回合满意度影响本回合口碑/入住率）
- 缺少品牌资产/累计市场份额对入住率的正向反馈

**改进建议**：
```python
# 在 CumulativeResult 中累计 renovation_investment
# 入住率增加：brand_effect = min(cumulative_market_share * 0.3, 0.05)
# 装修效果按折旧：renovation_remaining = Σ(renovation_budget_t × 0.5^(current_round - t))
```

#### 🟡 问题 6：市场份额计算不区分房型
当前按总收入一刀切，实际上低价团队靠标准间走量、高价团队靠套房高单价，两者市场定位不同，直接比较份额有失公允。

#### 🟢 问题 7：缺少随机扰动
当前所有计算都是确定性的，学生在第 1 回合摸清公式后就能精确预测结果，失去了模拟的"探索性"。

**改进建议**：在入住率和餐饮收入上加入 ±5% 的随机噪声（固定种子保证可复盘）：
```python
random.seed(hash((game.pk, round_number, team.pk)))
noise = 1 + random.uniform(-0.05, 0.05)
occupancy *= noise
```

### 9.2 性能优化
[_update_cumulative_results](file:///Users/linyile/projects/new/2/backend/simulation/engine.py#L164-L197) 对每个团队单独查询 N 次数据库，N 回合后复杂度 O(T×R)。

**改进建议**：用 `annotate + aggregate` 一次查询：
```python
from django.db.models import Sum, Avg
round_results = RoundResult.objects.filter(game=game).values('team').annotate(
    total_revenue=Sum('revenue_total'),
    total_profit=Sum('profit'),
    avg_satisfaction=Avg('customer_satisfaction'),
)
```

### 9.3 安全性建议
- [settings.py#L5](file:///Users/linyile/projects/new/2/backend/backend/settings.py#L5) 中 `SECRET_KEY` 已硬编码，生产环境必须从环境变量读取
- [settings.py#L81](file:///Users/linyile/projects/new/2/backend/backend/settings.py#L81) `CORS_ALLOW_ALL_ORIGINS = True` 生产环境应限制具体域名
- 缺少决策提交的"截止时间"校验（可在 Game 上加 `round_deadline` 字段）

---

## 十、总结

| 维度 | 评价 |
|---|---|
| 功能完整性 | ✅ 覆盖教师/学生双角色，模拟全生命周期闭环 |
| 代码结构 | ✅ Django 分 App 组织，Vue 按 views/components 分层，可读性好 |
| 算法合理性 | ⚠️ 核心公式有明显漏洞（培训预算无用、模型线性），需按 §9 优化 |
| 可扩展性 | ⚠️ 引擎常量硬编码在类中，建议抽离到 GameParameter 便于教师配置 |
| 教学实用性 | ✅ ECharts 看板丰富，复盘讨论场景友好 |

建议在投入教学使用前，优先修复 §9.1 中 **问题 2（培训预算无效）** 和 **问题 7（缺少随机性）**，这两个对学生策略体验影响最大。
