"""Small independent contract, scorer, causality and integer arithmetic checks."""
import json
import unittest
import numpy as np
from .signals import encode, make_stream, TASKS
from .models import Frontend, Features, collect, configurations
from .scoring import score, training_labels
from .learning import decisions, quantize
from .resources import count
from .receiver import Receiver


def compress(values):
    result = []
    for x in values:
        if result and result[-1][0] == x:
            result[-1][1] += 1
        else:
            result.append([x,1])
    return result


class Contracts(unittest.TestCase):
    def test_hand_vectors_and_xor(self):
        rng = np.random.default_rng(1)
        self.assertEqual(encode("pulse",0,rng),[(1,3),(0,3),(1,8)])
        self.assertEqual(encode("pulse",1,rng),[(1,8),(0,3),(1,3)])
        for cls in (0,1):
            for _ in range(100):
                r = encode("context",cls,rng)
                highs = [d for v,d in r if v]
                self.assertEqual(((highs[0]-3)//3)^((highs[5]-3)//3),cls)
                self.assertEqual(highs[-2:],[3,6])

    def test_nominal_completion_and_gate(self):
        for task in (*TASKS,"transfer"):
            s = make_stream(task,421,"clean",30)
            front = Frontend(True)
            gates = [(t,o[6]) for t,u in enumerate(s["samples"]) if (o:=front.step(u))[5]]
            self.assertEqual(len(gates),len(s["events"]),task)
            self.assertEqual(gates,[(e["end"]+10,e["end"]+1) for e in s["events"]],task)
            # Independent RLE verifies activity blocks and delimiter locations.
            self.assertTrue(all(s["samples"][e["end"]-1] and not s["samples"][e["end"]] for e in s["events"]))

    def test_two_lane_relationship_and_codewords(self):
        rng = np.random.default_rng(32)
        for cls,word in enumerate(("001101","110001")):
            runs = encode("clockdata",cls,rng)
            decoded = ''.join(str(v>>1) for v,n in runs[2:] if v&1)
            self.assertEqual(decoded,word)
            runs = encode("biphase",cls,rng)[2:]
            self.assertEqual(''.join(str(runs[i+1][0]) for i in range(0,len(runs),2)),word)
            self.assertTrue(all(runs[i][0] != runs[i+1][0] for i in range(0,len(runs),2)))

    def test_unknown_words_not_known(self):
        for task in TASKS:
            known = {tuple(encode(task,c,np.random.default_rng(i))) for i in range(100) for c in (0,1)}
            unknown = {tuple(encode(task,7,np.random.default_rng(i),novel=novel)) for i in range(100) for novel in (False,True)}
            self.assertFalse(known&unknown,task)


class Integrity(unittest.TestCase):
    def test_transaction_includes_idle_extras(self):
        events=[{"class":0,"start":i*40,"end":i*40+20,"group":0} for i in range(4)]
        s={"events":events,"ticks":200}
        p=[{"class":0,"tick":e["end"]+10,"stamp":e["end"]} for e in events]
        self.assertEqual(score(s,p)["transaction_ok"],1)
        self.assertEqual(score(s,p+[{"class":7,"tick":190,"stamp":180}])["transaction_ok"],0)

    def test_snapshot_and_quantized_new_representations(self):
        from .run import read,ROOT
        s=make_stream("context",821,"mixed",12)
        for cfg in read(ROOT/"configs/representation.json")+read(ROOT/"configs/final_development.json"):
            rec=collect([s],cfg)
            n=rec[0]["x"].shape[1]
            rng=np.random.default_rng(82)
            q=quantize({"type":"ridge","weights":rng.normal(0,.01,(n,3)).tolist(),
                        "bias":[.3,.1,.2],"floor":.2,"margin":.05},8,True)
            receiver=Receiver(cfg,q)
            pred=[]
            for t,u in enumerate(s["samples"]):
                if t in (1,17,len(s["samples"])//2):
                    receiver=Receiver.restore(json.loads(json.dumps(receiver.snapshot())))
                p=receiver.step(u)
                if p is not None:
                    pred.append(p)
            self.assertEqual(pred,decisions(rec,q,scalar=True)[0])
            w,b=np.asarray(q["weights"]),np.asarray(q["bias"])
            self.assertLessEqual(np.max(np.abs(rec[0]["x"]@w+b)),count(cfg,q)["score_abs_bound"])

    def test_duplicate_wrong_class_and_matching_edges(self):
        s = {"events":[{"class":0,"start":0,"end":20,"group":0}],"ticks":100}
        e = {"class":0,"tick":30,"stamp":20}
        self.assertEqual(score(s,[e,e])["fp"],1)
        self.assertEqual(score(s,[dict(e,**{"class":1})])["tp"],0)
        self.assertEqual(score(s,[dict(e,tick=27)])["tp"],0)
        self.assertEqual(score(s,[dict(e,tick=28)])["tp"],1)
        self.assertEqual(score(s,[dict(e,tick=34)])["tp"],1)
        self.assertEqual(score(s,[dict(e,tick=35)])["tp"],0)

    def test_causal_prefix_and_metadata_independence(self):
        s = make_stream("clockdata",81,"mixed",12)
        cut = len(s["samples"])//2
        suffix_changed = {**s,"events":[],"task":"ignored", "samples":s["samples"][:cut]+[3]*(len(s["samples"])-cut)}
        for cfg in configurations():
            a,b = collect([s,suffix_changed],cfg)
            ai,bi = a["ticks"]<cut,b["ticks"]<cut
            np.testing.assert_array_equal(a["ticks"][ai],b["ticks"][bi])
            np.testing.assert_array_equal(a["x"][ai],b["x"][bi])

    def test_scalar_integer_readout_and_bounds(self):
        rng = np.random.default_rng(83)
        s = make_stream("context",833,"mixed",12)
        for cfg in configurations():
            rec = collect([s],cfg)
            width = rec[0]["x"].shape[1]
            r = {"type":"ridge","weights":rng.normal(0,.01,(width,3)).tolist(),
                 "bias":[.1,.2,.3],"floor":.3,"margin":.1}
            q = quantize(r,8)
            np.testing.assert_array_equal(decisions(rec,q),decisions(rec,json.loads(json.dumps(q)),scalar=True))
            w,b = np.asarray(q["weights"]),np.asarray(q["bias"])
            self.assertTrue(np.max(np.abs(w))<=127)
            self.assertTrue(np.max(np.abs(rec[0]["x"]@w+b))<=count(cfg,q)["score_abs_bound"])

    def test_duration_information_necessary(self):
        # Equal total duration and occupancy, different order; current sample equal.
        x=[]
        for widths in ((3,8),(8,3)):
            samples = [0]*20+[1]*widths[0]+[0]*3+[1]*widths[1]+[0]*20
            x.append({"samples":samples})
        current = collect(x,{"kind":"sample","n":1})
        np.testing.assert_array_equal(current[0]["x"],current[1]["x"])
        run = collect(x,{"kind":"run","n":16,"degree":1})
        self.assertFalse(np.array_equal(run[0]["x"],run[1]["x"]))


if __name__ == "__main__":
    unittest.main()
