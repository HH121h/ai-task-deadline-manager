---
name: ai-homework-deadline-manager
description: "Use when the user needs to manage homework/task deadlines, prioritize daily work, or track time spent on assignments. Covers recording tasks with deadlines/estimated effort/difficulty, AI-powered daily priority scheduling, actual-time logging, and dynamic schedule adjustment based on past estimates vs reality."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [作业管理, deadline, 时间管理, 任务优先级, 学业, 可视化]
    related_skills: []
---

# AI 作业截止日 / 任务管理器

## 概述

这是一个基于 AI 的智能作业 / 任务管理器，解决学生群体最常见的四大痛点：
1. **待办列了一堆，不知道先做什么** — AI 每天自动排序
2. **经常赶 ddl 到凌晨** — 提前预警 + 合理排期
3. **低估任务耗时导致拖延** — 通过实际耗时反馈不断校准
4. **时间分配不合理** — AI 动态调整后续安排

**核心工作流：**
1. 录入所有作业 / 任务的截止日、预计耗时、难度
2. AI 每天告诉你今天最该先做什么
3. 做完后反馈实际耗时
4. AI 动态调整后续安排

**落地难度：** ⭐⭐⭐ 零门槛（纯命令行 + 浏览器仪表盘，无需安装数据库）

## 项目结构

```
ai-task-deadline-manager/
├── SKILL.md                       # 本技能文件
├── README.md                      # 项目说明
├── scripts/
│   ├── manage_homework.py         # 命令行工具
│   └── run_visual_dashboard.py    # 多 Tab 可视化 HTML 仪表盘
├── references/
│   └── visual_design.md           # 可视化设计规范
├── data/                          # 用户数据（homework.json 等）
├── tests/
│   └── test_record.md             # 测试记录
└── iteration/
    └── iteration_shturl           # 迭代记录
```

## 数据格式

作业 / 任务数据存储在 `data/homework.json`。

### 单条任务结构

```json
{
  "id": "uuid-string",
  "title": "高等数学-微分中值定理作业",
  "course": "高等数学",
  "type": "homework",
  "deadline": "2026-03-20T23:59:59",
  "estimated_hours": 3.0,
  "difficulty": 3,
  "priority_score": null,
  "status": "pending",
  "created_at": "2026-03-15T10:00:00",
  "actual_hours": null,
  "completed_at": null,
  "notes": ""
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | UUID，自动生成 |
| `title` | string | 任务名称 |
| `course` | string | 科目 / 课程名 |
| `type` | string | `homework` / `exam` / `project` / `reading` / `other` |
| `deadline` | ISO 8601 | 截止日期时间 |
| `estimated_hours` | number | 预计耗时（小时） |
| `difficulty` | number | 1-5，1最简单5最难 |
| `priority_score` | number | AI 计算出的优先级分（>=0），null 表示待计算 |
| `status` | string | `pending` / `in_progress` / `completed` / `overdue` |
| `created_at` | ISO 8601 | 创建时间 |
| `actual_hours` | number | 实际耗时（小时），完成时填写 |
| `completed_at` | ISO 8601 | 实际完成时间 |
| `notes` | string | 备注 |

### 偏差记录（自学习用）

存储在 `data/bias_history.json`。

## 核心功能

### 1. 录入任务

```bash
python scripts/manage_homework.py add \
  --title "高数作业" \
  --course "高等数学" \
  --deadline "2026-07-20 23:59" \
  --hours 3 \
  --difficulty 3
```

AI 也会自动从自然语言解析录入。

### 2. AI 每日优先级排序

**排序算法：**

```
priority_score = urgency_factor × difficulty_factor × time_pressure

urgency_factor = 1 / (hours_until_deadline + 1) × 100
  → 截止越近，分数越高；< 24h 时加倍

difficulty_factor = 1 + (difficulty - 1) × 0.3
  → 难度越高 buffer 越大

time_pressure = estimated_hours / available_hours
  → 逾期强制 time_pressure = 5
```

### 3. 完成任务并反馈

```bash
python scripts/manage_homework.py complete --title "高数" --actual 4.5
```

完成后自动：
- 记录偏差到 `bias_history.json`
- 更新课程偏差系数（取最近5条平均）
- 重新计算剩余任务优先级
- 智能预警来不及的任务

### 4. 可视化仪表盘

```bash
python scripts/run_visual_dashboard.py
```

自动打开浏览器，展示 4 个 Tab：

| Tab | 内容 | 图表类型 |
|-----|------|----------|
| 📋 今日任务 | 优先排序、紧急度仪表、难度分布、甘特图 | Gauge + Doughnut + 进度条 |
| 📅 本周总览 | 完成率、科目分布、逾期列表 | 环形图 + 饼图 + 统计卡片 |
| 📊 偏差分析 | 各科偏差柱状图、偏差趋势、智能建议 | 柱状图 + 折线图 |
| 🏆 复盘统计 | 学期汇总、耗时排名、完成趋势 | 统计卡片 + 排名图 |

### 5. 查看统计

```bash
python scripts/manage_homework.py stats
python scripts/manage_homework.py list
```

## 使用示例

### 场景1：新人入门

```bash
# 录入首批任务
python scripts/manage_homework.py add --title "高数作业" --course "高等数学" --deadline "2026-07-20 23:59" --hours 3 --difficulty 3
python scripts/manage_homework.py add --title "计组实验" --course "计算机组成原理" --deadline "2026-07-22 23:59" --hours 5 --difficulty 4

# 查看优先级排序
python scripts/manage_homework.py list

# 打开可视化仪表盘
python scripts/run_visual_dashboard.py
```

### 场景2：每日使用

```bash
# 今天先做什么？
python scripts/manage_homework.py list

# 做完反馈
python scripts/manage_homework.py complete --title "高数" --actual 4.5
```

### 场景3：复盘

```bash
python scripts/manage_homework.py stats
python scripts/run_visual_dashboard.py  # Tab 4 复盘统计
```

## 常见陷阱

1. **覆盖写入** — 始终读取 -> 追加/修改 -> 整体写入
2. **timezone** — 统一 UTC+8
3. **课程名称不一致** — "高数"和"高等数学"被视为不同课程，请保持一致
4. **偏差数据不足** — 某课程 < 3 条记录时使用全局平均偏差
5. **仪表盘打不开** — 手动打开 `data/dashboard.html`

## 验证清单

- [ ] `data/homework.json` 格式正确
- [ ] 录入 -> 排序 -> 完成 -> 偏差记录 闭环正常
- [ ] 仪表盘 4 个 Tab 均显示正确
- [ ] 智能校准建议有效
- [ ] 逾期任务正确标记
