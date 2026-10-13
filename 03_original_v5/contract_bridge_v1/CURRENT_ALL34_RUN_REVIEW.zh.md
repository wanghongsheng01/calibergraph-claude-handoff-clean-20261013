# 当前全 34 项回执审计

34/34 项均有回执，且锁定 manifest `32ee11faea4fee939964cd4ae03a9435d2ebe35877cecd221d7e65b2da30f3dd`；32 项追加队列已 ALL_SELECTED_DIAGNOSTICS_RETURNED。此处只读 JSON/哈希，并用独立短算术从记录 AST/固定数据库核对真值，没有导入目标/参考模块、没有重跑 native、solver 或 SQLite。审计者是实现代理，不能冒称独立执行者或真人审稿。

严格结果分为 **28 项正常完成、2 项监测异常、4 项预期整合同拒绝**。不存在“34 项全通过”的结论。`and_N1` 和 `lte_column_left_N2` 的 worker 均 COMPLETE、exit 0，但 supervisor 记录 RSS_OBSERVATION_UNAVAILABLE；两项保留为非正常完整。此记录不能单凭当前数据认定为某一种 race 根因，也不能删除 stop_reason。

30 个支持 case 的 normalized/reference XOR 回执均 UNSAT，其中严格正常 28，监测异常 2。original/reference XOR 为 8 SAT、22 UNSAT，均与注册方向控制吻合。支持病例的 150 个固定数据库真值均与独立读取 AST 后计算的原/参考语义一致，**未发现非预期真值分歧**；其中 140 格来自严格正常项、10 格来自异常项。另 4 拒绝 case 的 20 固定格仍 NOT_RUN，完整固定格注册分母为 170。四拒绝均发生在 native/solver 前。

两项实际 SQL pair 仍为 N1: NULL/6，N2: NULL/12；没有扩写成其他 pair 全部执行。3 种 admission 控制在 34 个入口重复，不算 102 种新语义测试。独立外部旧版本的 240 格不与本轮合并。

逐 case 的输入回执 SHA、exit、stop_reason、XOR、固定格和资源记录都保存在同名 JSON。资源观测保留原始值；没有补造硬 RSS 保证或原生始终单线程声明。旧 N1/N2 审计文件保留其早先 2/34 时间截面，不覆盖。本汇总不认证 v5 六臂接线或一般合同正确性。
