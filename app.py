import streamlit as st
import os
import sys

# 确保能找到同目录下的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import load_profile, save_profile, DEFAULT_PROFILE, load_settings, save_settings, load_chat_history, save_chat_history
from agent import get_ai_response_and_update_profile
from volcengine import load_voice_config, tts_generate, stt_recognize
from assessment_engine import get_assessment_status, record_answer, reset_progress, ASSESSMENT_ITEMS
from interactive_tasks import TASK_TEMPLATES, render_logic_balance_ui
from skills.report_generator import generate_assessment_report
from skills.math_solver import solve_math_expression
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder
import io

# 加载火山引擎语音配置（从 volcengine/voice_config.json）
_voice_cfg = load_voice_config()

st.set_page_config(page_title="AI 老师 - 记忆与画像系统", layout="wide", page_icon="🤖")

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 大模型 API 设置")
    
    settings = load_settings()
    saved_configs = settings.get("saved_configs", {}) # dict 格式 {"名称": {"api_key": "...", ...}}
    
    config_names = list(saved_configs.keys())
    selected_name = st.selectbox("📂 查看/加载已保存的配置", ["-- 手动输入新配置 --"] + config_names)
    
    # 确定输入框的初始值
    if selected_name != "-- 手动输入新配置 --":
        cur_config = saved_configs[selected_name]
        init_key = cur_config.get("api_key", "")
        init_base = cur_config.get("base_url", "https://api.openai.com/v1")
        init_model = cur_config.get("model_name", "gpt-4o")
    else:
        init_key = settings.get("last_api_key", "")
        init_base = settings.get("last_base_url", "https://api.openai.com/v1")
        init_model = settings.get("last_model_name", "gpt-4o")
    
    api_key = st.text_input("请输入大模型 API Key", type="password", value=init_key)
    base_url = st.text_input("Base URL (如用第三方 API 中转)", value=init_base)
    model_name = st.text_input("模型名称", value=init_model)
    
    
    st.write("---")
    config_save_name = st.text_input("给当前配置起个名字 (如: DeepSeek)", value=selected_name if selected_name != "-- 手动输入新配置 --" else "")
    
    if st.button("💾 保存/更新此配置"):
        if config_save_name.strip():
            saved_configs[config_save_name.strip()] = {
                "api_key": api_key,
                "base_url": base_url,
                "model_name": model_name
            }
            settings["saved_configs"] = saved_configs
            settings["last_api_key"] = api_key
            settings["last_base_url"] = base_url
            settings["last_model_name"] = model_name
            
            save_settings(settings)
            st.success(f"已成功保存配置：{config_save_name}")
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()
        else:
            st.warning("请先在上方输入配置名称！")
    
    # 后台静默保存最后一次输入的内容，防刷新丢失
    if api_key != settings.get("last_api_key") or base_url != settings.get("last_base_url") or model_name != settings.get("last_model_name"):
        settings["last_api_key"] = api_key
        settings["last_base_url"] = base_url
        settings["last_model_name"] = model_name
        save_settings(settings)
    
    st.divider()
    
    st.header("👤 实时学生画像看板")
    profile = load_profile()
    
    with st.expander("实时孩子画像档案", expanded=True):
        basic_info = profile.get("basic_info", {})
        edu_profile = profile.get("educational_profile", {})
        
        st.markdown("##### 👤 基础信息")
        col_a, col_b, col_c = st.columns(3)
        col_a.write(f"**姓名:** {basic_info.get('name', '未知')}")
        col_b.write(f"**年龄:** {basic_info.get('age', '未知')}")
        col_c.write(f"**年级:** {basic_info.get('grade', '未知')}")
        st.write(f"**兴趣爱好:** {', '.join(profile.get('interests', [])) if profile.get('interests') else '待发掘'}")
        
        st.markdown("---")
        st.markdown("##### 🧠 教育基线评估（四大维度）")
        
        dimensions = [
            ("1. 个性 (Personality)", "personality"),
            ("2. 行为特征 (Behavioral Traits)", "behavioral_traits"),
            ("3. 学习方式 (Learning Style)", "learning_style"),
            ("4. 数学能力 (Math Capability)", "math_capability"),
        ]
        
        for label, key in dimensions:
            dim_data = edu_profile.get(key, {})
            # 兼容旧格式（字符串）和新格式（字典）
            if isinstance(dim_data, str):
                st.info(f"**{label}**\n\n{dim_data}")
            else:
                status = dim_data.get("status", "待评估")
                hypotheses = dim_data.get("hypotheses", [])
                confirmed = dim_data.get("confirmed_traits", "")
                
                # 根据状态选择颜色
                if status == "已确认":
                    st.success(f"**{label}** ✅ 已确认\n\n{confirmed}")
                elif status == "评估中":
                    hypo_text = "\n".join([f"  • {h}" for h in hypotheses]) if hypotheses else "  （暂无）"
                    st.warning(f"**{label}** 🔄 评估中\n\n**待验证假设：**\n{hypo_text}")
                else:
                    st.info(f"**{label}** ⏳ 待评估")
        
        st.markdown("---")
        st.markdown("##### 📈 评估进度")
        st.caption(profile.get("assessment_progress", "未开始"))
        
        # 结构化评估进度条
        a_status = get_assessment_status()
        progress_pct = a_status['answered_count'] / max(a_status['total_items'], 1)
        st.progress(progress_pct)
        st.caption(f"结构化评估：{a_status['answered_count']}/{a_status['total_items']} 题")
        
        # 显示已完成维度的得分
        if a_status['dimension_scores']:
            st.markdown("**维度得分：**")
            for dim, score in a_status['dimension_scores'].items():
                st.caption(f"  • {dim}: {score} 分")
    
    # 专家内心独白（可折叠，方便家长/开发者查看 AI 的推理过程）
    expert_thoughts = profile.get("expert_inner_thoughts", "")
    if expert_thoughts:
        with st.expander("🔬 专家内心独白（AI 推理过程，孩子不可见）", expanded=False):
            st.markdown(expert_thoughts)
    
    if st.button("🗑️ 清空画像与聊天记录"):
        save_profile(DEFAULT_PROFILE)
        reset_progress()  # 同时重置评估进度
        default_msgs = [{"role": "assistant", "content": "你好呀！我是你的新朋友，也是你的数学辅导老师。今天过得开心吗？你平时喜欢玩什么呀？"}]
        st.session_state.messages = default_msgs
        save_chat_history(default_msgs)
        if hasattr(st, 'rerun'):
            st.rerun()
        else:
            st.experimental_rerun()

    st.write("---")
    st.subheader("📊 专家工具")
    if st.button("📑 生成专业评估报告", use_container_width=True):
        st.session_state["show_report"] = True

# --- 报告弹窗/显示逻辑 ---
if st.session_state.get("show_report"):
    st.markdown("---")
    st.header("📋 孩子成长发展评估报告")
    report_md = generate_assessment_report(profile, get_assessment_status())
    st.markdown(report_md)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("关闭报告"):
            st.session_state["show_report"] = False
            st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
    with col2:
        st.download_button("下载 Markdown 报告", report_md, file_name=f"Assessment_Report_{profile.get('basic_info',{}).get('name','child')}.md")
    st.markdown("---")

# --- 主界面 ---
st.title("🤖 AI 数学老师 (破冰评估版)")
st.markdown("在这个阶段，AI 会用轻松的方式和孩子随意聊天，并在后台自动提取孩子的特征档案。**请您扮演孩子在下方输入框和 AI 聊天，同时观察左侧栏档案的变化！**")

if "messages" not in st.session_state:
    saved_history = load_chat_history()
    if saved_history:
        st.session_state.messages = saved_history
    else:
        st.session_state.messages = [{"role": "assistant", "content": "你好呀！我是你的新朋友，也是你的数学辅导老师。今天过得开心吗？你平时喜欢玩什么呀？"}]

st.write("---")
total_msgs = len(st.session_state.messages)
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.info(f"**🧒 孩子:** {message['content']}")
    else:
        st.success(f"**🤖 AI老师:** {message['content']}")
        # 为每条 AI 消息添加朗读按钮
        btn_key = f"tts_btn_{idx}"
        if st.button("🔊 朗读这段话", key=btn_key):
            st.session_state[f"tts_play_{idx}"] = True
            
        should_play = st.session_state.get(f"tts_play_{idx}", False)
        is_latest_ai = (idx == total_msgs - 1 and message["role"] == "assistant")
        auto_play_done = st.session_state.get("last_auto_played", -1)
        
        if should_play or (is_latest_ai and idx != auto_play_done and st.session_state.get("auto_tts", True)):
            with st.spinner("🎵 正在通过 API 生成高音质语音..."):
                try:
                    tts_cfg = _voice_cfg["tts"]
                    
                    @st.cache_data(show_spinner=False)
                    def get_tts_audio_bytes(text, tts_key, tts_model, tts_voice):
                        return tts_generate(
                            text=text,
                            api_key=tts_key,
                            resource_id=tts_model,
                            voice=tts_voice,
                        )
                    
                    audio_bytes = get_tts_audio_bytes(
                        message['content'],
                        tts_cfg["api_key"],
                        tts_cfg["resource_id"],
                        tts_cfg["voice"],
                    )
                    
                    import base64
                    b64 = base64.b64encode(audio_bytes).decode()
                    md = f"""
                        <audio autoplay="true" controls style="width: 100%; height: 40px; margin-top: 5px;">
                            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                        </audio>
                    """
                    st.markdown(md, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"语音生成失败: {e}")
                    
            if should_play:
                st.session_state[f"tts_play_{idx}"] = False
            if is_latest_ai:
                st.session_state["last_auto_played"] = idx

st.write("---")

col1, col2 = st.columns([5, 1])

with col1:
    with st.form("chat_form", clear_on_submit=True):
        text_prompt = st.text_input("敲字回复，或者在右侧点击录音...", placeholder="扮演孩子，在这里输入回复吧...")
        submitted = st.form_submit_button("发送文字")

with col2:
    st.write(" ")
    st.write(" ")
    # 使用 mic_recorder 录制音频字节，发给大厂 API，注意必须用 wav 格式以支持大模型流式识别
    audio_bytes = mic_recorder(
        start_prompt="🎙️ 点击录音",
        stop_prompt="⏹️ 点击发送",
        format="wav",
        just_once=True,
        key='stt_recorder'
    )

# 统一处理输入：优先使用表单文字，如果没有则使用语音识别结果
prompt = None
if submitted and text_prompt:
    prompt = text_prompt
elif audio_bytes:
    # 防止 Streamlit 刷新时重复提交同一段录音
    audio_id = hash(audio_bytes['bytes'])
    if audio_id != st.session_state.get("last_audio_id", ""):
        st.session_state["last_audio_id"] = audio_id
        
        stt_cfg = _voice_cfg["stt"]
        with st.spinner("🎙️ 正在识别语音..."):
            try:
                prompt = stt_recognize(
                    audio_bytes=audio_bytes['bytes'],
                    api_key=stt_cfg["api_key"],
                    resource_id=stt_cfg["resource_id"],
                )
            except Exception as e:
                st.error(f"语音识别失败: {e}")

if prompt:
    if not api_key:
        st.error("请先在左侧栏设置 API Key 才能聊天哦！")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("老师正在回复..."):
        try:
            # 取最近 10 条记录
            history_for_llm = st.session_state.messages[-10:]
            
            reply, updated_profile, assessment_info = get_ai_response_and_update_profile(
                api_key=api_key,
                base_url=base_url if base_url else "https://api.openai.com/v1",
                chat_history=history_for_llm, 
                current_profile=profile,
                model_name=model_name
            )
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # 如果 AI 返回了结构化评估题目，存入 session_state
            if assessment_info:
                st.session_state["pending_assessment"] = assessment_info
            
            # 保存最新的画像和对话记录
            save_profile(updated_profile)
            save_chat_history(st.session_state.messages)
            
            # 重新运行刷新页面
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()
            
        except Exception as e:
            st.error(f"发生错误: {e}")

# ===== 结构化评估与互动任务 =====
pending = st.session_state.get("pending_assessment", None)
if pending:
    item_id = pending["item_id"]
    
    # 查找题目信息
    item_info = None
    for item in ASSESSMENT_ITEMS:
        if item["id"] == item_id:
            item_info = item
            break
    
    if item_info:
        task_type = item_info.get("task_type", "choice")
        dim_label = item_info.get("dim_label", "评估")
        
        st.markdown("---")
        
        # 1. 处理选择题 (Choice/Likert)
        if task_type in ["choice", "likert_3", "dialog"] and item_info.get("options"):
            choices = item_info["options"]
            st.markdown(f"📝 **{dim_label}** —— 请选择：")
            cols = st.columns(len(choices))
            for i, option in enumerate(choices):
                with cols[i]:
                    if st.button(option, key=f"assess_choice_{item_id}_{i}", use_container_width=True):
                        record_answer(item_id, option)
                        st.session_state.messages.append({"role": "user", "content": f"我选择：{option}"})
                        save_chat_history(st.session_state.messages)
                        st.session_state["pending_assessment"] = None
                        st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()

        # 2. 处理互动小游戏 (Game)
        elif task_type == "game":
            game_id = item_info.get("game_id")
            st.markdown(f"🎮 **{dim_label}挑战：{item_info['text']}**")
            
            if game_id == "memory_forest":
                # 渲染 HTML/JS 游戏
                components.html(TASK_TEMPLATES["memory_forest"]["html"], height=480)
                
                # 手动输入得分（因为 iframe 通讯在 Streamlit 中较复杂，先用简单交互）
                score_input = st.number_input("游戏结束了吗？请输入你的最高得分（如果没有看到得分，请先玩游戏哦）：", min_value=0, max_value=100, step=10)
                if st.button("提交游戏结果"):
                    record_answer(item_id, f"得分: {score_input}")
                    st.session_state.messages.append({"role": "user", "content": f"我完成了【记忆之森】，得分是 {score_input}！"})
                    save_chat_history(st.session_state.messages)
                    st.session_state["pending_assessment"] = None
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
            
            elif game_id == "logic_balance":
                options = render_logic_balance_ui()
                cols = st.columns(len(options))
                for i, opt in enumerate(options):
                    with cols[i]:
                        if st.button(opt, key=f"logic_opt_{i}", use_container_width=True):
                            record_answer(item_id, opt)
                            st.session_state.messages.append({"role": "user", "content": f"我觉得最重的是：{opt}"})
                            save_chat_history(st.session_state.messages)
                            st.session_state["pending_assessment"] = None
                            st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
            
            elif game_id == "number_sense":
                target = 7 # 简化版固定目标
                st.markdown(f"✨ **数感挑战**：请快速数一数下面有多少个星星？")
                st.write("🌟 " * target)
                guess = st.number_input("有多少个？", min_value=1, max_value=20)
                if st.button("我数好了"):
                    is_correct = (guess == target)
                    record_answer(item_id, "正确" if is_correct else f"错误(猜了{guess})")
                    st.session_state.messages.append({"role": "user", "content": f"我数出来了，是 {guess} 个！"})
                    save_chat_history(st.session_state.messages)
                    st.session_state["pending_assessment"] = None
                    st.rerun() if hasattr(st, 'rerun') else st.experimental_rerun()
