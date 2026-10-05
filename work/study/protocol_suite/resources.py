"""Whole-recognizer analytical counts, not synthesis/area/timing measurements."""
import math
import numpy as np
from .models import Features


def count(config, readout):
    model = Features(config)
    f,n,k = len(model.vector()),model.n,model.kind
    # 2 previous 2-lane samples, prev packed level, 8-bit saturating run counter,
    # armed bit, 16-bit modulo study timestamp, output class/stamp/valid register,
    # plus four estimated synchronizer flops (not simulated on sampled inputs).
    common_state = 4+2+8+1+16+20+4
    # Quiet setting, filter enable. No RX FIFO, synchronizer or analog pad model.
    configuration = 8+1
    topo = 0
    if k == "sample":
        state = 2*n + math.ceil(math.log2(n+1))
        state_ops = {"sample_bit_moves":2*n}
        bound = np.ones(f,dtype=np.int64)
    elif k == "run":
        state = n*7+math.ceil(math.log2(n+1))
        if config.get("guard"):
            state += 8+5+5
            configuration += 2*8+2*5
        if model.binary_runs:
            state = n*(2+len(config["thresholds"]))+math.ceil(math.log2(n+1))+(18 if config.get("guard") else 0)
            bound = np.ones(f,dtype=np.int64)
            configuration += 5*len(config["thresholds"])
        else:
            basebound = np.tile([4,4,27],n)
            bound = [basebound*4]
            if len(model.pairs):
                bound.extend([basebound[model.pairs[:,0]]*basebound[model.pairs[:,1]],np.full(n,27**2)])
            bound = np.concatenate(bound)
        state_ops = {"run_bit_moves_per_transition":7*n,"run_counter_increment_per_sample":1,
                     "signal_derived_history_clear":True}
    elif k == "recurrent":
        state = 6*n
        topo = n*(3*(math.ceil(math.log2(n))+1)+2*(3+1)+3)+3
        bound = np.full(f,31)
        state_ops = {"signed_tap_contributions_per_sample":5*n,"shifts_per_sample":2*n,
                     "leak_add_sub_per_sample":2*n,"saturations_per_sample":n}
    else:
        state = n
        topo = 8
        bound = np.ones(f,dtype=np.int64)
        state_ops = {"boolean_rule_evaluations_per_sample":n,"input_overwrites_per_sample":4}
    if config.get("latch"):
        state *= 2
    bits = readout.get("bits",64)
    if readout["type"] == "template":
        p = len(readout["prototypes"])
        # Each prototype is packed value(2)+duration(5) per run, length and class.
        storage = p*(7*n+math.ceil(math.log2(n+1))+1)
        contributions = p*3*n
        acc = 1+math.ceil(math.log2(35*3*n+1))
        scorebound = 35*3*n
    else:
        storage = f*3*bits+3*readout.get("bias_bits",bits)
        contributions = f*3
        w,b = np.asarray(readout["weights"]),np.asarray(readout["bias"])
        scorebound = float(np.max(bound@np.abs(w)+np.abs(b)))
        acc = 1+math.ceil(math.log2(scorebound+1)) if "bits" in readout else None
    # Loaded floor/margin and 2-bit classifier-kind setting; control modes fixed
    # by the built structure, not a promise that all families coexist on chip.
    threshold_bits = 2*(acc or 64)+2
    parameter_bits = storage+configuration+topo+threshold_bits
    pairs = len(getattr(model,"pairs",[]))
    products = pairs + (n if k=="run" and pairs and not model.binary_runs else 0)
    return {"status":"analytical EST; no synthesis, frequency, or RTL equivalence evidence",
            "persistent_entries":n,"history_state_bits":state,"front_end_and_output_state_bits":common_state,
            "dynamic_state_bits":state+common_state,"feature_count":f,"nonlinear_products_per_gate":products,
            "product_kind":"XNOR/sign selection" if k=="sample" or model.binary_runs else "small integer products; some sign selections",
            "readout_storage_bits":storage,"topology_bits":topo,"threshold_and_config_bits":threshold_bits+configuration,
            "parameter_bits":parameter_bits,"contributions_per_gate":contributions,
            "accumulator_bits":acc,"score_abs_bound":scorebound,"margin_subtract_bits":acc+1 if acc else None,
            "state_operations":state_ops,"front_end_per_sample":"2 lane majority votes, packed compare, counter increment, gate compare",
            "synchronizer_bits_estimate":4,"timestamp_bits":16,
            "stabilization":"one-shot after 10 observed idle ticks; registered class and timestamp; M=1",
            "in_budget":parameter_bits<=32768 and state+common_state<=4096 and contributions<=4096,
            "schedule":"State updates every sample. Feature/readout computed at observed end only. Sequential MAC needs contributions cycles/gate; no clock ratio proved."}
