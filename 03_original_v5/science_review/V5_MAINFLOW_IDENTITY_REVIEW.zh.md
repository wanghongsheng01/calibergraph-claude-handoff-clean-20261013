# v5 共用合同入口与来源锁补充静审

时间：2026-10-11T04:13:31.325663+00:00。本审只读代码、AST、JSON、SHA 与文件清单，不执行目标/native/solver/SQLite。审阅对象由 runtime_guard 实现，support_closure 另做主静审；本代理曾实现 earlier bridge，故不冒充对其自身参考算法的全新独立认证。

当前五源码哈希与两个锁内 runtime_programs/files 一致。VeriEQL 锁 853 文件、SpotIt 锁 861 文件全部实际哈希匹配；各源/绑定/support/dependency 根目录的实际文件清单与锁一致、未见符号链接或额外文件。两锁当前均 **PENDING_INDEPENDENT_STATIC_REVIEW**，不可直接运行；转 READY 后锁哈希必须另记，不能沿用本文 pending 哈希。

主流程静态上未发现绕过：六臂与 query differential 都在派发前经过空 Environment → 完整 exact-N schema → source AST 整体准入 → base-only SAT → 规范化副本实际编译 → base-only XOR UNSAT → 完整合同 SAT/不可删除基行门。canonical 快捷 UNSAT 也在共同门后；official/generic/fallback 使用同一个已绑定环境及完整事实哈希。unsupported、桥不一致、unknown、矛盾合同均保留并禁止回退到旧 IC。SAT 回放先独立核原 AST 具体真值，再过整数域/原 SQL 门。

发现并关闭一处 P1：初版 supervisor 可在 stop_reason 存在时仍把 exit 0 + worker COMPLETE 计作有效完成；新源在第 151 行增加无 stop_reason 条件。已静态核修复，尚未运行 v5 资源异常注入，不把此静态闭合称作新运行通过。晚到的 ContractStop 也保留已经发生的 query ledger，而不是写成从未运行。

来源边界：当前 v5 reference SHA `fdcee3a919930013945c571e64b7d4b478186c93ceee4546ff520879e99680e0` 在本桥 `781ce147…` 之上增加 BETWEEN；此前外部 `e57496ec…` 的 240 格、当前 bridge 34 项均不是这个新文件的直接执行覆盖。BETWEEN 只接单列整数上下界，NULL 不成立，倒置区间保留为矛盾；静态表达式一致，实际入口测试待 root 执行。原 22 个 case 字典完全保留，另有 6 个已暴露构造控制，共 28；不是自然样本增益。

本静审没有新增执行阻断；真正未闭合的是最终 READY 身份回执与 v5 实际主路径证据。规范化适配器须明确标注，不能将新六臂称作原封不动的上游 IC 行为，也不能把 source AST 局部审计升级为任意原始合同文本无丢失性、论文创新或投稿放行。
