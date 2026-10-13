"""Read-only stdlib aggregation of existing runs; no target module is imported."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

TODAY = Path(__file__).resolve().parent.parent
OUT = TODAY / "experiments"
LEET = TODAY / "public_leetcode"
V4 = TODAY / "public_v4_cached/runs/run_001"
OLD_KERNEL = "defa1812ec36c91a23d428f8d71d2070f808eddeb5f473748d3e7ac09fdfe5f3"
NEW_KERNEL = "17f652323839f0395e3224e5d82f646c143f34ff8245fb4d798724d3d7b9fa78"
TERMINAL = {"ELIGIBLE", "INELIGIBLE", "FRONTEND_UNSUPPORTED", "PARSE_OR_AST_RECORD_ERROR", "RECOGNIZER_ERROR", "INPUT_ERROR"}
FILES, CHECKS = {}, []


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def objsha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sqlsha(sql):
    return hashlib.sha256(sql.encode()).hexdigest()


def register(path):
    FILES[str(path)] = {"sha256": sha(path), "bytes": path.stat().st_size}
    return FILES[str(path)]["sha256"]


def read(path):
    raw = path.read_bytes()
    FILES[str(path)] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return json.loads(raw)


def check(name, value):
    CHECKS.append({"check": name, "pass": bool(value)})


def problem(row):
    r, d = row["source_record"], row["dataset"]
    if d == "leetcode":
        return [d, "file", r.get("file")]
    if d == "literature":
        return [d, "name", r.get("name")]
    return [d, "benchmark_index", r.get("benchmark"), r.get("index")]


class Stats:
    def __init__(self):
        self.slots = 0
        self.pairs = 0
        self.status = Counter()
        self.reason = Counter()
        self.pair_status = Counter()
        self.leaves = Counter()
        self.sql = Counter()
        self.problems = Counter()
        self.ordered_pairs = Counter()
        self.full_cases = Counter()
        self.eligible_ids = []

    def add(self, row):
        self.pairs += 1
        self.problems[json.dumps(problem(row), ensure_ascii=False)] += 1
        self.ordered_pairs[objsha(row["source_record"]["pair"])] += 1
        self.full_cases[objsha(row["source_record"])] += 1
        known = [q.get("eligible") for q in row["queries"]]
        self.pair_status["both_eligible" if all(x is True for x in known) else "known_false" if False in known else "unknown"] += 1
        for q in row["queries"]:
            self.slots += 1
            self.status[q["status"]] += 1
            self.reason[q.get("reason")] += 1
            self.sql[sqlsha(q["original_sql"])] += 1
            if q.get("eligible") is True:
                leaf = len(q["plan"]["leaves"])
                self.leaves[leaf] += 1
                self.eligible_ids.append({"row_id": row["id"], "query_index": q["query_index"], "leaf_count": leaf,
                                          "raw_sql_sha256": sqlsha(q["original_sql"]), "source_problem_key": problem(row)})

    def result(self):
        return {"pair_denominator": self.pairs, "query_slot_denominator": self.slots,
                "query_status_counts": dict(self.status), "query_reason_counts": dict(self.reason),
                "pair_status_counts": dict(self.pair_status), "eligible_leaf_histogram": dict(self.leaves),
                "eligible_join_queries": sum(v for k, v in self.leaves.items() if k > 0),
                "eligible_ids": self.eligible_ids,
                "distinct": {"raw_sql": len(self.sql), "raw_sql_repeated_slot_excess": self.slots-len(self.sql),
                    "raw_sql_values_repeated": sum(v > 1 for v in self.sql.values()),
                    "source_problem_labels": len(self.problems), "source_problem_pair_repetition_excess": self.pairs-len(self.problems),
                    "source_problem_labels_with_multiple_pairs": sum(v > 1 for v in self.problems.values()),
                    "ordered_sql_pairs": len(self.ordered_pairs), "repeated_ordered_pair_excess": self.pairs-len(self.ordered_pairs),
                    "full_source_cases": len(self.full_cases)},
                "source_problem_pair_counts": dict(self.problems)}


def event_audit(path):
    digest = register(path)
    events = Counter()
    result_ids = []
    with path.open() as f:
        for line in f:
            e = json.loads(line)
            events[e["event"]] += 1
            if e["event"] == "QUERY_RESULT":
                result_ids.append((e["row_id"], e["result"]["query_index"]))
    check(str(path) + ":unique_result_slots", len(set(result_ids)) == len(result_ids))
    return {"path": str(path), "sha256": digest, "event_counts": dict(events), "unique_result_slots": len(set(result_ids))}


def main():
    json_out = OUT / "PUBLIC_APPLICABILITY_FINAL_CUT.json"
    md_out = OUT / "PUBLIC_APPLICABILITY_FINAL_CUT.zh.md"
    if json_out.exists() or md_out.exists():
        raise ValueError("final cut is new-only; preserve existing outputs")
    v3 = {name: Stats() for name in ("leetcode", "dev", "combined", "calcite", "literature")}
    by_slot, parse_errors, attempts, resumes = {}, [], [], []
    source_paths = {"calcite": TODAY/"sources/verieql_v1/benchmarks/calcite/calcite2.jsonlines",
                    "literature": TODAY/"sources/verieql_v1/benchmarks/literature/literature-rewrite.jsonlines",
                    "leetcode": LEET/"leetcode.jsonlines"}
    streams = {k: p.open("rb") for k, p in source_paths.items()}
    for p in source_paths.values():
        register(p)
    register(LEET / "GLOBAL_MANIFEST.json")
    register(TODAY / "runtime_v3/runtime_paths.json")
    register(TODAY / "runtime_v3/aggregate_kernel.py")
    register(TODAY / "runtime_v4/aggregate_kernel.py")
    selected_paths = [("dev", TODAY/"public_dev/runs/full_scan_v3_all_01/scan_report.json",
                       TODAY/"public_dev/runs/full_scan_v3_all_01_supervision.json")]
    selected_paths += [(i, LEET/f"runs/chunk_{i:03d}/attempt_{2 if i in (9,16) else 1:03d}/scan_report.json",
                        LEET/f"runs/chunk_{i:03d}/supervision_{2 if i in (9,16) else 1:03d}.json") for i in range(24)]
    for key, path, supervisor_path in selected_paths:
        report, supervisor = read(path), read(supervisor_path)
        event_path = path.parent / "query_events.jsonl"
        events = event_audit(event_path)
        check(str(path)+":kernel", report["kernel_sha256"] == OLD_KERNEL)
        check(str(path)+":ALL", report["dialect"] == "ALL")
        check(str(path)+":worker_exit_zero", supervisor.get("exit_code") == 0)
        check(str(path)+":complete_report", report["status"] in ("COMPLETE_CHUNK_SCAN", "COMPLETE_CHUNK_SCAN_WITH_ERRORS", "COMPLETE_FULL_DEV_SCAN", "COMPLETE_FULL_DEV_SCAN_WITH_ERRORS"))
        check(str(path)+":event_hash", report.get("query_events_sha256") == events["sha256"])
        check(str(path)+":input_identity_flags", all(report.get(k) is True for k in ("inputs_unchanged_after_scan", "kernel_unchanged_after_scan", "runtime_lock_unchanged_after_scan")))
        attempt = {"block": key, "selected": True, "report_path": str(path), "report_sha256": FILES[str(path)]["sha256"],
                   "report_status": report["status"], "report_stop_reason": report.get("stop_reason"),
                   "supervision_path": str(supervisor_path), "supervision": supervisor,
                   "summary": {k: v for k, v in report["summary"].items() if k != "query_reason_counts"},
                   "events": events, "resume": report.get("resume")}
        attempts.append(attempt)
        previous_hashes = {}
        if key in (9, 16):
            previous_path = path.parent.parent / "attempt_001/scan_report.json"
            previous = read(previous_path)
            previous_supervisor_path = path.parent.parent / "supervision_001.json"
            previous_supervisor = read(previous_supervisor_path)
            prior_events = event_audit(previous_path.parent/"query_events.jsonl")
            for row in previous["rows"]:
                for q in row["queries"]:
                    if q["status"] in TERMINAL:
                        previous_hashes[(row["id"], q["query_index"])] = objsha(q)
            resume = {"block": key, "first_report": str(previous_path), "first_report_sha256": FILES[str(previous_path)]["sha256"],
                      "first_status": previous["status"], "stop_reason": previous.get("stop_reason"),
                      "first_supervision": previous_supervisor,
                      "first_query_status_counts": previous["summary"]["query_status_counts"],
                      "first_completed_slots": previous["summary"]["completed_query_slots"],
                      "first_uncompleted_slots": previous["summary"]["uncompleted_query_slots"],
                      "first_events": prior_events, "second_events": events,
                      "second_resume_record": report["resume"], "second_worker_exit_code": supervisor["exit_code"],
                      "completed_results_unchanged": True}
            resumes.append(resume)
            check(str(path)+":resume_event_source_hash", report["resume"]["prior_attempts"][0]["events_sha256"] == prior_events["sha256"])
            check(str(path)+":resume_count", report["resume"]["completed_queries_not_rerun"] == len(previous_hashes))
            del previous
        for row in report["rows"]:
            source_raw = streams[row["dataset"]].readline()
            check(row["id"]+":source_identity", hashlib.sha256(source_raw).hexdigest() == row["source_line_sha256"] and json.loads(source_raw) == row["source_record"])
            v3["combined"].add(row)
            v3["leetcode" if key != "dev" else "dev"].add(row)
            if key == "dev":
                v3[row["dataset"]].add(row)
            for q in row["queries"]:
                slot = (row["id"], q["query_index"])
                check(str(slot)+":original_sql", q["original_sql"] == row["source_record"]["pair"][q["query_index"]])
                by_slot[slot] = {"status": q["status"], "eligible": q.get("eligible"), "ast_sha256": objsha(q.get("ast")), "sql_sha256": sqlsha(q["original_sql"])}
                if slot in previous_hashes and previous_hashes[slot] != objsha(q):
                    resumes[-1]["completed_results_unchanged"] = False
                if q["status"] == "PARSE_OR_AST_RECORD_ERROR":
                    parse_errors.append({"row_id": row["id"], "query_index": q["query_index"], "reason": q["reason"],
                                         "source_report": str(path), "source_report_sha256": FILES[str(path)]["sha256"],
                                         "original_sql_sha256": sqlsha(q["original_sql"]),
                                         "original_query_record_sha256": objsha(q)})
        if previous_hashes:
            check(str(path)+":all_resumed_completed_results_unchanged", resumes[-1]["completed_results_unchanged"])
        del report
    for k, f in streams.items():
        check(k+":source_stream_exhausted", f.read(1) == b"")
        f.close()
    check("v3_leetcode_denominator", (v3["leetcode"].pairs,v3["leetcode"].slots)==(23994,47988))
    check("v3_combined_denominator", (v3["combined"].pairs,v3["combined"].slots)==(24455,48910))
    v4_report, v4_super = read(V4/"scan_report.json"), read(V4/"supervisor_report.json")
    v4_status, transitions, leaves, unknown_reasons, by_dataset = Counter(), Counter(), Counter(), Counter(), defaultdict(Counter)
    v4_eligible, unknown_slots, seen = [], [], set()
    for block in v4_report["cached_blocks"]:
        sel = block["selected"]
        check("v4_cache_block:"+str(block["block"]), sel is not None and FILES.get(sel["path"],{}).get("sha256") == sel["sha256"] and sel["unchanged_after_scan"] is True)
    register(V4/"slots.jsonl")
    with (V4/"slots.jsonl").open() as f:
        for line in f:
            q=json.loads(line); slot=(q["row_id"],q["query_index"]); old=by_slot[slot]
            seen.add(q["slot_ordinal"]); v4_status[q["status"]]+=1; by_dataset[q["dataset"]][q["status"]]+=1
            transitions[old["status"]+" -> "+q["status"]]+=1
            check(str(slot)+":v4_original_evidence", q["original_status"]==old["status"] and objsha(q.get("ast"))==old["ast_sha256"] and q["sql_sha256"]==old["sql_sha256"])
            if q["eligible"] is True:
                leaves[q["leaf_count"]]+=1; v4_eligible.append({k:q[k] for k in ("row_id","query_index","sql_sha256","source_problem_key","leaf_count")})
            if q["status"]=="UNKNOWN":
                unknown_reasons[q["reason"]]+=1
                unknown_slots.append({k:q[k] for k in ("row_id","query_index","original_status","original_reason","reason","ast_sha256")})
    check("v4_all_unique_ordinals", seen==set(range(48910)) and sum(v4_status.values())==48910)
    check("v4_report_counts", all(v4_report["summary"]["query_status_counts"].get(k,0)==v for k,v in v4_status.items()))
    check("v4_complete_exit_zero", v4_super["status"]=="COMPLETE" and v4_super["worker_returncode"]==0 and v4_report["status"]=="COMPLETE_FULL_DENOMINATOR_CACHED_SCAN")
    check("v4_kernel", v4_report["kernel_sha256"]==NEW_KERNEL)
    for entry in v4_report["inputs"]:
        check("v4_input:"+entry["path"], register(Path(entry["path"]))==entry["sha256"] and entry["unchanged_after_scan"] is True)
    for name,digest in v4_report["output_hashes"].items():
        check("v4_output:"+name,register(V4/name)==digest)
    queues=[]
    for path in sorted(LEET.glob("QUEUE_CHUNKS_*.json")):
        q=read(path)
        queues.append({"path":str(path),"sha256":FILES[str(path)]["sha256"],"status":q["status"],
                       "jobs":[{k:j.get(k) for k in ("chunk_index","attempt","status","exit_code","scan_status")} for j in q["jobs"]]})
    progress=read(LEET/"GLOBAL_PROGRESS.json")
    progress_status=progress["status"]
    register(Path(__file__))
    results={k:v.result() for k,v in v3.items()}
    failures=[c for c in CHECKS if not c["pass"]]
    cut={"status":"COMPLETE_READ_ONLY_FINAL_CUT" if not failures else "AUDIT_DISCREPANCY_REQUIRES_REVIEW",
         "created_utc":datetime.now(timezone.utc).isoformat(),"method":"stdlib-only reading/hashing/counting of existing immutable result snapshots; no kernel/parser/solver imported or executed",
         "full_denominators":{"leetcode_pairs":23994,"leetcode_query_slots":47988,"dev_pairs":461,"dev_query_slots":922,"combined_pairs":24455,"combined_query_slots":48910},
         "v3":results,"v3_selected_attempts":attempts,"budget_resume_evidence":resumes,
         "original_parse_or_ast_errors":parse_errors,"v4":{"summary":v4_report["summary"],"independent_slot_counts":dict(v4_status),
            "independent_by_dataset":{k:dict(v) for k,v in by_dataset.items()},"transitions_from_v3":dict(transitions),
            "eligible_slots":v4_eligible,"eligible_leaf_histogram":dict(leaves),"unknown_reason_counts":dict(unknown_reasons),
            "unknown_slots":unknown_slots,"supervision":v4_super,"scope":v4_report["scope"],"kernel_sha256":NEW_KERNEL},
         "queues":queues,"global_progress_header_status":progress_status,
         "cautions":["GLOBAL_PROGRESS header remains PARTIAL_EXTERNAL_APPLICABILITY_SCAN; final completeness is established from all 24 selected reports, not this stale aggregate label.",
             "Queue job exit_code is the supervisor process exit; for stopped attempts 9/16 it is 0 while supervision child exit_code is 2. Preserve worker status and stop reason.",
             "Six eligible slots all have zero non-root leaves. External supported JOIN coverage is zero; no evidence for factorized JOIN benefit or generalization.",
             "v4 reuses prior official ALL AST and performs no new parse, IC assertion, solver run or performance comparison.",
             "Source problem labels and repeated pair/SQL counts are descriptive source units, not independent human gold or independent semantic tasks.",
             "38 Calcite non-JSON serialized ASTs become UNKNOWN; all original AST/status/reason retained. This is conservative cached representation refusal, not a new parser failure or success."],
         "audit":{"checks":len(CHECKS),"failed_checks":failures,"all_checks_pass":not failures,
                  "independent_v4_review":"/root/contract_audit/contract_independent_review independently confirmed full ordinal set, counts, and 38 utils.ValuesTable nodes; no target executed"},
         "file_provenance":FILES}
    json_out.write_text(json.dumps(cut,ensure_ascii=False,indent=2)+"\n")
    leet,dev=results["leetcode"],results["dev"]
    s=v4_report["summary"]; d=leet["distinct"]
    lines=["# 公共可用性最终截面", "", "结论：完整 LeetCode 47,988 查询槽无一被 v3 或 v4 接纳。合并 Calcite / literature 后，48,910 槽仍只有原来的 6 个阳性（2 对双侧阳性），全部是单表、leaf = 0；真正 JOIN 覆盖为 0。不能据此主张外部 JOIN 泛化、因子化收益或稳定强基线增益。", "",
           "| 数据 / 阶段 | 原始对数 | 查询槽 | ELIGIBLE | INELIGIBLE | FRONTEND_UNSUPPORTED | 原 parse/AST 错误 | UNKNOWN | NOT_RUN |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for label,stats in [("LeetCode v3",leet),("开发集 v3",dev),("合并 v3",results["combined"])]:
        c=stats["query_status_counts"]
        lines.append(f"| {label} | {stats['pair_denominator']:,} | {stats['query_slot_denominator']:,} | {c.get('ELIGIBLE',0):,} | {c.get('INELIGIBLE',0):,} | {c.get('FRONTEND_UNSUPPORTED',0):,} | {c.get('PARSE_OR_AST_RECORD_ERROR',0):,} | {c.get('UNKNOWN',0):,} | {c.get('NOT_RUN',0):,} |")
    c=dict(v4_status)
    lines += [f"| 合并 cached-AST v4 | 24,455 | 48,910 | {c.get('ELIGIBLE',0):,} | {c.get('INELIGIBLE',0):,} | {c.get('FRONTEND_UNSUPPORTED',0):,} | {c.get('PARSE_OR_AST_RECORD_ERROR',0):,} | {c.get('UNKNOWN',0):,} | {c.get('NOT_RUN',0):,} |", "",
      f"LeetCode 有 {d['source_problem_labels']} 个原始 `file` 问题标签、{d['raw_sql']:,} 条 distinct 原始 SQL、{d['ordered_sql_pairs']:,} 个 distinct 有序 SQL 对；重复 SQL 槽超额 {d['raw_sql_repeated_slot_excess']:,}、问题标签上的重复对超额 {d['source_problem_pair_repetition_excess']:,}。分母始终保留全部 23,994 对 / 47,988 槽，未按 distinct 数缩减。合并数据有 {s['distinct']['all_source_problem_labels']} 个来源标签和 {s['distinct']['all_raw_sql']:,} 条原始 SQL；6 阳性仅对应 4 条 distinct SQL、5 个完整上下文和 4 个来源标签。来源标签不是经真人验证的独立语义问题。", "",
      "38 个 UNKNOWN 全来自 Calcite 的 35 对；缓存中每槽含一个序列化 `utils.ValuesTable` 节点。v3 原状态均为 INELIGIBLE（原因为 subquery_or_non_inner_join 30、extra_select_clause 5、unsupported_identifier 3），v4 不重建特殊对象而保守标 UNKNOWN。所有原状态、AST 和原因仍保留。没有新增阳性，没有把解析失败修成可答样本。", "",
      "选定缓存为 chunk 9 和 16 的 attempt_002，其余 22 块 attempt_001。24 个选定 worker 都 exit 0，完整分母已处理；它们与 v4 所用缓存 SHA 一致。两次资源中止保留如下：", "",
      "| 块 | 首次停止 | 首次已完成 | 首次未完成 | 原 completed 不重跑 | 续跑新增结果 | 最终 worker exit |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in resumes:
        lines.append(f"| {r['block']} | CPU_SOFT_43_SECONDS_RESERVE_FOR_FINAL_REPORT | {r['first_completed_slots']} | {r['first_uncompleted_slots']} | {r['second_resume_record']['completed_queries_not_rerun']} | {r['second_events']['event_counts'].get('QUERY_RESULT',0)} | {r['second_worker_exit_code']} |")
    lines += ["", "两次首次 worker 均 exit 2；此前 completed 查询记录与续跑结果逐条哈希一致。chunk 9 的原末尾状态为 1 个 ATTEMPTED_EFFECT_UNKNOWN + 26 个 NOT_RUN，chunk 16 为 1 + 21，均由原槽续跑补完。原 parse/AST 错误没有被删去：LeetCode 1,229 槽，加开发集 17 槽，共 1,246 槽。JSON 附有每项原错误原文、定位及原始报告 / 查询记录哈希，也保留全部选中 supervisor、停止与续跑事件摘要。", "",
      "`GLOBAL_PROGRESS.json` 顶层仍叫 PARTIAL_EXTERNAL_APPLICABILITY_SCAN，不能把旧聚合标签当最终完成依据；这里按 24 个选中报告逐条重算。队列 job 的 exit_code 是 supervisor 进程码，两次停止时为 0，但 supervisor 内记录的计算 worker exit 为 2；本报告保留这一区别。", "",
      f"v4 supervisor 为 COMPLETE / worker exit 0，总墙钟 {v4_super['total_wall_seconds']:.6f} 秒，父子合计采样峰值 RSS {v4_super['sampled_peak_combined_rss_bytes']:,} 字节。这些仅是资源护栏证据，不是与基线的性能比较；它复用固定官方 ALL AST，只运行原始标识符检查及 v4 recognizer，没有新解析、约束断言或求解。", "",
      f"本汇总只执行标准库读取、哈希和计数；{len(CHECKS):,} 项身份 / 槽位 / 输出核对，失败 {len(failures)} 项。完整输入与输出 SHA 见 [PUBLIC_APPLICABILITY_FINAL_CUT.json](PUBLIC_APPLICABILITY_FINAL_CUT.json)。冻结 kernel SHA：`{NEW_KERNEL}`。", ""]
    md_out.write_text("\n".join(lines))
    print(json.dumps({"status":cut["status"],"failed_checks":failures,"v3_leetcode_status":leet["query_status_counts"],
                      "v3_leetcode_distinct":d,"v4_status":dict(v4_status),"paths":[str(json_out),str(md_out)]},ensure_ascii=False))


if __name__ == "__main__":
    main()
