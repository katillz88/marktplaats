# Genereert voice-over (ElevenLabs, stem Seyfullah Kartal, eleven_v4) + timing-cues voor een short.
# Gebruik: python3 voice.py <map> <tr|en>
import json,subprocess,urllib.request,sys,os,re
d,lang=sys.argv[1],sys.argv[2]
src=open(f'{d}/config.js').read()
js=src[src.index('{'):src.rindex('}')+1]
# config.js is a JS object literal; convert to JSON via node
cfg=json.loads(subprocess.run(['node','-e',f'const window={{}};{src};console.log(JSON.stringify(window.CFG))'],capture_output=True,text=True,check=True).stdout)
T=cfg['voice'][lang]; GAP=cfg.get('gaps',{'v2':.45,'v3':.5,'v4':.6,'v5':.8,'v6':.8,'v7':.8,'v8':.8})
VOICE='mF7tIc9VLrznhGooGjaT'; os.makedirs(f'{d}/voice/{lang}',exist_ok=True)
cues={}; t=.3
for k,txt in T.items():
    mp3=f'{d}/voice/{lang}/{k}.mp3'; wav=f'{d}/voice/{lang}/{k}.wav'
    if not os.path.exists(wav):
        body=json.dumps({"text":txt,"model_id":"eleven_v4","language_code":lang,"voice_settings":{"stability":0.5,"similarity_boost":0.8,"style":0.25,"use_speaker_boost":True}}).encode()
        req=urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_192",data=body,headers={"Content-Type":"application/json"})
        open(mp3,'wb').write(urllib.request.urlopen(req).read())
        subprocess.run(['ffmpeg','-y','-v','error','-i',mp3,'-af','silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse',wav],check=True)
    dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',wav],capture_output=True,text=True).stdout)
    t+=GAP.get(k,0); cues[k]=[round(t,3),round(dur,3)]; t+=dur
total=round(t+cfg.get('tail',3.4),2)
open(f'{d}/data_{lang}.js','w').write(f'window.CUES={json.dumps(cues)};window.TOTAL={total};\n')
print(d,lang,total)
