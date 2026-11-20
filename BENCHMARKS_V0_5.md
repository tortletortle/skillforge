# SKILLFORGE V0.5 — External Benchmark Adapters

V0.5 adds local-repository adapters, paired-run planning, result normalization,
group-disjoint split generation, Agent Skills export, and isolated SWE skill overlays.

## Important: what has and has not been run

The adapter package and its fixture-based integration tests run locally. The four
upstream benchmark repositories/datasets are **not bundled** in this archive.
This environment could not resolve GitHub/Hugging Face hosts, and no Docker
benchmark runtime or model API credentials were available. Therefore V0.5 does
**not** claim official benchmark scores or completed real-agent trials.

Use the commands below after cloning/downloading each upstream benchmark. All
benchmark commands are dry-run plans until `benchmark execute --execute` is
explicitly supplied.

## Supported suites and pinned protocols

| Adapter key | Upstream project | Expected local signature | Evaluation protocol |
|---|---|---|---|
| `skillflow` | ZhangZi-a/SkillFlow lifelong benchmark | `family_job_runner.py`, `iterative_shared_skills_runner.py`, `test_tasks/` | family-local sequential learning; baseline vs iterative shared skills |
| `skilllearnbench` | cxcscmu/SkillLearnBench | `evaluate_skills.py`, `generate_skills.py`, `tasks/` | no-skill, human-authored, one-shot, self-feedback, teacher-feedback, Skill Creator, SKILLFORGE |
| `skillsbench` | benchflow-ai/skillsbench v1.1 | `tasks/*/task.md` | oracle gate, no-skill, official skills, optional SKILLFORGE skill directory |
| `swe-skills-bench` | ControllableModel/SWE-Skills-Bench | `main.py`, `config/benchmark_config.yaml`, `skills/`, `tasks/` | paired `none` vs `one` cells; generated skills evaluated in an isolated overlay copy |

**Name disambiguation:** “SkillFlow” is used by two different 2026 projects.
This adapter targets ZhangZi-a's lifelong skill-discovery/evolution benchmark
(166 tasks, 20 workflow families). The separate COLM paper “SkillFlow: Scalable
and Efficient Agent Skill Retrieval System” is a retrieval method evaluated on
SkillsBench and Terminal-Bench; it is not the same benchmark.

## Bootstrap in WSL2

From your WSL2 Ubuntu shell:

```bash
bash scripts/bootstrap_external_benchmarks.sh "$HOME/skillforge_external"
```

The script clones the four repositories, downloads the SkillFlow task dataset,
and writes `REVISION_MANIFEST.txt`. It does not install model credentials or
launch experiments. Pin the revisions in that manifest before final runs.

## Install / obtain upstream projects

Use the upstream instructions and pin the exact repository revision and dataset
revision in the experiment record. Do not run against a moving `main` branch for
final comparisons.

- SkillFlow: `https://github.com/ZhangZi-a/SkillFlow`
  - Task data is separate: `zhang-ziao/SkillFlow-Task` on Hugging Face.
  - Upstream README uses Harbor and `uv sync`; baseline and iterative runners
    read their YAML configs.
- SkillLearnBench: `https://github.com/cxcscmu/SkillLearnBench`
  - Docker is required. API credentials and some task-specific variables may
    also be required.
  - Skill generation must receive `instance-1` input **without** verifier/test
    artifacts.
- SkillsBench: `https://github.com/benchflow-ai/skillsbench`
  - V0.5 targets v1.1: 87 task packages across 8 domains.
  - The v1.1 release instructions require BenchFlow `>=0.6.3,<0.7`.
  - Run the oracle validity gate before agent runs. Docker can be used locally.
- SWE-Skills-Bench: `https://github.com/ControllableModel/SWE-Skills-Bench`
  - The current repository README describes 98 skills and 10 requirements per
    skill, paired `none` / `one` runs, pinned repositories and hidden tests.
  - The arXiv paper/Hugging Face release describes an earlier 49-skill / 565-task
    dataset. These are different release snapshots; pin and report the exact
    commit and manifest. Do not combine their scores.

## CLI

```bash
# Inspect local repositories and create task manifests
python -m skillforge.cli benchmark inspect skillflow --root /path/to/SkillFlow --output runs/skillflow_manifest.json
python -m skillforge.cli benchmark inspect skilllearnbench --root /path/to/SkillLearnBench
python -m skillforge.cli benchmark inspect skillsbench --root /path/to/skillsbench
python -m skillforge.cli benchmark inspect swe-skills-bench --root /path/to/SWE-Skills-Bench

# Create plans (no benchmark execution)
python -m skillforge.cli benchmark plan skillflow --root /path/to/SkillFlow --output runs/skillflow_plan.json
python -m skillforge.cli benchmark plan skilllearnbench --root /path/to/SkillLearnBench --tasks court-form-filling github-repo-analytics --skill-dir /path/to/generated/skills --output runs/slb_plan.json
python -m skillforge.cli benchmark plan skillsbench --root /path/to/skillsbench --tasks <task-id> --agent claude-agent-acp --model anthropic/claude-sonnet-4-6 --sandbox docker --skill-dir /path/to/task-specific/skills --output runs/skillsbench_plan.json
python -m skillforge.cli benchmark plan swe-skills-bench --root /path/to/SWE-Skills-Bench --tasks fastapi-patterns --agent claude --model claude-haiku-4-5 --output runs/swe_plan.json

# One cross-suite plan can be generated from the JSON template:
python -m skillforge.cli benchmark matrix --config benchmarks/external_benchmarks.example.json --output runs/cross_suite_plan.json

# Dry-run is the default. Review argv, cwd, model, and task revisions first.
python -m skillforge.cli benchmark execute runs/skillsbench_plan.json

# Actually run only after installing the upstream dependencies, validating Docker,
# setting API credentials, and reviewing the plan:
python -m skillforge.cli benchmark execute runs/skillsbench_plan.json --execute --timeout 7200 --output runs/skillsbench_execution.json

# Export SKILLFORGE IR into the benchmark's skill format
python -m skillforge.cli benchmark export-skill skill.json --suite skilllearnbench --task-id court-form-filling --output /path/to/SkillLearnBench/skills/skillforge-v0.5
# For SkillsBench, output is the task package root; then pass the task's environment/skills directory as --skill-dir.
python -m skillforge.cli benchmark export-skill skill.json --suite skillsbench --output /path/to/skillsbench/tasks/<task-id>

# For SWE-Skills-Bench, create a disposable copy and replace only one skill.
python -m skillforge.cli benchmark stage-swe-skill --root /path/to/SWE-Skills-Bench --skill-id fastapi-patterns --skill-json skill.json --output-root /path/to/SWE-Skills-Bench-SKILLFORGE
# Then plan against the overlay root to compare its `one` arm with the original repo's `none` arm.
# Preserve the original repo unchanged.

# Normalize upstream result JSON/JSONL/CSV and compute task-paired deltas.
python -m skillforge.cli benchmark collect skillsbench --results /path/to/results --treatment skillforge_v0.5 --control no_skill --output runs/skillsbench_normalized.json

# Group-disjoint holdout split (e.g. SkillLearnBench by category; SkillFlow by family)
python -m skillforge.cli benchmark split skilllearnbench --root /path/to/SkillLearnBench --group-field category --seed 20261119 --output runs/slb_split.json
python -m skillforge.cli benchmark split skillflow --root /path/to/SkillFlow --protocol family_sequence --train-ratio 0.7 --output runs/skillflow_forward_split.json
python -m skillforge.cli benchmark split skillflow --root /path/to/SkillFlow --protocol grouped_holdout --group-field family --seed 20261119 --output runs/skillflow_family_holdout.json
```

## Fair-comparison rules

1. **Pin all revisions:** upstream Git commit, dataset revision, task manifest,
   Docker image digest, benchmark runner version and SKILLFORGE commit.
2. **Paired cells:** same task, task revision, model, agent harness, temperature,
   context window, max turns, tool policy, container image, timeout and trial count.
3. **Oracle / infrastructure gates:** an invalid environment or failed oracle
   must be fixed before counting an agent failure. Keep infra-invalid trials
   separate and rerun them.
4. **No verifier leakage:** skill generation must not read hidden tests,
   verifier scripts, oracle solutions or expected-output labels. The
   `assert_no_verifier_leakage` helper rejects common forbidden path names.
5. **Task-family holdout:** SkillFlow must preserve within-family task order;
   also report leave-family-out transfer. SkillLearnBench should use category
   or task-level holdout, and never split instances of one task across train/test
   if the skill was learned from instance-1.
6. **No pooled leaderboard:** benchmark tasks and scoring rubrics differ. Report
   per-suite metrics and confidence intervals; do not average pass rates across
   the four suites.
7. **Cost accounting:** report success, tokens, tool calls/turns, wall-clock,
   API cost, and number of skill revisions. Use the same model pricing snapshot.
8. **Repeated trials:** use at least 3 trials where the benchmark permits; report
   task-level bootstrap 95% confidence intervals and per-task deltas.
9. **Baseline integrity:** preserve official baselines as published. SKILLFORGE
   is an additional arm, not a replacement for one-shot, self-feedback,
   teacher-feedback, Skill Creator, official skills or no-skill conditions.

## V0.5 metrics

- Task pass rate / verifier success
- Paired delta versus no-skill and official-skill controls
- Skill quality: functional coverage, executability, safety
- Trajectory quality: key-point recall, order correctness, completeness
- Transfer: within-family future-task gain and leave-family-out gain
- Evolution: skill reuse, patch count, repair acceptance rate, rollback rate
- Efficiency: tokens, API cost, wall-clock, turns
- Robustness: infra-invalid rate, variance across trials, regression rate

`benchmark collect` normalizes common fields from JSON, JSONL and CSV. It keeps
the original row under `raw`; if an upstream schema does not expose a per-task
condition, the report will be aggregate-only and cannot support paired inference.
