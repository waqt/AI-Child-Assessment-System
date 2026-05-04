# -*- coding: utf-8 -*-
"""
Bayesian Knowledge Tracing (BKT) Core Skill
基于伯克利 pyBKT 的核心数学模型，用于追踪学生对特定知识点的掌握概率。
"""

class BKTModel:
    def __init__(self, p_init=0.3, p_learn=0.1, p_guess=0.2, p_slip=0.1):
        """
        初始化 BKT 参数：
        :param p_init:  初始掌握概率 (Prior)
        :param p_learn: 学习率 (从不掌握到掌握的概率)
        :param p_guess: 猜测率 (没掌握但做对的概率)
        :param p_slip:  失误率 (掌握了但做错的概率)
        """
        self.p_init = p_init
        self.p_learn = p_learn
        self.p_guess = p_guess
        self.p_slip = p_slip

    def update_mastery(self, current_p_known, is_correct):
        """
        根据观察到的行为（正确/错误）更新掌握概率
        """
        if is_correct:
            # P(Known | Correct)
            p_known_given_obs = (current_p_known * (1 - self.p_slip)) / \
                                (current_p_known * (1 - self.p_slip) + (1 - current_p_known) * self.p_guess)
        else:
            # P(Known | Incorrect)
            p_known_given_obs = (current_p_known * self.p_slip) / \
                                (current_p_known * self.p_slip + (1 - current_p_known) * (1 - self.p_guess))
        
        # 考虑学习过程后的新概率
        p_known_next = p_known_given_obs + (1 - p_known_given_obs) * self.p_learn
        return round(p_known_next, 4)

# 针对不同领域的默认模型配置
DEFAULT_MODELS = {
    "math_logic": BKTModel(p_init=0.25, p_learn=0.15, p_guess=0.2, p_slip=0.1),
    "working_memory": BKTModel(p_init=0.4, p_learn=0.05, p_guess=0.1, p_slip=0.15), # 认知能力学习率较低
}

def track_student_knowledge(skill_name, history_results):
    """
    追踪学生对某个技能的掌握情况。
    :param skill_name: 技能名称
    :param history_results: 历史对错序列 (如 [True, False, True])
    """
    model = DEFAULT_MODELS.get(skill_name, BKTModel())
    p_known = model.p_init
    
    for res in history_results:
        p_known = model.update_mastery(p_known, res)
        
    return p_known

if __name__ == "__main__":
    # 测试：连续做对 3 次
    results = [True, True, True]
    mastery = track_student_knowledge("math_logic", results)
    print(f"连续做对3次后的掌握概率: {mastery}")
    
    # 测试：一对比，一做错
    results = [True, False]
    mastery = track_student_knowledge("math_logic", results)
    print(f"一对一错后的掌握概率: {mastery}")
