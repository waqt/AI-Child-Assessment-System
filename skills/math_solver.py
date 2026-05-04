# -*- coding: utf-8 -*-
import math
import re

def solve_math_expression(expression: str) -> str:
    """
    一个简单的数学解题工具，用于验证计算结果并提供分步解释。
    支持基础运算、平方根等。
    """
    # 简单的安全性清理
    expression = expression.replace(" ", "")
    if not re.match(r'^[0-9+\-*/().sqrt^]+$', expression):
        return "抱歉，这个表达式有点太复杂了，我还在学习中！"
    
    try:
        # 转换某些符号
        safe_expr = expression.replace("^", "**").replace("sqrt", "math.sqrt")
        result = eval(safe_expr, {"__builtins__": None, "math": math})
        
        # 生成简单的解释
        explanation = f"计算过程：\n1. 输入表达式: {expression}\n2. 计算结果为: {result}"
        return explanation
    except Exception as e:
        return f"计算出错了：{e}"

if __name__ == "__main__":
    print(solve_math_expression("3 * (4 + 5)"))
    print(solve_math_expression("sqrt(16) + 2^3"))
