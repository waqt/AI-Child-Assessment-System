# -*- coding: utf-8 -*-
"""
轻量级知识库检索模块 (Knowledge RAG)
=====================================
使用 TF-IDF + 余弦相似度实现知识文档的语义检索。
无需外部向量数据库，兼容 Python 3.7+。

用法:
    from knowledge_rag import KnowledgeRetriever
    retriever = KnowledgeRetriever()
    relevant_docs = retriever.retrieve("数学焦虑", top_k=3)
"""

import os
import glob
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_KNOWLEDGE_DIR = os.path.join("systems", "profiler", "knowledge")


def _split_document(filepath, chunk_size=500, overlap=100):
    """
    将一个 Markdown 文档按段落/标题切分为多个 chunk。
    优先按 ## 标题切分；如果单个段落太长，再按 chunk_size 切分。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    
    # 按 ## 标题切分
    sections = re.split(r'\n(?=##\s)', content)
    
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        if len(section) <= chunk_size:
            chunks.append({
                "text": section,
                "source": filename,
                "length": len(section)
            })
        else:
            # 长段落按 chunk_size 切分
            words = section
            for i in range(0, len(words), chunk_size - overlap):
                chunk_text = words[i:i + chunk_size]
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text,
                        "source": filename,
                        "length": len(chunk_text)
                    })
    
    return chunks


class KnowledgeRetriever:
    """基于 TF-IDF 的轻量级知识检索器"""
    
    def __init__(self, knowledge_dir=None):
        self.knowledge_dir = knowledge_dir or _KNOWLEDGE_DIR
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()
    
    def _build_index(self):
        """加载所有知识文档并建立 TF-IDF 索引"""
        md_files = glob.glob(os.path.join(self.knowledge_dir, "*.md"))
        
        self.chunks = []
        for filepath in md_files:
            doc_chunks = _split_document(filepath)
            self.chunks.extend(doc_chunks)
        
        if not self.chunks:
            print("[KnowledgeRAG] WARNING: No knowledge documents found!")
            return
        
        texts = [c["text"] for c in self.chunks]
        
        # 使用 TF-IDF 向量化（支持中英文混合）
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",  # 字符级分析，天然支持中文
            ngram_range=(2, 4),  # 2-4 字符的 n-gram
            max_features=10000,
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        print(f"[KnowledgeRAG] Indexed {len(self.chunks)} chunks from {len(md_files)} documents")
    
    def retrieve(self, query, top_k=5, min_score=0.05):
        """
        检索与 query 最相关的知识片段。
        
        Args:
            query: 查询文本（可以是用户的话、AI 的推理、或维度关键词）
            top_k: 返回最多 top_k 个相关片段
            min_score: 最低相关度阈值
            
        Returns:
            list[dict]: 包含 text, source, score 的结果列表
        """
        if not self.chunks or self.vectorizer is None:
            return []
        
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # 按分数降序排列
        ranked_indices = scores.argsort()[::-1]
        
        results = []
        seen_sources = set()
        
        for idx in ranked_indices:
            if len(results) >= top_k:
                break
            
            score = scores[idx]
            if score < min_score:
                break
            
            chunk = self.chunks[idx]
            
            results.append({
                "text": chunk["text"],
                "source": chunk["source"],
                "score": round(float(score), 4)
            })
        
        return results
    
    def retrieve_for_dimensions(self, dimensions, top_k=3):
        """
        根据评估维度列表检索相关理论。
        
        Args:
            dimensions: 维度关键词列表，如 ["数学焦虑", "成长型思维", "同伴关系"]
            top_k: 每个维度返回的片段数
            
        Returns:
            str: 拼接后的相关知识文本
        """
        all_results = []
        seen_texts = set()
        
        for dim in dimensions:
            results = self.retrieve(dim, top_k=top_k)
            for r in results:
                # 去重
                text_hash = hash(r["text"][:100])
                if text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    all_results.append(r)
        
        if not all_results:
            return ""
        
        # 按 score 降序排列
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 拼接为文本
        parts = []
        for r in all_results[:top_k * len(dimensions)]:
            parts.append(f"[来源: {r['source']} | 相关度: {r['score']}]\n{r['text']}")
        
        return "\n\n---\n\n".join(parts)
    
    def get_stats(self):
        """返回知识库统计信息"""
        sources = set(c["source"] for c in self.chunks)
        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(sources),
            "documents": list(sources),
            "total_characters": sum(c["length"] for c in self.chunks)
        }


# 全局单例（避免重复建索引）
_retriever = None

def get_retriever():
    """获取全局知识检索器单例"""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


if __name__ == "__main__":
    # 测试
    retriever = KnowledgeRetriever()
    print("\n=== 知识库统计 ===")
    stats = retriever.get_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    print("\n=== 测试检索: '数学焦虑' ===")
    results = retriever.retrieve("数学焦虑", top_k=3)
    for r in results:
        print(f"[{r['source']}] score={r['score']}")
        print(f"  {r['text'][:80]}...")
    
    print("\n=== 测试检索: '同伴关系 社交' ===")
    results = retriever.retrieve("同伴关系 社交", top_k=3)
    for r in results:
        print(f"[{r['source']}] score={r['score']}")
        print(f"  {r['text'][:80]}...")
