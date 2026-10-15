"""Frozen hero-shape definitions and deterministic offline stream annotations.

A run tuple alternates high/low durations, beginning and ending high. The online
receiver receives only ``samples``. Cases, class ids and generator boundaries are
used by fitting/scoring after inference, never to reset or trigger a stage.
"""

from hashlib import sha256
import random

from work.model.conditioning import InputConditioner


IDLE_TICKS = 20
NORMAL_GAP = 24
FAMILIES = {
    "pulse_order": {
        "templates": {0: (4, 4, 8, 4, 4), 1: (8, 4, 4, 4, 4)},
        "description": "The first two pulse widths swap; count, duration and final pulse agree.",
        "scales": (1,),
    },
    "gap_order": {
        "templates": {0: (4, 3, 4, 9, 4, 3, 4), 1: (4, 9, 4, 3, 4, 3, 4)},
        "description": "The long internal silence moves; pulse widths and final motif agree.",
        "scales": (1,),
    },
    "relative_order": {
        "templates": {0: (3, 3, 7, 3, 5), 1: (7, 3, 3, 3, 5)},
        "description": "Short/long pulse order at two loaded speeds with a common medium ending.",
        "scales": (1, 2),
    },
}
SPLITS = ("train", "dev", "heldout")
RESERVED_CONDITIONS = ("unknown_prefix_splice", "unknown_suffix_splice", "unknown_missing_delimiter")
RESERVED_RELATIVE_CONDITIONS = ("unknown_out_of_scale",)


def expand_runs(runs):
    """Expand a positive odd-length high/low duration sequence into binary samples."""
    runs = tuple(runs)
    if not runs or len(runs) % 2 != 1 or any(type(n) is not int or n < 1 for n in runs):
        raise ValueError("runs must be positive integer durations, beginning and ending high")
    return [int(index % 2 == 0) for index, n in enumerate(runs) for _ in range(n)]


def _runs(samples):
    """Return the high-to-high run representation, dropping only exterior lows."""
    if not any(samples):
        return ()
    start = samples.index(1)
    stop = len(samples) - samples[::-1].index(1)
    lengths = []
    previous = None
    for level in samples[start:stop]:
        if level != previous:
            lengths.append(1)
            previous = level
        else:
            lengths[-1] += 1
    return tuple(lengths)


def conditioned_runs(samples):
    """Offline collision audit using the actual shared two-sample conditioner."""
    conditioner = InputConditioner(stable_ticks=2)
    padded = [0] * NORMAL_GAP + list(samples) + [0] * NORMAL_GAP
    return _runs([conditioner.step(level).level for level in padded])


def known_matches(family, runs):
    """All known labels within the stipulated independent +/-1 tick tolerance."""
    result = []
    for class_id, template in FAMILIES[family]["templates"].items():
        for scale in FAMILIES[family]["scales"]:
            target = tuple(n * scale for n in template)
            if len(runs) == len(target) and all(abs(a - b) <= 1 for a, b in zip(runs, target)):
                result.append((class_id, scale))
    return result


def _jitter(runs, split, rng):
    # Hash the whole perturbation rather than taking one coordinate modulo 3;
    # each split sees both signs at every position, but no perturbation vector
    # is reused across fitting, selection and confirmation.
    while True:
        delta = tuple(rng.choice((-1, 0, 1)) for _ in runs)
        key = ",".join(map(str, delta)).encode("ascii")
        partition = int.from_bytes(sha256(key).digest()[:4], "big") % len(SPLITS)
        if any(delta) and partition == SPLITS.index(split):
            return tuple(n + d for n, d in zip(runs, delta)), delta


def _unknown(runs, condition, family, rng):
    """Transform a template; reject accidental overlap with any known envelope."""
    for attempt in range(200):
        candidate = list(runs)
        if condition == "unknown_same_suffix":
            candidate[0] += 3 + attempt % 4
        elif condition == "unknown_same_prefix":
            candidate[-1] += 3 + attempt % 4
        elif condition == "unknown_same_count":
            index = rng.choice(list(range(1, len(runs), 2)))
            candidate[index] += 3 + attempt % 4
        elif condition == "unknown_same_duration":
            source = rng.choice([i for i, n in enumerate(runs) if n >= 4])
            target = rng.choice([i for i in range(len(runs)) if i != source])
            candidate[source] -= 2
            candidate[target] += 2
        elif condition == "unknown_near_long":
            # Independent audit found that percentage tolerance can accept this
            # outside the declared +/-1-tick vocabulary. Kept in development.
            index = max(range(len(runs)), key=lambda i: runs[i])
            candidate[index] += rng.choice((-2, 2))
        elif condition == "unknown_missing_edges":
            index = rng.choice(list(range(1, len(runs), 2)))
            candidate[index - 1:index + 2] = [sum(candidate[index - 1:index + 2])]
        elif condition == "unknown_extra_edges":
            index = max(range(len(runs)), key=lambda i: runs[i])
            # The inserted two-tick opposite level survives conditioning.
            candidate[index:index + 1] = [2, 2, runs[index] - 4]
        elif condition == "unknown_partial":
            candidate = candidate[2:]
        elif condition == "unknown_junk":
            candidate = [rng.randint(2, 12) for _ in range(rng.choice((3, 9, 11)))]
        elif condition == "unknown_prefix_splice":
            candidate = [2 + attempt % 3, 2] + candidate
        elif condition == "unknown_suffix_splice":
            candidate += [2, 2 + attempt % 3]
        elif condition == "unknown_missing_delimiter":
            other = FAMILIES[family]["templates"][rng.choice((0, 1))]
            candidate += [rng.choice((10, 15, 19))] + list(other)
        elif condition == "unknown_out_of_scale":
            # Known scale support is explicitly the loaded discrete set {1,2},
            # not unrestricted ratios. This held-out structural challenge was
            # declared before freeze, after diagnosing scale-normalization loss.
            if family != "relative_order":
                raise ValueError("out-of-scale challenge is defined only for relative_order")
            candidate = list(runs)
        else:
            raise ValueError(condition)
        if min(candidate) < 2 or any(n >= IDLE_TICKS for n in candidate[1::2]):
            continue
        samples = expand_runs(candidate)
        observed = conditioned_runs(samples)
        if observed and not known_matches(family, observed):
            return samples, tuple(candidate)
    raise RuntimeError(f"could not make collision-free {condition} for {family}")


def _stream(family, split, seed):
    if family not in FAMILIES:
        raise ValueError(f"unknown family: {family}")
    return {
        "family": family,
        "split": split,
        "seed": seed,
        "samples": [],
        "cases": [],
        "unobservable_cases": [],
        "definitions": {
            "templates": {str(k): list(v) for k, v in FAMILIES[family]["templates"].items()},
            "scales": list(FAMILIES[family]["scales"]),
            "idle_ticks": IDLE_TICKS,
            "conditioning_stable_ticks": 2,
            "known_jitter_ticks": 1,
            "scale_scope": "Only the discrete loaded scales are known; other exact ratios are unfamiliar.",
            "end_tick_meaning": "raw final falling edge, exclusive waveform end",
            "case_window": "start_tick through end_tick + 22 inclusive",
            "jitter_partition": "SHA256 of entire perturbation vector modulo 3: train/dev/heldout",
            "label_collision_policy": "unknown conditioned runs must lie outside all known +/-1 envelopes; startup validity is separate",
        },
    }


def _append_case(stream, waveform, condition, class_id, nominal_class_id=None,
                 scale=None, gap=NORMAL_GAP, notes="", boundary_challenge=False,
                 startup_invalid=False, jitter_delta=None):
    waveform = list(waveform)
    if not waveform or waveform[0] != 1 or waveform[-1] != 1:
        raise ValueError("annotated case waveform must begin and end high")
    observed = conditioned_runs(waveform)
    matches = known_matches(stream["family"], observed)
    if class_id is None and matches and not startup_invalid:
        raise ValueError(f"unknown label collides with known conditioned waveform: {condition}")
    if class_id is not None and not any(match[0] == class_id for match in matches):
        raise ValueError(f"known label lost in conditioning: {condition}")
    start = len(stream["samples"])
    stream["samples"].extend(waveform)
    end = len(stream["samples"])
    stream["cases"].append({
        "id": f"{stream['family']}-{stream['split']}-{len(stream['cases']):03d}",
        "condition": condition,
        "start_tick": start,
        "end_tick": end,
        "class_id": class_id,
        "nominal_class_id": nominal_class_id,
        "scale": scale,
        "raw_runs": list(_runs(waveform)),
        "conditioned_runs": list(observed),
        "jitter_delta": list(jitter_delta) if jitter_delta is not None else None,
        "trailing_idle_ticks": gap,
        "boundary_challenge": boundary_challenge,
        "expected_valid_frame": not startup_invalid,
        "notes": notes,
    })
    stream["samples"].extend([0] * gap)


def _background_glitch(stream):
    start = len(stream["samples"])
    stream["samples"].extend([1] + [0] * NORMAL_GAP)
    stream["unobservable_cases"].append({
        "condition": "background_single_sample_glitch",
        "start_tick": start,
        "end_tick": start + 1,
        "reason": "The two-sample filter removes this pulse completely; expect no observation or event.",
    })


def build_stream(family, split, seed, repeats=None):
    """Build one continuous, once-reset stream; train has only known examples.

    Defaults yield 12/24 train, 34/46 development and 60/81 held-out cases
    (single-scale/two-scale). Seeds change perturbations, order and idle gaps.
    Exact clean templates deliberately recur, while jitter vocabularies and
    confirmation-only splice mechanisms stay separate.
    """
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    if repeats is None:
        repeats = 3 if split == "heldout" else 2
    if type(repeats) is not int or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    rng = random.Random(seed)
    stream = _stream(family, split, seed)
    stream["repeats"] = repeats
    stream["samples"].extend([0] * rng.randint(NORMAL_GAP, 45))
    templates = FAMILIES[family]["templates"]
    scales = FAMILIES[family]["scales"]
    for repeat in range(repeats):
        examples = []
        for class_id, nominal in templates.items():
            for scale in scales:
                runs = tuple(n * scale for n in nominal)
                examples.append(("known_clean", class_id, scale, expand_runs(runs), None))
                jitter_count = 2 if split == "train" else 1
                for _ in range(jitter_count):
                    jittered, delta = _jitter(runs, split, rng)
                    examples.append(("known_jitter", class_id, scale, expand_runs(jittered), delta))
                if split != "train":
                    waveform = expand_runs(runs)
                    eligible = [i for i, n in enumerate(runs) if n >= 5]
                    index = rng.choice(eligible)
                    flip = sum(runs[:index]) + rng.randint(2, runs[index] - 3)
                    waveform[flip] = 1 - waveform[flip]
                    if conditioned_runs(waveform) != runs:
                        raise AssertionError("glitch placement changed conditioned shape")
                    examples.append(("known_glitch", class_id, scale, waveform, None))
        rng.shuffle(examples)
        for condition, class_id, scale, waveform, delta in examples:
            _append_case(stream, waveform, condition, class_id, class_id, scale,
                         gap=rng.randint(NORMAL_GAP, 63), jitter_delta=delta,
                         notes="Interior single-sample flip is suppressed; the full shape survives." if condition == "known_glitch" else "")
        if split == "train":
            continue
        conditions = ["unknown_same_suffix", "unknown_same_prefix", "unknown_same_count",
                      "unknown_same_duration", "unknown_missing_edges", "unknown_extra_edges",
                      "unknown_partial", "unknown_junk", "unknown_near_long"]
        if split == "heldout":
            conditions.extend(RESERVED_CONDITIONS)
            if family == "relative_order":
                conditions.extend(RESERVED_RELATIVE_CONDITIONS)
        rng.shuffle(conditions)
        for condition in conditions:
            class_id = rng.choice((0, 1))
            scale = 3 if condition == "unknown_out_of_scale" else rng.choice(scales)
            runs = tuple(n * scale for n in templates[class_id])
            waveform, _ = _unknown(runs, condition, family, rng)
            _append_case(stream, waveform, condition, None, class_id, scale,
                         gap=rng.randint(NORMAL_GAP, 63),
                         notes="Two known shapes joined without an observable delimiter; one unknown combined burst." if condition == "unknown_missing_delimiter" else "")
            if condition == "unknown_junk":
                recovery_class = 1 - class_id
                recovery = tuple(n * scale for n in templates[recovery_class])
                _append_case(stream, expand_runs(recovery), "recovery_known", recovery_class,
                             recovery_class, scale, gap=rng.randint(NORMAL_GAP, 63))
        # A true minimum delimiter: conditioning shifts both surviving edges by
        # one tick. Completion of the first precedes the next conditioned rise.
        # Its broad scoring window overlaps the next raw onset by two ticks;
        # associate decisions with final-edge targets, not the most recent start.
        for class_id in (repeat % 2, 1 - repeat % 2):
            _append_case(stream, expand_runs(templates[class_id]), "known_back_to_back",
                         class_id, class_id, 1, gap=IDLE_TICKS if class_id == repeat % 2 else NORMAL_GAP,
                         boundary_challenge=True,
                         notes="Exactly twenty raw low samples separate this pair.")
        _background_glitch(stream)
    stream["samples"].extend([0] * NORMAL_GAP)
    return stream


def build_startup_streams(family, seed):
    """Separate once-reset starts with no trusted framing, then clean recovery."""
    rng = random.Random(seed)
    streams = []
    for mode in ("partial_high", "mid_low", "no_delimiter"):
        stream = _stream(family, f"startup_{mode}", seed)
        class_id = rng.choice((0, 1))
        template = FAMILIES[family]["templates"][class_id]
        if mode == "partial_high":
            partial = (max(2, template[0] // 2),) + template[1:]
            prefix = []
        elif mode == "mid_low":
            partial = template[2:]
            prefix = [0] * rng.randint(2, IDLE_TICKS - 1)
        else:
            partial = template
            prefix = [0] * (IDLE_TICKS - 1)
        stream["samples"].extend(prefix)
        _append_case(stream, expand_runs(partial), f"startup_{mode}", None,
                     class_id, 1, startup_invalid=True,
                     notes="No full delimiter has been observed since reset. Even template-like observed runs are invalid at startup.")
        for recovery_class in (0, 1):
            _append_case(stream, expand_runs(FAMILIES[family]["templates"][recovery_class]),
                         "startup_recovery_known", recovery_class, recovery_class, 1,
                         gap=NORMAL_GAP)
        stream["samples"].extend([0] * NORMAL_GAP)
        streams.append(stream)
    return streams


def nominal_diagnostic_pairs(family):
    """Clean known pairs and shared-summary unknowns for offline collision tests."""
    result = []
    for scale in FAMILIES[family]["scales"]:
        pair = {class_id: tuple(n * scale for n in template)
                for class_id, template in FAMILIES[family]["templates"].items()}
        result.append({"name": "known_equal_count_duration_common_suffix", "scale": scale,
                       "left_runs": list(pair[0]), "left_class_id": 0,
                       "right_runs": list(pair[1]), "right_class_id": 1})
        waveform, unknown = _unknown(pair[0], "unknown_same_duration", family, random.Random(17))
        result.append({"name": "unknown_equal_count_duration", "scale": scale,
                       "left_runs": list(pair[0]), "left_class_id": 0,
                       "right_runs": list(unknown), "right_class_id": None})
    return result
