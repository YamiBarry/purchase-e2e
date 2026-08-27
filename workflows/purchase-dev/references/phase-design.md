# Phase design

按 PRD + UIH 产出 HTML 静态设计稿并上传 Google Drive。

本阶段在 `phase-pm.json` 的 `need_design == "no"` 时自动跳过。

## 产出契约

`outputs/phase-design.json` 必填字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `html_paths` | array | HTML 文件路径列表，放在 `outputs/design/` 下 |
| `drive_url` | string | **真实可访问的 Google Drive 链接**，不允许填占位值 |
| `summary` | string | 产出了什么 |

选填：`components_reused`(array)、`components_new`(array，非空时需说明理由)、`responsive`(string)。

`outputs/phase-design.md`：设计说明（设计意图、与 PRD 的对应关系）。

## 上传失败时

Drive 上传是硬要求，失败不要填假链接，转人工：

```bash
python3 <complete-phase.py> "<instance-dir>" block "Google Drive 上传失败：<错误>。需确认凭证对目标文件夹的写权限"
```

## 路由

产出合法后完成本阶段 → `design_review`。
