"""Finish the active experiment once all already-running finalist jobs complete."""
import json
from pathlib import Path
import subprocess
import sys
import time
from .run import ROOT


def main():
    root=ROOT/'runs'/'run01'
    while True:
        ledger=root/'finalists_ledger.json'
        r=json.loads(ledger.read_text()) if ledger.exists() else {}
        if r.get('failures'):raise RuntimeError('finalist worker failure; inspect ledger')
        if len(r.get('completed',[]))==168:break
        time.sleep(5)
    for module,action in [('evaluation','freeze'),('evaluation','generate'),('evaluation','evaluate'),
                          ('evaluation','diagnostics'),('validation','verify'),('report',None)]:
        command=[sys.executable,'-B','-m',f'work.study.protocol_hero_search.{module}']
        if action:command.append(action)
        command+=['--output',str(root)]
        if action=='evaluate':command+=['--workers','8']
        print(json.dumps(dict(starting=command)),flush=True)
        subprocess.run(command,check=True)

if __name__=='__main__':main()
