"""Keep the failed fresh pause result separate from its coverage intervention."""
import csv,json
from .run import ROOT,digest
from .train import write_json


def report():
    root=ROOT/'runs/connectivity01';rows=[]
    for file in sorted((root/'models/phase_clocked_pause_v20').glob('*/*/*/block_0012.json')):
        b=json.loads(file.read_text());history=[json.loads(line) for line in (file.parent/'history.jsonl').read_text().splitlines()];before=history[0];after=b['selected'];scan=json.loads((file.parent/'training_scan_0000.json').read_text())
        rows.append(dict(shape=b['shape'],profile=b['profile'],seed=b['seed'],rounds=b['epochs'],selected_epoch=b['selected_epoch'],exposure_ticks=b['exposure_ticks'],
                         before_training_errors=scan['canonical_errors'],after_training_errors=b['selected_training_scan']['canonical_errors'],
                         before_exact=before['exact_messages'],after_exact=after['exact_messages'],valid_messages=after['valid_messages'],
                         before_boundaries=before['boundary_errors'],after_boundaries=after['boundary_errors'],invalid_accepted=after['invalid_accepted'],background_accepted=after['background_accepted'],
                         full_training_closure=b['full_training_closure'],block=str(file),block_sha256=digest(file)))
    if rows:
        with (root/'clocked_pause_v20_trials.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# Clock-pause failures and independent coverage repair','',
           'The reduced-readout graph failed fresh confirmation A (`readout_cost_full_v3a`): SPI1 had only four passing seeds, despite all six passing its earlier development suite. SPI1 seed47 recovered997/1000 pause messages; seed101 recovered998/1000 with two missing STOP boundaries. SPI2 seed47 recovered988/1000 pause messages. Float and Q3.12 showed the same failures. All other fresh profiles met their required seed counts. The failed snapshot is retained and must be a regression in every retry.','',
           '## What the causal traces show','',
           'For each first failure, the dense and reduced graphs have exactly identical continuous48-state backbones. The dense head emits the correct event, while the reduced head misses a BIT0, misses STOP, or emits BIT0 one sample early. Diagnostic head predictions reproduce the saved frozen scalar predictions. This local result locates the difference in the nonlinear/output mapping; it does not establish inadequate recurrent memory or prove the reduced mapping can represent every required case.','',
           '![Identical backbone, missed STOP](runs/connectivity01/figures/pause_failure_v20_spi1_101.png)','',
           '[Three causal traces and exact margins](runs/connectivity01/pause_failure_diagnostic_v20.json). These confirmation states are read-only diagnostics and never enter fitting.','',
           '## Independent training intervention','',
           'Both graphs and all six seeds receive the same new SPI1/SPI2 waveform pool:4096 continuous pause messages and512 mixed messages, plus the14 original corrected corpora. Training uses family411000000 and profile/stream offsets; independent development uses family413000000 and adds1024 pause messages to the original suite. Payloads are checked against the independent waveform parser. No failed confirmation example is reused for training or selection.','',
           'Only the existing six affine output rows are fitted; every recurrent/input/hidden-head parameter, leak and physical edge stays fixed. Each round rescans every training tick, retains bounded worst-margin states by file/class, and preserves all previous constraints. The conditional program allows12 rounds of up to500 L-BFGS iterations, margin0.5, prior1e-6, trust±0.5 and absolute parameter bound7.99. A passing source with complete training-label closure is retained unchanged. Actual exposure therefore differs by seed and is reported.','',
           'Selection requires whole expanded development and prefers full training-label closure, then the original development key. That extra training audit cannot replace independent confirmation. Failed or still-improving fits remain training/recipe evidence, not architecture impossibility.','',
           f'Completed paired fits: {len(rows)}/24.','',
           '| Graph | Profile / seed | Rounds | Training label errors before → after | Expanded development exact before → after | Boundary errors before → after | Full training closure |',
           '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        lines.append(f"| {r['shape'].split('_readout16_')[-1]} | {r['profile']}/{r['seed']} | {r['rounds']} | {r['before_training_errors']} → {r['after_training_errors']} | {r['before_exact']} → {r['after_exact']}/{r['valid_messages']} | {r['before_boundaries']} → {r['after_boundaries']} | {r['full_training_closure']} |")
    lines+=['','[All selected fits and exposure](runs/connectivity01/clocked_pause_v20_trials.csv). Full per-file scans, scalar development cases, source hashes, checkpoints and raw learning curves are stored with every fit.','',
            'The practical threshold remains>=15% fewer MACs and parameters with comparable per-condition recovery in at least five paired seeds. Mandatory qualification still requires exact complete messages/boundaries, rejection/recovery/timing and at least five of six seeds per profile on fresh plus regression suites. The next freeze must preserve A as a regression and use an unused fresh family. QUALIFIED_SHAPES.md is the current qualification record.']
    verification=root/'reproductions/v20_spi1_seed47_01/reproduction_verification.json'
    if verification.exists():
        v=json.loads(verification.read_text());assert all(v[k] for k in ('weights_bitwise_equal','leaks_bitwise_equal','development_scores_equal','same_selected_epoch'))
        lines+=['','## Actual fitting reproduction','',
                'Reduced-readout SPI1 seed47 was rerun from its frozen source in a clean output directory. The full training-state scan, output fitting and scalar development produced bitwise-identical weights and leaks, the same selected epoch and identical development scores. Maximum weight difference was0. This repeats training from the retained source checkpoint; it is not new confirmation.','',
                '[Reproduction verification](runs/connectivity01/reproductions/v20_spi1_seed47_01/reproduction_verification.json). Use `reproduce_pause_job` with a nonexistent output directory to repeat it.']
    (ROOT/'CLOCKED_PAUSE_V20.md').write_text('\n'.join(lines)+'\n');print('Pause fits',len(rows),'/24',flush=True)


if __name__=='__main__':report()
