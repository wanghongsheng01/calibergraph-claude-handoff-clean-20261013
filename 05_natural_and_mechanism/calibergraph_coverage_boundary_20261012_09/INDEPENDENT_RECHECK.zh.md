# R1 限定复核

结论：**PASS_AFTER_REQUIRED_CORRECTION**。初审唯一阻断 R1 已修正；初审 `INDEPENDENT_REVIEW.zh.md/json` 的 MUST_FIX 原文保留。

本次仅核查原 dail 行与官方 `predicted.strip()` 输入的区分及相关哈希，没有新增审查事项、网络访问或实验。

- REPORT 明确说明官方 strip 步骤、#750 原行尾空格，以及包内 predicted 与官方实际输入/JSONL 一致。
- SOURCE_CHECKS 的10例均分列原行比较、官方 strip 后比较及两种SHA-256；逐例重算20个哈希和比较布尔值均相符。原行一致9例，只有 #750 为false；官方 strip 输入一致10例。#750 差异严格为末尾一个 ASCII 空格。
- AUTHOR_REVISIONS 的当前文件哈希正确；reviewed_initial 中 REPORT、SOURCE_CHECKS 与初审记录的原始哈希一致。其余初审已记录作者文件哈希未变，40个候选 SQL/DDL/记录文件哈希均保持不变。

这次通过只解除源字节保真表述的阻断。初审对静态证据、开发暴露、N=1 类型/full-C 准入及资源控制的限定保持有效；不构成运行准入、实验授权、完整 SQLite 等价或新机制结论。

新增科学执行 **0**；SQL/SMT/基线调用 **0**；新test **0**。仅写本限定复核的两份文件，未修改初审或作者材料，未备份。
