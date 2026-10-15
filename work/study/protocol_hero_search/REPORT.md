# Measured reservoir shape search

**0 of the two final candidates qualify.** The fixed-hardware search, floating-point qualification, and integer replay are separate results.

## Two strongest measured candidates

| Shape | Allocation | Why it advanced | Qualification |
| --- | --- | --- | --- |
| stack3_registered_64 | 24 → 20 → 20 | Development-only weakest-profile ranking after six-seed continuation | not qualified |
| stack2_registered_64 | 32 → 32 | Development-only weakest-profile ranking after six-seed continuation | not qualified |

These are fully trained sparse recurrent networks inspired by reservoir computing. The broad search also includes fixed-reservoir, readout-only ESN controls. Each physical mask, input route, activation, readout and schedule remains identical across protocol configurations. Learned weights are demonstration configurations.

## Fresh confirmation

Pass counts below require the entire profile suite, including all timing conditions, malformed/background rejection and startup/recovery. The gate is at least five of six seeds for **every** profile. Message exactness includes frame/transaction boundaries; boundaries are compared at exact causal reference ticks, with no tolerance added after seeing results.

| Shape | Profile | Float passing seeds / 6 | Fixed-point passing seeds / 6 | No-recurrence control / 1 |
| --- | --- | ---: | ---: | ---: |
| stack3_registered_64 | uart_n | 0 | 0 | 0 |
| stack3_registered_64 | uart_e | 0 | 0 | 0 |
| stack3_registered_64 | i2c | 6 | 6 | 0 |
| stack3_registered_64 | spi0 | 4 | 4 | 1 |
| stack3_registered_64 | spi1 | 0 | 0 | 0 |
| stack3_registered_64 | spi2 | 5 | 5 | 1 |
| stack3_registered_64 | spi3 | 0 | 0 | 1 |
| stack2_registered_64 | uart_n | 0 | 0 | 0 |
| stack2_registered_64 | uart_e | 0 | 0 | 0 |
| stack2_registered_64 | i2c | 5 | 5 | 0 |
| stack2_registered_64 | spi0 | 4 | 4 | 1 |
| stack2_registered_64 | spi1 | 2 | 2 | 0 |
| stack2_registered_64 | spi2 | 6 | 6 | 1 |
| stack2_registered_64 | spi3 | 0 | 0 | 1 |

Unmet five-of-six requirements:

- **stack3_registered_64**: uart_n (0/6), uart_e (0/6), spi0 (4/6), spi1 (0/6), spi3 (0/6).
- **stack2_registered_64**: uart_n (0/6), uart_e (0/6), spi0 (4/6), spi1 (2/6), spi3 (0/6).

| Shape | Profile | Exact-message accuracy range across valid conditions and seeds |
| --- | --- | ---: |
| stack3_registered_64 | uart_n | 0.00%–0.60% |
| stack3_registered_64 | uart_e | 0.00%–1.20% |
| stack3_registered_64 | i2c | 100.00%–100.00% |
| stack3_registered_64 | spi0 | 46.50%–100.00% |
| stack3_registered_64 | spi1 | 0.40%–100.00% |
| stack3_registered_64 | spi2 | 0.20%–100.00% |
| stack3_registered_64 | spi3 | 0.30%–100.00% |
| stack2_registered_64 | uart_n | 0.00%–0.00% |
| stack2_registered_64 | uart_e | 0.00%–0.00% |
| stack2_registered_64 | i2c | 0.00%–100.00% |
| stack2_registered_64 | spi0 | 4.10%–100.00% |
| stack2_registered_64 | spi1 | 0.40%–100.00% |
| stack2_registered_64 | spi2 | 100.00%–100.00% |
| stack2_registered_64 | spi3 | 0.30%–100.00% |

Detailed per-condition counts, failed seeds, exact-message rates, boundary errors and accepted-invalid counts are in [per_condition.csv](runs/run01/per_condition.csv). Every condition retains its complete prediction trace and accepted/expected message records under `runs/run01/confirmation/`.

Each valid timing condition contains at least 1,000 complete messages. Every condition includes all byte values, 0x00/0xff/0x55/0xaa, random payloads and a 1,024-byte message. UART covers nominal, ±3%, bounded one-tick edge jitter, combined corners and gaps. I2C covers duty, pauses/stretching and repeated START, with read/write direction, ninth-clock ACK/NACK and additional address/write NACK examples. SPI covers modes 0–3, duty, pauses and one-tick setup. Invalid/partial transfers and break/parity/framing recovery are separate.

The ambiguous prefix after midstream startup is measured but is not required to be rejected: it can be indistinguishable from valid traffic. Qualification resumes after an observable synchronization opportunity. Long idle and cold startup are retained; no between-message state reset is supplied.

## Training adequacy and limits

The screen completed 1134 fits across 27 physical shapes (six families, with current/registered scheduling variants), 32/48/64 nodes, three seeds, seven profiles and two training regimes. Every fit received 60 epochs: the requested initial 30 plus a matched extra block before ranking. 1111 screening fits remained improving and are explicitly **training-limited**, not architectural failures.

Four shapes advanced to six seeds (11,29,47,71,101,131), totaling 168 finalist fits. Finalist runs reached 240–3840 epochs. Continuation used the requested message/boundary/loss improvement rule, then two stale blocks, lower-learning-rate continuation and a 1,024-tick window rescue. A recorded plateau is a plateau of this recipe and corpus, **not proof that the architecture lacks capacity**.

Training uses three fixed, independently seeded continuous curricula of at least 8,192 ticks per profile. The first five epochs use clean short traffic, the next five repeated patterns, and all remaining epochs the mixed distribution. This is a modest training corpus; repeated epochs do not equal fresh examples. Exposure counts and optimizer steps are retained in each checkpoint. Training never uses confirmation payloads or boundaries. Larger/diversified training data remain a possible remedy; no architectural impossibility claim is made.

Checkpoint selection uses complete development messages, then boundary errors, false accepted messages, false events, and loss. Development selection sees about 8,192 ticks per profile; this small development sample is a limitation. Every epoch, including worse checkpoints, is retained with Adam moments and ending recurrent state. States and feature ages continue through messages and truncations; each independent epoch stream begins cold.

## Timing, resources and configurations

| Shape | Nodes | Weights + biases | Input / registered / same-tick edges | MACs per tick | Q12 model bytes | Tanh evaluations / tick |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| stack3_registered_64 | 64 | 1086 | 216 / 416 / 0 | 1016 | 2300 | 64 |
| stack2_registered_64 | 64 | 1126 | 288 / 384 / 0 | 1056 | 2380 | 64 |

These counts exclude no reservoir branch. The full [cost ledger](runs/run01/costs.json) separately lists leaks, state banks, preprocessing, pulse register, lane mapping, shared divider, accumulator width, activation scheduling and assembly storage. The Q12 activation table adds 8,194 bytes if stored literally. The Python assembler is not synthesized; its buffer/control area is unmeasured, so model parameter counts are not total chip area.

Fixed-point replay uses signed Q3.12 weights/states, integer Q24 accumulation in 64-bit accumulators, specified nearest rounding and a 4,097-entry Q12 tanh table. It is independently checked against scalar integer calculations. This is simulation evidence, not RTL, post-route timing or electrical qualification. `clock_hz` remains 0.

Observation and decision ticks are explicit in the event interface. There is no look-ahead or decision buffer. UART labels sample at offsets 7,23,… from a visible start edge. I2C commits bits on the falling edge ending the high phase; that includes a high-phase delay from the preceding rising-edge observation. Current-layer computation requires sequential within-tick activation stages; registered layers use the preceding tick. Physical decision time depends on an unimplemented schedule/clock and is not measured in seconds.

Exact masks, node leaks, allocations and demonstration weights are in [demonstration_configs](runs/run01/demonstration_configs/). Seed 11 is provided consistently rather than chosen to conceal seed failures. All six seeds remain under `models/`.

![stack3_registered_64 connection diagram](runs/run01/figures/stack3_registered_64_connections.png)

![stack2_registered_64 connection diagram](runs/run01/figures/stack2_registered_64_connections.png)

![UART learning curves](runs/run01/figures/uart_learning_curves.png)

## Audits and deferred work

Artifact verification: PASS; 444960 checkpoints checked; 10087 pre-existing files checked for preservation. Analytic gradients were checked numerically for every schedule. Causal prefix, online/batch state, repeated-bit occurrence, every-byte corner cases, malformed recovery, integer replay, and exact epoch-59→60 continuation checks passed. Fresh per-configuration replay audits accompany confirmation results.

The [diagnostics](runs/run01/diagnostics.json) report memory gradients through 16/64/176/512/1024 ticks and close states with conflicting labels. These diagnose fitted configurations; small gradients or near-collisions alone do not prove an architectural information bound. No-recurrence controls remove within-layer recurrent weights while retaining inter-layer routes, generic edge-age preprocessing and leak state; they are not memoryless classifiers.

Pre-training generator/reference failures are preserved in [HARNESS_FAILURES.md](HARNESS_FAILURES.md). The earlier UART/I2C studies and unrelated working-tree changes remain intact. No reference-design gate or specification was changed.

USB low-speed and 10BASE-T are **not attempted** because mandatory qualification was not achieved; both are untested scope, not failed architectures. The 20–24-node successful-family reduction is deferred because no family met the mandatory multi-protocol gate. No 72-node comparison was authorized by the required specific 64-node memory diagnosis, so none was substituted for adequate training.

## Reproduce

From the repository root, use a fresh output directory (never overwrite this run):

```sh
export OPENBLAS_NUM_THREADS=1
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/protocol_hero_search/runs/reproduction01
$PY -B -m work.study.protocol_hero_search.run generate --output "$OUT"
$PY -B -m unittest work.study.protocol_hero_search.test_experiment -v
$PY -B -m work.study.protocol_hero_search.run screen --output "$OUT" --workers 8
$PY -B -m work.study.protocol_hero_search.run select --output "$OUT"
$PY -B -m work.study.protocol_hero_search.run finalists --output "$OUT" --workers 8
$PY -B -m work.study.protocol_hero_search.validation continuation --output "$OUT"
$PY -B -m work.study.protocol_hero_search.evaluation freeze --output "$OUT"
$PY -B -m work.study.protocol_hero_search.evaluation generate --output "$OUT"
$PY -B -m work.study.protocol_hero_search.evaluation evaluate --output "$OUT" --workers 8
$PY -B -m work.study.protocol_hero_search.evaluation diagnostics --output "$OUT"
$PY -B -m work.study.protocol_hero_search.validation verify --output "$OUT"
$PY -B -m work.study.protocol_hero_search.report --output "$OUT"
```

Python/NumPy, a C++17 compiler and Matplotlib are required. Compilation uses double arithmetic without fast-math. Dataset, topology, weight and selection hashes are retained. CPU/compiler differences may prevent bitwise identity; the tests and full confirmation remain required. See [the supplied plan](PLAN.md), [research rationale](RESEARCH.md), and [protocol source/profile details](PROFILES.md).

## Failure interpretation and explicit seed lists

See [the failure detail](runs/run01/FINDINGS.md) for every failed seed, the failing conditions, representative traces, and the distinction between learned-configuration failures and architectural limits.
