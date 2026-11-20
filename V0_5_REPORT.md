# SKILLFORGE V0.5 — External Benchmark Integration Report

## 1. Executive summary

V0.5 turns SKILLFORGE from an internal synthetic-repair research prototype into
an external-benchmark integration layer. It adds four suite adapters:

1. ZhangZi-a SkillFlow lifelong skill discovery/evolution benchmark.
2. cxcscmu SkillLearnBench.
3. BenchFlow SkillsBench v1.1.
4. ControllableModel SWE-Skills-Bench.

Implemented capabilities:
- Local benchmark repository signature detection.
- Task discovery and per-task revision hashing.
- Paired baseline / SKILLFORGE run-plan generation.
- Oracle and infrastructure validity-gate planning where supported.
- Agent Skills `SKILL.md` export.
- Isolated SWE-Skills-Bench skill-overlay staging.
- Group-disjoint train/test split generation and SkillFlow family-local forward splits that honor `ALL_TASK_DIFFICULTY_RANKING.json` when available.
- JSON / JSONL / CSV result normalization.
- Task-paired treatment-control deltas and bootstrap confidence intervals.
- Explicit dry-run execution; actual subprocess execution requires `--execute`.

## 2. Research-grounded benchmark specifications

### 2.1 SkillFlow lifelong benchmark

Upstream: https://github.com/ZhangZi-a/SkillFlow  
Task dataset: https://huggingface.co/datasets/zhang-ziao/SkillFlow-Task

The benchmark has 166 executable tasks across 20 workflow families and five
domains. Task data is distributed separately from the runner repository.
Its baseline and iterative settings use `family_job_runner.py` and
`iterative_shared_skills_runner.py`, respectively. The iterative setting
carries a shared skill library forward within each workflow family.

V0.5 adapter behavior:
- Detects the two upstream runners.
- Discovers `task.toml` packages under `test_tasks/`.
- Records family, metadata and task-manifest SHA-256.
- Emits native baseline and iterative runner plans.
- Warns that task order is part of the family-local lifelong protocol.

Important limitation: the upstream runners use YAML configuration files and
do not expose an arbitrary per-task CLI filter in the inspected README. The
adapter therefore does not invent task flags. Select tasks/families in the
upstream config before execution.

### 2.2 SkillLearnBench

Upstream: https://github.com/cxcscmu/SkillLearnBench  
Paper: https://arxiv.org/abs/2604.20087

The public repository describes 20 skill-dependent tasks, 15 sub-domains and
100 verified instances. Its evaluation framework covers task success, skill
quality and trajectory quality. Published baselines include one-shot,
self-feedback, teacher-feedback and Skill Creator, plus human-authored and
no-skill controls. Docker is a hard requirement for evaluation.

V0.5 adapter behavior:
- Detects `evaluate_skills.py`, `generate_skills.py` and task packages.
- Maps the published 20-task roster to six categories.
- Plans no-skill, human-authored and any baseline directories actually present
  (`b1`–`b4`), plus a SKILLFORGE method directory.
- Exports skills to `<method-root>/<task-id>/<skill-name>/SKILL.md`.
- Includes an explicit verifier-leakage guard.

Critical protocol rule: the benchmark instructions say to provide instance-1
input to the skill generator without its verifier. Tests, verifier scripts,
oracle solutions and hidden labels must not enter skill-generation context.

### 2.3 SkillsBench v1.1

Upstream: https://github.com/benchflow-ai/skillsbench  
Docs: https://www.benchflow.ai/docs/skillsbench/getting-started

The current v1.1 task registry contains 87 task packages across eight
professional domains. The release notes specify BenchFlow `>=0.6.3,<0.7` for
reproducing v1.1. The documented task lifecycle includes an oracle validity
run and paired agent runs with `no-skill` and `with-skill` modes.

V0.5 adapter behavior:
- Detects native `tasks/<task-id>/task.md` packages.
- Extracts simple YAML frontmatter metadata.
- Plans the oracle gate first.
- Plans no-skill and official-skill conditions.
- Adds the SKILLFORGE condition only when a separate `--skill-dir` is supplied.
- Exports generated skills into `environment/skills/<skill-name>/SKILL.md`.

Do not count agent runs for tasks whose oracle gate fails. The adapter does not
overwrite official task assets.

### 2.4 SWE-Skills-Bench

Upstream repository: https://github.com/ControllableModel/SWE-Skills-Bench  
Paper: https://arxiv.org/abs/2603.15401

The inspected repository README describes 98 skills, ten requirements per
skill, fixed repository commits, isolated containers and paired `none` / `one`
skill modes. It also describes an infrastructure-clean gate: turn-zero
infrastructure failures must be rerun rather than scored as agent failures.

There is a release-snapshot discrepancy: the paper/Hugging Face dataset
description refers to 49 skills and 565 task instances, while the inspected
repository README describes 98 skills and 980 skill-requirement pairs per
condition. These must be treated as different snapshots until exact commit and
manifest identity are established.

V0.5 adapter behavior:
- Detects `main.py` and `config/benchmark_config.yaml`.
- Discovers skill IDs with `SKILL.md`.
- Plans paired `none` and `one` runs.
- Can create a disposable repository copy and replace one skill with a
  SKILLFORGE-generated artifact. The original benchmark repository remains
  untouched.
- Does not infer unsupported CLI flags for custom skill injection.

## 3. Algorithm / method comparison plan

| Suite | Published baselines | SKILLFORGE arm | Primary question |
|---|---|---|---|
| SkillFlow | baseline vs iterative shared-skill evolution | to be connected to upstream Harbor agent loop | Does a skill learned from earlier tasks improve later tasks in the same workflow family? |
| SkillLearnBench | no-skill, human-authored, b1 one-shot, b2 self-feedback, b3 teacher-feedback, b4 Skill Creator | SKILLFORGE skill library | Does repair/verification-driven skill evolution improve task, skill and trajectory quality? |
| SkillsBench | oracle, no-skill, official skills | SKILLFORGE skill directory | Do generated skills help under compositional tasks and distractor skills? |
| SWE-Skills-Bench | no-skill vs curated skill | isolated SKILLFORGE overlay | Does the generated skill improve hidden-test pass rate on fixed real repositories? |

CodeTriage is not itself one of these four skill benchmarks. It is an external
repair-search method and should be evaluated as a method-level baseline only
when the same candidate patch frontier and budget are available. Do not compare
its published code-repair scores directly to skill-benchmark pass rates.

## 4. Fair experimental protocol

### 4.1 Shared controls

Record and hold constant:
- Model provider and exact model identifier.
- Agent CLI / harness version.
- Temperature, sampling parameters and context limit.
- Tool permissions and tool versions.
- Task commit and dataset revision.
- Container image digest and sandbox backend.
- Timeout, max turns, retry policy and trial count.
- Skill exposure mode and skill directory contents.
- Pricing snapshot for API-cost calculations.

### 4.2 Split design

Do not randomly split rows if related tasks share a workflow family or skill.

- SkillFlow: preserve official within-family task order; report future-task
  transfer within family and a separate leave-family-out test.
- SkillLearnBench: group by published category or task; if skill generation
  uses instance-1, do not let instances from the same task leak across
  train/test.
- SkillsBench: split by task/domain, preserving paired conditions.
- SWE-Skills-Bench: group by skill/repository; do not split requirements for
  one skill across train and test when the skill was learned from one of them.

The `benchmark split` command provides deterministic group-disjoint splits.
It is an auxiliary split tool, not a replacement for each benchmark's official
evaluation protocol.

### 4.3 Metrics

Report per suite:
- Primary task verifier pass rate.
- Paired task-level delta versus no-skill and official-skill controls.
- 95% task-bootstrap confidence interval.
- Skill quality: coverage, executability, safety (where available).
- Trajectory quality: key-point recall, ordering, completeness (where available).
- Transfer: future-task and held-out-family gain.
- Efficiency: tokens, tool calls, wall-clock, cost.
- Evolution: skill reuse, number of revisions, repair acceptance, rollback rate.
- Validity: oracle failures and infrastructure-invalid trials separately.

Never pool the four suite pass rates into a single score: their tasks and
verifiers are not statistically exchangeable.

## 5. Implementation and local verification

New package:
- `skillforge/benchmarks/adapters.py`
- `skillforge/benchmarks/results.py`

New CLI:
- `benchmark inspect`
- `benchmark plan`
- `benchmark execute` (dry-run by default)
- `benchmark collect`
- `benchmark split`
- `benchmark export-skill`
- `benchmark stage-swe-skill`
- `benchmark matrix`

New tests cover repository detection, task discovery, run planning, skill
export, verifier-leakage rejection, overlay isolation, result ingestion,
paired deltas and grouped split integrity.

Local verification:
- V0.1–V0.4 inherited tests: 45 passed.
- V0.5 external-adapter tests: 12 passed.
- Total: 57 passed.

## 6. External benchmark execution status

**Not run in this environment.**

Reasons:
- The four upstream repositories and task datasets were not present in the
  working directory.
- `git ls-remote` could not resolve `github.com` from this execution
  environment.
- Docker / BenchFlow / Harbor task images and model API credentials were not
  provisioned here.

Therefore the 56/56 result is a local adapter and regression-test result, not
an official benchmark result. No real cross-task pass-rate improvement is
claimed. The generated run plans are ready to execute once the upstream
repositories, datasets, container runtime and credentials are available.

## 7. Next research questions

1. Integrate EGRS as a native lifelong agent loop in SkillFlow / Harbor rather
   than only running upstream baseline scripts.
2. Generate and export task-family skills for SkillLearnBench without verifier
   leakage, then evaluate them using the official runner.
3. Build a paired SkillBench experiment with no-skill, official skills and
   SKILLFORGE-generated skills at identical task revisions.
4. Run SWE-Skills-Bench official and isolated SKILLFORGE overlays with the
   infra-clean gate and per-cell trajectory audit.
5. Only after real benchmark data exists, train an external evidence ranker
   and report leave-family-out / leave-repository-out transfer.
