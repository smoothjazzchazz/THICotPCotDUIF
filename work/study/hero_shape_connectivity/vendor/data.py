"""Offline stimulus and causal reference labels. Never imported by the receiver."""
import numpy as np
from .network import events, pulses

NONE,BIT0,BIT1,START,STOP,INVALID=range(6)


def reference_labels(lines,profile):
    """Independent waveform parser used only for labels/audits, never inference."""
    labels=np.zeros(len(lines),dtype=np.int32)
    previous=np.ones(3,dtype=int)
    active=False;due=-1;position=0;high_pending=False;high_bit=0
    blocked=False;high_run=16
    for t,row in enumerate(lines):
        if profile.startswith('uart'):
            v=int(row[0]);high_run=high_run+1 if v else 0
            if blocked and high_run>=16: blocked=False
            if not active and not blocked and previous[0] and not v:
                active=True;due=t+7;position=0
            if active and t==due:
                last=10 if profile=='uart_e' else 9
                if position==0:
                    labels[t]=START if not v else INVALID
                    if v: active=False
                elif position<last: labels[t]=BIT0+v
                else:
                    labels[t]=STOP if v else INVALID
                    active=False;blocked=not bool(v)
                position+=1;due+=16
        elif profile=='i2c':
            scl,sda=int(row[0]),int(row[1])
            if previous[0] and scl and previous[1]!=sda:
                labels[t]=START if not sda else STOP
                active=not bool(sda);high_pending=False
            elif active and not previous[0] and scl:
                high_pending=True;high_bit=sda
            elif active and previous[0] and not scl and high_pending:
                labels[t]=BIT0+high_bit;high_pending=False
        else:
            mode=int(profile[-1]);cpol=mode//2;cpha=mode%2
            clk,cs,data=map(int,row)
            if previous[1] and not cs: labels[t]=START;active=True
            elif not previous[1] and cs: labels[t]=STOP;active=False
            elif active and clk!=previous[0] and clk==(cpol if cpha else 1-cpol):
                labels[t]=BIT0+data
        previous=row
    return labels


def assemble(event_list,profile):
    """Only learned events enter here. No lines, elapsed timers, or labels."""
    accepted=[];rejected=0;bits=[];segments=[];onset=None;bad=False
    def bytes_from(values,width,lsb=False):
        return [sum(v<<j for j,v in enumerate(values[i:i+width])) if lsb else
                sum(v<<(width-1-j) for j,v in enumerate(values[i:i+width]))
                for i in range(0,len(values),width)]
    def phase():
        if not bits or len(bits)%9: return None
        return dict(bytes=[sum(bits[i+j]<<(7-j) for j in range(8)) for i in range(0,len(bits),9)],
                    ack=[bits[i+8] for i in range(0,len(bits),9)])
    for e in event_list:
        k=e['kind'];t=e['decision_tick']
        if k==START:
            if profile=='i2c' and onset is not None:
                p=phase();bad|=p is None
                if p is not None:
                    if sum(len(s['bytes']) for s in segments)+len(p['bytes'])>1026:bad=True
                    else:segments.append(p)
            else:
                if onset is not None: rejected+=1
                onset=t;segments=[];bad=False
            bits=[]
        elif k in (BIT0,BIT1):
            if onset is not None:
                if len(bits)<9*1025:bits.append(e['bit'])
                else:bad=True
        elif k==INVALID:
            rejected+=1;bits=[];segments=[];onset=None;bad=False
        elif k==STOP:
            if onset is None: continue
            value=None
            if profile.startswith('uart'):
                count=9 if profile=='uart_e' else 8
                if len(bits)==count and (count==8 or sum(bits)%2==0):
                    value=dict(bytes=bytes_from(bits[:8],8,True))
            elif profile=='i2c':
                p=phase()
                if p is not None: value=dict(segments=segments+[p])
            elif bits and len(bits)%8==0: value=dict(bytes=bytes_from(bits,8))
            if value is not None and not bad: accepted.append(dict(start=onset,stop=t,**value))
            else: rejected+=1
            onset=None;bits=[];segments=[];bad=False
    return accepted,rejected


class Builder:
    def __init__(self,profile,seed):
        self.profile=profile;self.rng=np.random.default_rng(seed)
        self.lines=[];self.groups=[]
    def hold(self,row,n): self.lines.extend([tuple(map(int,row))]*int(n))
    def idle(self,n):
        row=(int(self.profile[-1])//2,1,1) if self.profile.startswith('spi') else (1,1,1)
        self.hold(row,n)
    def message(self,payload,condition='nominal',invalid=None):
        rng=self.rng;self.idle(int(rng.integers(17,49)))
        begin=len(self.lines);payload=list(map(int,payload))
        if self.profile.startswith('uart'):
            ratio=.97 if 'minus' in condition else 1.03 if 'plus' in condition else 1.
            elapsed=float(len(self.lines))+rng.random()
            if invalid=='break': self.hold((0,1,1),400)
            else:
                for index,value in enumerate(payload):
                    bits=[(value>>i)&1 for i in range(8)]
                    if self.profile=='uart_e': bits.append(sum(bits)%2 ^ int(invalid=='parity'))
                    cells=[0]+bits+[0 if invalid=='framing' else 1]
                    for v in cells:
                        elapsed+=16*ratio
                        # Bounded edge jitter, not an unbounded random walk in cell widths.
                        edge_jitter=int(rng.integers(-1,2)) if 'jitter' in condition else 0
                        self.hold((v,1,1),max(3,round(elapsed)+edge_jitter-len(self.lines)))
                    if condition=='gaps':
                        gap=int(rng.integers(0,5))*16;self.idle(gap);elapsed+=gap
        elif self.profile=='i2c':
            low,high=(12,5) if condition=='duty' else (8,8)
            address=int(rng.integers(0x20,0x70));read=bool(rng.integers(0,2))
            if condition in ('write_nack','address_nack'):read=False
            previous_bit=0
            def start():
                nonlocal previous_bit
                self.hold((0,1,1),low);self.hold((1,1,1),high);self.hold((1,0,1),high)
                previous_bit=0
            def bit(v):
                nonlocal previous_bit
                if condition=='phase':
                    self.hold((0,previous_bit,1),low-1);self.hold((0,v,1),1)
                else:self.hold((0,v,1),low+(int(rng.integers(1,97)) if condition=='pauses' and rng.random()<.15 else 0))
                self.hold((1,v,1),high);self.hold((0,v,1),1)
                previous_bit=v
            def octet(v,ack):
                for shift in range(7,-1,-1):bit((v>>shift)&1)
                bit(ack)
            start()
            octet((address<<1)|int(read),int(condition=='address_nack'))
            if invalid=='partial':
                for v in (0,1,0):bit(v)
            else:
                split=len(payload)//2 if condition=='repeated' and len(payload)>1 else len(payload)
                for i,v in enumerate(payload):
                    if i==split:
                        start();read=not read;octet((address<<1)|int(read),0)
                    octet(v,int((read and (i==len(payload)-1 or i==split-1)) or
                                (condition=='write_nack' and i==len(payload)-1)))
            self.hold((0,0,1),low);self.hold((1,0,1),high);self.hold((1,1,1),high)
        else:
            mode=int(self.profile[-1]);cpol=mode//2;cpha=mode%2
            a,b=(3,9) if condition=='duty' else (4,4)
            bits=[(v>>i)&1 for v in payload for i in range(7,-1,-1)]
            if invalid=='partial':bits=bits[:max(1,len(bits)-3)]
            self.hold((cpol,0,bits[0]),a+int(rng.integers(0,4)))
            old=bits[0]
            for v in bits:
                if condition=='phase':
                    if cpha:
                        self.hold((cpol,0,old),a)
                        self.hold((1-cpol,0,old),b-1)
                        self.hold((1-cpol,0,v),1)
                    else:
                        self.hold((cpol,0,old),a-1)
                        self.hold((cpol,0,v),1)
                        self.hold((1-cpol,0,v),b)
                else:
                    self.hold((cpol,0,v),a+(int(rng.integers(1,97)) if condition=='pauses' and rng.random()<.15 else 0))
                    self.hold((1-cpol,0,v),b)
                self.hold((cpol,0,v),a)
                old=v
            self.hold((cpol,1,bits[-1]),a)
        end=len(self.lines);self.idle(32)
        self.groups.append(dict(start=begin,end=end,valid=invalid is None,condition=condition,
                                invalid=invalid,payload=payload))
    def finish(self):
        lines=np.array(self.lines,dtype=np.uint8)
        y=reference_labels(lines,self.profile)
        truth,rejected=assemble(events(y),self.profile)
        # Independent payload contract: generated bytes must survive the waveform oracle.
        for g in self.groups:
            accepted=[a for a in truth if g['start']<=a['start']<g['end']]
            if g['valid']:
                if self.profile=='i2c':
                    got=[v for a in accepted for s in a['segments'] for v in s['bytes'][1:]]
                else:got=[v for a in accepted for v in a['bytes']]
                if got!=g['payload']:
                    raise AssertionError((self.profile,g,got,'oracle/generator disagreement'))
            elif accepted: raise AssertionError(('invalid accepted by oracle',self.profile,g,accepted))
        return dict(lines=lines,labels=y,groups=self.groups,truth=truth,reference_rejections=rejected,profile=self.profile)


def corpus(profile,seed,ticks=8192,stage='mixed',groups=None):
    b=Builder(profile,seed);i=0
    while (len(b.lines)<ticks if groups is None else i<groups):
        length=int(b.rng.integers(1,3 if stage=='clean' else 9))
        payload=b.rng.integers(0,256,length).tolist()
        if stage!='clean' and i%4==0:payload=[(0,255,85,170)[i//4%4]]*length
        condition='nominal';invalid=None
        if stage=='mixed':
            choices=(['nominal','gaps','minus','plus','jitter','minus_jitter','plus_jitter']
                     if profile.startswith('uart') else ['nominal','duty','pauses']+(['repeated'] if profile=='i2c' else []))
            condition=choices[i%len(choices)]
            if i%7==6:
                invalid=(('framing','break','parity' if profile=='uart_e' else 'framing')[i//7%3]
                         if profile.startswith('uart') else 'partial')
                payload=payload[:1]
        b.message(payload,condition,invalid);i+=1
    return b.finish()


def score(stream,kinds,keep_trace=False):
    kinds=pulses(kinds)
    actual,rejected=assemble(events(kinds),stream['profile']);expected=stream['truth']
    exact=byte_exact=valid=invalid_accepted=0
    for g in stream['groups']:
        truth=[a for a in expected if g['start']<=a['start']<g['end']]
        got=[a for a in actual if g['start']<=a['start']<g['end']]
        if g['valid']:
            valid+=1;exact+=int(got==truth)
            byte_exact+=int([{k:v for k,v in a.items() if k not in ('start','stop')} for a in got]==
                            [{k:v for k,v in a.items() if k not in ('start','stop')} for a in truth])
        else:invalid_accepted+=len(got)
    truth_events=stream['labels'];pred=np.asarray(kinds)
    boundaries=np.isin(truth_events,[START,STOP]);pbound=np.isin(pred,[START,STOP])
    tp=int(np.sum(boundaries & (truth_events==pred)))
    denom=int(boundaries.sum()+pbound.sum())
    extra=sum(not any(g['start']<=a['start']<g['end'] for g in stream['groups']) for a in actual)
    row=dict(valid_messages=valid,exact_messages=exact,byte_exact_messages=byte_exact,
             message_accuracy=exact/max(1,valid),boundary_f1=2*tp/max(1,denom),
             boundary_errors=int(np.sum((boundaries|pbound)&(truth_events!=pred))),
             false_events=int(np.sum((pred!=0)&(pred!=truth_events))),
             missed_events=int(np.sum((truth_events!=0)&(pred!=truth_events))),
             invalid_accepted=invalid_accepted,background_accepted=extra,
             accepted_messages=len(actual),rejections=rejected,ticks=len(pred))
    if keep_trace:
        row['accepted']=actual;row['expected']=expected
        row['first_event_errors']=[dict(tick=int(t),expected=int(truth_events[t]),actual=int(pred[t]))
                                   for t in np.flatnonzero(truth_events!=pred)[:128]]
    return row
