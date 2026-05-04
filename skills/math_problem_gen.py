# -*- coding: utf-8 -*-
import random

def generate_math_problem(difficulty=1, topic="addition"):
    """
    轻量级数学题目生成器，覆盖小学 1-3 年级核心知识点。
    """
    if topic == "addition":
        if difficulty == 1: # 20以内加法
            a, b = random.randint(1, 10), random.randint(1, 10)
        elif difficulty == 2: # 100以内进位加法
            a, b = random.randint(10, 50), random.randint(10, 50)
        else: # 万以内加法
            a, b = random.randint(100, 1000), random.randint(100, 1000)
        return {"q": f"{a} + {b} = ?", "a": a + b}
    
    elif topic == "logic_series": # 找规律
        start = random.randint(1, 10)
        step = random.randint(2, 5)
        series = [start + i*step for i in range(4)]
        return {"q": f"观察数列: {series[0]}, {series[1]}, {series[2]}, {series[3]}, ... 下一个是？", "a": series[3] + step}
    
    elif topic == "geometry_basic": # 基础几何
        width = random.randint(2, 10)
        height = random.randint(2, 10)
        return {"q": f"长方形的宽是 {width}cm，长是 {height}cm，它的面积是多少平方厘米？", "a": width * height}

    return {"q": "1 + 1 = ?", "a": 2}

def get_problem_set(level="Grade3", count=3):
    """
    根据年级生成一套练习题
    """
    topics = ["addition", "logic_series", "geometry_basic"]
    problems = []
    diff = 2 if level == "Grade3" else 1
    
    for _ in range(count):
        t = random.choice(topics)
        problems.append(generate_math_problem(difficulty=diff, topic=t))
    
    return problems

if __name__ == "__main__":
    print(get_problem_set("Grade3", 2))
