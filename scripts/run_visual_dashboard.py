#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 作业截止日 / 任务管理器 — 可视化仪表盘生成器
"""
import json, webbrowser
from pathlib import Path
from datetime import datetime, timedelta

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = (REPO_DIR / "data") if ((REPO_DIR / "SKILL.md").exists() and (REPO_DIR / "data").exists()) else (Path.home() / ".hermes" / "homework")

def load_json(fname):
    fp = DATA_DIR / fname
    return json.load(open(fp, "r", encoding="utf-8")) if fp.exists() else ([] if fname != "course_bias.json" else {})

def rt(pending, now):
    if not pending: return '<div class="empty-state"><div class="emoji">🎉</div><div>暂无待办任务！</div></div>'
    h = ""
    for i, t in enumerate(pending[:8]):
        r = i+1; rc = f"rank-{r}" if r<=3 else "rank-other"
        dl = datetime.fromisoformat(t["deadline"]); d = (dl-now).days
        if d<0: ts, bg = f"已超期 {-d}天", '<span class="badge badge-red">逾期</span>'
        elif d==0: ts, bg = f"今天 {dl.strftime('%H:%M')} 截止", '<span class="badge badge-red">今日截止</span>'
        elif d==1: ts, bg = f"明天 {dl.strftime('%H:%M')} 截止", '<span class="badge badge-yellow">明天截止</span>'
        else: ts, bg = f"还剩 {d}天", '<span class="badge badge-blue">进行中</span>'
        eh, bc, bw = t.get("estimated_hours",1), "#EF4444" if d<1 else ("#F59E0B" if d<3 else "#3B82F6"), min(max(t.get("estimated_hours",1)*10,10),100)
        h += f'<div class="task-item"><div class="task-rank {rc}">#{r}</div><div class="task-info"><div class="task-title">{t["title"]} {bg}</div><div class="task-meta">{t["course"]} · 预计 {eh}h · 难度 {"⭐"*t.get("difficulty",3)} · {ts}</div><div class="task-bar"><div class="task-bar-fill" style="width:{bw}%;background:{bc};"></div></div></div></div>'
    if len(pending)>8: h += f'<div style="text-align:center;padding:8px;font-size:13px;color:var(--text-secondary);">还有 {len(pending)-8} 项待办...</div>'
    return h

def ru(pending, now):
    if not pending: return "暂无待办"
    u = sum(1 for t in pending if (datetime.fromisoformat(t["deadline"])-now).days<2)
    return "✅ 今天没有紧急截止的任务" if u==0 else (f"⚠️ 有 {u} 项任务即将截止，建议优先处理" if u<=2 else f"🔴 有 {u} 项任务即将截止，请立即安排")

def rg(pending, now):
    if not pending: return '<div class="empty-state"><div class="emoji">📅</div><div>暂无待排期任务</div></div>'
    h = ""
    for t in pending[:6]:
        dl, hu = datetime.fromisoformat(t["deadline"]), (datetime.fromisoformat(t["deadline"])-now).total_seconds()/3600
        eh, rw, ew = t.get("estimated_hours",1), max(min(hu/168*100,100),2), min(t.get("estimated_hours",1)/40*100,100)
        c = "#EF4444" if hu<=0 else ("#F59E0B" if hu<24 else ("#3B82F6" if hu<72 else "#10B981"))
        h += f'<div style="margin-bottom:14px;"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;"><span style="font-weight:600;">{t["title"]}</span><span style="color:var(--text-secondary);">截止 {dl.strftime("%m/%d %H:%M")} · 预计 {eh}h</span></div><div style="display:flex;align-items:center;gap:8px;"><span style="font-size:11px;color:var(--text-secondary);min-width:32px;">剩余</span><div style="flex:1;height:8px;background:#E2E8F0;border-radius:4px;"><div style="height:100%;width:{rw}%;background:{c};border-radius:4px;"></div></div></div><div style="display:flex;align-items:center;gap:8px;margin-top:2px;"><span style="font-size:11px;color:var(--text-secondary);min-width:32px;">耗时</span><div style="flex:1;height:6px;background:#E2E8F0;border-radius:3px;"><div style="height:100%;width:{ew}%;background:{c};border-radius:3px;opacity:0.6;"></div></div></div></div>'
    if len(pending)>6: h += f'<div style="text-align:center;font-size:13px;color:var(--text-secondary);">还有 {len(pending)-6} 项...</div>'
    return h

def ro(overdue, now):
    if not overdue: return '<div class="empty-state"><div class="emoji">🎉</div><div>没有逾期任务！</div></div>'
    h = ""
    for t in overdue[:5]:
        dl, dd = datetime.fromisoformat(t["deadline"]), max((now-datetime.fromisoformat(t["deadline"])).days,0)
        h += f'<div class="task-item"><div style="width:28px;height:28px;border-radius:8px;background:var(--danger-light);display:flex;align-items:center;justify-content:center;font-size:16px;">🔴</div><div class="task-info"><div class="task-title">{t["title"]} <span class="badge badge-red">超期 {dd}天</span></div><div class="task-meta">{t["course"]} · 原截止 {dl.strftime("%m-%d %H:%M")} · 预计 {t.get("estimated_hours",1)}h</div></div></div>'
    if len(overdue)>5: h += f'<div style="text-align:center;font-size:13px;color:var(--text-secondary);">还有 {len(overdue)-5} 项逾期...</div>'
    return h

def rbs(course_biases, pending):
    if not course_biases: return '<div class="empty-state"><div class="emoji">📊</div><div>暂无足够数据生成建议</div></div>'
    h = ""
    for c, info in course_biases.items():
        b, n = info.get("avg_bias",1), info.get("sample_count",0)
        if n<2: continue
        if b>1.2: cl, ic, msg = "danger", "📈", f"{c} 平均偏差 {b}x，你总是低估该类任务耗时。建议录入时自动将预计时间 *{b:.1f}"
        elif b<0.8: cl, ic, msg = "warn", "📉", f"{c} 平均偏差 {b}x，你偏高估了耗时。可以更自信地安排紧凑些"
        else: cl, ic, msg = "", "✅", f"{c} 估算偏差 {b}x，你的时间感很准！"
        rl, th = [t for t in pending if t["course"]==c], ""
        if rl and b>1.2:
            te = sum(t.get("estimated_hours",0) for t in rl)
            th = f"当前有 {len(rl)} 项待办，预计共 {te}h，建议预留 {te*b:.1f}h"
        ht = f'<br><span style="font-size:12px;color:var(--text-secondary);">{th}</span>' if th else ""
        h += f'<div class="suggestion-item {cl}"><strong>{ic} {c}</strong> — {msg}{ht}<br><span style="font-size:11px;color:var(--text-secondary);">基于 {n} 条记录</span></div>'
    return h if h else '<div class="empty-state"><div class="emoji">📊</div><div>暂无足够偏差数据（每个科目至少需要2条完成记录）</div></div>'

def generate_html():
    tasks, biases, course_biases = load_json("homework.json"), load_json("bias_history.json"), load_json("course_bias.json")
    now = datetime.now()
    pending, completed, overdue = [t for t in tasks if t["status"] in ("pending","in_progress")], [t for t in tasks if t["status"]=="completed"], [t for t in tasks if t["status"]=="overdue"]
    for t in pending:
        hu = (datetime.fromisoformat(t["deadline"])-now).total_seconds()/3600
        t["_priority"] = 500 if hu<=0 else round((1/(hu+1)*100*(2 if hu<24 else 1))*(1+(t.get("difficulty",3)-1)*0.3)*(t.get("estimated_hours",1)/max(hu*0.4,0.5)),2)
        t["_hours_until"] = hu
    pending.sort(key=lambda t: t.get("_priority",0), reverse=True)
    ws, we = now-timedelta(days=now.weekday()), now-timedelta(days=now.weekday())+timedelta(days=7)
    wc = [t for t in tasks if t["status"]=="completed" and t.get("completed_at") and ws<=datetime.fromisoformat(t["completed_at"])<we]
    ph, wh = sum(t.get("estimated_hours",0) for t in pending), sum(t.get("actual_hours") or t.get("estimated_hours",0) for t in wc)
    tc, ti, tn = len(completed), sum(t.get("actual_hours",t.get("estimated_hours",0)) for t in completed), len(set(t["course"] for t in tasks))
    gb = sum(b["bias_ratio"] for b in biases)/len(biases) if biases else 1.0
    d_tasks, d_pending, d_biases, d_cb = json.dumps(tasks,ensure_ascii=False), json.dumps(pending,ensure_ascii=False), json.dumps(biases,ensure_ascii=False), json.dumps(course_biases,ensure_ascii=False)
    cm = sorted([{"m":k,"c":v} for k,v in __import__("collections").Counter(t["completed_at"][:7] for t in completed if t.get("completed_at")).items()], key=lambda x:x["m"])
    d_cm = json.dumps(cm, ensure_ascii=False)
    tt, ut, gt, ot, bs = rt(pending,now), ru(pending,now), rg(pending,now), ro(overdue,now), rbs(course_biases,pending)
    return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>AI 作业截止日管理器</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>:root{{--bg:#f8fafc;--card:#fff;--primary:#3B82F6;--primary-light:#EFF6FF;--warn:#F59E0B;--warn-light:#FFFBEB;--danger:#EF4444;--danger-light:#FEF2F2;--success:#10B981;--success-light:#ECFDF5;--text:#1E293B;--text-secondary:#64748B;--border:#E2E8F0;--shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);--radius:12px}}*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}.app-header{{background:linear-gradient(135deg,#1E40AF,#3B82F6);color:#fff;padding:24px 32px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(59,130,246,0.3)}}.app-header h1{{font-size:22px;font-weight:700}}.app-header p{{font-size:13px;opacity:0.85;margin-top:4px}}.container{{max-width:1280px;margin:0 auto;padding:24px}}.tabs{{display:flex;gap:4px;background:var(--card);border-radius:var(--radius);padding:4px;margin-bottom:24px;box-shadow:var(--shadow);overflow-x:auto}}.tab-btn{{flex:1;padding:10px 16px;border:none;background:transparent;border-radius:8px;cursor:pointer;font-size:14px;font-weight:500;color:var(--text-secondary);transition:all .2s;white-space:nowrap}}.tab-btn:hover{{background:var(--primary-light);color:var(--primary)}}.tab-btn.active{{background:var(--primary);color:#fff}}.tab-content{{display:none}}.tab-content.active{{display:block;animation:fadeIn .3s}}@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}.grid{{display:grid;gap:20px}}.grid-2{{grid-template-columns:1fr 1fr}}.grid-3{{grid-template-columns:1fr 1fr 1fr}}.grid-4{{grid-template-columns:1fr 1fr 1fr 1fr}}@media(max-width:768px){{.grid-2,.grid-3,.grid-4{{grid-template-columns:1fr}}}}.card{{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border)}}.card-title{{font-size:14px;font-weight:600;color:var(--text-secondary);margin-bottom:16px;display:flex;align-items:center;gap:6px}}.stat-value{{font-size:32px;font-weight:700;line-height:1.2}}.stat-label{{font-size:13px;color:var(--text-secondary);margin-top:2px}}.task-item{{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}}.task-item:last-child{{border-bottom:none}}.task-rank{{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;flex-shrink:0}}.rank-1{{background:#EF4444}}.rank-2{{background:#F59E0B}}.rank-3{{background:#3B82F6}}.rank-other{{background:#94A3B8}}.task-info{{flex:1;min-width:0}}.task-title{{font-weight:600;font-size:14px}}.task-meta{{font-size:12px;color:var(--text-secondary);margin-top:2px}}.task-bar{{height:6px;background:var(--border);border-radius:3px;margin-top:6px}}.task-bar-fill{{height:100%;border-radius:3px;transition:width .5s}}.chart-container{{position:relative;height:220px}}.chart-container-full{{position:relative;height:280px}}.badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}}.badge-red{{background:var(--danger-light);color:var(--danger)}}.badge-yellow{{background:var(--warn-light);color:var(--warn)}}.badge-green{{background:var(--success-light);color:var(--success)}}.badge-blue{{background:var(--primary-light);color:var(--primary)}}.suggestion-item{{padding:12px;border-left:3px solid var(--primary);background:var(--primary-light);border-radius:0 8px 8px 0;margin-bottom:8px}}.suggestion-item.warn{{border-left-color:var(--warn);background:var(--warn-light)}}.suggestion-item.danger{{border-left-color:var(--danger);background:var(--danger-light)}}.empty-state{{text-align:center;padding:48px 24px;color:var(--text-secondary)}}.empty-state .emoji{{font-size:48px;margin-bottom:12px}}</style></head><body><div class="app-header"><h1>📚 AI 作业截止日管理器</h1><p>数据更新于 {now.strftime('%Y-%m-%d %H:%M')} · 共 {len(tasks)} 项任务</p></div><div class="container"><div class="tabs"><button class="tab-btn active" onclick="st(0)">📋 今日任务</button><button class="tab-btn" onclick="st(1)">📅 本周总览</button><button class="tab-btn" onclick="st(2)">📊 偏差分析</button><button class="tab-btn" onclick="st(3)">🏆 复盘统计</button></div>
<div id="tab-0" class="tab-content active"><div class="grid grid-2"><div class="card"><div class="card-title">🎯 今日优先顺序</div>{tt}</div><div class="grid" style="gap:20px;"><div class="card"><div class="card-title">⏰ 紧急度仪表</div><div class="chart-container"><canvas id="urgencyGauge"></canvas></div><div style="text-align:center;font-size:13px;color:var(--text-secondary);margin-top:4px;">{ut}</div></div><div class="card"><div class="card-title">📊 今日任务难度分布</div><div class="chart-container"><canvas id="todayDifficulty"></canvas></div></div></div></div><div class="card" style="margin-top:20px;"><div class="card-title">📈 时间估算 · 甘特视图</div>{gt}</div></div>
<div id="tab-1" class="tab-content"><div class="grid grid-4" style="margin-bottom:20px;"><div class="card" style="text-align:center;"><div class="stat-value" style="color:var(--success);">{len(wc)}</div><div class="stat-label">本周已完成</div></div><div class="card" style="text-align:center;"><div class="stat-value" style="color:var(--primary);">{ph:.1f}</div><div class="stat-label">待完成预计耗时 (h)</div></div><div class="card" style="text-align:center;"><div class="stat-value" style="color:var(--warn);">{wh:.1f}</div><div class="stat-label">本周已投入 (h)</div></div><div class="card" style="text-align:center;"><div class="stat-value" style="color:var(--danger);">{len(overdue)}</div><div class="stat-label">逾期任务</div></div></div><div class="grid grid-2"><div class="card"><div class="card-title">🔄 任务完成率</div><div class="chart-container"><canvas id="completionRing"></canvas></div></div><div class="card"><div class="card-title">📚 各科目任务分布</div><div class="chart-container"><canvas id="courseDist"></canvas></div></div></div><div class="card" style="margin-top:20px;"><div class="card-title">🔴 逾期任务</div>{ot}</div></div>
<div id="tab-2" class="tab-content"><div class="grid grid-2"><div class="card"><div class="card-title">📏 各科估算偏差（实际/预计）</div><div class="chart-container-full"><canvas id="biasBar"></canvas></div></div><div class="card"><div class="card-title">📈 偏差趋势</div><div class="chart-container-full"><canvas id="biasTrend"></canvas></div></div></div><div class="card" style="margin-top:20px;"><div class="card-title">💡 智能校准建议</div>{bs}</div></div>
<div id="tab-3" class="tab-content"><div class="grid grid-4" style="margin-bottom:20px;"><div class="card" style="text-align:center;"><div class="stat-value">{tc}</div><div class="stat-label">总完成任务</div></div><div class="card" style="text-align:center;"><div class="stat-value">{ti:.1f}</div><div class="stat-label">总投入时间 (h)</div></div><div class="card" style="text-align:center;"><div class="stat-value" style="color:var(--primary);">{tn}</div><div class="stat-label">课程数</div></div><div class="card" style="text-align:center;"><div class="stat-value" style="color:{"var(--success)" if 0.9<=gb<=1.1 else "var(--warn)"};">{gb:.2f}x</div><div class="stat-label">全局平均偏差</div></div></div><div class="grid grid-2"><div class="card"><div class="card-title">⏳ 各科耗时排名</div><div class="chart-container-full"><canvas id="courseHoursRank"></canvas></div></div><div class="card"><div class="card-title">🎯 完成任务趋势</div><div class="chart-container-full"><canvas id="completionTrend"></canvas></div></div></div></div></div>
<script>
const tasks={d_tasks},pendingTasks={d_pending},allBiases={d_biases},courseBiases={d_cb},completionMonths={d_cm};
const C=['#3B82F6','#10B981','#F59E0B','#EF4444','#8B5CF6','#EC4899','#14B8A6','#F97316','#6366F1','#84CC16'];
function st(i){{document.querySelectorAll('.tab-content').forEach((e,j)=>e.classList.toggle('active',j===i));document.querySelectorAll('.tab-btn').forEach((e,j)=>e.classList.toggle('active',j===i));setTimeout(()=>{{Object.values(Chart.instances).forEach(c=>c?.resize())}},100)}}
(()=>{{const p=pendingTasks;if(!p.length)return;const u=Math.min(p.reduce((s,t)=>s+(t._hours_until<24?2:1)*(t._hours_until<48?1.5:1),0)/(p.length*3)*100,100);new Chart(document.getElementById('urgencyGauge'),{{type:'doughnut',data:{{datasets:[{{data:[u,Math.max(100-u,0)],backgroundColor:['#EF4444','#E2E8F0'],borderWidth:0,circumference:180,rotation:270}}]}},options:{{cutout:'70%',responsive:true,maintainAspectRatio:false,plugins:{{tooltip:{{enabled:false}},legend:{{display:false}}}}}},plugins:[{{id:'g',afterDraw(c){{const{{ctx,d}}=c;const m=c.getDatasetMeta(0);if(!m.data.length)return;const x=m.data[0].x,y=m.data[0].y;ctx.save();ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#EF4444';ctx.font='bold 32px sans-serif';ctx.fillText(Math.round(d.datasets[0].data[0])+'%',x,y+10);ctx.fillStyle='#64748B';ctx.font='13px sans-serif';ctx.fillText('紧急度',x,y-18);ctx.restore()}}}}]}})}})();
(()=>{{const p=pendingTasks;if(!p.length)return;const d={{}};p.forEach(t=>{{const k=t.difficulty||3;d[k]=(d[k]||0)+1}});const l=Object.keys(d).map(x=>'⭐'.repeat(parseInt(x))),v=Object.values(d);new Chart(document.getElementById('todayDifficulty'),{{type:'doughnut',data:{{labels:l,datasets:[{{data:v,backgroundColor:C.slice(0,v.length),borderWidth:2,borderColor:'#fff'}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},padding:8}}}}}}}}}})}})();
(()=>{{const c=tasks.filter(t=>t.status==='completed').length,p=tasks.filter(t=>t.status==='pending'||t.status==='in_progress').length,o=tasks.filter(t=>t.status==='overdue').length;new Chart(document.getElementById('completionRing'),{{type:'doughnut',data:{{labels:['已完成','待完成','已逾期'],datasets:[{{data:[c,p,o],backgroundColor:['#10B981','#3B82F6','#EF4444'],borderWidth:2,borderColor:'#fff'}}]}},options:{{cutout:'65%',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},padding:10}}}}}}}}}})}})();
(()=>{{const c={{}};tasks.forEach(t=>{{c[t.course]=(c[t.course]||0)+1}});const l=Object.keys(c),v=Object.values(c);new Chart(document.getElementById('courseDist'),{{type:'pie',data:{{labels:l,datasets:[{{data:v,backgroundColor:C.slice(0,l.length),borderWidth:2,borderColor:'#fff'}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},padding:8}}}}}}}}}})}})();
(()=>{{const e=Object.entries(courseBiases);if(!e.length)return;const l=e.map(x=>x[0]),b=e.map(x=>x[1].avg_bias||1),c=b.map(b=>b>1.1?'#EF4444':b<0.9?'#F59E0B':'#10B981');new Chart(document.getElementById('biasBar'),{{type:'bar',data:{{labels:l,datasets:[{{label:'偏差比',data:b,backgroundColor:c,borderRadius:4}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,scales:{{x:{{min:0,grid:{{color:'#F1F5F9'}}}},y:{{grid:{{display:false}}}}}},plugins:{{legend:{{display:false}}}}}}}})}})();
(()=>{{const d=allBiases;if(d.length<2)return;const s=[...d].sort((a,b)=>new Date(a.recorded_at)-new Date(b.recorded_at)),l=s.map((_,i)=>'#'+(i+1)),v=s.map(b=>b.bias_ratio);new Chart(document.getElementById('biasTrend'),{{type:'line',data:{{labels:l,datasets:[{{label:'偏差比',data:v,borderColor:'#3B82F6',backgroundColor:'#3B82F688',fill:true,tension:0.3,pointRadius:4,pointBackgroundColor:'#3B82F6'}},{{label:'准确线',data:Array(l.length).fill(1.0),borderColor:'#10B981',borderDash:[6,4],pointRadius:0,borderWidth:2}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{min:0,grid:{{color:'#F1F5F9'}}}},x:{{grid:{{display:false}}}}}},plugins:{{legend:{{position:'top',labels:{{font:{{size:11}},padding:8}}}}}}}}}})}})();
(()=>{{const h={{}};tasks.filter(t=>t.status==='completed').forEach(t=>{{const c=t.course;h[c]=(h[c]||0)+(t.actual_hours||t.estimated_hours||0)}});const e=Object.entries(h).sort((a,b)=>b[1]-a[1]);if(!e.length)return;const l=e.map(x=>x[0]),v=e.map(x=>x[1]);new Chart(document.getElementById('courseHoursRank'),{{type:'bar',data:{{labels:l,datasets:[{{label:'耗时(h)',data:v,backgroundColor:C.slice(0,l.length),borderRadius:4}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,scales:{{x:{{grid:{{color:'#F1F5F9'}}}},y:{{grid:{{display:false}}}}}},plugins:{{legend:{{display:false}}}}}}}})}})();
(()=>{{const d=completionMonths;if(!d.length)return;const l=d.map(x=>x.m),v=d.map(x=>x.c);new Chart(document.getElementById('completionTrend'),{{type:'line',data:{{labels:l,datasets:[{{label:'完成任务数',data:v,borderColor:'#10B981',backgroundColor:'#10B98144',fill:true,tension:0.3,pointRadius:5,pointBackgroundColor:'#10B981'}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{beginAtZero:true,grid:{{color:'#F1F5F9'}}}},x:{{grid:{{display:false}}}}}},plugins:{{legend:{{display:false}}}}}}}})}})();
</script></body></html>'''


def main():
    html = generate_html()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "dashboard.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📊 仪表盘已生成: {out}")
    print("🚀 正在打开浏览器...")
    try:
        webbrowser.open(out.resolve().as_uri())
    except Exception:
        print(f"请手动打开: {out}")


if __name__ == "__main__":
    main()
