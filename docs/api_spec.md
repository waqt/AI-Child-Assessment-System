# 内部 API 与模块规范 (Internal API Spec)

## 1. agent.py
负责大模型调用逻辑。

### `get_ai_response_and_update_profile(...)`
- **输入**: `chat_history`, `current_profile`, `model_config`
- **输出**: `(reply, updated_profile, assessment_info)`
- **逻辑**: 构建 System Prompt，调用 LLM，解析 JSON 结果。

## 2. assessment_engine.py
结构化题目与评估进度管理。

### `get_suggested_items_text()`
- **描述**: 为 AI 准备“推荐题目”的描述文本。

### `record_answer(item_id, answer)`
- **描述**: 记录结构化题目的得分，更新 `assessment_progress.json`。

## 3. knowledge_rag.py
知识库检索逻辑。

### `get_relevant_theories(context, top_k=3)`
- **描述**: 根据对话上下文，从 Markdown 文档中检索专业理论。

## 4. volcengine/voice_service.py
语音能力。

### `tts_generate(text)` -> `bytes`
- **描述**: 文字转语音。

### `stt_recognize(audio_bytes)` -> `str`
- **描述**: 语音转文字。
