# Phase pm

结构化分析需求，产出 PRD/UIH，判定后续阶段路由。

## 产出契约

`outputs/phase-pm.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `task_type` | string | `feature` / `bug` / `config` / `data` |
| `need_design` | string | `yes` / `no` ← **控制 design 阶段是否跳过** |
| `need_code` | string | `yes` / `no` ← **控制 api/arch/code/ut/review/qa 是否跳过** |
| `summary` | string | 一句话说清做什么，下游所有阶段都会读 |
| `prd_path` | string | 相对 instance-dir 的路径，如 `outputs/prd.md` |

选填但建议：`uih_path`、`srd_path`、`op_number`、`services`(array)、`acceptance`(array)、`prd_doc_url`。

`outputs/phase-pm.md`：PRD 正文。

## 两个开关的取值规则

- `params.need_design` 是 `yes`/`no` 时直接沿用；是 `auto` 时自行判定（有视觉变更填 `yes`）
- 判 `need_code: no` 前必须实地查过代码或表结构，不能凭需求描述推断

## 信息不足时

不要脑补，暂停等需求方回复（回复会注入下轮 prompt 的 § 0）：

```bash
python3 <complete-phase.py> "<instance-dir>" pause "需确认：1) xxx 2) xxx"
```

## 路由

产出合法后完成本阶段 → `pm_review`。
