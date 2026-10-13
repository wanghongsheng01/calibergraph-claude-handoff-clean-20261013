# 静态分析恢复说明

作者成果归档至既有私有仓库 `wanghongsheng01/calibergraph-method-research-20261011` 的 `masking_prior_analysis_20261012_08/`。父提交为 `bef42b3e17bdc7b5f9148f1edde6c9de892a7a40`，其中 `sampled_diagnostic_20261012_07/` 包含原运行、保存候选与此前独立复算；`mechanism_synthesis_20261012_02/` 包含此前先例证据。新分析不覆盖或替换这些文件。

恢复时在有该私有仓库权限的干净机器克隆并定位本包，先用 MANIFEST.json 对包内文件计算 SHA-256。再沿 EVIDENCE.json 的父包路径、哈希核对原运行及审核证据。原工作区前缀 `calibergraph_` 与备份子目录映射由各包 RECOVERY 说明给出；EVIDENCE 中绝对根依赖可用该映射解析。

第三方 SQL/DDL、完整源码、论文和依赖不重新分发。本包仅保存来源网址、固定 commit、局部源码 SHA-256 和作者分析。需要恢复源码时使用固定 commit 的官方来源，校验 EVIDENCE.json 中 SHA-256；核心 XData Java 尚未核实，不能把恢复链接当作恢复成功证据。

本包没有可运行的研究实现。不要执行旧 supervisor、删除旧唯一尝试标记、重跑旧基线或将预案当作科学运行授权。静态恢复和文件哈希检查不能提升任何实验结论。独立审核文件只代表其中明列的审核范围。

历史第三方 raw/native 永久恢复 BACKUP_BLOCKED、公共研究源 DATAHUB_REGISTRATION_BLOCKED 继续保留。当前作者包私有备份验证是另一项状态，只有远端 HEAD 与本地一致且仓库为 private 才能报告该作者包备份成功。
