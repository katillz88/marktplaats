# Genereert de voice-over via ElevenLabs en schrijft de timing (cues) voor de animatie.
# Gebruik: python3 voice.py en|tr
import json,subprocess,urllib.request,sys,os
lang=sys.argv[1]; T=json.load(open('voice/teksten.json'))[lang]
VOICE='mF7tIc9VLrznhGooGjaT'; GAP={'v2':.45,'v3':.3,'v4':.6,'v5':.8,'v6':.8}
cues={}; t=.3
for k,txt in T.items():
    mp3=f'voice/{lang}/{k}.mp3'; wav=f'voice/{lang}/{k}.wav'
    if not os.path.exists(wav):
        body=json.dumps({"text":txt,"model_id":"eleven_v4","language_code":lang,"voice_settings":{"stability":0.5,"similarity_boost":0.8,"style":0.25,"use_speaker_boost":True}}).encode()
        req=urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_192",data=body,headers={"Content-Type":"application/json"})
        open(mp3,'wb').write(urllib.request.urlopen(req).read())
        subprocess.run(['ffmpeg','-y','-v','error','-i',mp3,'-af','silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse',wav],check=True)
    d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',wav],capture_output=True,text=True).stdout)
    t+=GAP.get(k,0); cues[k]=[round(t,3),round(d,3)]; t+=d
total=round(t+3.4,2)
open(f'data_{lang}.js','w').write(f'window.CUES={json.dumps(cues)};window.TOTAL={total};\n')
print(lang,cues,total)
