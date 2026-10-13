最终静审结论：当前审阅范围没有未关闭的 P0/P1/P2。先前三项 P2 已由稿件作者修改，我已完整重读更新后的 main.tex，未改论文或代码。

审阅快照：main.tex SHA d3581eca84bb69ada554db367c51265d5f0263286cf546dc7caef4ca2fb81b8c；contract_bridge_v5.tex SHA 4bcdbc6117f7fa768e298282e2a961dc66487f6d69569cd51d6d2216a1c3f7e5。冻结 v5 实际加载 runtime_v4/aggregate_kernel.py，SHA 17f652323839f0395e3224e5d82f646c143f34ff8245fb4d798724d3d7b9fa78；五个运行入口程序均与最终锁一致。全部实际查看文件及读取范围、SHA 见 JSON。

角色披露：我是未参与该稿撰写的 AI 内部复核者；此前参与支持包、公共扫描器及隔离诊断准备，并审阅过 v5 运行入口、合同桥和固定数据库 oracle。此次不是首次不知情的代码盲审，也不是真人同行评审。另一 AI 仅窄审初版贡献与基线措辞；最终稿由我重读。没有导入或执行 target/native/solver。

逐项对应结果：

- NULL / COUNT(expr)：严格传播表达式 NULL；贡献条件包含根存活、根谓词 TRUE 和参数非 NULL。非 NULL 零仍计 COUNT；COUNT 永不 NULL，SUM 在无非 NULL 贡献时为 NULL。标量差异忽略 NULL 的数值载荷。
- 根算术与三种编码：根列/整数及正负号、加减乘的语言一致；展平的 n-ary 加乘对应数学二元表达式。精确叶匹配和进入乘积或选择器，无叶空积为一。选择器只替换重数乘积，根表达式/合同仍可非线性。抽象恒等式和差分新变量无环检查不被扩大成完整实现定理。
- exact rows 与完整 C：全部物理表保留；正行数、INT32 与存活事实来自基础编码。原 AST、规范化副本和每叶映射保留，不支持项使整 C 拒绝。BASE 在 C 之前捕获，XOR 前提不含待测 C；随后完整 C 的 SAT/无删除门独立执行，矛盾合同不算查询等价。
- 所有路径与 oracle：六臂、fallback、差分共用已审 Environment。SAT 完整数据库先核原 C，再做整数域检查和原 SQL 回放。共享 plan 不冒充独立真值；源 AST 桥不认证文本 parser，差分仍相对官方编码。
- 贡献与基线：因子化、count product 与有限域分支明示已有；flat 仅为诊断。Polygon 正向有界和 IC 路径得到承认。历史 SpotIt direct-engine auto/set 不冒充完整 SpotIt+ 或 general bag baseline。没有发现把修复或桥包装为论文级首次的措辞。

已关闭的三项 P2：

1. main:72、149 具体给出 alias 唯一、禁止重复物理表、qualified/unqualified 联合唯一匹配、whole-SQL 引号/美元拒绝，以及物理 schema 的 uppercase/双下划线/first-separator 往返限制。
2. main:151 明确成本/差分入口的 MYSQL 与公共 cached AST 的 ALL 是不同配置，不推出跨方言保证。
3. main:54 将模糊的 “executed tool” 限定为历史 direct-engine adapter 的自动路径。

本次不认证 pending 数值表、campaign 92082 或任何新实验成功；未重新检索全部文献，也未做重叠与作者资格的完整鉴定。静态一致并不建立可发表新贡献、自然 join 适用性或 selector 特有收益；这些仍为真实科学开放项。最终数值必须保留失败与 NOT_RUN 分母并区分 v4/v5。

未上传或推送：BACKUP_BLOCKED_BY_USER_NO_UPLOAD_NO_PUSH。
