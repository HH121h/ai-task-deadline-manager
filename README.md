# AI 作业截止日 / 任务管理器

> 选题系统名称：AI 作业截止日 / 任务管理器
> 所属分类：学习学业
> 落地难度：⭐⭐⭐ 零门槛

## 核心痛点点

- ❌ 待办列了一堆，不知道先做什么
- ❌ 经常赶 ddl 到凌晨
- ❌ 低估任务耗时导致拖延
- ❌ 时间分配不合理

## MVP 核心功能

1. **📝 录入任务** — 录入所有作业/任务的截止日、预计耗时、难度
2. **🤖 AI 每日排序** — 每天告诉你今天最该先做什么
3. **✅ 反馈实际耗时** — 做完后记录实际耗时
4. **🔄 动态调整** — AI 根据偏差自动调整后续安排

## 快速开始

```bash
# 1. 录入任务
python scripts/manage_homework.py add --title "高数作业" --course "高等数学" --deadline "2026-07-20 23:59" --hours 3 --difficulty 3

# 2. 查看优先级
python scripts/manage_homework.py list

# 3. 完成任务
python scripts/manage_homework.py complete --title "高数" --actual 4.5

# 4. 打开可视化仪表盘（4个Tab，多张图表）
python scripts/run_visual_dashboard.py
```

## 项目结构

```
ai-task-deadline-manager/
├── SKILL.md                      # Hermes skill 主文件
├── README.md                     # 本文件
├── scripts/
│   ├── manage_homework.py        # 命令行管理工具
│   └── run_visual_dashboard.py   # 多 Tab 可视化仪表盘
├── references/
│   └── visual_design.md          # 可视化设计规范
├── data/                         # 用户数据（自动生成）
│   ├── homework.json
│   ├── bias_history.json
│   ├── course_bias.json
│   └── dashboard.html            # 生成的仪表盘
├── tests/
│   └── test_record.md
└── iteration/
    └── iteration_shturl
```

## 仪表盘预览

| Tab | 内容 | 图表类型 |
|-----|------|----------|
| 📋 今日任务 | 优先级排序、紧急度仪表、难度分布、甘特图 | Gauge + Doughnut + 进度条 |
| 📅 本周总览 | 完成率、科目分布、逾期列表 | 环形图 + 饼图 + 统计卡片 |
| 📊 偏差分析 | 各科偏差柱状图、偏差趋势、智能建议 | 柱状图 + 折线图 |
| 🏆 复盘统计 | 学期汇总、耗时排名、完成趋势 | 统计卡片 + 排名图 |

## 优先级算法

```
priority_score = urgency_factor × difficulty_factor × time_pressure

urgency_factor    = 1 / (剩余小时数 + 1) × 100
difficulty_factor = 1 + (难度 - 1) × 0.3
time_pressure     = 预计耗时 / 可用时间
```

## License

MIT
