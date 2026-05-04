# -*- coding: utf-8 -*-
"""
互动评估任务模块 (Interactive Tasks Module)
===========================================
包含各种互动小游戏的 HTML/JS 模板和逻辑。
"""

import json

# ============================================================
# 1. 【记忆之森】 (Working Memory Game)
# ============================================================

MEMORY_QUEST_HTML = """
<div id="game-container" style="
    background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
    padding: 20px;
    border-radius: 15px;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
">
    <h2 style="margin-bottom: 10px;">💎 记忆之森挑战</h2>
    <p id="instruction">看仔细！记住闪烁宝石的顺序...</p>
    
    <div id="grid" style="
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        max-width: 300px;
        margin: 20px auto;
    ">
        <div class="gem" id="gem-0" onclick="handleGemClick(0)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-1" onclick="handleGemClick(1)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-2" onclick="handleGemClick(2)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-3" onclick="handleGemClick(3)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-4" onclick="handleGemClick(4)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-5" onclick="handleGemClick(5)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-6" onclick="handleGemClick(6)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-7" onclick="handleGemClick(7)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
        <div class="gem" id="gem-8" onclick="handleGemClick(8)" style="height: 80px; background: rgba(255,255,255,0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s;"></div>
    </div>
    
    <button id="start-btn" onclick="startGame()" style="
        padding: 10px 30px;
        font-size: 18px;
        background: #fff;
        color: #b21f1f;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    ">开始闯关</button>

    <div id="result" style="margin-top: 15px; font-weight: bold; display: none;"></div>
</div>

<script>
    let sequence = [];
    let playerSequence = [];
    let level = 1;
    let isShowing = false;

    function startGame() {
        document.getElementById('start-btn').style.display = 'none';
        document.getElementById('result').style.display = 'none';
        level = 1;
        nextLevel();
    }

    function nextLevel() {
        playerSequence = [];
        sequence.push(Math.floor(Math.random() * 9));
        showSequence();
    }

    function showSequence() {
        isShowing = true;
        document.getElementById('instruction').innerText = "记住这个顺序！(第 " + level + " 关)";
        let i = 0;
        const interval = setInterval(() => {
            flashGem(sequence[i]);
            i++;
            if (i >= sequence.length) {
                clearInterval(interval);
                isShowing = false;
                document.getElementById('instruction').innerText = "到你了！请按顺序点击宝石";
            }
        }, 800);
    }

    function flashGem(id) {
        const gem = document.getElementById('gem-' + id);
        gem.style.background = '#fff';
        gem.style.boxShadow = '0 0 20px #fff';
        setTimeout(() => {
            gem.style.background = 'rgba(255,255,255,0.2)';
            gem.style.boxShadow = 'none';
        }, 500);
    }

    function handleGemClick(id) {
        if (isShowing) return;
        
        flashGem(id);
        playerSequence.push(id);
        
        const currentStep = playerSequence.length - 1;
        if (playerSequence[currentStep] !== sequence[currentStep]) {
            endGame(false);
            return;
        }
        
        if (playerSequence.length === sequence.length) {
            if (level >= 5) {
                endGame(true);
            } else {
                level++;
                setTimeout(nextLevel, 1000);
            }
        }
    }

    function endGame(win) {
        const resultDiv = document.getElementById('result');
        resultDiv.style.display = 'block';
        if (win) {
            resultDiv.innerHTML = "🎉 太棒了！你是记忆达人！<br>评估分数: 100";
            document.getElementById('instruction').innerText = "挑战成功！";
        } else {
            resultDiv.innerHTML = "😟 哎呀，记错了~ 再接再厉！<br>评估分数: " + (level * 20 - 20);
            document.getElementById('instruction').innerText = "挑战结束";
        }
        
        // 发送结果给 Streamlit (通过 window.parent)
        const score = win ? 100 : (level * 20 - 20);
        window.parent.postMessage({
            type: 'streamlit:set_component_value',
            value: {game: 'memory_forest', score: score, level: level}
        }, '*');
    }
</script>
"""

# ============================================================
# 2. 【逻辑天平】 (Logical Reasoning)
# ============================================================
# 这里我们使用 Streamlit 原生组件结合 CSS 实现，不使用复杂的 HTML 组件，以保证稳定性

def render_logic_balance_ui():
    """
    使用 Streamlit 原生组件渲染逻辑天平题。
    """
    import streamlit as st
    st.markdown("### ⚖️ 逻辑天平挑战")
    st.info("森林里的小动物在玩跷跷板，请根据它们的情况推断一下：")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **已知条件 1：**
        🐘 大象 > 🦓 斑马
        """)
    with col2:
        st.markdown("""
        **已知条件 2：**
        🦓 斑马 > 🐕 小狗
        """)
        
    st.write("---")
    st.write("**问题：谁最重？**")
    
    # 结果通过按钮返回
    return ["🐘 大象", "🦓 斑马", "🐕 小狗"]

# ============================================================
# 3. 【数感连连看】 (Number Sense Game)
# ============================================================

def get_number_sense_game():
    """
    快速识别数量的小游戏。
    """
    import random
    # 随机生成一个 4-12 之间的数量
    target = random.randint(4, 12)
    return target

# 任务定义字典
TASK_TEMPLATES = {
    "memory_forest": {
        "name": "记忆之森",
        "html": MEMORY_QUEST_HTML,
        "dimension": "executive_function.working_memory",
        "height": 450
    },
    "logic_balance": {
        "name": "逻辑天平",
        "dimension": "math_capability.logic_reasoning"
    },
    "number_sense": {
        "name": "数感连连看",
        "dimension": "math_capability.number_sense"
    }
}
