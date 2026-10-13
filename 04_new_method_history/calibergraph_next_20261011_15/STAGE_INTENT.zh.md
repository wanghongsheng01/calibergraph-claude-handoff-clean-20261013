# 第15阶段意图：公开开发SQL的bound增长诊断

2026-10-11。用户要求持续研究，同时纠正此前多轮人工理论例缺少自然适用性的路线。本阶段首先比较一手文献与既有实际query结果；当前没有候选新方法，不写原稿、不投稿。

唯一拟研究问题H15：在原SQL、schema、完整operational C、exact-N活行语义和所有资源预算不变时，原第06轮四个固定来源的2行快判是否可在较高bound重复失效；可用证据将成本定位于冷启动/解析编码/查询SMT哪一段？这只是工具开发诊断。source提供C，不代表C的业务真实性或完备性已验证；21对全暴露开发，不是新test。

第06轮已实际有2/4/8结果，不得隐去：4来源×3bound的12槽中5查询UNSAT、4 UNKNOWN、3比较编码前退出；两INT来源2行UNSAT、4行timeout、8行OOM。已知基础恒等式能解释两INT pair，因此即使复现资源瓶颈，也不能把简单规范化或约束消元重新命名为科学贡献。

拟最小新登记保持全部四来源indices[6,9,14,3]，而非只挑旧慢例；N=(2,3,4)，两次固定冷进程重复，共24槽。第1遍原source序、每source 2/3/4；第2遍反source序、每source 4/3/2。旧12槽仍作为历史完整分母保存，不与新24槽拼成独立样本。所有拒绝、编码异常、UNKNOWN、资源截尾和未运行槽保留，不替换。

拟预算与第06轮保持一致：一个active worker，nice15；单worker硬CPU3秒、wall4秒、采样RSS256MiB；C检查100ms、查询检查700ms、Z3内存128MB；整批保守CPU60秒（含准备10秒与尾部0.2秒保守预留）。逐槽load≤4且free memory≥25%，资源/probe/integrity失败即截尾。只允许一次登记批次，不自动延时、增bound或重试。

原第13轮失败完全冻结，禁止改权限重跑该轮。本阶段如需要host执行，应使用工具支持的`require_escalated`受审路径，保留nice和全部限制，先做独立的无科学计算能力检查；不删保护、不改系统安全，不猜第06轮外层sandbox模式。自动审核若拒绝，停止该新执行并准确报告拒绝理由。能力检查及所有准备开销须进入本阶段账本。

尚未执行capability probe、SQL、solver或任何新科学程序；新source/protocol均应disabled/DRAFT。执行前必须先向用户报告一手差异、拟问题、允许范围，然后完成独立preexec审查和精确source/runtime/source-data冻结。

拟判读门（须进入最终协议）：每source同时列两遍状态，不取最快值；至少两遍同样出现低bound返回、高boundUNKNOWN才记“在该预算下重复的编码成本现象”。这不证明科学困难。比较编码未到达或异常缺阶段计时必须记null/unmeasured/censored，不能记0；嵌套时间不可双计。若现有强简单恒等式/成熟工具足以解释，机制晋升仍NULL。未形成可重复残余瓶颈前，不开新机制或更大队列。

历史私有备份精确repo为 https://github.com/wanghongsheng01/calibergraph-method-research-20261011 ，已核private且local/remote一致commit `fb64a9550b93957b5b06c28cef7f781b77522ecc`，涵盖截至14的新增作者与独审材料。该验收不涵盖尚未完成的第15阶段；历史raw evidence/native runtime clean restore仍BACKUP_BLOCKED，DataHub canonical注册仍BLOCKED。
