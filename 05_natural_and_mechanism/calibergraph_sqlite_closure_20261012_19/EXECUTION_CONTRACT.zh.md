# 执行合同

仅回放18包已列8个候选：1073日期前缀/nullable PK；45 TEXT、大整数、1/3分组、0/0 bag；1526 N1原差异与两交易/三月份控制。使用09固定原SQL/DDL/C，全部表列原样保留，SQLite内存库，PRAGMA foreign_keys=ON、threads=0，完整插入、提交、foreign_key_check、integrity_check及NN/唯一性核对。保存实际存储值与原输出，失败保留，不将预期当结果。

另对原Polygon固定ExpressionEncoder的COUNT(*)做最小合成AST边界测试：bound0/1/2、全部删除掩码、无FILTER/真/假/NULL，独立SQLite count对照。原分支缺陷确认后才在新包生成单行补丁，将append移出if并构造Int指示。补丁仅内存编译测试，不写旧源，不调用Environment.check、FormulaManager.search或任何Z3。记录实际parser到普通COUNT(*) AST路径，但不声称完整自然查询流水线已验证或补丁已并入基线。

作者回放、作者边界测试、独立验证脚本在同一进程同一连续60秒墙钟内顺序执行；无并行worker，无辅助SQLite线程，禁止Thread.start、subprocess、fork和网络。共同owned.lock排他，运行前记录负载，不查询unrelated_project或外部进程。一次标记防重入，预算耗尽后剩余项明确未完成。独立审阅者只编写自己的验证代码，统一由此批执行，再由其审查回执。

不修改原输入、旧冻结、原稿，不获取新来源，不生成新公共案例，不commit/push。候选是合成数据库而非真实业务记录，1526原question/evidence日期冲突仅为数据质量事实，不能推断业务真值。修COUNT(*)是工程纠错，不是方法创新。已有4/8 bounded baseline运行覆盖不因SQLite回放而增加。
