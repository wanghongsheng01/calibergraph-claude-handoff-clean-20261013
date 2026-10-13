# 运行前判读计划

本轮唯一问题：同四个已暴露来源、原SQL/schema/full operational C、exact-live每表N=2/3/4时，两次预定冷进程重复是否都出现低界返回而较高界UNKNOWN，成本发生在哪一段？不声明新方法、自然业务缺陷、最终test或速度优势。

24槽全列，预定两个重复逐一对齐；旧第06轮12槽单独并列，不合并为独立样本。每个来源保留N2/N3/N4的两遍C状态、query状态/UNKNOWN原因、前端/编码异常、query-check到达证据、原SQL重放范围及成本。资源中断、未启动、invalid receipt留在分母；null/censored不替换为0。

仅当同一来源两遍都出现低界query UNSAT/返回且较高界query UNKNOWN，并且UNKNOWN原因为相同预算原因，称“在此预算下重复的工具成本现象”。一次出现、原因不一致、C非SAT、阶段未到或缺收据均不足。跨exact-N不是嵌套域，不能推等价/非等价的单调性；即使达到此判据，也不晋升新科学机制。

phase CPU按是否实际进入记录；导入/准入、parse/analyze、scope/compare encode、C check/query check、模型导出/合法性/原SQL replay和cleanup分别列示。嵌套阶段不双加，整体wait4/SELF+CHILDREN及外层time记录启动退出成本；观测费用、prep10、tail预留单列，实测与预留不混称。未知/失败槽不会从总成本或分母中删除，不取重复中的最快值或只对成功者报总体均值。

所有C-model sanity必须标为非query-SAT反例；query-SAT若有，只有导出数据库、独立完整C检查及原SQL精确重放都通过才计有效区分见证。DATE/ROUND等未准入profile不能冒称SQLite一致语义。

强解析对照沿用原CASE默认NULL、内连接交换、外连接左右互换、IFNULL/COALESCE等成熟恒等式。没有实现或计时这些baseline，不声称本工具优于它们或SQLSolver/Polygon。重复瓶颈只允许提出下一步受控诊断；不存在残余机制证据时维持NONE/NO_GO。

任一科学supervisor启动即消耗唯一batch；resource/monitor/integrity/CPU门停止后，不回到等待、不补齐24、不换源、不扩大预算、不重试。运行完成与否均交独立结果审核。第15轮24未启动和第13轮98未知分母保持原状。
