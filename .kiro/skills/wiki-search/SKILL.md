---
name: wiki-search
description: 从本地 Wiki 知识库中检索相关知识。当需要了解历史决策、踩坑记录、最佳实践或用户偏好时使用。
---

# Wiki 知识检索

## 用途
检索本地 Wiki 知识库中的词条。Wiki 存储在 workbench/data/memory/ 目录下。

## 目录结构
- concepts/ — 概念词条（What）
- decisions/ — 决策记录（Why）
- patterns/ — 模式/最佳实践（How）
- pitfalls/ — 踩坑记录（Don't）
- preferences/ — 个人偏好（Style）

## 使用方式

### 查看索引
cat /mnt/d/workspace/agentflow-pipeline/workbench/data/memory/_index.md

### 按关键词搜索
grep -rl "关键词" /mnt/d/workspace/agentflow-pipeline/workbench/data/memory/

### 读取具体词条
cat /mnt/d/workspace/agentflow-pipeline/workbench/data/memory/patterns/xxx.md

## 词条格式
每个词条是一个 Markdown 文件，带 YAML frontmatter：
```yaml
---
title: 词条标题
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [other-entry]
source: session/YYYY-MM-DD-xxx
---
```
