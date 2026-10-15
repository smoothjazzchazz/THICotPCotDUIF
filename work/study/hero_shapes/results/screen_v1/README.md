# Retained first development screen

This directory is a failed development trial, not held-out confirmation.
Twenty-one shape/architecture combinations and every rejection setting remain.
Only the percentage-error streaming template on pulse order met the initial
development sample criteria. An independent audit then demonstrated that its
loaded threshold accepted an unfamiliar longest run changed by two ticks, outside
the waveform vocabulary's declared one-tick tolerance. Gap order had the same
rejection hole. See `audit/hero_shapes_audit_screen_v1_templates.json`.

The second screen retains those models, adds `unknown_near_long` to development,
and adds an absolute-tick-error streaming template variant as the eighth setting.
This revision happened before any final confirmation; no held-out data motivated
it. All first-screen input samples and fitted configurations remain here.

The source hash guard correctly refused a freeze because the stimulus author had
corrected held-out scale metadata while screening ran. No held-out samples had
been generated. The two metadata edits were reversed in `source_at_screen/`;
every archived Python file now matches `screen_manifest.json` exactly. That
archive is the source used for this screen, not the revised live implementation.
No first-screen measurements have been overwritten or called confirmation.

Original command, from the repository root:

```sh
python3 -B -m work.study.hero_shapes.run_study screen --output work/study/hero_shapes/results/screen_v1
```

To replay the old implementation independently, enter `source_at_screen/` and
run its module with a new output directory beneath its own `work/study/`.
