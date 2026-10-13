# 第15阶段沿用第06轮语义控制

本阶段未增加方法、fixed-witness comparator或计时基线。原4来源SQL/schema/full operational C与两个INT回放profile不变，因此完整沿用 [第06轮控制原字节](ANALYTIC_CONTROLS.round06_verbatim.zh.md)；副本中“第六轮/12单元/本轮实际读取”只指其历史来源，不是第15阶段新增读取或执行声称。

第15阶段计划分母是24槽：rep1按来源6/9/14/3、bound2/3/4；rep2按来源3/14/9/6、bound4/3/2。每槽一次Environment。CASE默认NULL、内连接换序、LEFT/RIGHT保留侧反转、行相等与IFNULL/COALESCE恒等式仍是两个INT来源的强语义解释；没有给这些静态规则虚构0秒费用。

DATE/ROUND/除法、decimal/VARCHAR与比较编码提前退出的边界原样保留。UNKNOWN、异常、零query-check、C sanity不区分、资源失败、NOT_RUN均留在24槽分母。整个计划仍为已暴露开发诊断，business C真实/完备性UNKNOWN，不是独立最终测试或新机制证据。
