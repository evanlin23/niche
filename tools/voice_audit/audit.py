"""Audit synthetic voices for AI tells. Usage: python audit.py <scratch> <voice_dir> [...]
Per voice: Whisper intelligibility (WER, low-confidence words), prosody (pitch spread, repeated sentence-end melody),
drift between separately synthesized lines (pitch, timbre, loudness), pacing (rate variation, pauses)."""
import sys, os, json, re, itertools
import numpy as np, soundfile as sf, parselmouth
from num2words import num2words
S=sys.argv[1]
REF={l.split("\t")[0]:l.rstrip("\n").split("\t")[1] for l in open(os.path.join(S,"tools/passage.txt")) if l.strip()}
def norm(t):
    t=t.replace("%"," percent").replace("$"," dollars ")
    t=re.sub(r"(\d+)\.(\d+)", lambda m: num2words(int(m.group(1)))+" point "+" ".join(num2words(int(c)) for c in m.group(2)), t)
    t=re.sub(r"\d+", lambda m: num2words(int(m.group(0))), t)
    t=t.lower().replace("-"," ")
    return re.findall(r"[a-z']+", t)
def wer(ref,hyp):
    d=np.arange(len(hyp)+1)
    for i,r in enumerate(ref,1):
        prev=d.copy(); d[0]=i
        for j,h in enumerate(hyp,1): d[j]=min(prev[j]+1,d[j-1]+1,prev[j-1]+(r!=h))
    return d[-1]/max(1,len(ref))
from faster_whisper import WhisperModel
ASR=WhisperModel("small.en",device="cpu",compute_type="int8",download_root=os.path.join(S,"models/whisper"))
def st(f): return 12*np.log2(f/100.0)
def line_feats(path, female):
    snd=parselmouth.Sound(path)
    p=snd.to_pitch(time_step=0.01,pitch_floor=75 if female else 60,pitch_ceiling=500 if female else 300)
    f=p.selected_array["frequency"]; tt=p.xs(); v=f>0
    mf=snd.to_mfcc(number_of_coefficients=12).to_array()[1:13]  # drop c0 (energy)
    a,sr=sf.read(path,dtype="float32")
    rms=20*np.log10(np.sqrt(np.mean(a**2))+1e-9)
    # pauses inside the line: 25 ms frames under -40 dB relative to line peak, runs >= 120 ms, excluding edges
    fr=int(0.025*sr); e=np.array([np.sqrt(np.mean(a[i:i+fr]**2))+1e-9 for i in range(0,len(a)-fr,fr)])
    db=20*np.log10(e/e.max()); sil=db<-40
    idx=np.where(~sil)[0]; inner=sil[idx[0]:idx[-1]] if len(idx) else sil
    runs=[len(list(g)) for k,g in itertools.groupby(inner) if k]; pauses=sum(1 for r in runs if r*0.025>=0.12)
    return dict(f0=st(f[v]), t=tt[v], dur=len(a)/sr, mfcc=mf.mean(axis=1), rms=rms, pauses=pauses, sr=sr)
def audit(vdir):
    meta=json.load(open(os.path.join(vdir,"_meta.json"))); name=os.path.basename(vdir)
    female=bool(re.search(r"(^kokoro_[ab]f_)|amy|cori|lessac",name))
    import subprocess
    raw=subprocess.run(["ffmpeg","-loglevel","error","-i",os.path.join(vdir,"_full.wav"),"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
    seg,info=ASR.transcribe(np.frombuffer(raw,np.float32).copy(),word_timestamps=True,language="en",beam_size=5)
    words=[w for s in seg for w in s.words]; hyp=norm(" ".join(w.word for w in words))
    ref=[x for lid,_ in meta["lines"] for x in norm(REF[lid])]
    low=[w.word.strip() for w in words if w.probability<0.5]
    L={lid:line_feats(os.path.join(vdir,f"{lid}.wav"),female) for lid,_ in meta["lines"]}
    allf0=np.concatenate([x["f0"] for x in L.values()])
    ends=[]
    for x in L.values():
        m=x["t"]>=x["t"].max()-0.8 if len(x["t"]) else []
        if len(x["f0"])>8 and np.sum(m)>5:
            c=x["f0"][m]-np.median(x["f0"]); ends.append(np.interp(np.linspace(0,1,16),np.linspace(0,1,len(c)),c))
    corr=[np.corrcoef(a,b)[0,1] for a,b in itertools.combinations(ends,2)]
    med=np.array([np.median(x["f0"]) for x in L.values()])
    M=np.array([x["mfcc"] for x in L.values()]); mu=M.mean(0)
    cos=[1-np.dot(m,mu)/(np.linalg.norm(m)*np.linalg.norm(mu)) for m in M]
    rate=np.array([len(norm(REF[lid]))/L[lid]["dur"] for lid in L])
    nwords=len(ref)
    return dict(voice=name, sr=meta["sr"], wer=round(wer(ref,hyp),3), low_conf=len(low), low_words=low[:8],
        f0_sd_st=round(float(np.std(allf0)),2), end_melody_corr=round(float(np.mean(corr)),2) if corr else None,
        line_pitch_drift_st=round(float(np.std(med)),2), timbre_drift=round(float(np.max(cos))*1000,1),
        loud_sd_db=round(float(np.std([x["rms"] for x in L.values()])),2),
        wps=round(float(rate.mean()),2), rate_cv=round(float(rate.std()/rate.mean()),3),
        pauses_per_100w=round(100*sum(x["pauses"] for x in L.values())/nwords,1))
res=[audit(d) for d in sys.argv[2:]]
json.dump(res,open(os.path.join(S,"out","_audit.json"),"w"),indent=1)
for r in res: print(json.dumps(r))
