# -*- coding: utf-8 -*-
import json
import requests
import io
import os
from expert_knowledge import get_full_knowledge_base
from assessment_engine import get_suggested_items_text, get_assessment_status

# 暖心老师 Prompt (Teacher Agent)
# 专注于共情交互、自然对话，并根据建议触发评估任务
TEACHER_SYSTEM_PROMPT_TEMPLATE = """
你是一位温柔亲切的 AI 数学启蒙老师。你的目标是通过自然对话和有趣的游戏，评估并辅导 8-9 岁的孩子。

【你的行为准则】
1. 身份：温柔的大哥哥/大姐姐。语气亲切活泼，多用鼓励性词汇（如：太棒了、真聪明、没关系）。
2. 简短：回复限制在 2-3 句话内（<80字），每次只问一个简短问题（<25字）。
3. 顺势而为：100% 顺着孩子的话题走。不要生硬地转场。
4. 任务植入：根据下方的【建议评估任务】，自然地将其融入对话或邀请孩子玩游戏。

【当前建议评测任务】
{assessment_suggestions}

【当前画像参考（了解孩子兴趣）】
{interests}

【当前教学阶段】: {stage}

【输出格式】
你必须返回 JSON 格式：
{{
    "reply": "对孩子说的话",
    "assessment_item_id": "触发的任务ID (如果有)",
    "assessment_choice_options": ["选项A", "选项B"]
}}
"""

# 幕后专家 Prompt (Analyst Agent)
# 专注于心理学分析、理论映射、画像更新，不直接与孩子沟通
ANALYST_SYSTEM_PROMPT_TEMPLATE = """
你是一位顶尖的儿童教育心理学评估专家。你的任务是分析对话流，并精准更新学生画像。

【你的分析框架】
1. 理论基础：必须引用具体理论（如：SDQ, Erikson, VARK, Growth Mindset）。
2. 假设管理：区分“观察到的现象”与“确认为特征”。至少经过两次不同情境的验证才能确认为特征。
3. 去伪存真：识别社会期望偏差（孩子可能在迎合大人）。

【当前画像】
{current_profile}

【专家知识库 (RAG)】
{knowledge_base}

【最新对话记录】
{latest_dialogue}

【输出要求】
1. 在 expert_reasoning 中详细记录你的分析推理过程。
2. 在 updated_profile 中提供完整的更新后的画像 JSON。

你必须返回 JSON 格式：
{{
    "expert_reasoning": "分析推理...",
    "updated_profile": {{ ... }}
}}
"""

def get_ai_response_and_update_profile(api_key: str, base_url: str, chat_history: list, current_profile: dict, model_name: str = "gpt-4o"):
    """
    双 Agent 协同逻辑：
    1. 老师 Agent：生成回复语和触发任务（面向孩子，高响应度）。
    2. 专家 Agent：静默分析并更新画像（面向后台，深度逻辑）。
    """
    
    # --- 1. 准备上下文与 RAG ---
    recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
    conversation_context = ""
    for msg in recent_messages:
        role = "孩子" if msg["role"] == "user" else "老师"
        conversation_context += f"{role}: {msg['content']}\n"
        
    knowledge_base = get_full_knowledge_base(conversation_context)
    assessment_suggestions = get_suggested_items_text(max_items=3)
    
    # 获取当前阶段 (Workflow 简单实现)
    status = get_assessment_status()
    answered_count = status['answered_count']
    if answered_count == 0:
        stage = "破冰阶段 (Icebreak)"
    elif answered_count < 8:
        stage = "基础评测阶段 (Baseline)"
    else:
        stage = "深度画像阶段 (DeepDive)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # 强制不使用系统代理，防止国内 API 报错
    no_proxy = {"http": None, "https": None}

    # --- 2. 调用老师 Agent (生成回复) ---
    teacher_prompt = TEACHER_SYSTEM_PROMPT_TEMPLATE.format(
        assessment_suggestions=assessment_suggestions,
        interests=json.dumps(current_profile.get("interests", []), ensure_ascii=False),
        stage=stage
    )
    
    teacher_payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": teacher_prompt},
            *chat_history
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=teacher_payload, timeout=30, proxies=no_proxy)
        teacher_res = response.json()
        content = teacher_res['choices'][0]['message']['content']
        teacher_data = json.loads(content)
        
        reply = teacher_data.get("reply", "哎呀，刚才老师走神了，你能再说一遍吗？")
        assessment_item_id = teacher_data.get("assessment_item_id", None)
        assessment_choices = teacher_data.get("assessment_choice_options", None)
    except Exception as e:
        print(f"Teacher Agent Error: {e}")
        reply = "老师正在思考一个很有趣的问题，稍等我一下哦..."
        assessment_item_id = None
        assessment_choices = None

    # --- 3. 调用专家 Agent (后台分析) ---
    analyst_prompt = ANALYST_SYSTEM_PROMPT_TEMPLATE.format(
        current_profile=json.dumps(current_profile, ensure_ascii=False, indent=2),
        knowledge_base=knowledge_base,
        latest_dialogue=conversation_context
    )
    
    analyst_payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": analyst_prompt},
            {"role": "user", "content": "请分析以上对话并生成最新的 updated_profile。"}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        # 专家分析可以稍微慢一点，设置更长的 timeout
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=analyst_payload, timeout=60, proxies=no_proxy)
        analyst_res = response.json()
        content = analyst_res['choices'][0]['message']['content']
        analyst_data = json.loads(content)
        
        updated_profile = analyst_data.get("updated_profile", current_profile)
        expert_reasoning = analyst_data.get("expert_reasoning", "持续观察中。")
        
        # 将分析过程存入画像，以便 UI 展示
        if updated_profile:
            updated_profile["expert_inner_thoughts"] = expert_reasoning
            updated_profile["assessment_progress"] = f"当前处于 {stage}，已完成 {answered_count} 项评测。"
    except Exception as e:
        print(f"Analyst Agent Error: {e}")
        updated_profile = current_profile

    # 封装评估信息
    assessment_info = None
    if assessment_item_id and assessment_item_id != "null":
        assessment_info = {
            "item_id": assessment_item_id,
            "choices": assessment_choices
        }
    
    return reply, updated_profile, assessment_info
