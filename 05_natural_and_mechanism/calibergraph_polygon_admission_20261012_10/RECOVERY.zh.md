# 准入停止包恢复

作者包备份至既有私有仓库 `wanghongsheng01/calibergraph-method-research-20261011` 的 `polygon_admission_20261012_10/`。不重新分发原SQL/DDL/第三方源码；`admission_local/` 中包含原模式属性的完整派生映射仅本地保存，Git保留标准库提取器、摘要和哈希。

克隆备份后核对MANIFEST，再按 `coverage_boundary_20261012_09/RECOVERY.zh.md` 恢复#750/#319的固定官方SQL/C。INPUT_FREEZE绑定原文件及旧1172唯一尝试标记。旧标记仅用于不可变性核对，不能因换机器缺少标记而启动旧实验。

只需重建静态约束清单时，在新的恢复布局中运行 `map_source_constraints.py`；它只读两份DDL文本、拒绝未识别语法、不导入SQL/科学包、不执行SQL或求解器。比较C_MAPPING_SUMMARY中的文件哈希与计数。已有admission_local目录时失败，不覆盖历史记录。

SOURCE_ANCHORS记录固定Polygon源码和旧保护器哈希，原来源与恢复办法沿用strong_baseline_prep、sampled_diagnostic包。当前26个Polygon快照文件（24个内容、2个元数据）不是完整运行环境；本包不声称完整环境已备份或已运行。

RESOURCE_PROBE是根任务对真实工具返回的结构化记录，不是独立系统鉴定或全进程列表；独审不再请求ps权限。本批BATCH_CLOSED是资源准入失败的结束记录，4个NOT_RUN槽不是可重试实验。恢复不授权启动、换例、扩展资源或安装。历史第三方raw/native BACKUP_BLOCKED、公共研究源DATAHUB_REGISTRATION_BLOCKED保持；本作者包备份状态另行验证。
