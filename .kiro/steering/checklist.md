---
inclusion: manual
---

# 设计输出自检清单

输出前逐项检查，任何一项不通过先修正再输出。

## 样式规范
- [ ] 无硬编码颜色（无 #xxxxxx 直接赋值）
- [ ] 无硬编码间距（无 padding: 16px 直接数值）
- [ ] 无硬编码圆角
- [ ] 无外部 CSS 框架

## HTML 注释安全
- [ ] 注释块内无嵌套 `<!--` 或 `-->`（会导致浏览器提前结束注释）
- [ ] 注释块内无 HTML 标签（如 `<script>`、`<style>`）

## 组件规范
- [ ] CTA 按钮使用 Primary Button 规范
- [ ] 弹窗使用 shadow-level-3
- [ ] 卡片使用 radius-lg
- [ ] 标签使用 radius-full

## 交互说明
- [ ] 顶部注释包含触发时机
- [ ] 顶部注释包含关闭方式
- [ ] 顶部注释包含动画描述
- [ ] 顶部注释包含移动端处理

## 无障碍
- [ ] 弹窗有 role="dialog" aria-modal aria-labelledby
- [ ] 图标按钮有 aria-label
- [ ] 焦点样式使用 var(--color-blue-500)

## 响应式
- [ ] 有 @media (max-width: 767px) Mobile 样式
- [ ] Mobile 弹窗适配（bottom sheet 或 max-width）
- [ ] prefers-reduced-motion 已处理

## 静态多状态
- [ ] 无 JS 交互逻辑
- [ ] 所有状态均已输出
- [ ] 每个状态有 <!-- STATE: xxx --> 标识
- [ ] [COMPONENT CODE START/END] 边界标记完整

## 开发交付标记
- [ ] ▼▼▼ COMPONENT ▼▼▼ 标记存在
- [ ] ▼▼▼ COMPONENT STYLES ▼▼▼ 标记存在
- [ ] 📦 开发复制指南已写入

## Google Drive 上传（铁律）
- [ ] upload_file 已调用（folder_id: 1QQHE-D8ICnp10uNZr8czDuiaVxjvCqkR）
- [ ] 📁 Google Drive 链接已输出
