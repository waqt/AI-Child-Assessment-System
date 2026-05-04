# -*- coding: utf-8 -*-
import json
import requests
import io
import os
import speech_recognition as sr
from expert_knowledge import get_full_knowledge_base
from assessment_engine import get_suggested_items_text, get_assessment_status

def get_ai_response_and_update_profile(api_key: str, base_url: str, chat_history: list, current_profile: dict, model_name: str = "gpt-4o"):
    """
    Calls the LLM to get a chat response AND an updated profile.
    Implements Chain-of-Thought reasoning, hypothesis-testing (AB verification),
    and RAG-enhanced expert knowledge base injection.
    """
    
    # 提取最近对话上下文用于 RAG 检索
    recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
    conversation_context = " ".join([msg.get("content", "") for msg in recent_messages])
    
    # 获取专家知识库（RAG 模式：根据对话上下文检索相关理论）
    knowledge_base = get_full_knowledge_base(conversation_context)
    
    # 获取结构化评估建议
    assessment_suggestions = get_suggested_items_text(max_items=3)
    assessment_status = get_assessment_status()
    
    system_prompt = f"""
    你是一位顶尖的儿童教育心理学专家（同时精通发展心理学、教育行为学）兼 AI 数学启蒙老师。
    你的身份对外是一个温柔亲切的大哥哥/大姐姐，但内心你是一个训练有素的专业评估师。

    ═══════════════════════════════════════
    ▎第一部分：你的专家知识库（请基于以下理论进行分析和提问）
    ═══════════════════════════════════════
    {knowledge_base}

    ═══════════════════════════════════════
    ▎结构化评估题目（可选用，自然穿插到对话中）
    ═══════════════════════════════════════
    评估进度：已完成 {assessment_status['answered_count']}/{assessment_status['total_items']} 题
    {assessment_suggestions}

    ═══════════════════════════════════════
    ▎第二部分：当前孩子的画像档案
    ═══════════════════════════════════════
    {json.dumps(current_profile, ensure_ascii=False, indent=2)}

    ═══════════════════════════════════════
    ▎第三部分：你的工作流程（每次回复必须严格执行）
    ═══════════════════════════════════════

    【步骤 1：专家内心独白 (Chain of Thought)】
    在你输出最终回复之前，你必须先在 "expert_reasoning" 字段中写出你的内心分析过程（这段话孩子看不到，只有后台能看到）。
    内心独白必须包含：
    a) 孩子刚才这句话透露了什么潜在信息？背后的动机/情绪/认知特征是什么？
    b) 这能映射到我知识库中的哪个理论框架？（引用具体理论名称）
    c) 我当前有哪些假设 (hypotheses)？哪些已被验证、哪些需要交叉验证？
    d) 我接下来的提问策略是什么？我要用什么方式来验证或推翻某个假设？
    e) 【去伪存真分析】孩子这句话是否存在社会期望偏差的嫌疑？有没有以下信号：
       - 过度强调/修饰（"我超级喜欢"）
       - 模仿大人语气（"数学很重要要好好学"）
       - 与之前的回答矛盾（前面说不怕后面又回避）
       - 快速转移话题/反问回避
       如果检测到以上信号，记录为"疑似社会期望偏差"，并在下次使用第三人称投射法或故事续写法来交叉验证真实想法。

    【步骤 2：假设管理 (Hypothesis Testing / AB Test)】
    - 当你从对话中发现某个维度的线索时，将其记为一个 hypothesis（假设），格式为：
      "来源: 孩子说了XXX → 假设: YYY（基于ZZZ理论）→ 状态: 待验证"
    - 特别注意：如果线索来自孩子的直接自我陈述（如"我很喜欢数学"），信度较低，标记为"需交叉验证（自我陈述，可能有社会期望偏差）"。
    - 如果线索来自无意流露、第三人称投射、故事续写中的投射，信度较高。
    - 下一次对话中，你必须设计一个【不同角度/不同情境】的问题来验证这个假设（即 AB Test）。
    - 只有经过至少两次不同情境的验证，才能将假设升级为 confirmed_traits（已确认特征）。
    - 如果两次结论矛盾，标记为"需进一步观察"，并设计第三次测试。

    【步骤 3：生成回复 (Reply Generation)】
    ⚠️ 核心禁令：禁止僵化提问！
    - 严禁连续三轮使用相同的评估情境（如一直聊分宝石、数砖块）。
    - 严禁直接抛出干巴巴的数学题。
    - 必须从《评估场景库》中获取灵感，并将其与孩子当前的话题【无缝融合】。
    - 如果孩子在聊游戏，就用 Minecraft 场景；如果孩子聊到动物，就用动物园场景。
    - 回复总长度严格控制在 2-3 句话以内（不超过80个字），外加 1 个简短的问题。
    - 绝对不要一次问多个问题！每次回复只能包含 1 个问题。
    - 问题本身也要简短（不超过25个字），要让三年级孩子一听就懂。
    - 你的回复必须 100% 顺着孩子当前的话题走！
    - 【去伪存真提问技巧优先级】（从高到低）：
      1. 交互式小游戏 (当探测到孩子注意力下降或提到“玩”、“挑战”时，优先触发游戏类评估项)
      2. 第三人称投射法
      3. 故事续写法
      4. 强制双正选择法
    注意：游戏类任务非常适合评估“工作记忆”、“逻辑推理”等硬能力，要自然地邀请孩子参加。

    【步骤 4：更新画像档案】
    - 根据本轮对话的新信息或上一轮的游戏结果，更新 updated_profile。

    ═══════════════════════════════════════
    ▎第四部分：严格的 JSON 输出格式
    ═══════════════════════════════════════
    你必须且只能返回以下 JSON 格式：
    {{
        "expert_reasoning": "分析过程...",
        "reply": "回复内容... (如果是触发游戏，请使用邀请语气，如：'太棒了！那我们来玩个【记忆之森】的小游戏挑战一下吧？')",
        "assessment_item_id": "填入结构化评估 ID 或游戏 ID（如 game_memory）",
        "assessment_choice_options": ["选项A", "选项B"],
        "updated_profile": {{
            "basic_info": {{
                "name": "孩子名字或'未知'",
                "age": "年龄或'未知'",
                "grade": "年级或'未知'"
            }},
            "interests": ["爱好1", "爱好2"],
            "educational_profile": {{
                "personality": {{
                    "status": "待评估/评估中/已确认",
                    "hypotheses": [
                        "来源: 孩子说了XXX → 假设: 外向活泼 (Big Five外向性) → 状态: 待验证"
                    ],
                    "confirmed_traits": "经过交叉验证后的最终结论"
                }},
                "behavioral_traits": {{
                    "status": "待评估/评估中/已确认",
                    "hypotheses": [],
                    "confirmed_traits": ""
                }},
                "learning_style": {{
                    "status": "待评估/评估中/已确认",
                    "hypotheses": [],
                    "confirmed_traits": ""
                }},
                "math_capability": {{
                    "status": "待评估/评估中/已确认",
                    "hypotheses": [],
                    "confirmed_traits": ""
                }}
            }},
            "expert_inner_thoughts": "本轮完整的内心独白",
            "assessment_progress": "当前评估的整体进度描述"
        }}
    }}
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    # 转换历史记录格式
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7
    }

    url = f"{base_url.rstrip('/')}/chat/completions"

    # 国内大模型 API（如 DeepSeek）不需要走代理，强制直连
    no_proxy = {"http": None, "https": None}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120, proxies=no_proxy)
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            return f"API 返回错误 (HTTP {response.status_code}): {response.text[:500]}", current_profile, None
        
        # 尝试解析 API 响应
        try:
            result_data = response.json()
        except Exception:
            return f"API 返回的不是 JSON: {response.text[:500]}", current_profile, None
        
        # 提取模型回复内容
        if "choices" not in result_data or len(result_data["choices"]) == 0:
            return f"API 返回数据异常（无 choices）: {str(result_data)[:500]}", current_profile, None
        
        result_str = result_data["choices"][0]["message"]["content"]
        
        # 检查空响应
        if not result_str or not result_str.strip():
            return "老师刚刚走神了，再说一遍好不好？😊", current_profile, None
        
        # 清理可能的 Markdown 代码块包裹
        cleaned = result_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # 尝试解析模型输出的 JSON
        try:
            result_json = json.loads(cleaned)
        except json.JSONDecodeError:
            # 尝试用正则从文本中提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    result_json = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result_json = None
            else:
                result_json = None
            
            if result_json is None:
                # 最终兜底：直接把原文当回复返回，不丢失对话
                return (cleaned[:300] if cleaned else "老师刚刚走神了，再说一遍好不好？😊"), current_profile, None
        
        # ===== 调试日志：检查模型是否返回了画像更新 =====
        reply_text = result_json.get("reply", "抱歉，老师刚刚走神了~")
        new_profile = result_json.get("updated_profile", None)
        
        # 提取结构化评估信息
        assessment_item_id = result_json.get("assessment_item_id", None)
        assessment_choices = result_json.get("assessment_choice_options", None)
        
        print("\n==== [Agent Debug] ====")
        print(f"Reply: {reply_text[:80]}")
        if assessment_item_id:
            print(f"Assessment Item: {assessment_item_id}, Choices: {assessment_choices}")
        if new_profile:
            print(f"Profile updated: YES")
            # 打印关键变化
            edu = new_profile.get("educational_profile", {})
            for dim in ["personality", "behavioral_traits", "learning_style", "math_capability"]:
                d = edu.get(dim, {})
                status = d.get("status", "N/A")
                hypos = d.get("hypotheses", [])
                confirmed = d.get("confirmed_traits", "")
                if hypos or confirmed or status != "待评估":
                    print(f"  {dim}: status={status}, hypotheses={len(hypos)}, confirmed={bool(confirmed)}")
        else:
            print(f"Profile updated: NO (model did not return updated_profile!)")
        print("======================\n")
        
        # 构建评估信息（如果有的话）
        assessment_info = None
        if assessment_item_id and assessment_item_id != "null":
            assessment_info = {
                "item_id": assessment_item_id,
                "choices": assessment_choices if isinstance(assessment_choices, list) else None
            }
        
        return reply_text, new_profile if new_profile else current_profile, assessment_info
    except requests.exceptions.Timeout:
        return "API 请求超时了，可能是网络不太稳定或者问题太复杂。请再试一次！", current_profile, None
    except Exception as e:
        return f"API 调用出错: {str(e)}", current_profile, None

def transcribe_audio_to_text(audio_bytes: bytes, api_key: str = "", base_url: str = "") -> str:
    """
    Takes raw WAV audio bytes, tries to use OpenAI Whisper API if available via proxy/base_url,
    and falls back to Google's SpeechRecognition API.
    """
    # 策略 1：尝试使用用户提供的 API 接口（很多国内中转站支持 whisper 接口）
    if api_key and base_url:
        try:
            url = f"{base_url.rstrip('/')}/audio/transcriptions"
            headers = {"Authorization": f"Bearer {api_key}"}
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"model": "whisper-1"}
            # 不使用代理请求大模型 API
            response = requests.post(url, headers=headers, files=files, data=data, timeout=5)
            if response.status_code == 200:
                return response.json().get("text", "")
        except Exception:
            pass # 如果不支持或报错，静默降级到 Google 免费方案

    # 策略 2：强制设置本地代理，调用 Google 免费语音服务
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
    
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
        text = recognizer.recognize_google(audio_data, language="zh-CN")
        return text
    except sr.UnknownValueError:
        return "" # 没听清
    except Exception as e:
        return f"（语音处理出错: {e}。提示：请在 Clash 中尝试切换一个别的节点，当前节点可能被 Google 拒绝连接了）"
