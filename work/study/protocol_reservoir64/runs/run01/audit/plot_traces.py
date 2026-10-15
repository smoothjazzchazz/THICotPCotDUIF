"""Render saved final waveforms; no model fitting or new inference."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'font.family': 'DejaVu Sans'})
fig, axes = plt.subplots(2, 1, figsize=(12, 6.5), constrained_layout=True)

p=ROOT/'final/traces/uart_n_quantized_11_phrase'
a=np.load(p/'waveform.npz')
t=np.arange(720)
axes[0].step(t,a['lines'][:720,0]+2,where='post',color='#34495e',lw=1.3)
axes[0].step(t,a['output'][:720],where='post',color='#2c7fb8',lw=1.4)
for k,color in ((1,'#009e73'),(2,'#0072b2'),(3,'#e69f00'),(6,'#cc3311')):
 e=a['events']; ticks=e[(e[:,0]==k)&(e[:,2]<720),2]
 axes[0].scatter(ticks,np.full(len(ticks),1.65),color=color,s=20,marker='|' if k!=6 else 'x',
                 label={1:'BIT0',2:'BIT1',3:'START',6:'INVALID / uncertain'}[k])
axes[0].set(yticks=[.5,1.65,2.5],yticklabels=['Echo TX','RX events','Incoming UART'],
            ylim=(-.3,3.5),xlim=(0,720),xlabel='Simulation tick (first 720 shown)',
            title='UART 8N1: input phrase present, independently decoded echo is empty')
axes[0].legend(loc='upper right',ncol=4,fontsize=8)

p=ROOT/'final/traces/i2c_quantized_11_phrase'
a=np.load(p/'waveform.npz'); n=len(a['lines']); lo=n-320;t=np.arange(lo,n)
axes[1].step(t,a['lines'][lo:,0]+4,where='post',color='#34495e',lw=1.3)
axes[1].step(t,a['lines'][lo:,1]+2,where='post',color='#2c7fb8',lw=1.3)
axes[1].step(t,a['enables'][lo:,1].astype(int),where='post',color='#009e73',lw=1.3)
# STOP is independently visible as SDA rising while SCL remains high.
lines=a['lines']; stops=[j for j in range(lo+1,n) if lines[j-1,0]==lines[j,0]==1 and lines[j-1,1]==0 and lines[j,1]==1]
for tick in stops:
 axes[1].axvline(tick,color='#cc3311',ls='--',lw=1)
 axes[1].annotate('STOP missed by receiver',xy=(tick,3),xytext=(tick-135,5.5),
                  arrowprops={'arrowstyle':'->','color':'#cc3311'},color='#aa2211',fontsize=9)
axes[1].set(yticks=[.5,2.5,4.5],yticklabels=['Target pulls SDA low','Resolved SDA','Resolved SCL'],
            ylim=(-.3,6),xlim=(lo,n),xlabel='Simulation tick (end of live read transaction)',
            title='I2C seed 11: all 27 phrase bytes returned exactly; final STOP event missing')
fig.suptitle('Frozen quantized inference: waveform-to-waveform evidence',fontsize=15,fontweight='bold')
fig.savefig(ROOT/'final/phrase_waveforms.png',dpi=160)
fig.savefig(ROOT/'final/phrase_waveforms.svg')
print(ROOT/'final/phrase_waveforms.png')
