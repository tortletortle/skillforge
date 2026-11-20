# SKILLFORGE V0.2 — Engineering and Experiment Report

## Executive summary

V0.2 extends the V0.1 contract-guided skill compiler with a constrained repair and release lifecycle. A detected regression can produce a declarative patch, the candidate is recompiled and tested, all historical accepted examples are replayed, and only a passing candidate is published as a new immutable version. Rollback changes the active-version pointer while retaining every historical version.

This is a research prototype. The automatic repair strategy currently handles one explicit failure family (literal ASCII-space replacement that fails on tabs/newlines). It is not a general autonomous code-repair system and does not use an LLM to invent arbitrary code.

## Implemented components

### 1. Structured failure evidence

`validate_skill()` now returns `test_failures`, containing the failed test name, input, expected output, actual output (when execution succeeded), and error details. This gives a repair strategy concrete evidence instead of asking it to infer a failure from a prose string.

### 2. Constrained patch generation

`skillforge/patching.py` implements:

- `generate_repair_patch(skill, validation_report)`
- `apply_patch(skill, patch)`

The V0.2 rule identifies a `replace` operation configured with `old=" "` and a failing input containing tabs/newlines. It proposes a replacement with the registered `replace_whitespace` operation and preserves the newly observed failing example as a regression test.

Patch operations are allowlisted:

- `replace_step`
- `add_test`

A patch cannot inject Python, shell, dynamic imports, or arbitrary operation names. `compile_skill()` validates the resulting Skill IR against the fixed operation registry before execution.

### 3. Immutable version registry

`skillforge/versioning.py` implements `SkillVersionStore`:

- `install(skill)` validates before installation.
- `get(skill_id, version=None)` loads the active or specified version and verifies its SHA-256 digest.
- `list_versions(skill_id)` returns version history and events.
- `publish_patch(skill_id, patch)` uses optimistic base-version checking, candidate validation, historical regression, semantic version increment, and atomic manifest update.
- `rollback(skill_id, target_version, reason)` switches the active pointer without deleting version files.

Version files are immutable. A per-skill OS file lock serializes installation, publication, and rollback. Writes use a temporary file followed by atomic replacement. Version numbering advances from the latest published version, even after rollback.

### 4. Historical regression

`skillforge/regression.py` replays unique input/expected-output pairs from all accepted historical versions. It also checks historical preconditions and postconditions on the candidate. A candidate is rejected if it fails its own tests or any historical regression case.

### 5. CLI

New commands:

```powershell
python -m skillforge.cli install <skill.json> --repo .skillforge
python -m skillforge.cli repair <skill_id> --repo .skillforge --observed-skill <observed.json>
python -m skillforge.cli versions <skill_id> --repo .skillforge
python -m skillforge.cli rollback <skill_id> <version> --repo .skillforge --reason "..."
python -m skillforge.cli v02-demo
```

`--observed-skill` represents newly observed failure evidence. Its skill ID and base version must match the active version in the registry. The repair command does not silently replace the active skill with the observed file.

## Demonstration

The demo uses `spaces_to_hyphens` as a controlled defective skill:

- Baseline version `0.1.0` replaces only literal ASCII spaces.
- A newly observed example contains a tab and newline; the old skill fails its no-whitespace postcondition and expected output.
- The repair engine proposes `replace_whitespace` and adds the new example to the candidate regression suite.
- The candidate passes its own validation and all historical tests.
- The store publishes `0.1.1`.
- The demo rolls back to `0.1.0` and confirms the new input fails again, then restores `0.1.1`.

Observed demonstration results:

| Check | Result |
|---|---:|
| Initial failing examples | 1 |
| Candidate examples passed | 2/2 |
| Candidate contract tests passed | 2/2 |
| Candidate generated negative tests passed | 1/1 |
| Historical regression cases passed | 1/1 |
| Published version | 0.1.1 |
| Repaired tab/newline output | `alpha-beta-gamma` |
| Rollback to 0.1.0 | successful |
| Restore 0.1.1 | successful |

## Automated tests

Command:

```powershell
python -m unittest discover -s tests -v
```

Result: **21 tests passed** (12 V0.1 regression tests + 9 V0.2 tests).

V0.2 tests cover:

1. Structured failure evidence.
2. Repair patch generation and regression-case preservation.
3. Rejection of arbitrary code/unknown operations.
4. Publish and rollback.
5. Rejection of a behavior-breaking candidate.
6. Stale patch rejection.
7. SHA-256 integrity check for immutable versions.
8. Historical regression detection.
9. No patch generation when no failure exists.

## Safety and correctness boundaries

- The patch generator is deterministic and rule-based, not a general LLM patch generator.
- The runtime executes only registered built-in operations.
- Patch application is constrained to a small allowlist.
- A candidate must pass compilation, current validation, and historical regression before publication.
- Rejected patch evidence is retained in the patch directory.
- Rollback does not delete or rewrite versions.
- SHA-256 checks detect version-file modification relative to the local manifest; they do not provide a signed supply-chain guarantee if an attacker can also rewrite the manifest.
- OS file locking protects concurrent operations on a local filesystem. This is not a distributed lock or network registry protocol.
- The historical suite is only as strong as the tests and contracts stored in earlier accepted versions. It does not prove semantic equivalence for all possible inputs.

## Main limitations and V0.3 research questions

1. **Repair coverage:** extend from one deterministic pattern to a diagnosis taxonomy, while requiring evidence-backed patches.
2. **Patch quality:** generate candidate patches from richer execution traces and compare multiple hypotheses without allowing arbitrary code execution.
3. **Property-based tests:** infer invariants and metamorphic properties from contracts and successful trajectories.
4. **Transfer testing:** evaluate across held-out task families, tool adapters, input distributions, and execution environments.
5. **Skill dependency graph:** identify downstream skills and pipelines affected by a changed skill, then run impact-scoped regression tests.
6. **Human approval policy:** add configurable approval thresholds for patches with broad side effects.
7. **External benchmarks:** add adapters for SkillFlow, SkillLearnBench, and AFTER; report benchmark versions and exact splits.

## Research positioning

V0.2 does not claim novelty for skill compilation, skill memory, generic patch generation, semantic versioning, or regression testing as isolated ideas. Its current contribution is an integrated, auditable prototype that connects a constrained evidence-driven repair patch to immutable skill versions, historical contract-aware regression, and rollback. Whether this integration or future algorithms are novel requires a deeper literature and patent review plus comparative experiments.
