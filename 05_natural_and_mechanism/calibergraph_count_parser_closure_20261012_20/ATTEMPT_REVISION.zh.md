# 20 轮执行修订（不覆盖旧记录）

001 用了 shell 默认 Python 3.9，原源码类型注解要求较新版本，导入失败，尚未执行测试。002 显式使用现有 Python 3.12：28矩阵原版12通过/4值错/12类型错误，P1/P2各28通过。14算子链保存所有结果，但测试解释器错误地把Implies.premise/conclusion读作a/b，部分测试未完成；另真实parser把FILTER (WHERE x)解析为Literal('x')，缺失的Env.string_hash让此路径报错。

003使用新parser_test_v2.py，旧脚本及PARSER_RESULTS.json不改。测试解释器修正Implies字段，测试Env复用冻结Environment.string_hash的行为，使原parser的错误结果可被观察，不伪装成正确列值。测试数据/SQL和28+14分母不改。

新P3是独立复制P2，仅增加真实SQLParser三处聚合FILTER入口的裸str→Attribute转换；带引号字面量仍由原字典literal分支解析。四版本分别记录original/P1/P2/P3，不把parser修复混入P2或历史baseline。P3仅承诺本轮整数列/NULL/常量FILTER测试的COUNT(*)闭环，不宣称所有SQLite字符串数值转换或其他聚合FILTER均正确。

每段目标运行均扣同一累计60秒预算。001/002合计0.4445960418871939秒，零solver。RSS采用50ms虚拟CPU定时采样超过256MiB停止，不是OS硬内存限制。P3及v2脚本重新冻结再运行。
