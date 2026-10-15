# Per-condition confirmation counts

All configurations were frozen before these continuous streams were generated. Known timing tuples had additionally been enumerated by the disclosed preconfirmation interval audit; fresh evidence is scoped to stream mixtures and reserved unknown mechanisms. No thresholds were revised from these results.

Correct = correctly classified known cases. Reject = explicit unknown cases. False = known events on unknown input. Miss = no observation/event at all; an incorrectly rejected known is reported separately. Counts describe this finite synthetic suite.

## gap_order/reservoir3

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 15 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 55}; response sample mismatches: 0.

[Full counts and event details](gap_order/reservoir3/heldout.json); [startup details](gap_order/reservoir3/startup.json).

## gap_order/ring16

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 14 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 54}; response sample mismatches: 0.

[Full counts and event details](gap_order/ring16/heldout.json); [startup details](gap_order/ring16/startup.json).

## gap_order/run_history

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 56}; response sample mismatches: 0.

[Full counts and event details](gap_order/run_history/heldout.json); [startup details](gap_order/run_history/startup.json).

## gap_order/sample12

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 1 | 15 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': None, 'mean': None, 'min': None, 'n': 0}; response sample mismatches: 0.

[Full counts and event details](gap_order/sample12/heldout.json); [startup details](gap_order/sample12/startup.json).

## gap_order/sample64

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 5 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 14 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 12 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 39}; response sample mismatches: 0.

[Full counts and event details](gap_order/sample64/heldout.json); [startup details](gap_order/sample64/startup.json).

## gap_order/sparse16

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 15 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 55}; response sample mismatches: 0.

[Full counts and event details](gap_order/sparse16/heldout.json); [startup details](gap_order/sparse16/startup.json).

## gap_order/stream_intervals

Local criteria: **pass**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 72}; response sample mismatches: 0.

[Full counts and event details](gap_order/stream_intervals/heldout.json); [startup details](gap_order/stream_intervals/startup.json).

## gap_order/stream_templates

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 56}; response sample mismatches: 0.

[Full counts and event details](gap_order/stream_templates/heldout.json); [startup details](gap_order/stream_templates/startup.json).

## pulse_order/reservoir3

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 15 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 55}; response sample mismatches: 0.

[Full counts and event details](pulse_order/reservoir3/heldout.json); [startup details](pulse_order/reservoir3/startup.json).

## pulse_order/ring16

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 8 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 4 | 0 | 12 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 5 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 3 | 0 | 13 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 3 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 23}; response sample mismatches: 0.

[Full counts and event details](pulse_order/ring16/heldout.json); [startup details](pulse_order/ring16/startup.json).

## pulse_order/run_history

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 9 | 0 | 7 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 65}; response sample mismatches: 0.

[Full counts and event details](pulse_order/run_history/heldout.json); [startup details](pulse_order/run_history/startup.json).

## pulse_order/sample12

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 5 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 4 | 4 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 6 | 2 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 6 | 2 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 0 | 8 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 61}; response sample mismatches: 0.

[Full counts and event details](pulse_order/sample12/heldout.json); [startup details](pulse_order/sample12/startup.json).

## pulse_order/sample64

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': None, 'mean': None, 'min': None, 'n': 0}; response sample mismatches: 0.

[Full counts and event details](pulse_order/sample64/heldout.json); [startup details](pulse_order/sample64/startup.json).

## pulse_order/sparse16

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 1 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 5 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 5 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 15}; response sample mismatches: 0.

[Full counts and event details](pulse_order/sparse16/heldout.json); [startup details](pulse_order/sparse16/startup.json).

## pulse_order/stream_intervals

Local criteria: **pass**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 72}; response sample mismatches: 0.

[Full counts and event details](pulse_order/stream_intervals/heldout.json); [startup details](pulse_order/stream_intervals/startup.json).

## pulse_order/stream_templates

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 16 | 1 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 57}; response sample mismatches: 0.

[Full counts and event details](pulse_order/stream_templates/heldout.json); [startup details](pulse_order/stream_templates/startup.json).

## relative_order/reservoir3

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 2 | 0 | 14 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 10 | 0 | 22 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 8 | 0 | 24 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 2 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 22}; response sample mismatches: 0.

[Full counts and event details](relative_order/reservoir3/heldout.json); [startup details](relative_order/reservoir3/startup.json).

## relative_order/ring16

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 3 | 0 | 13 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 13 | 0 | 19 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 16 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 36}; response sample mismatches: 0.

[Full counts and event details](relative_order/ring16/heldout.json); [startup details](relative_order/ring16/startup.json).

## relative_order/run_history

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 1 | 0 | 31 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 0 | 8 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 89}; response sample mismatches: 0.

[Full counts and event details](relative_order/run_history/heldout.json); [startup details](relative_order/run_history/startup.json).

## relative_order/sample12

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 8 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 8 | 0 | 24 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 8 | 0 | 24 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 4 | 3 | 25 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 3 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 7 | 1 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 6 | 2 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 31}; response sample mismatches: 0.

[Full counts and event details](relative_order/sample12/heldout.json); [startup details](relative_order/sample12/startup.json).

## relative_order/sample64

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 7 | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 7 | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 2 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 16}; response sample mismatches: 0.

[Full counts and event details](relative_order/sample64/heldout.json); [startup details](relative_order/sample64/startup.json).

## relative_order/sparse16

Local criteria: **fail**; separate startup/recovery: **fail**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 4 | 0 | 12 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 13 | 0 | 19 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 16 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 37}; response sample mismatches: 0.

[Full counts and event details](relative_order/sparse16/heldout.json); [startup details](relative_order/sparse16/startup.json).

## relative_order/stream_intervals

Local criteria: **pass**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 120}; response sample mismatches: 0.

[Full counts and event details](relative_order/stream_intervals/heldout.json); [startup details](relative_order/stream_intervals/startup.json).

## relative_order/stream_templates

Local criteria: **fail**; separate startup/recovery: **pass**.

| Condition | Known | Correct | Wrong class | Rejected known | Unknown | Reject | False | Miss | Duplicates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| known_back_to_back | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_clean | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_glitch | 32 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| known_jitter | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 0 |
| recovery_known | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unknown_extra_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_junk | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_delimiter | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_missing_edges | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_near_long | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_out_of_scale | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_partial | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_prefix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_count | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_duration | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_prefix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_same_suffix | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| unknown_suffix_splice | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |

Background known/unknown events: 0/0; decision-end latency on matched known: {'max': 21, 'mean': 21, 'min': 21, 'n': 88}; response sample mismatches: 0.

[Full counts and event details](relative_order/stream_templates/heldout.json); [startup details](relative_order/stream_templates/startup.json).

