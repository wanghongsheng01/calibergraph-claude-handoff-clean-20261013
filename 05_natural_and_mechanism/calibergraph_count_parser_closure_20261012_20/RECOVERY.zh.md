# 本地恢复入口

先读 RESULT.zh.md、FINAL_FACTS.json 与 review_local/FINAL_REVIEW.zh.md。最终修复为 patched_p3/polygon/，三个实际修改文件：sql_parser.py、visitors/expression_encoder.py、visitors/group_expression_encoder.py；COUNT_P3.patch 是相对13包冻结运行基线的差异。不要应用到旧冻结包。

001/002失败、原parser_test.py及PARSER_RESULTS.json必须保留。003是新parser_test_v2.py及独立verify_results_v2.py的最终运行。控制器run_budget.py有STARTED排他标记及累计60秒账本，不删除marker重跑；本轮已结束。任何新范围验证另建目录/计划，显式区分开发回归与最终测试。

复原依赖继续使用13包既有固定Python依赖与原来源；运行解释器为 /opt/homebrew/bin/python3.12。只复制源码/依赖不代表已验证部署，原始mo_imports会启动后台监控，而本轮测试使用共同同步监控适配维持一线程。报告已限定具体赋值算子验证与完整求解流水线的区别。

PRESERVATION.json如实记录早期一个未执行辅助文件的准备期变更；003冻结541项全匹配。DELIVERY_MANIFEST.json为交付后完整性清单，不是运行前freeze。

禁止push，未commit，不运行备份钩子，不绕过既有批准流程。本包目前仅本地保存。
