# AI 老师 - 儿童心理与认知评估系统

本项目是一款专为 8-9 岁儿童设计的智能数学辅导与评估 Agent。它结合了教育心理学量表与自然对话技术，旨在通过“无感”的沟通与互动游戏，构建精准的学生画像。

## 核心功能

- **智能画像评估**：基于 SDQ（长处和困难问卷）、成长型思维、VARK 学习风格等 8 大教育心理学理论。
- **互动小游戏**：内置【记忆之森】（工作记忆）、【逻辑天平】（演绎推理）等互动任务，提升评估趣味性。
- **自然语音交互**：集成火山引擎高音质 TTS 与 STT，支持流畅的语音对话。
- **动态 RAG 知识库**：根据对话内容实时检索专业教育理论，辅助 AI 生成更具深度的诊断结果。

## 快速开始

### 1. 环境准备
确保您的电脑已安装 Python 3.7+。建议使用 Anaconda 或 venv 创建独立环境：

```bash
pip install streamlit requests scikit-learn streamlit-mic-recorder
```

### 2. 配置 API
为了保护隐私，核心配置文件已忽略。请根据模板创建您的本地配置：

- **大模型配置**：
  将 `settings.json.example` 重命名为 `settings.json`，并填入您的 DeepSeek 或 OpenAI 兼容的 API Key。
- **语音配置**：
  将 `volcengine/voice_config.json.example` 重命名为 `volcengine/voice_config.json`，并填入您的火山引擎 API Key。

### 3. 启动应用
在项目根目录下运行：

```bash
streamlit run app.py
```

## 项目文档

完整的需求与设计文档已整理在 `docs/` 目录下：
- [需求说明书 (PRD)](docs/PRD.md)
- [架构设计说明 (Architecture)](docs/architecture_design.md)
- [内部模块规范 (API Spec)](docs/api_spec.md)

## 快速开始
本项目仅供教育与研究使用。
