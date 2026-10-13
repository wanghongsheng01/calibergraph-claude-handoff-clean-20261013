# 来源恢复与静态提取

作者文件映射至既有私有仓库 `wanghongsheng01/calibergraph-method-research-20261011` 的 `coverage_boundary_20261012_09/`。只备份作者报告、来源/哈希、规则、去留清单、标准库抽取代码、独立审核和本说明；不备份 `sources_local/` 内第三方SQL/DDL/原记录。

干净机器克隆私有仓库并核对本包MANIFEST。还原固定ParSEval commit `88cfe245bcf249a5b0df561a6b09c116ff2a2896` 的 `scripts/disprove_bird.py`、`data/sqlite/dev.json`、`dail.txt`、`schema.json`。相对工作区原路径为 `calibergraph_parseval_admission_20261011_03/sources_local/parseval_official/`。校验 SOURCE_CHECKS.json 中文件SHA-256，不能使用当前main替代。

按 `distinct_evidence_20261012_03/RECOVERY.zh.md` 恢复官方run `37547685455` 的artifact `11452059162`（ZIP SHA-256 `dc967b50b776d01faf4177f406fb25618218ed0d36bd893ef64797008010c5cf`）。提取其中 `disprove-bird.jsonl`，把JSONL与原schema放到 `calibergraph_distinct_evidence_20261012_03/sources_local/`；应与 SELECTION_PROTOCOL.json 的两个输入哈希一致。原artifact有到期时间，不能承诺长期可取回；历史原证据 BACKUP_BLOCKED 未因此解除。

仅在一个新的恢复目录布局下运行本包 `extract_static.py`：它只读JSON/文本，不导入SQL/科学包，不执行SQL、生成器或求解器。它按冻结规则重建10例本地原文并写出作者选择清单；`sources_local` 已存在时主动失败，避免覆盖。结果应与已归档 CANDIDATES、SELECTION_INVENTORY、EXTRACTION_RECEIPT 核对，不能以恢复为理由重选或开展实验。CASE_INDEX中的绝对链接对应本机原路径，换机器需使用CANDIDATES的相对路径定位。

Polygon固定源码 `5e18237394d025dbb805cf833b4f54c321470774` 和XData固定证据按 SOURCE_BOUNDARIES及前包来源恢复，核对哈希。XData核心实现仍未核实，恢复作者摘要不等于恢复/验证核心代码。

本包下一pilot是提案，不是可执行实现或本轮授权。原1172唯一运行标记不能删除/重置。新运行前需要满足报告明确的完整C、语义、进程树资源和独立复核条件。既有 DATAHUB_REGISTRATION_BLOCKED（缺公开研究源模块，当前范围不改外部canonical registry）继续保留。
