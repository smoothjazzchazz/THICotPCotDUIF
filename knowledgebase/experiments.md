# Experimental scope

This fork's scope amendment, 6 October 2026. v0.3 as amended by v0.31 remains the reference design. This page decides which of its choices an experiment may challenge. It takes precedence over mechanism restrictions in the pitch documents and knowledgebase for experimental work. It does not select a replacement chip architecture.

**Experiments may challenge any architectural choice. Adopting their results into the reference design is a separate decision.** Agents may make those departures within an assigned experiment without asking for permission for each one.

## What stays

The project is a configurable waveform translator: recognize shapes arriving over time and produce timed responses, with new behavior supplied as configuration, weights, tables, or firmware. A useful experiment must answer a question about that system. Familiar protocols remain eventual coverage requirements; a focused experiment need not implement them all or build the whole translator.

- **Causality.** Online decisions use only information available at that time. Labels may train or score a model; future samples and generator-supplied boundaries may not guide inference. State any assumed clock, delimiter, reset, or training support.
- **Unknown input.** Measure rejection and false known events separately from recognition. The unknown indication need not be class 7.
- **Time.** Define sampling, decision time, timestamp meaning, and response latency. Include preprocessing and buffering in the cost of a decision.
- **Resources.** Keep a path toward the project's 6×4 target. Account for state, parameters, computation, and scheduling. Larger or floating-point models may establish a useful comparison; label them as such until implementation cost is checked.
- **Evidence.** Keep reproducible settings and failed trials. Distinguish measured behavior, estimates, and proposals. Existing rules for electrical, silicon, timing, and proof claims still apply.

## What may change

These are reference-design choices, not experimental limits:

| Part | Permitted experiments |
| --- | --- |
| Input representation | Different conditioning, temporal encoders, timing measurements, lane arrangements, normalization, and sample- or event-driven updates |
| Memory and computation | Different reservoir sizes, precision, topology, dynamics, timescales, explicit memory, or architectures with no recurrent reservoir |
| Readout and learning | Different features, classifiers, rejection rules, training methods, and causal adaptation |
| Internal interfaces | Different class counts, timestamp formats, confidence, partial observations, decision triggers, buffering, or stabilization |
| System organization | One listener, several listeners, cascades, or a unified receiver; different controllers, firmware responsibilities, transmit engines, and response paths |
| Pin access | Modeled direct access or bypass paths, and different output ownership or arbitration, with timing and conflicts made explicit |

The existing emulator, receiver API, two-listener arrangement, and mandatory reservoir are available comparisons. An experiment need not import their code or preserve their structure. Earlier versions and archived studies may supply ideas without becoming the design to ship. A reservoir must earn its place through useful behavior; removing it is an admissible result.

## How to work

Put each experiment in a descriptive folder under `work/study/`. It may contain its own receiver and complete system model. Preserve the reference model and historical reports unless the task explicitly includes changing them. Synthesizable RTL still follows the `src/` placement and frozen-template rules.

Start with a short README: the question, departures from the reference, assumptions, comparison, and success criteria. Record configs, seeds, source hashes, and commands with the results. No separate design approval or new spec version is needed to try an architecture inside this scope.

Use common inputs and scoring when comparing candidates. If their interfaces differ, compare the resulting waveform behavior and account for adapters. Choose settings on development data before evaluating fresh held-out data. Report relevant failures by condition, including rejection, recovery, latency, and cost. A narrow diagnostic may test one property; say which system questions it leaves open.

## What a result changes

An experiment may recommend a different total architecture, or reject every candidate. It need not preserve both listeners, produce a hero shape, or defend the reference design. Its local success criteria do not pass a project gate.

Changing the reference design itself follows [versioning.md](versioning.md): record the selected change in a new delta, update the contracts, and identify the integration and verification work. Until that adoption, [architecture.md](architecture.md) and [phases.md](phases.md) describe the reference implementation and its gates. Experimental findings are evidence for that decision.
