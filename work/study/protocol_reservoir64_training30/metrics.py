"""Original end-to-end acceptance logic, with a disjoint seeded live peer."""
import numpy as np
from work.model.stream_reservoir import FALL, NAMES
from work.study.protocol_reservoir64.scoring import score_events, byte_errors, distribution
from work.study.protocol_reservoir64.checkers import i2c_decode, bus_events
from work.study.protocol_reservoir64.evaluation import score_uart
from .simulation import run_i2c

def score_i2c(case, receiver, config=None):
    result = run_i2c(case['payload'], receiver, low=case.get('low', 10), high=case.get('high', 10),
        address=case.get('address', 0x32), repeated=case.get('repeated', True),
        malformed=case.get('malformed', False), disturbance=case.get('disturbance', False),
        jitter=case['name'] == 'jitter', config=config, peer_seed=case['seed'])
    decoded = i2c_decode(result['lines'])
    read_transactions = [d for d in decoded if d['bytes'] and d['bytes'][0] == ((case.get('address', 0x32) << 1) | 1)]
    output = [b for d in read_transactions for b in d['bytes'][1:]]
    expected = [] if case.get('address', 0x32) != 0x32 else list(case['payload'])
    symbols, matched = score_events(bus_events(result['lines']), result['events'])
    fall_ticks = {e.decision_tick for e in result['events'] if e.kind == FALL}
    latencies = [due - matched[t] for t, due in result['controller'].response_requests if t in fall_ticks and t in matched]
    deadlines = sum(latency > 6 for latency in latencies)
    if expected:
        deadlines += sum(not ack for ack in result['peer'].acks)
        deadlines += max(0, len(expected) + 2 - len(result['peer'].acks))
    foreign_ack = bool(any(result['peer'].acks)) if not expected else False
    metrics = dict(bytes=byte_errors(expected, output), output_bytes=output,
        controller_bytes=byte_errors(expected, result['controller'].received), symbols=symbols,
        response_latency=distribution(latencies), deadline_misses=deadlines,
        controller_errors=len(result['controller'].errors), buffer_overflows=result['controller'].overflow + result['tx'].overflow,
        peer_read=result['peer'].read, independent_peer_agree=output == result['peer'].read,
        peer_acks=result['peer'].acks, peer_timeout=result['peer'].timeout or not result['peer'].done,
        foreign_address_ack=foreign_ack, stretch_waits=distribution(result['peer'].stretches),
        recovery_success=(output == expected) if not case['valid'] else None,
        ticks=len(result['lines']), input_presented_bytes=len(result['controller'].received),
        attempted_payload_bytes=len(case['payload']), independent_bus_transactions=decoded)
    metrics['passes'] = (output == expected and result['controller'].received == expected
        and not symbols['totals']['errors'] and not deadlines and not metrics['buffer_overflows']
        and not metrics['peer_timeout'] and not foreign_ack and metrics['independent_peer_agree']
        and (not expected or bool(result['peer'].stretches)))
    return metrics, result



def score_case(profile, case, receiver, config=None):
    if profile == 'i2c':
        metrics, result = score_i2c(case, receiver, config)
    else:
        metrics, result = score_uart(case, case['seed'] - 90001, receiver,
                                    profile == 'uart_e', config)
    add_precision(metrics['symbols'], result['events'])
    return metrics, result


def add_precision(score, events):
    counts = np.bincount([e.kind for e in events], minlength=8)
    for k, name in enumerate(NAMES[1:], 1):
        row = score['by_kind'][name]
        row['emitted'] = int(counts[k])
        row['precision'] = row['correct'] / max(row['emitted'], 1)
        row['recall'] = row['correct'] / max(row['expected'], 1)
        row['f1'] = 2 * row['correct'] / max(row['emitted'] + row['expected'], 1)
    return score


def aggregate(rows):
    valid = [r for r in rows if r.get('valid', True)]
    events = {name: {k: sum(r['symbols']['by_kind'][name].get(k, 0) for r in rows)
                     for k in ('correct', 'expected', 'emitted')} for name in NAMES[1:]}
    for r in events.values():
        r['precision'] = r['correct'] / max(r['emitted'], 1)
        r['recall'] = r['correct'] / max(r['expected'], 1)
        r['f1'] = 2 * r['correct'] / max(r['expected'] + r['emitted'], 1)
    supervised = [r['f1'] for r in events.values() if r['expected']]
    expected = sum(r['bytes']['expected'] for r in valid)
    correct = sum(max(0, r['bytes']['expected'] - r['bytes']['deletions'] - r['bytes']['substitutions']) for r in valid)
    return dict(strict_exchanges=sum(r['passes'] for r in valid), valid_exchanges=len(valid),
                byte_exact_exchanges=sum(r['bytes']['exact'] for r in valid),
                aligned_bytes=correct, expected_bytes=expected,
                aligned_byte_fraction=correct / max(expected, 1),
                boundary_f1=min(events['START']['f1'], events['STOP']['f1']),
                macro_f1=float(np.mean(supervised)) if supervised else 0.,
                false_events=sum(r['symbols']['totals']['false_known'] + r['symbols']['totals']['false_invalid'] for r in rows),
                event_errors=sum(r['symbols']['totals']['errors'] for r in rows),
                ticks=sum(r['ticks'] for r in rows), events=events)


def selection_key(summary, dev_loss):
    return (summary['strict_exchanges'], summary['byte_exact_exchanges'],
            summary['aligned_bytes'], summary['boundary_f1'], summary['macro_f1'],
            -summary['false_events'] / max(summary['ticks'], 1), -dev_loss)
