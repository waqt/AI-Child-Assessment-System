# -*- coding: utf-8 -*-
import json
import os

class KnowledgeGraphManager:
    def __init__(self, graph_path):
        with open(graph_path, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
        self.nodes = {node['id']: node for node in self.graph['nodes']}
        
    def get_prerequisites(self, node_id):
        """获取前置知识点"""
        return [edge['source'] for edge in self.graph['edges'] if edge['target'] == node_id]

    def get_next_topics(self, node_id):
        """获取后续可以学习的知识点"""
        return [edge['target'] for edge in self.graph['edges'] if edge['source'] == node_id]

    def get_learning_path(self, target_node_id):
        """生成学习路径（深度优先搜索）"""
        path = []
        visited = set()

        def dfs(curr_id):
            if curr_id in visited: return
            visited.add(curr_id)
            for pre in self.get_prerequisites(curr_id):
                dfs(pre)
            path.append(self.nodes[curr_id]['name'])

        dfs(target_node_id)
        return " -> ".join(path)

# 全局单例
_graph_path = os.path.join(os.path.dirname(__file__), "data", "math_elementary.json")
kg_manager = KnowledgeGraphManager(_graph_path)

if __name__ == "__main__":
    print(f"乘法基础的前置要求: {kg_manager.get_prerequisites('multiplication_basic')}")
    print(f"除法基础的学习路径: {kg_manager.get_learning_path('division_basic')}")
