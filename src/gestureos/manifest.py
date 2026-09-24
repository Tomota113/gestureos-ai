"""Revalidate a frozen split and load samples from the verified file snapshots."""
from pathlib import Path, PurePosixPath

from .dataset import fingerprint, load_capture, read_object, require
from .split import PARTITIONS, group_key


def load_manifest(path, collection_config, *, raw_root=None):
    manifest_bytes = Path(path).read_bytes()
    manifest = read_object(manifest_bytes)
    config_bytes = Path(collection_config).read_bytes()
    config = read_object(config_bytes)
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
            "Unsupported manifest schema")
    require(manifest.get("status") == "ready" and manifest.get("rejected") == [],
            "Only a ready manifest with no rejected captures can be used")
    require(manifest.get("config_sha256") == fingerprint(config_bytes),
            "Collection configuration changed since split creation")
    labels = manifest.get("labels")
    require(isinstance(labels, list) and labels and all(isinstance(x, str) for x in labels)
            and len(set(labels)) == len(labels) and labels == config.get("labels"),
            "Manifest label order or taxonomy differs from collection configuration")
    root = Path(raw_root if raw_root is not None else manifest["raw_root"]).resolve()
    require(root.is_dir(), "RAW root is missing; supply --raw-root if dataset moved")
    entries = manifest.get("captures")
    require(isinstance(entries, list) and entries, "Manifest contains no captures")
    validated, rows_by_id, signal_hashes = {}, {}, set()
    for saved in entries:
        require(isinstance(saved, dict) and isinstance(saved.get("path"), str), "Invalid capture entry")
        relative = PurePosixPath(saved["path"])
        require(not relative.is_absolute() and len(relative.parts) == 3
                and not any(x in (".", "..") for x in relative.parts), "Unsafe capture path")
        current, rows = load_capture(root / saved["path"], root, labels, include_rows=True)
        require(current == saved, f"Capture changed since split: {saved['path']}")
        identity = current["capture_id"]
        require(identity not in validated and current["content_sha256"] not in signal_hashes,
                "Duplicate capture identity or signal in manifest")
        validated[identity], rows_by_id[identity] = current, rows
        signal_hashes.add(current["content_sha256"])
    split = manifest.get("split")
    require(isinstance(split, dict), "Missing split")
    grouping = split.get("group_by")
    require(grouping in ("session", "subject") and grouping == manifest.get("group_by"),
            "Inconsistent grouping strategy")
    require(type(split.get("seed")) is int and split["seed"] == manifest.get("seed"),
            "Inconsistent split seed")
    partitions = split.get("partitions")
    require(isinstance(partitions, dict) and set(partitions) == set(PARTITIONS), "Invalid partitions")
    seen_ids, seen_groups, counts = set(), set(), {}
    for name in PARTITIONS:
        ids = partitions[name]
        require(isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids),
                f"Empty or invalid {name} partition")
        require(len(set(ids)) == len(ids) and set(ids) <= validated.keys()
                and seen_ids.isdisjoint(ids), "Missing, repeated or unknown capture assignment")
        groups = {group_key(validated[i], grouping) for i in ids}
        require(seen_groups.isdisjoint(groups), "A subject/session group crosses partitions")
        require({validated[i]["label"] for i in ids} == set(labels), "Incomplete label coverage")
        seen_groups.update(groups)
        seen_ids.update(ids)
        counts[name] = len(ids)
    require(seen_ids == validated.keys() and counts == split.get("actual_counts"),
            "Split omits captures or reports inconsistent counts")
    return {"manifest": manifest, "manifest_sha256": fingerprint(manifest_bytes),
            "raw_root": str(root), "rows": rows_by_id}
