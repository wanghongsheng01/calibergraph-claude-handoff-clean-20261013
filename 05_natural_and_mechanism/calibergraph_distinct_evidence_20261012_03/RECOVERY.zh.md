# 取证包恢复

本地 `calibergraph_distinct_evidence_20261012_03` 映射到既有私有仓库 `distinct_evidence_20261012_03`。私有备份仅包含作者结论、来源/哈希、静态证明和未执行的诊断建议；`sources_local/` 的第三方 SQL、DDL、JSONL、ZIP 和日志摘录全部排除。`MANIFEST.json` 校验作者文件；`EVIDENCE.json.local_sources` 校验本地原始证据，二者不能混用。

恢复原始证据：通过官方 GitHub connector 读取固定 commit 的 `data/sqlite/schema.json`（Git blob `92a9750d0dab4c2e89a4f2cab81ee5f292063e75`）；取得 run `37547685455` 的 artifact `11452059162` 并校验 ZIP SHA-256。只读 ZIP 中 `disprove-bird.jsonl`，按 dbid=`thrombosis_prediction`、index=`1172` 唯一选中第 1173 行，原样保存 gold/predicted；按同版本 `scripts/disprove_bird.py` 用 `;\n` 拼接该数据库键的全部三表 DDL。校验 EVIDENCE 中 SHA-256。禁止以未来 main、删列/删表模式、手写替代 SQL 或重新运行实验替代原始材料。

Actions artifact 目前未过期；API 显示 2027-01-04 到期，此后可能不可恢复。本次本地 ZIP 已验证，第三方原始内容不再分发到私有 Git；不声称永久历史原证据恢复已解决。旧 raw/native 恢复 `BACKUP_BLOCKED` 与 DataHub 固定公开研究源模块 `DATAHUB_REGISTRATION_BLOCKED` 仍保留。未改 canonical registry 或其他项目。

克隆此包不会执行任何 SQL/求解器，不授权启动 FINDING 中的未来诊断。仅建议一次，仍需父任务下一轮决定；科学方向不变。原稿、旧冻结结果、unrelated_project 均不在本轮修改范围。
