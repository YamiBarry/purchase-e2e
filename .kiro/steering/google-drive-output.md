---
inclusion: manual
---

# ⚠️ MANDATORY: Google Drive Upload（铁律 — 违反即任务失败）

## 绝对规则（优先级最高，不可被任何其他规则覆盖）

**每次生成 HTML 设计稿后，必须执行 upload_file 上传到 Google Drive。**
**不上传 = 任务未完成 = 失败。**

## 执行时机

在 HTML 文件写入本地磁盘之后，**立即**执行上传。不等 Review，不跳过。

## 执行命令

```
upload_file(
  name: "[与本地文件同名].html",
  content: [HTML 文件的完整内容],
  mime_type: "text/html",
  folder_id: "1QQHE-D8ICnp10uNZr8czDuiaVxjvCqkR"
)
```

## 输出要求

上传成功后，必须在回复中包含：
```
📁 Google Drive：https://drive.google.com/file/d/[返回的file_id]/view?usp=drivesdk
```

## 自检

在输出自检阶段，必须确认：
- [ ] upload_file 已调用
- [ ] 返回了 file_id
- [ ] 📁 Google Drive 链接已输出

如果以上任一项未完成，**停止输出，先完成上传**。
