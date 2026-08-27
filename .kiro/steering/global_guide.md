---
inclusion: always
---
# 我是谁
1. 我是`主人`，我的角色是开发者

# 全局规则
1. 必须全程使用中文进行表述和回复，确保信息传递的准确性和一致性。
2. 生成Github提交信息，使用中文生成。
3. 在执行系统命令行操作时，根据当前操作系统选择终端：Windows 使用 PowerShell，macOS/Linux 使用 bash
4. 如果要获取当前时间，请一定使用shell脚本获取当前时间
5. 数据库时间字段设计请使用时间戳，单位秒
6. 快速了解项目的方式：阅读每个文件夹下，或者每个git项目下的README.md文件
7. 如果当前是git项目每个小任务结束，创建一个git commit提交
8. 所有生成的临时文件，都放在当前工作区根目录的docs目录下

# Code Review 规则
1. 涉及数据库字段的代码，写代码前和 code review 时必须执行 `SHOW FULL COLUMNS FROM <table>` 查看字段类型和备注，逐个比对：
   - Entity 字段类型是否与 DB 类型匹配（int/bigint/varchar/tinyint）
   - 代码中的枚举值/映射 key 是否与 DB 实际存储值一致
   - 不能仅凭需求文档假设字段值，必须以 DB schema 为准
2. Code review 时必须检查 MyBatis XML resultMap 是否覆盖了 Entity 中所有被代码使用的字段

# Subagent 调度规则

**禁止使用 `use_subagent` 工具。** 该工具不可用。

当需要调度其他 agent 执行子任务时，**必须使用 `run-agent` skill**（通过 `execute_bash` 调用脚本）：

```bash
# 同步（等待结果）
python3 /home/e2e/workspace/purchase/bin/run-agent.py --agent <agent-name> --query "任务描述"

# 异步（立即返回 task_id）
TASK_ID=$(python3 /home/e2e/workspace/purchase/bin/run-agent.py --async --agent <agent-name> --query "任务描述")
python3 /home/e2e/workspace/purchase/bin/run-agent.py wait $TASK_ID
```

详细用法参考 `run-agent` skill 文档。
