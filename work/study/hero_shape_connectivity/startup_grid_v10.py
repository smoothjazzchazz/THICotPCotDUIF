"""Balanced first-byte training coverage; cold state is explicit, never inferred."""
import hashlib,json
import numpy as np
from .vendor.data import Builder
from .shapes import features
from .data import conditions
from .startup_audit import mismatches


def case(profile,idle,condition_index,value):
    assert profile in ('uart_n','uart_e') and 17<=idle<=48 and 0<=value<256
    seed=391000000+int(profile=='uart_e')*1000000+((idle-17)*7+condition_index)*256+value
    b=Builder(profile,seed);b.message([value],conditions(profile)[condition_index])
    old=b.groups[0]['start'];shift=idle-old
    b.lines=[(1,1,1)]*idle+b.lines[old:]
    b.groups=[{**g,'start':g['start']+shift,'end':g['end']+shift} for g in b.groups]
    s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
    assert not mismatches(s) and s['groups'][0]['start']==idle
    return s


def block(profile,idle,condition_index):
    return [case(profile,idle,condition_index,value) for value in range(256)]


def identity(streams):
    h=hashlib.sha256()
    for s in streams:
        h.update(s['lines'].tobytes());h.update(s['labels'].tobytes());h.update(json.dumps(s['groups'],sort_keys=True).encode())
    return h.hexdigest()
