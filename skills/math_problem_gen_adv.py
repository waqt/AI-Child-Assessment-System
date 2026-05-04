# -*- coding: utf-8 -*-
try:
    import mathgenerator
    HAS_MATHGEN = True
except ImportError:
    HAS_MATHGEN = False
    import random

def get_advanced_problem(topic_id=None):
    """
    使用开源 mathgenerator 生成题目。
    如果库未安装，则回退到内置的简易逻辑。
    """
    if HAS_MATHGEN:
        # mathgenerator ID 示例: 0:Addition, 1:Subtraction, 2:Multiplication
        if topic_id is None:
            topic_id = random.randint(0, 2)
        problem, answer = mathgenerator.genById(topic_id)
        return {"q": problem, "a": answer, "source": "mathgenerator"}
    else:
        # 回退逻辑
        from .math_problem_gen import generate_math_problem
        return generate_math_problem()

if __name__ == "__main__":
    print(get_advanced_problem())
