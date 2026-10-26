"""Chinese narrated edition; speech determines shot lengths. Run with bundled Python."""
import sys,asyncio,json,subprocess,wave,math,hashlib
from pathlib import Path
import numpy as np
import make_rhythm as R
M=R.M
sys.path.insert(0,str(M.BASE/'.tts-venv/Lib/site-packages'))
import edge_tts
ROOT=M.ROOT/'style02-narrated'
for folder in ['audio/lines','renders','review']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
LINES=[
'每天忙不停，为什么还是没余裕？',
'忙上一整天，只能捕到一条鱼。',
'吃完，明天又得重来。',
'小岛上的三个人，都这样生活。',
'一个人突然想到，能不能换个方法？',
'做一张网，捕鱼会不会更快？',
'但织网的这一天，就没空去捕鱼。',
'放弃的那条鱼，就是这次选择的机会成本。',
'而且，网也可能做不成。',
'于是，他每天留下一点口粮。',
'产出里没有被消费的部分，就叫储蓄。',
'这些存粮，换来一段不用捕鱼的时间。',
'他终于可以坐下来，开始织网。',
'口粮支持生活，劳动和材料，变成渔网。',
'成功了！这一次，一天捕到了两条鱼！',
'同样一天，产出从一条变成两条。',
'每单位劳动的产出更多，劳动生产率就提高了。',
'他可以照常工作，吃一条，留一条。',
'也可以只捕够口粮，把半天留给生活。',
'这张网，就是帮助生产的资本品。',
'积累不只靠少花，更要把资源用得更好。',
'你的网，可以是技能、工具，或者更好的工作方法。',
'但别忘了，生活不该只剩忍耐。',
'所以，财富只等于钱吗？',
'钱方便交换，网提高生产效率。',
'知识和技能，也会影响未来的收入。',
'除了下一条鱼，你正在积累什么？']
VOICE='zh-CN-YunxiNeural';RATE='+8%';SR=44100
async def speech():
    sem=asyncio.Semaphore(3)
    async def one(i,text):
        path=ROOT/f'audio/lines/{i:02}.mp3'
        if path.exists() and path.stat().st_size>1000:return
        async with sem:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(text,VOICE,rate=RATE).save(str(path))
                    print(f'Speech {i+1}/27',flush=True);return
                except Exception:
                    if attempt==2:raise
                    await asyncio.sleep(1)
    await asyncio.gather(*(one(i,text) for i,text in enumerate(LINES)))
def read_pcm(path):
    p=subprocess.run([M.FF,'-v','error','-i',str(path),'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True,check=True)
    return np.frombuffer(p.stdout,dtype='<f4').copy()
def savewav(path,data):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes((np.clip(data,-.98,.98)*32767).astype('<i2').tobytes())
def main():
    asyncio.run(speech())
    clips=[];times=[0.];rows=[]
    for i in range(27):
        data=read_pcm(ROOT/f'audio/lines/{i:02}.mp3')
        active=np.flatnonzero(np.abs(data)>.004)
        if not len(active):raise RuntimeError(f'Empty speech {i}')
        data=data[max(0,active[0]-int(.07*SR)):min(len(data),active[-1]+int(.12*SR))]
        peak=np.max(np.abs(data));data*=min(2.2,.78/peak)
        clips.append(data)
        duration=max(R.CUTS[i][1],len(data)/SR+.42)
        if i==26:duration+=.65
        end=math.ceil((times[-1]+duration)*30)/30
        rows.append({'text':LINES[i],'start':times[-1]+.12,'speech_end':times[-1]+.12+len(data)/SR,'shot_end':end})
        times.append(end)
    R.TIMES=times;R.LENGTH=times[-1]
    total=round(R.LENGTH*SR)
    spoken=np.zeros(total);duck=np.ones(total)
    for row,data in zip(rows,clips):
        a=round(row['start']*SR);b=a+len(data);spoken[a:b]+=data
        duck[max(0,a-int(.12*SR)):min(total,b+int(.18*SR))]=.42
    # Smooth ducking boundaries; music stays beneath the narration.
    kernel=np.ones(4410)/4410
    duck=np.convolve(np.pad(duck,(2205,2205),mode='edge'),kernel,mode='valid')[:total]
    music=read_pcm(M.BGM) if M.BGM.is_file() else np.zeros(total)
    if len(music)<total:music=np.tile(music,math.ceil(total/len(music)))
    music=music[:total]*.22*duck
    effects=np.zeros(total)
    for i,start in enumerate(times[:-1]):
        success=i==14;dur=.3 if success else .08;x=np.arange(round(SR*dur))/SR
        tone=.045*np.sin(2*np.pi*(784 if success else 440)*x)*np.exp(-x*(12 if success else 48))
        a=round(start*SR);effects[a:a+len(tone)]+=tone
    music[-SR:]*=np.linspace(1,0,SR)
    music[:SR//5]*=np.linspace(0,1,SR//5)
    mix=spoken+music+effects
    if np.max(np.abs(mix))>.96:mix*=.96/np.max(np.abs(mix))
    savewav(ROOT/'audio/旁白.wav',spoken)
    savewav(ROOT/'audio/完整混音.wav',mix)
    (ROOT/'旁白文案.txt').write_text('\n'.join(LINES),encoding='utf-8')
    (ROOT/'字幕.srt').write_text('\n\n'.join(f'{i+1}\n{R.timestamp(row["start"])} --> {R.timestamp(row["speech_end"])}\n{row["text"]}' for i,row in enumerate(rows)),encoding='utf-8')
    (ROOT/'review/timeline.json').write_text(json.dumps({'voice':VOICE,'rate':RATE,'times':times,'lines':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    # Pixel animation follows the newly measured timing, never cuts off a sentence.
    out=ROOT/'renders/小岛经济学-海蓝像素-中文旁白版.mp4'
    cmd=[M.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-i',str(ROOT/'audio/完整混音.wav'),'-t',str(R.LENGTH),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
    with open(ROOT/'review/render.log','w') as log:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        for n in range(round(R.LENGTH*30)):
            p.stdin.write(R.frame(n/30).tobytes())
            if n%300==0:print(f'Render {n/30:.0f}/{R.LENGTH:.1f}s',flush=True)
        p.stdin.close()
        if p.wait():raise RuntimeError('Encode failed')
    clean=out.with_name('小岛经济学-海蓝像素-仅旁白无配乐.mp4')
    subprocess.run([M.FF,'-y','-v','error','-i',str(out),'-i',str(ROOT/'audio/旁白.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(clean)],check=True)
    for f in [out,clean]:subprocess.run([M.FF,'-v','error','-i',str(f),'-f','null','-'],check=True)
    assert all(row['speech_end']<row['shot_end'] for row in rows)
    report={'duration':R.LENGTH,'voice':VOICE,'speech_segments':len(rows),'no_sentence_overlap':True,'full_decode':'passed','mix_peak':float(np.max(np.abs(mix))),'files':[{'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [out,clean]]}
    (ROOT/'review/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',R.LENGTH,flush=True)
if __name__=='__main__':main()
