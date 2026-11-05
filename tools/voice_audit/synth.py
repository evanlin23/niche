import sys, json, wave, subprocess, os
import numpy as np, soundfile as sf
S=sys.argv[1]; engine=sys.argv[2]; voice=sys.argv[3]
lines=[l.rstrip("\n").split("\t",1) for l in open(os.path.join(S,"tools/passage.txt")) if l.strip()]
outdir=os.path.join(S,"out",f"{engine}_{voice}"); os.makedirs(outdir,exist_ok=True)
segs=[]; sr=None
if engine=="kokoro":
    from kokoro_onnx import Kokoro
    k=Kokoro(os.path.join(S,"models/kokoro-v1.0.onnx"), os.path.join(S,"models/voices-v1.0.bin"))
    for lid,t in lines:
        a,sr=k.create(t, voice=voice, speed=0.95, lang="en-gb" if voice.startswith("b") else "en-us")
        a=np.asarray(a,np.float32); sf.write(os.path.join(outdir,f"{lid}.wav"),a,sr); segs.append((lid,a))
else:
    model=os.path.join(S,"models/piper",voice+".onnx")
    for lid,t in lines:
        f=os.path.join(outdir,f"{lid}.wav")
        subprocess.run([sys.executable,"-m","piper","-m",model,"-f",f,"--length-scale","1.15"],input=t.encode(),check=True,capture_output=True)
        a,sr=sf.read(f,dtype="float32"); segs.append((lid,a))
gap=np.zeros(int(0.35*sr),np.float32)
full=np.concatenate([np.concatenate([a,gap]) for _,a in segs])
sf.write(os.path.join(outdir,"_full.wav"),full,sr)
json.dump({"sr":sr,"lines":[(lid,len(a)/sr) for lid,a in segs]},open(os.path.join(outdir,"_meta.json"),"w"))
print(engine,voice,"ok",round(len(full)/sr,1),"s")
