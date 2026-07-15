#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 作业截止日 / 任务管理器 — 命令行工具

用法:
  python manage_homework.py add --title "高数作业" --course "高等数学" --deadline "2026-07-20 23:59" --hours 3 --difficulty 3
  python manage_homework.py complete --title "高数作业" --actual 4.0
  python manage_homework.py list [--status pending|completed|overdue]
  python manage_homework.py stats
  python manage_homework.py dashboard
"""

import json
import uuid
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta

# ─── 数据目录（相对于项目根目录） ───
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def ensure_data_dir():
    """确保数据目录和基础文件存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ["homework.json", "bias_history.json", "course_bias.json"]:
        fp = DATA_DIR / fname
        if not fp.exists():
            with open(fp, "w", encoding="utf-8") as f:
                json.dump([] if fname != "course_bias.json" else {}, f)


def load_json(fname):
    ensure_data_dir()
    fp = DATA_DIR / fname
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(fname, data):
    ensure_data_dir()
    fp = DATA_DIR / fname
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tasks():
    return load_json("homework.json")


def save_tasks(tasks):
    save_json("homework.json", tasks)


def load_biases():
    return load_json("bias_history.json")


def save_biases(biases):
    save_json("bias_history.json", biases)


def load_course_biases():
    return load_json("course_bias.json")


def save_course_biases(cb):
    save_json("course_bias.json", cb)


def parse_deadline(s):
    """解析截止日期，支持多种格式"""
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(s, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt.isoformat()
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {s}，请使用 YYYY-MM-DD HH:MM 格式")


def calculate_priority(task, now=None):
    """计算单任务的 priority_score"""
    if now is None:
        now = datetime.now()
    deadline = datetime.fromisoformat(task["deadline"])
    hours_until = (deadline - now).total_seconds() / 3600

    if hours_until <= 0:
        return 500  # 已逾期 — 最高优先级

    urgency = 1 / (hours_until + 1) * 100
    if hours_until < 24:
        urgency *= 2

    difficulty = task.get("difficulty", 3)
    difficulty_factor = 1 + (difficulty - 1) * 0.3

    estimated = task.get("estimated_hours", 1)
    available = max(hours_until * 0.4, 0.5)
    time_pressure = estimated / available

    return round(urgency * difficulty_factor * time_pressure, 2)


def recalculate_all_priorities():
    """重新计算所有 pending 任务的优先级"""
    tasks = load_tasks()
    now = datetime.now()
    for t in tasks:
        if t["status"] in ("pending", "in_progress"):
            t["priority_score"] = calculate_priority(t, now)
            if datetime.fromisoformat(t["deadline"]) < now:
                t["status"] = "overdue"
    save_tasks(tasks)
    return tasks


def get_course_bias(course):
    cb = load_course_biases()
    return cb.get(course, None)


def update_course_bias(course):
    """根据 bias_history 重新计算课程偏差系数（取最近5条平均）"""
    biases = load_biases()
    course_entries = [b for b in biases if b["course"] == course][-5:]
    if not course_entries:
        return
    avg_bias = sum(b["bias_ratio"] for b in course_entries) / len(course_entries)
    cb = load_course_biases()
    cb[course] = {
        "avg_bias": round(avg_bias, 2),
        "sample_count": len(course_entries),
        "last_updated": datetime.now().isoformat()
    }
    save_course_biases(cb)


def smart_suggest(tasks, now=None):
    """智能建议：根据偏差系数给出时间调整建议"""
    if now is None:
        now = datetime.now()
    cb = load_course_biases()
    suggestions = []
    for t in tasks:
        if t["status"] != "pending":
            continue
        course = t["course"]
        bias_info = cb.get(course)
        if bias_info and bias_info["sample_count"] >= 2:
            adjusted = t["estimated_hours"] * bias_info["avg_bias"]
            if abs(adjusted - t["estimated_hours"]) > 0.5:
                suggestions.append({
                    "title": t["title"],
                    "course": course,
                    "original": t["estimated_hours"],
                    "adjusted": round(adjusted, 1),
                    "bias": bias_info["avg_bias"]
                })
    return suggestions


# ─── 子命令 ───

def cmd_add(args):
    tasks = load_tasks()
    deadline_iso = parse_deadline(args.deadline)

    bias = get_course_bias(args.course)
    est = args.hours
    note = ""
    if bias and bias["sample_count"] >= 2:
        adjusted = round(est * bias["avg_bias"], 1)
        if abs(adjusted - est) > 0.5:
            note = f"基于历史数据（偏差{bias['avg_bias']}x），建议调整为 {adjusted} 小时"

    task = {
        "id": str(uuid.uuid4())[:8],
        "title": args.title,
        "course": args.course,
        "type": args.type,
        "deadline": deadline_iso,
        "estimated_hours": est,
        "difficulty": args.difficulty,
        "priority_score": None,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "actual_hours": None,
        "completed_at": None,
        "notes": note
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"✅ 已录入：{args.title}")
    print(f"   课程：{args.course} | 截止：{args.deadline} | 预计：{est}h | 难度：{'⭐' * args.difficulty}")
    if note:
        print(f"   💡 {note}")


def cmd_complete(args):
    tasks = load_tasks()
    matched = [t for t in tasks if args.title.lower() in t["title"].lower() and t["status"] in ("pending", "in_progress")]
    if not matched:
        print(f"❌ 未找到匹配的任务: {args.title}")
        return
    t = matched[0]
    t["status"] = "completed"
    t["actual_hours"] = args.actual
    t["completed_at"] = datetime.now().isoformat()
    t["priority_score"] = None
    save_tasks(tasks)

    bias_ratio = round(args.actual / t["estimated_hours"], 2)
    bias_entry = {
        "id": t["id"],
        "course": t["course"],
        "estimated_hours": t["estimated_hours"],
        "actual_hours": args.actual,
        "bias_ratio": bias_ratio,
        "difficulty": t["difficulty"],
        "recorded_at": datetime.now().isoformat()
    }
    biases = load_biases()
    biases.append(bias_entry)
    save_biases(biases)
    update_course_bias(t["course"])

    print(f"✅ 已完成：{t['title']}")
    print(f"   预计 {t['estimated_hours']}h → 实际 {args.actual}h（偏差 {bias_ratio}x）")

    tasks = recalculate_all_priorities()
    suggestions = smart_suggest(tasks)
    if suggestions:
        for s in suggestions:
            print(f"   💡 建议：{s['title']}（{s['course']}）预计 {s['original']}h，历史偏差 {s['bias']}x → 建议调整为 {s['adjusted']}h")


def cmd_list(args):
    tasks = load_tasks()
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]

    if not tasks:
        print("📭 暂无任务")
        return

    for t in tasks:
        if t["priority_score"] is None and t["status"] in ("pending", "in_progress"):
            t["priority_score"] = calculate_priority(t)
    tasks.sort(key=lambda t: t.get("priority_score", 0) or 0, reverse=True)

    now = datetime.now()
    print(f"\n📋 任务列表（共 {len(tasks)} 项）")
    print("═" * 50)
    for i, t in enumerate(tasks, 1):
        deadline = datetime.fromisoformat(t["deadline"])
        remaining = deadline - now
        status_icon = {"pending": "⏳", "completed": "✅", "overdue": "🔴", "in_progress": "🔄"}.get(t["status"], "⏳")
        days_left = remaining.days if remaining.days >= 0 else f"超期 {-remaining.days}天"
        print(f"\n{status_icon} #{i} {t['title']}")
        print(f"   课程：{t['course']} | 截止：{deadline.strftime('%m-%d %H:%M')}（还剩 {days_left}）")
        print(f"   预计：{t['estimated_hours']}h | 难度：{'⭐' * t['difficulty']} | 状态：{t['status']}")
        if t["status"] == "completed" and t["actual_hours"]:
            print(f"   实际耗时：{t['actual_hours']}h")
        if t["priority_score"] and t["status"] != "completed":
            score = t["priority_score"]
            bar = "█" * min(int(score / 20), 20) + "░" * max(20 - min(int(score / 20), 20), 0)
            print(f"   优先级：{bar} ({score})")
        if t.get("notes"):
            print(f"   备注：{t['notes']}")


def cmd_stats(args):
    tasks = load_tasks()
    biases = load_biases()

    total = len(tasks)
    pending = len([t for t in tasks if t["status"] == "pending"])
    completed = len([t for t in tasks if t["status"] == "completed"])
    overdue = len([t for t in tasks if t["status"] == "overdue"])

    print(f"\n📊 任务统计总览")
    print("═" * 40)
    print(f"总任务数：{total}")
    print(f"✅ 已完成：{completed}")
    print(f"⏳ 待完成：{pending}")
    print(f"🔴 已逾期：{overdue}")

    if biases:
        print(f"\n📈 时间估算偏差")
        print("═" * 40)
        bias_by_course = {}
        for b in biases:
            bias_by_course.setdefault(b["course"], []).append(b["bias_ratio"])
        for course, ratios in sorted(bias_by_course.items()):
            avg = sum(ratios) / len(ratios)
            direction = "偏低估 📈" if avg > 1.1 else ("偏高估 📉" if avg < 0.9 else "较准 ✅")
            print(f"  {course}：平均偏差 {avg:.2f}x（{direction}）样本数：{len(ratios)}")

    if pending > 0:
        print(f"\n⏳ 待办提醒")
        print("═" * 40)
        pending_tasks = [t for t in tasks if t["status"] == "pending"]
        now = datetime.now()
        urgent = [t for t in pending_tasks if (datetime.fromisoformat(t["deadline"]) - now).days < 2]
        if urgent:
            print(f"  紧急（2天内截止）：")
            for t in urgent:
                print(f"    🔴 {t['title']} — 截止 {datetime.fromisoformat(t['deadline']).strftime('%m-%d %H:%M')}")


def cmd_dashboard(args):
    dashboard_script = Path(__file__).parent / "run_visual_dashboard.py"
    if dashboard_script.exists():
        os.system(f'python "{dashboard_script}"')
    else:
        print("❌ 找不到可视化脚本，请确保 scripts/run_visual_dashboard.py 存在")


def main():
    parser = argparse.ArgumentParser(description="AI 作业截止日 / 任务管理器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_add = subparsers.add_parser("add", help="录入新任务")
    p_add.add_argument("--title", required=True, help="任务名称")
    p_add.add_argument("--course", required=True, help="课程名称")
    p_add.add_argument("--deadline", required=True, help="截止日期，如 2026-07-20 23:59")
    p_add.add_argument("--hours", type=float, required=True, help="预计耗时（小时）")
    p_add.add_argument("--difficulty", type=int, default=3, choices=[1, 2, 3, 4, 5], help="难度 1-5")
    p_add.add_argument("--type", default="homework", choices=["homework", "exam", "project", "reading", "other"], help="任务类型")

    p_comp = subparsers.add_parser("complete", help="标记任务完成")
    p_comp.add_argument("--title", required=True, help="任务名称（支持模糊匹配）")
    p_comp.add_argument("--actual", type=float, required=True, help="实际耗时（小时）")

    p_list = subparsers.add_parser("list", help="列出任务")
    p_list.add_argument("--status", default=None, choices=["pending", "completed", "overdue", "in_progress"], help="按状态筛选")

    subparsers.add_parser("stats", help="查看统计概览")
    subparsers.add_parser("dashboard", help="打开可视化仪表盘")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
