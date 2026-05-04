# AI Teacher - 智慧教师画像与教学决策系统

本项目致力于打造一个全周期的 AI 教师系统，通过 3-6 年级数学知识框架，结合教育心理学理论，为孩子提供个性化的评估、规划与教学建议。

## 🌟 核心架构：三大子系统

本项目采用模块化设计，将教师职责拆分为相互协作的三大核心系统：

1.  **性格与行为分析系统 (Profiling System)**:
    - 负责了解孩子的个性、动机、敏感点及学习风格。
    - 包含：专家级分析 Agent、结构化评测量表（SDQ、VARK 等）、互动小游戏。
2.  **知识管理系统 (Knowledge System)**:
    - 负责管理 K12 数学知识图谱，评估知识掌握程度。
    - 包含：数学知识追踪 (BKT)、语义知识检索 (RAG)、动态图谱导航。
3.  **课程与练习系统 (Curriculum System)**:
    - 负责设定长短期目标，产出个性化学习任务。
    - 包含：战略规划师 Agent、自适应题目生成器 (MathGenerator)。

---

## 📂 目录结构

```text
/profiling_system/
├── app.py                   # 系统启动入口
├── core/                    # 公共底层服务 (存储、语音、工具类)
├── systems/                 # --- 三大子系统 ---
│   ├── profiler/            # 系统一：性格与行为分析
│   ├── knowledge/           # 系统二：知识管理系统
│   └── curriculum/          # 系统三：课程与练习系统
├── storage/                 # 动态数据存储 (画像、计划、历史)
├── docs/                    # PRD、架构与 API 文档
└── requirements.txt         # 依赖环境清单
```

---

## 🚀 快速开始

### 1. 环境准备
推荐使用 Conda 创建独立环境：
```bash
conda create -n aiteacher python=3.10
conda activate aiteacher
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 核心配置
- **模型配置**：在 `storage/` 下创建 `settings.json`（可参考 `settings.json.example`），填入 API Key。
- **语音配置**：在 `core/voice/` 下创建 `voice_config.json`，配置火山引擎 Key。

### 3. 系统体检
启动前建议运行体检脚本确保依赖完整：
```bash
python core/health_check.py
```

### 4. 运行应用
```bash
streamlit run app.py
```

---

## 📚 开发文档
- [产品需求说明 (PRD)](docs/PRD.md)
- [三系统架构设计](docs/architecture_design.md)
- [开发者 API 指南](docs/api_spec.md)

---
*本项目由 AI 驱动开发，旨在探索教育科技的前沿。*
