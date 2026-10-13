# 外部合同检查的版本身份核验

只读核验时间：2026-10-11T04:05:50.120190+00:00。未执行目标、native、SQLite 或 solver，未改冻结文件。

外部目录为 `/Users/loctek/Documents/Codex/2026-10-10/task-3/calibergraph_audit_20261011/contract_patch_review_01`。主报告 `CONTRACT_PATCH_REVIEW.zh.md`，运行回执 `INDEPENDENT_ORACLE_ATTEMPT_01.json`（SHA `57c9c584dfa86f26e8b20f61316c4b045aa06af72a931f3f7e39955d8ca71528`）；原始冻结清单 SHA `2b184507d3cf935e0e28664df91b5b0c51478d7ae5aa6df9a6c5ec227b5b9b9d`。29 个冻结文件逐个读取哈希，29 匹配、0 漂移。

外部实际测试本桥的早期开发截面：reference SHA `e57496ec0b1d1198370c0d96cb8891fad31a34ebfed4dd162c9738920cb9bdd1`。当前 reference 为 `781ce147e8bf9f8f8323621b745b30920df4da57e68f0c0daeab70387e990e7c`，不是同一版本。外部自写脚本 `independent_contract_oracle.py` SHA `8edbca437e45e4815470befdcd5cd3640497d2796536cfc456e1151baea74c0e`，没有运行本桥的 `run_diagnostic.py`。它使用的 runtime_v3 lock SHA `505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7` 也不同于当前入口使用的 v4 lock。

外部回执记录 240/240 固定格修正后一致，旧编码 24 格不一致，24/24 symbolic XOR UNSAT，20 parser 检查和 2 实际官方 pair 检查。规范化合同下得到 A=6，原文 SQL 输出 NULL / 6。这些证据属于该旧截面；不能直接认证当前 runner、后加标识符门或六臂集成。`UPSTREAM_DRIFT.json` 与 `.patch`（patch SHA `d2473616edcc1139105186648f0168cd95631799baeea0b8572dc1ef0306a495`）明确记录了差异。

目标回执为 `PASS_LIMITED_PATCH_ORACLE`；外层 `/usr/bin/time -l` 因 `sysctl kern.clockrate` 被拒返回 **exit 1**。不能把它混称目标数值失败，也不能称整个 shell 命令 exit 0。目标记录 CPU 1.903335 s、内部墙钟 2.010126125 s、峰值 RSS 117145600 B；完整外层资源测量有缺口。

当前 N1/N2 的新运行证据另见 `CURRENT_N1_N2_RUN_REVIEW.json`。此身份核验不增加实验分母，不构成通用合同证书或论文创新证明。
