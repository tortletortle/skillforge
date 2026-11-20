"""Budgeted multi-hypothesis coverage search over a fixed patch frontier.

Scores are heuristic, not calibrated probabilities. No oracle/held-out inputs.
"""
from __future__ import annotations
import json
from typing import Any

POLICIES = ('egrs', 'coverage', 'diversity', 'full', 'cardinality')


def locus(cause):
    # Multiple hypotheses explaining the same output compete for coverage credit.
    return ('output', cause['output_name']) if cause.get('output_name') else ('step', cause.get('step_id') or cause['id'])


def edits(candidate):
    return frozenset(json.dumps(x, sort_keys=True, ensure_ascii=False) for x in candidate['patch']['operations'] if x['op'] != 'add_test')


def similarity(a, b):
    return len(a & b) / max(1, len(a | b))


class CoverageSearch:
    def __init__(self, ranked, diagnosis, *, policy='full', coverage_weight=.65, diversity_weight=.25):
        if policy not in POLICIES:
            raise ValueError(f'unknown policy: {policy}')
        self.policy = policy
        self.coverage_weight = coverage_weight if policy in ('coverage', 'full') else 0.
        self.diversity_weight = diversity_weight if policy in ('diversity', 'full') else 0.
        self.items = list(ranked)
        ids = [x['candidate']['candidate_id'] for x in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate candidate IDs')
        self.causes = {c['id']: c for c in diagnosis.get('root_causes', []) if c.get('repairable')}
        self.weights = {}
        for c in self.causes.values():
            key = locus(c)
            self.weights[key] = max(self.weights.get(key, 0.), float(c.get('confidence', 0.)))
        self.seen = []
        self.pending = None
        self.features = {}
        for i, item in enumerate(self.items):
            c = item['candidate']; links = [self.causes[k] for k in c.get('root_cause_ids', []) if k in self.causes]
            groups = {locus(x) for x in links}
            coverage = sum(self.weights[k] for k in groups) / max(1e-9, sum(self.weights.values()))
            # Ordinal normalization avoids interpreting the frozen synthetic ranker as calibrated.
            prior = 1. - i / max(1, len(self.items)-1)
            self.features[c['candidate_id']] = (prior, coverage, edits(c), len(groups))

    def select(self):
        if self.pending is not None:
            raise RuntimeError('observe previous attempt before selecting again')
        if not self.items:
            return None
        def scored(item):
            key = item['candidate']['candidate_id']; prior, coverage, signature, count = self.features[key]
            # Negative feedback discourages near-duplicates of unsuccessful edits.
            redundancy = max((similarity(signature, s) for s in self.seen), default=0.)
            score = ((1-self.coverage_weight)*prior + self.coverage_weight*coverage - self.diversity_weight*redundancy)
            if self.policy == 'cardinality':
                score = coverage
            return score, prior, coverage, redundancy
        best = max(self.items, key=lambda item: (scored(item)[0], scored(item)[1]))
        score, prior, coverage, redundancy = scored(best)
        self.items.remove(best)
        self.pending = best['candidate']['candidate_id']
        return {**best, 'search_score':score, 'coverage':coverage, 'redundancy':redundancy, 'search_policy':self.policy}

    def observe(self, candidate_id, *, eligible):
        if candidate_id != self.pending or self.pending is None:
            raise ValueError('feedback must correspond to the selected candidate')
        if not eligible:
            self.seen.append(self.features[candidate_id][2])
        self.pending = None
