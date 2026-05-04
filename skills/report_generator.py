# -*- coding: utf-8 -*-
import json
import datetime

def generate_assessment_report(profile: dict, progress: dict) -> str:
    """
    根据画像和评测进度生成一份给家长的专业报告。
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    name = profile.get("basic_info", {}).get("name", "小同学")
    
    report = f"""# 孩子成长发展评估报告
**报告日期**: {now}
**学生姓名**: {name}
**评估阶段**: {profile.get('assessment_progress', '评估中')}

---

## 1. 核心特征概览
以下是 AI 老师通过对话与互动任务观察到的核心特征：

### 🌟 性格与社交 (Personality & Social)
- **状态**: {profile.get('educational_profile', {}).get('personality', {}).get('status', '评估中')}
- **特征**: {profile.get('educational_profile', {}).get('personality', {}).get('confirmed_traits', '正在深入了解中')}

### 🚀 学习动机与行为 (Behavioral)
- **状态**: {profile.get('educational_profile', {}).get('behavioral_traits', {}).get('status', '评估中')}
- **特征**: {profile.get('educational_profile', {}).get('behavioral_traits', {}).get('confirmed_traits', '正在观察学习坚持度与思维模式')}

### 🧠 认知与数学潜力 (Cognitive & Math)
- **状态**: {profile.get('educational_profile', {}).get('math_capability', {}).get('status', '评估中')}
- **特征**: {profile.get('educational_profile', {}).get('math_capability', {}).get('confirmed_traits', '正在评估逻辑推理与数感')}

---

## 2. 评测进度详情
当前结构化评测完成度：**{progress.get('answered_count', 0)}/{progress.get('total_items', 19)}**

| 维度 | 得分/表现 | 状态 |
|------|-----------|------|
"""
    # 动态添加维度得分
    scores = progress.get("dimension_scores", {})
    for dim, score in scores.items():
        report += f"| {dim} | {score} | 已记录 |\n"

    report += """
---

## 3. 专家深度分析 (Inner Insights)
> {expert_thoughts}

---

## 4. 教育建议
根据目前的画像，建议家长：
1. **兴趣引导**：利用孩子对 {interests} 的兴趣，设计相关的数学应用场景。
2. **思维培养**：在日常生活中多鼓励“过程性评价”，强化成长型思维。
3. **针对性练习**：重点关注画像中标记为“待加强”的认知领域。

---
*本报告由 AI 智能评估引擎生成，仅供家庭教育参考。*
""".format(
        expert_thoughts=profile.get("expert_inner_thoughts", "评估尚在初期，建议继续进行对话以获取更精准的分析。"),
        interests="、".join(profile.get("interests", ["学习"]))
    )
    
    return report
