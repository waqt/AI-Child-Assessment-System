# -*- coding: utf-8 -*-
"""
AI Teacher System Health Check
自动化体检脚本，验证核心模块连通性。
"""
import sys
import os

def check_imports():
    print("--- 1. Dependency Check ---")
    libs = ["streamlit", "openai", "sklearn", "mathgenerator", "streamlit_mic_recorder"]
    for lib in libs:
        try:
            __import__(lib)
            print(f"[OK] {lib:20}")
        except ImportError:
            print(f"[MISSING] {lib:20}")

def check_local_modules():
    print("\n--- 2. Local Module Check ---")
    modules = [
        "systems.profiler.agent", 
        "systems.profiler.assessment", 
        "core.memory", 
        "systems.knowledge.graph"
    ]
    for mod in modules:
        try:
            __import__(mod)
            print(f"[OK] {mod:20}")
        except Exception as e:
            print(f"[ERROR] {mod:20} ({str(e)})")

def check_data_files():
    print("\n--- 3. Data File Check ---")
    files = [
        os.path.join("storage", "profiles", "student_profile.json"),
        os.path.join("systems", "knowledge", "data", "math_elementary.json"),
        os.path.join("storage", "plans", "learning_plan.json")
    ]
    for f in files:
        if os.path.exists(f):
            print(f"[EXISTS] {f:20}")
        else:
            print(f"[NOT_FOUND] {f:20}")

if __name__ == "__main__":
    print("Starting System Health Check...\n")
    check_imports()
    check_local_modules()
    check_data_files()
    print("\nHealth check finished. If all items are OK, you can run 'streamlit run app.py'.")
