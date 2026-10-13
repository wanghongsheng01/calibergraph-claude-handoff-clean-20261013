# Hash-first original SQL representatives

Selection: ascending SHA256(stable ID), at most three per structural category across both sources. Original SQL copied verbatim from the pinned source line. No labels or performance used; none is an eligible strict-elimination case.

## different_selection_same_input: verieql_leetcode|benchmark/leetcode/raw_data/595.csv|13|line2815|90cb7d67cd0dab01
Source: `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/public_leetcode/leetcode.jsonlines` line 2815
Static DAG before/after: 5/5; shared nodes: 1; events: `{"P_common_context": 1, "S_different_same_input_descriptive": 1}`

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE AREA >= 3000000 OR POPULATION >= 25000000
```

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE (AREA) > 3000000 OR POPULATION > 25000000
```

## different_selection_same_input: verieql_leetcode|benchmark/leetcode/raw_data/595.csv|37|line2839|b429578d998c5029
Source: `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/public_leetcode/leetcode.jsonlines` line 2839
Static DAG before/after: 5/5; shared nodes: 1; events: `{"P_common_context": 1, "S_different_same_input_descriptive": 1}`

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE AREA >= 3000000 OR POPULATION >= 25000000
```

```sql
SELECT NAME ,POPULATION ,AREA FROM WORLD WHERE 1=1 AND (POPULATION >= 25000000 OR AREA >= 3000000 )
```

## different_selection_same_input: verieql_leetcode|benchmark/leetcode/raw_data/595.csv|20|line2822|f431bf01f12d8b0a
Source: `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/public_leetcode/leetcode.jsonlines` line 2822
Static DAG before/after: 5/5; shared nodes: 1; events: `{"P_common_context": 1, "S_different_same_input_descriptive": 1}`

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE AREA >= 3000000 OR POPULATION >= 25000000
```

```sql
SELECT NAME , POPULATION , AREA FROM WORLD WHERE (AREA > 3000000) OR(POPULATION>25000000)
```

## nontrivial_JOIN: parseval_bird|codebase_community|575|line576|1e201c94359adfb2
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 576
Static DAG before/after: 8/9; shared nodes: 2; events: `{}`

```sql
SELECT T2.Name FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T1.DisplayName = 'SilentGhost'
```

```sql
SELECT T1.Name FROM badges AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id WHERE T2.DisplayName = 'SilentGhost'
```

## nontrivial_JOIN: parseval_bird|student_club|1429|line1430|7d5f9d3142c0ecc7
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 1430
Static DAG before/after: 11/12; shared nodes: 3; events: `{}`

```sql
SELECT T2.event_name FROM attendance AS T1 INNER JOIN event AS T2 ON T2.event_id = T1.link_to_event INNER JOIN member AS T3 ON T1.link_to_member = T3.member_id WHERE T3.position = 'Vice President' AND T2.location = '900 E. Washington St.' AND T2.type = 'Social'
```

```sql
SELECT T1.event_name FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id WHERE T1.type = 'Social' AND T3.position = 'Vice President' AND T1.location = '900 E. Washington St.'
```

## nontrivial_JOIN: parseval_bird|superhero|825|line826|8ff71c0d4934cb84
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 826
Static DAG before/after: 14/15; shared nodes: 4; events: `{}`

```sql
SELECT T4.gender FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id INNER JOIN gender AS T4 ON T1.gender_id = T4.id WHERE T3.power_name = 'Phoenix Force'
```

```sql
SELECT T2.gender FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id INNER JOIN hero_power AS T3 ON T1.id = T3.hero_id INNER JOIN superpower AS T4 ON T3.power_id = T4.id WHERE T4.power_name = 'Phoenix Force'
```

## same_projection: verieql_leetcode|benchmark/leetcode/raw_data/595.csv|13|line2815|90cb7d67cd0dab01
Source: `/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011/public_leetcode/leetcode.jsonlines` line 2815
Static DAG before/after: 5/5; shared nodes: 1; events: `{"P_common_context": 1, "S_different_same_input_descriptive": 1}`

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE AREA >= 3000000 OR POPULATION >= 25000000
```

```sql
SELECT NAME, POPULATION, AREA FROM WORLD WHERE (AREA) > 3000000 OR POPULATION > 25000000
```

## same_projection: parseval_bird|formula_1|875|line876|a358de40f9a1571a
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 876
Static DAG before/after: 8/7; shared nodes: 2; events: `{"P_common_context": 1, "S_common_context": 1}`

```sql
SELECT T2.url FROM races AS T1 INNER JOIN seasons AS T2 ON T2.year = T1.year WHERE T1.raceId = 901
```

```sql
SELECT T2.url FROM races AS T1 INNER JOIN seasons AS T2 ON T1.year = T2.year WHERE T1.raceId = 901
```

## same_projection: parseval_bird|card_games|471|line472|f295df6ccedc26ec
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 472
Static DAG before/after: 8/7; shared nodes: 2; events: `{"P_common_context": 1, "S_common_context": 1}`

```sql
SELECT T1.type FROM sets AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.code WHERE T2.translation = 'Hauptset Zehnte Edition'
```

```sql
SELECT T1.type FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.translation = 'Hauptset Zehnte Edition'
```

## same_selection: parseval_bird|formula_1|875|line876|a358de40f9a1571a
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 876
Static DAG before/after: 8/7; shared nodes: 2; events: `{"P_common_context": 1, "S_common_context": 1}`

```sql
SELECT T2.url FROM races AS T1 INNER JOIN seasons AS T2 ON T2.year = T1.year WHERE T1.raceId = 901
```

```sql
SELECT T2.url FROM races AS T1 INNER JOIN seasons AS T2 ON T1.year = T2.year WHERE T1.raceId = 901
```

## same_selection: parseval_bird|card_games|471|line472|f295df6ccedc26ec
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 472
Static DAG before/after: 8/7; shared nodes: 2; events: `{"P_common_context": 1, "S_common_context": 1}`

```sql
SELECT T1.type FROM sets AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.code WHERE T2.translation = 'Hauptset Zehnte Edition'
```

```sql
SELECT T1.type FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.translation = 'Hauptset Zehnte Edition'
```

## same_selection: parseval_bird|card_games|502|line503|df22523dd81dc38c
Source: `/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_distinct_evidence_20261012_03/sources_local/disprove-bird.jsonl` line 503
Static DAG before/after: 8/7; shared nodes: 2; events: `{"P_common_context": 1, "S_common_context": 1}`

```sql
SELECT T1.releaseDate FROM sets AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.code WHERE T2.translation = 'Ola de frío'
```

```sql
SELECT T1.releaseDate FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.translation = 'Ola de frío'
```
