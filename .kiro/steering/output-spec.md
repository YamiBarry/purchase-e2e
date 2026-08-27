---
inclusion: manual
---

# 设计输出规范

## 静态多状态输出规则

所有输出的组件必须是静态多状态展示，禁止输出可交互组件。

- ❌ 禁止：用 JavaScript 实现状态切换（onclick、addEventListener）
- ❌ 禁止：用 JS 动态构建或注入 HTML
- ❌ 禁止：只输出单一默认状态
- ✅ 要求：每个状态作为独立的静态 HTML 块输出

## HTML 注释嵌套禁止规则（铁律）

**在 HTML 注释块 `<!-- ... -->` 内部，禁止出现 `<!--` 或 `-->`。**

浏览器遇到注释内部的 `-->` 会认为注释提前结束，导致后续文字被渲染为可见内容。

- ❌ 禁止：注释内写 `<!-- ▼▼▼ COMPONENT: ... ▼▼▼ -->`
- ❌ 禁止：注释内写 `<script>`、`<style>` 等 HTML 标签（可能触发解析异常）
- ✅ 正确：注释内引用标记时去掉 `<!--` 和 `-->`，只写纯文字
- ✅ 正确：`3. 组件 HTML → 复制 ▼▼▼ COMPONENT ▼▼▼ 到结束标记之间的内容`

## 代码边界标记

```html
<!-- ==========================================
     [DESIGN CONTEXT - NOT FOR CODING]
     ========================================== -->
<div class="design-annotation" style="display:none">
  <ul>
    <li>STATE: default — [说明]</li>
    <li>STATE: hover — [说明]</li>
  </ul>
</div>
<!-- [/DESIGN CONTEXT] -->

<!-- ==========================================
     [COMPONENT CODE START]
     Coding Agent 只处理此标记内的内容
     ========================================== -->
<style>/* Token 变量 + 样式 */</style>
<!-- STATE: default -->
<div class="component-state" data-state="default">...</div>
<!-- STATE: hover -->
<div class="component-state" data-state="hover">...</div>
<!-- [COMPONENT CODE END] -->
```

## 开发交付标记

HTML 组件标记：
```html
<!-- ▼▼▼ COMPONENT: [组件名称] — COPY FROM HERE ▼▼▼ -->
...
<!-- ▲▲▲ COMPONENT: [组件名称] — COPY TO HERE ▲▲▲ -->
```

CSS 组件样式标记：
```css
/* ▼▼▼ COMPONENT STYLES: [组件名称] — COPY FROM HERE ▼▼▼ */
...
/* ▲▲▲ COMPONENT STYLES: [组件名称] — COPY TO HERE ▲▲▲ */
```

交付说明必须包含：
```
📦 开发复制指南：
1. CSS Token 变量  → 复制 <style> 内 :root { ... } 部分
2. 组件样式        → 复制 ▼▼▼ COMPONENT STYLES ▼▼▼ 到结束标记之间的内容
3. 组件 HTML       → 复制 ▼▼▼ COMPONENT ▼▼▼ 到结束标记之间的内容
⚠️  不需要复制：设计日志注释、<script> 内伪代码
```

## 输出结构（顶部注释）

```html
<!--
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YAMI DESIGN AGENT OUTPUT
  组件：[组件名称]
  页面：[所在页面]
  版本：1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  【交互说明】
  触发时机 / 出现位置 / 关闭方式 / 动画描述 / 移动端 / body 滚动

  【交付说明】
  ✅ 已完成 / ⚠️ 开发接管 / 📦 开发复制指南 / Coding Agent 提取规则

  【Token 对照】
  所有 Token 变量及对应 design-system-context.md 章节
-->
```

## 设计推导日志格式

```html
<!--
  ╔═══════════════════════════════════════════╗
  ║   DESIGN AGENT INTERPRETATION LOG         ║
  ╚═══════════════════════════════════════════╝

  ── 业务理解 ──
  业务目标 / 触发场景 / 目标用户 / 核心内容 / 操作路径 / 交付形式

  ── 组件匹配 ──
  场景识别 / 匹配级别 / 匹配结果 / 匹配依据

  ── 设计推导 ──
  组件类型 / 关闭方式 / Mobile 适配 / 视觉层级 / 输出类型 / 输出状态

  [AUTO-PROCEEDING TO GENERATION]
-->
```

## 完整页面 vs 组件片段

**完整页面**：<!DOCTYPE html> + Sticky Nav + Section 背景交替（#FFFFFF / neutral/50）+ 全量 Token
**组件片段**：只输出 <style> + HTML 片段 + <script> 伪代码，禁止 html/head/body

## Mobile Bottom Sheet — Drag Handle 规则

- 有 ✕ 或遮罩关闭 → 不显示 Drag Handle
- 无任何关闭方式 → 显示 Drag Handle
- 原则：关闭方式和 Drag Handle 不同时出现
