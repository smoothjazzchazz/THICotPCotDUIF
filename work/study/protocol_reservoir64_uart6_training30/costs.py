"""Original logical accounting with all current UART candidates."""
import numpy as np
from work.model.stream_reservoir import ARCHITECTURE_HASH,load_weights
from .data import PROFILES
from .training import SEEDS
def resource_cost(output):
    weights, variants = {}, []
    for profile in PROFILES:
        for seed in SEEDS:
            w, _ = load_weights(output / 'models' / profile / f'seed_{seed}' / 'selected.npz')
            effective = np.diag(1 - np.tile([1, .5, .25, .125], 16)) + np.diag(np.tile([1, .5, .25, .125], 16)) @ w['wh']
            variants.append(dict(profile=profile, seed=seed,
                recurrent_spectral_radius=float(max(abs(np.linalg.eigvals(w['wh'])))),
                unsaturated_linearization_radius=float(max(abs(np.linalg.eigvals(effective)))),
                max_abs_weight=max(float(abs(v).max()) for v in w.values())))
    return dict(architecture_hash=ARCHITECTURE_HASH,
        parameters=dict(input_weights=384, recurrent_weights=256, state_bias=64,
                        readout_weights=512, readout_bias=8, total_trained=1224,
                        fixed_leaks=64, recurrent_indices_bits=256 * 6),
        logical_storage_bytes=dict(float64_coefficients=1224 * 8, quantized_int16_coefficients=1224 * 2,
            float64_state_double_buffer=64 * 8 * 2, quantized_state_double_buffer=64 * 2 * 2,
            leak_q15=128, recurrent_indices_packed=192, tanh_lut_q14=4097 * 2,
            preprocessor_previous_levels=2, preprocessor_edge_ages=2,
            event_register_64bit_timestamps_and_class=17, decision_last_class=1, tick_counter=8,
            uart_logical_frame_capacity=32, uart_assembly_bits_and_count=3, uart_queue_deadlines_64bit=32 * 8,
            uart_schedule_counter=8, i2c_byte_storage=4096, i2c_controller_fields_upper_bound=64,
            tx_pending_commands_512x25bytes=512 * 25, tx_output_latches=4),
        arithmetic_per_tick=dict(sparse_MAC=384 + 256 + 512, dense_numpy_MAC=384 + 4096 + 512,
            leak_blend_products=128, tanh_or_LUT=64, bias_additions=72,
            quant_accumulator_bits=64, worst_case_drive_abs_bound=88,
            worst_case_readout_abs_bound=520, top_two_readout_comparisons_upper_bound=16),
        implementation_notes=[
            'UART frame capacity is represented by scheduler commands/deadlines, not a separately allocated byte FIFO.',
            'Float reference uses float64; quantized steps use int64 NumPy arrays for overflow-safe arithmetic.',
            'Logical int16 parameter/state storage and sparse MAC counts are a packing proposal, not the Python process footprint.',
            'Current NumPy execution stores dense 64x64 recurrence even though only 256 entries can be nonzero.',
            'Tanh ROM generated once off-line; LUT and fixed-point rounding are used in online quantized steps.',
            'Python logs, full traces, emitted-event lists and recovered-byte lists are diagnostic sinks, not runtime decision inputs.',
            'Master/stimulus, training BPTT buffers and independent checkers are external to emulator; not counted as device storage.',
            'No accelerator schedule, area, achievable frequency, power, electrical or silicon feasibility measured.',
            'Linearization radii do not prove echo-state behavior or long-term stability.'],
        trained_dynamics=variants)

