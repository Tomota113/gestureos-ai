"""Deterministic grouped split using only identities and labels, never signals."""
from collections import Counter
import random

PARTITIONS = ("train", "validation", "test")


def group_key(entry, group_by):
    if group_by == "subject":
        return (entry["subject_id"],)
    if group_by == "session":
        return (entry["subject_id"], entry["session_id"])
    raise ValueError("group_by must be session or subject")


def grouped_split(entries, labels, *, group_by="session", seed=42, attempts=512):
    if not entries:
        raise ValueError("No eligible captures")
    if type(seed) is not int or type(attempts) is not int or not 1 <= attempts <= 10000:
        raise ValueError("Seed must be an integer; attempts must be 1..10000")
    for field in ("capture_id", "content_sha256"):
        if len({e[field] for e in entries}) != len(entries):
            raise ValueError(f"Duplicate {field} in split input")
    if any(e.get("source_kind") != "hardware" for e in entries):
        raise ValueError("Only original hardware captures may enter partitions")
    labels = set(labels)
    if not labels or any(e["label"] not in labels for e in entries):
        raise ValueError("Invalid or inconsistent taxonomy")
    groups = {}
    for entry in sorted(entries, key=lambda e: e["capture_id"]):
        groups.setdefault(group_key(entry, group_by), []).append(entry)
    if len(groups) < 3:
        raise ValueError(f"Need at least 3 independent {group_by} groups; found {len(groups)}")
    for label in sorted(labels):
        available = sum(any(e["label"] == label for e in group) for group in groups.values())
        if available < 3:
            raise ValueError(f"Label {label!r} needs at least 3 {group_by} groups; found {available}")
    held_out = max(1, round(len(groups) * .2))
    sizes = (len(groups) - 2 * held_out, held_out, held_out)
    rng, best = random.Random(seed), None
    targets = (.6, .2, .2)
    totals = Counter(e["label"] for e in entries)
    for _ in range(attempts):
        keys = sorted(groups)
        rng.shuffle(keys)
        buckets, start = {}, 0
        for name, size in zip(PARTITIONS, sizes):
            buckets[name] = [e for key in keys[start:start + size] for e in groups[key]]
            start += size
        if any({e["label"] for e in bucket} != labels for bucket in buckets.values()):
            continue
        score = 0
        for name, target in zip(PARTITIONS, targets):
            counts = Counter(e["label"] for e in buckets[name])
            score += abs(len(buckets[name]) / len(entries) - target)
            score += sum(abs(counts[label] / totals[label] - target) for label in sorted(labels))
        candidate = {name: sorted(e["capture_id"] for e in bucket) for name, bucket in buckets.items()}
        if best is None or score < best[0]:
            best = score, candidate
    if best is None:
        raise ValueError("No split with every label in every partition found within search budget; "
                         "collect more diverse groups or review grouping; no random-row fallback")
    return {"group_by": group_by, "seed": seed, "search_attempts": attempts,
            "target_fractions": dict(zip(PARTITIONS, targets)), "partitions": best[1],
            "actual_counts": {k: len(v) for k, v in best[1].items()}}
