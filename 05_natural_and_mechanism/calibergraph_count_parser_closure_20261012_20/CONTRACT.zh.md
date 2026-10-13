# 20 轮执行口径

用户授权工程闭环：真实 parser 入口、COUNT(*) 编码、SQLite 参考、空库/NULL/重复/分组边界；不把工程修复当创新。原基线及历史包不改，禁止 push，本轮不 commit。

三版本：original 是13包冻结运行基线（不是无适配的全新官方安装）；P1 是19包 COUNT(*) 一语句补丁；P2 另修 GroupExpressionEncoder 的 COUNT(*) FILTER 忽略。其余 grouped aggregate FILTER 不在修复承诺内。

测试分母预先固定：28项旧矩阵从真实 SQLParser.parse/parse_query进入ExpressionEncoder；14项经真实FProject，分组时再经真实FGroupBy，检查具体赋值下全部生成约束并与SQLite原SQL bag对比。空库用至少1个全部deleted槽表示，额外28矩阵包含物理bound0表达式；不声称完整Environment.check/QueryEncoder/SMT求解或一般正确性证明。未调用求解器，不使用一个可选自然对的求解额度。

依赖mo_imports监控线程替换为同步测试watchdog，仅start/join为空操作；真实expect/export/import保持执行，导入完成必须无未解析export。两修复版和原版共用此适配。parser源码不改，不把它称无适配部署验证。

累计目标运行预算60秒，一线程。公共锁、机器load门、进程RSS256MiB停止、禁止子进程/网络/真实Thread.start。每次执行先冻结，STARTED排他创建，失败保留。如果测试自身需修正，用新文件和新freeze消耗剩余累计预算，不覆盖旧结果。没有要求强行通过；每个未通过边界归档。

写作与独审分离，历史影响由独立审查核对SQL、实际SMT及旧回放。原版与P1/P2输出分别保存；本轮耗时只作资源成本，不作官方性能结果。
