# 第五轮独立审核

结论：支持本轮限定的理论与公开元数据裁决。无未解决 P0/P1；一项 P2 是审核覆盖限制。本轮保留新方法假说为 0 合理，不意味着终止 CaliberGraph 的其他理论研究。

【证据·独立手推】S0 的合法 lift 构造成立，并不需要无环性。三个微例均算术一致。树形 B→A←C 中，两份合法实例拥有相同 payload 重数、逐 FK 流及各边单独的父度数多重集，连接 COUNT 仍可为 4 和 0。因此被否定的是查询保真，不能说合法重构不存在。

【证据·一手核查】独立读取了 [Atserias–Kolaitis 原文](https://arxiv.org/pdf/2012.12126) 的 Lemma 2、Theorem 2、Theorem 6 和关键构造。确切范围及页码记录在 `PRIMARY_ANCHOR_CHECK.json`；没有把其完整 bag 边际假设替换为普通 FK 边流。

【判断】作者把简单分配、共享父行耦合、完整边际先例与压缩边界分开，未把修补已有错误基线包装成新机制。hypothesis=null 有根据。

【证据·公开元数据补查】独立辅助审核重取 [官网](https://www.cse.iitb.ac.in/infolab/XData/XData.html)、[项目元数据](https://gitlab.com/api/v4/projects/xdata%2Fxdatapublic?license=true)和 [release 端点](https://gitlab.com/api/v4/projects/xdata%2Fxdatapublic/releases?per_page=100)，确认公开仓库指向、license 字段为 null、release 数组为空。这些都不证明系统不可用或任何地方不存在许可／发布物。正式 artifact pin、匹配许可和编码接口仍为 unknown。

【审核限制】没有独立重取作者报告的所有原始 HTTP 字节、git refs、CLI 输出，也没有逐篇复核其余全部引用。未独立确认的内容继续按作者报告对待。canonical root 的不同记录已有来源范围说明，本次未读取任务外 AGENTS 文件。

这是独立文档与理论审核，非实验复跑；未运行 SQL、parser、solver、Java 或实验，未读新 benchmark、DDL、test、reserve 或结果内容，未修改作者文件。完整逐项裁决、允许／禁止主张及剩余门禁见 `review_result.json`。输入与输出的精确绑定见 `REVIEW_MANIFEST.json`。
