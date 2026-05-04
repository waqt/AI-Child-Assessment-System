# -*- coding: utf-8 -*-
"""
结构化评估引擎 (Assessment Engine)
====================================
管理标准化量表题目，跟踪评估进度，自动推荐下一步评估方向。
AI 在对话中自然穿插使用这些题目（方案 A）。
"""

import json
import os

_PROGRESS_FILE = os.path.join("storage", "profiles", "assessment_progress.json")

# ============================================================
# 结构化评估题库
# ============================================================

ASSESSMENT_ITEMS = [
    # ── SDQ 情绪症状 ──
    {"id": "sdq_e1", "source": "SDQ", "dimension": "emotional", "dim_label": "情绪症状",
     "text": "我经常头疼、肚子疼或不舒服",
     "dialog_hint": "上学之前有没有觉得肚子不太舒服的时候？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},
    {"id": "sdq_e2", "source": "SDQ", "dimension": "emotional", "dim_label": "情绪症状",
     "text": "我经常担心很多事情",
     "dialog_hint": "你睡觉前脑子里会不会转好多念头？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},
    {"id": "sdq_e4", "source": "SDQ", "dimension": "emotional", "dim_label": "情绪症状",
     "text": "在新的环境里我会紧张，容易失去信心",
     "dialog_hint": "如果换到一个新班级，你觉得你会怎么样？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},

    # ── SDQ 多动/注意力 ──
    {"id": "sdq_h3", "source": "SDQ", "dimension": "hyperactivity", "dim_label": "注意力",
     "text": "我容易分心，很难集中注意力",
     "dialog_hint": "做作业的时候你能一直做还是会想玩一会儿？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},
    {"id": "sdq_h4", "source": "SDQ", "dimension": "hyperactivity", "dim_label": "注意力",
     "text": "我做事之前会先想想",
     "dialog_hint": "遇到一道新题，你是先想再写，还是直接写？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": True},
    {"id": "sdq_h5", "source": "SDQ", "dimension": "hyperactivity", "dim_label": "注意力",
     "text": "我做事善始善终，注意力很好",
     "dialog_hint": "你开始画一幅画，一般会画完还是画一半去做别的？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": True},

    # ── SDQ 同伴关系 ──
    {"id": "sdq_p1", "source": "SDQ", "dimension": "peer", "dim_label": "同伴关系",
     "text": "我更喜欢一个人待着",
     "dialog_hint": "下课了你喜欢跟同学一起玩还是自己待着？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},
    {"id": "sdq_p2", "source": "SDQ", "dimension": "peer", "dim_label": "同伴关系",
     "text": "我有一个或更多好朋友",
     "dialog_hint": "你在学校有最好的朋友吗？你们一般一起干什么？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": True},

    # ── SDQ 亲社会行为 ──
    {"id": "sdq_s1", "source": "SDQ", "dimension": "prosocial", "dim_label": "亲社会行为",
     "text": "我会关心别人的感受",
     "dialog_hint": "如果你看到一个同学哭了，你会怎么做？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},
    {"id": "sdq_s2", "source": "SDQ", "dimension": "prosocial", "dim_label": "亲社会行为",
     "text": "我愿意跟别人分享",
     "dialog_hint": "如果你有两个冰淇淋但朋友没有，你会怎么办？",
     "type": "likert_3", "task_type": "dialog", "options": ["不太符合", "有点符合", "完全符合"], "reverse": False},

    # ── 成长型思维 ──
    {"id": "gm_1", "source": "GM-C", "dimension": "growth_mindset", "dim_label": "成长型思维",
     "text": "你觉得一个人有多聪明，是天生的还是可以改变的？",
     "dialog_hint": "你觉得数学厉害的人，是天生脑子好，还是练得特别多？",
     "type": "choice", "task_type": "choice", "options": ["天生的，改不了", "努力可以变聪明", "不太确定"], "reverse": False},
    {"id": "gm_2", "source": "GM-C", "dimension": "growth_mindset", "dim_label": "成长型思维",
     "text": "做一道题做了三遍都做错，你觉得是为什么？",
     "dialog_hint": "如果一道题做了三遍都做错，你觉得是因为不够聪明，还是没找到对的方法？",
     "type": "choice", "task_type": "choice", "options": ["可能我不够聪明", "我还没找到好方法", "题目太难了"], "reverse": False},

    # ── 数学态度 ──
    {"id": "math_conf", "source": "MATH", "dimension": "math_confidence", "dim_label": "数学自信",
     "text": "你觉得自己数学怎么样？",
     "dialog_hint": "你觉得你在班上数学算好的、中等的、还是不太好的？",
     "type": "choice", "task_type": "choice", "options": ["算好的", "中等吧", "不太好"], "reverse": False},

    # ── 互动小游戏 (NEW) ──
    {"id": "game_memory", "source": "GAME", "dimension": "working_memory", "dim_label": "工作记忆",
     "text": "记忆之森挑战（3x3 矩阵宝石记忆）",
     "dialog_hint": "我们来玩个好玩的记忆力挑战游戏【记忆之森】吧？",
     "type": "game", "task_type": "game", "game_id": "memory_forest", "options": None},
    
    {"id": "game_logic", "source": "GAME", "dimension": "logic_reasoning", "dim_label": "逻辑推理",
     "text": "逻辑天平挑战（动物体重推理）",
     "dialog_hint": "我这里有个关于森林小动物跷跷板的谜题，你想挑战一下吗？",
     "type": "game", "task_type": "game", "game_id": "logic_balance", "options": None},

    {"id": "game_number", "source": "GAME", "dimension": "number_sense", "dim_label": "数感捕捉",
     "text": "数感连连看（快速识别阵列数量）",
     "dialog_hint": "嘿，你能一眼看出来这里有多少个果子吗？我们玩个【数感连连看】吧！",
     "type": "game", "task_type": "game", "game_id": "number_sense", "options": None},
]

# 维度 → 最大可得分映射
DIMENSION_MAX_SCORES = {
    "emotional": 6,       # 3 题 × 2 分
    "hyperactivity": 6,
    "peer": 4,            # 2 题 × 2 分
    "prosocial": 4,
    "growth_mindset": 3,  # 3 题，按选项赋分
    "math_confidence": 1,
    "math_anxiety": 1,
    "math_enjoyment": 1,
    "self_management": 2,
    "multiple_intelligence": 1,
}


def _load_progress():
    """加载评估进度"""
    if os.path.exists(_PROGRESS_FILE):
        with open(_PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"answered": {}, "scores": {}}


def _save_progress(progress):
    """保存评估进度"""
    with open(_PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def get_assessment_status():
    """
    返回当前评估进度概览。
    
    Returns:
        dict: {
            "total_items": int,
            "answered_count": int,
            "pending_dimensions": list[str],
            "completed_dimensions": list[str],
            "dimension_scores": dict
        }
    """
    progress = _load_progress()
    answered_ids = set(progress.get("answered", {}).keys())
    
    # 统计每个维度的完成情况
    dim_total = {}
    dim_done = {}
    for item in ASSESSMENT_ITEMS:
        dim = item["dimension"]
        dim_total[dim] = dim_total.get(dim, 0) + 1
        if item["id"] in answered_ids:
            dim_done[dim] = dim_done.get(dim, 0) + 1
    
    pending = [d for d in dim_total if dim_done.get(d, 0) < dim_total[d]]
    completed = [d for d in dim_total if dim_done.get(d, 0) >= dim_total[d]]
    
    return {
        "total_items": len(ASSESSMENT_ITEMS),
        "answered_count": len(answered_ids),
        "pending_dimensions": pending,
        "completed_dimensions": completed,
        "dimension_scores": progress.get("scores", {}),
    }


def get_pending_items(max_items=3):
    """
    获取待评估的题目（优先选择未覆盖的维度）。
    
    Args:
        max_items: 最多返回几道题
        
    Returns:
        list[dict]: 包含题目信息的列表
    """
    progress = _load_progress()
    answered_ids = set(progress.get("answered", {}).keys())
    
    # 未答题目
    pending = [item for item in ASSESSMENT_ITEMS if item["id"] not in answered_ids]
    
    if not pending:
        return []
    
    # 按维度分组，优先选未覆盖的维度
    dim_counts = {}
    for item_id in answered_ids:
        for item in ASSESSMENT_ITEMS:
            if item["id"] == item_id:
                dim = item["dimension"]
                dim_counts[dim] = dim_counts.get(dim, 0) + 1
    
    # 按维度已完成题数排序（少的优先）
    pending.sort(key=lambda x: dim_counts.get(x["dimension"], 0))
    
    return pending[:max_items]


def get_suggested_items_text(max_items=3):
    """
    生成建议题目的文本描述，供注入 system prompt。
    
    Returns:
        str: 格式化的建议题目文本
    """
    items = get_pending_items(max_items)
    if not items:
        return "【所有结构化评估题目已完成！请继续通过自由对话进行深度探索。】"
    
    lines = ["【以下是你可以在对话中自然穿插的评估任务（选 1 项即可）】"]
    for item in items:
        task_info = f"类型: {item['task_type']}"
        if item['task_type'] == 'game':
            task_info += f", 游戏名: {item.get('game_id')}"
        
        lines.append(
            f"  - [{item['dim_label']}] {item['dialog_hint']} ({task_info}, ID: {item['id']})"
        )
    
    lines.append("\n策略提示：")
    lines.append("1. 如果孩子表现出疲劳，优先触发【游戏】类任务。")
    lines.append("2. 触发游戏时，你的 reply 应该是邀请孩子玩游戏的开场白，例如：'哎呀，我这里有个超级好玩的【记忆之森】挑战，你想不想试试看？'")
    lines.append("3. 如果你在回复中使用了某道题或游戏，请在 JSON 输出中包含 assessment_item_id 字段。")
    
    return "\n".join(lines)


def record_answer(item_id, answer, raw_text=""):
    """
    记录一道题目的回答并计分。
    
    Args:
        item_id: 题目 ID
        answer: 用户的选择（选项文本或自由文本）
        raw_text: 原始对话文本
    """
    progress = _load_progress()
    
    # 查找题目
    item = None
    for it in ASSESSMENT_ITEMS:
        if it["id"] == item_id:
            item = it
            break
    
    if not item:
        print(f"[Assessment] WARNING: Unknown item_id: {item_id}")
        return
    
    # 计分
    score = 0
    if item["type"] == "likert_3" and item["options"]:
        score_map = {item["options"][0]: 0, item["options"][1]: 1, item["options"][2]: 2}
        if item.get("reverse"):
            score_map = {item["options"][0]: 2, item["options"][1]: 1, item["options"][2]: 0}
        score = score_map.get(answer, 0)
    elif item["type"] == "choice":
        # 不同题目有不同的评分逻辑，这里简单记录选择序号
        if item["options"] and answer in item["options"]:
            score = item["options"].index(answer)
    
    # 保存
    if "answered" not in progress:
        progress["answered"] = {}
    if "scores" not in progress:
        progress["scores"] = {}
    
    progress["answered"][item_id] = {
        "answer": answer,
        "score": score,
        "raw_text": raw_text,
    }
    
    # 更新维度总分
    dim = item["dimension"]
    dim_score = sum(
        progress["answered"][aid]["score"]
        for aid in progress["answered"]
        if any(it["id"] == aid and it["dimension"] == dim for it in ASSESSMENT_ITEMS)
    )
    progress["scores"][dim] = dim_score
    
    _save_progress(progress)
    print(f"[Assessment] Recorded: {item_id} = '{answer}' (score={score}, dim={dim}, total={dim_score})")


def reset_progress():
    """重置所有评估进度"""
    _save_progress({"answered": {}, "scores": {}})
    print("[Assessment] Progress reset.")
