"""Interpretable IMU features; units and ordering form a versioned contract."""
import math
import statistics

AXES = ("ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps")
CHANNELS = (*AXES, "acc_magnitude_g", "gyro_magnitude_dps")
STATS = ("mean", "std", "min", "max", "rms", "median", "iqr")
PAIRS = ((0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5))
FEATURE_NAMES = tuple(f"{channel}_{stat}" for channel in CHANNELS for stat in STATS) + (
    "duration_s", "acc_jerk_rms_g_s", *(f"corr_{AXES[a]}_{AXES[b]}" for a, b in PAIRS))


def quantile(values, fraction):
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (index - lower) * (ordered[upper] - ordered[lower])


def extract_features(sequence, duration_s):
    if len(sequence) < 2 or not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("Features require at least two points and positive duration")
    if any(len(row) != 6 or not all(math.isfinite(x) for x in row) for row in sequence):
        raise ValueError("Features require six finite channels")
    channels = [list(channel) for channel in zip(*sequence)]
    channels.extend([[math.sqrt(sum(x*x for x in row[start:start+3])) for row in sequence]
                     for start in (0, 3)])
    features = []
    for values in channels:
        features.extend([statistics.fmean(values), statistics.pstdev(values), min(values), max(values),
                         math.sqrt(statistics.fmean(x*x for x in values)), statistics.median(values),
                         quantile(values, .75) - quantile(values, .25)])
    step = duration_s / (len(sequence) - 1)
    jerk_squared = [sum(((b[i] - a[i]) / step)**2 for i in range(3))
                    for a, b in zip(sequence, sequence[1:])]
    features.extend([duration_s, math.sqrt(statistics.fmean(jerk_squared))])
    for a, b in PAIRS:
        mean_a, mean_b = statistics.fmean(channels[a]), statistics.fmean(channels[b])
        da, db = [x - mean_a for x in channels[a]], [x - mean_b for x in channels[b]]
        denominator = math.sqrt(sum(x*x for x in da) * sum(x*x for x in db))
        correlation = sum(x*y for x, y in zip(da, db)) / denominator if denominator else 0.0
        features.append(max(-1.0, min(1.0, correlation)))
    if not all(math.isfinite(x) for x in features):
        raise ValueError("Non-finite feature calculation")
    return features
