"""Short, caption-led ocean pixel cut. No narration. Original files preserved."""
import math,bisect,json,wave,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import make_style02 as S
M=S.M
ROOT=M.ROOT/'style02-rhythm'
for name in ['renders','review','audio']:(ROOT/name).mkdir(parents=True,exist_ok=True)
# Source scene, duration, concise caption. Holds are longer for concepts than actions.
CUTS=[
(0,2.4,'每天忙不停，为什么还是没余裕？'),
(4,2.4,'忙一天 → 一条鱼'),(5,1.6,'吃完，明天重来'),
(3,2.4,'这座岛上，三个人都这样生活'),
(6,2.4,'一个人突然想到：换个方法！'),
(7,2.4,'做一张网，会不会更快？'),
(8,3.2,'但织网这天，就没空捕鱼'),
(9,3.2,'放弃的那条鱼，就是机会成本'),
(10,2.4,'而且，网也可能做不成'),
(11,2.4,'他决定：每天留一点口粮'),
(12,3.2,'产出里没被消费的部分，叫储蓄'),
(13,2.4,'存粮，换来不用捕鱼的时间'),
(14,2.4,'于是，他开始织网'),
(15,3.2,'口粮支持生活，劳动和材料变成网'),
(16,3.2,'成功了！一天，捕到两条鱼'),
(17,2.4,'同样一天：1 条 → 2 条'),
(18,3.2,'每单位劳动产出更多，生产率提高'),
(19,3.2,'可以多留一条鱼'),
(20,3.2,'也可以少干半天，多一点生活'),
(21,3.2,'这张网，就是帮助生产的资本品'),
(22,3.2,'不仅要积累，也要把资源用得更好'),
(24,3.2,'你的网，可以是技能、工具和方法'),
(25,2.4,'但生活，不该只剩忍耐'),
(26,2.4,'所以，财富只等于钱吗？'),
(29,3.2,'钱方便交换，网提高生产效率'),
(28,3.2,'知识和技能，也影响未来的收入'),
(30,4.0,'除了下一条鱼，你正在积累什么？')]
onsets=json.loads((M.ROOT/'audio/analysis.json').read_text(encoding='utf-8'))['onsets']
TIMES=[0.0]
nominal=0
for _,duration,_ in CUTS:
    nominal+=duration
    near=[x for x in onsets if abs(x-nominal)<.16]
    TIMES.append(round((min(near,key=lambda x:abs(x-nominal)) if near else nominal)*30)/30)
LENGTH=TIMES[-1]
STATE={}
def actor(im,index,x,t,height=360,foot=769,flip=False):
    """Pose changes plus anticipation, follow-through, steps and breathing."""
    scene=STATE['scene'];p=STATE['p'];local=STATE['local']
    jump=0;lean=0;sx=1;sy=1;dx=0
    if scene in ('hook','fishing'):
        cycle=(local/1.2)%1
        lean=(-7*math.sin(cycle*math.pi*2))
        sy=1-.035*math.sin(cycle*math.pi*2)
        dx=12*math.sin(cycle*math.pi*2)
    elif scene in ('idea','blueprint'):
        jump=22*max(0,math.sin(min(1,local/.65)*math.pi))
        lean=3*math.sin(local*4)
    elif scene in ('weave','learn','skills'):
        lean=4*math.sin(local*9);sy=1+.025*math.sin(local*9)
    elif scene=='net':
        cycle=(local/.8)%1
        jump=65*max(0,math.sin(cycle*math.pi))
        sx=1+.07*math.cos(cycle*math.pi*2);sy=1-.07*math.cos(cycle*math.pi*2)
        lean=5*math.sin(local*7)
    elif scene in ('risk','choice','cost'):
        lean=4*math.sin(local*3);dx=8*math.sin(local*3)
    elif scene in ('rest','optiontime','question'):
        sy=1+.012*math.sin(local*2.5)
    else:
        sy=1+.016*math.sin(local*5);lean=1.5*math.sin(local*3)
    # A brief walk-in uses alternating lateral steps and a footfall bob.
    if scene in ('island','save','work'):
        entry=max(0,1-local/.65)
        dx-=100*entry
        jump=abs(math.sin(local*13))*8*max(entry,.15)
        lean=3*math.sin(local*13)*max(entry,.15)
    a=S.sprite(index,int(height),flip)
    a=a.resize((round(a.width*sx),round(a.height*sy)),Image.Resampling.NEAREST)
    a=a.rotate(lean,resample=Image.Resampling.NEAREST,expand=True)
    d=ImageDraw.Draw(im);shadow=max(.6,1-jump/170)
    d.ellipse((x+dx-a.width*.24*shadow,foot-4,x+dx+a.width*.24*shadow,foot+10),fill='#b7954f')
    im.paste(a,(round(x+dx-a.width/2),round(foot-a.height-jump)),a)
    if scene in ('weave','learn'):
        # Small moving thread strokes follow the working pose.
        xx=x+45+math.sin(local*9)*13;yy=foot-height*.24
        d.line((xx-16,yy,xx+22,yy-12),fill=S.YELLOW,width=4)
        if int(local*8)%3==0:
            d.line((xx+35,yy-25,xx+35,yy-42),fill=S.WHITE,width=3)
            d.line((xx+27,yy-33,xx+43,yy-33),fill=S.WHITE,width=3)
S.actor=actor
def frame(t):
    i=min(len(CUTS)-1,bisect.bisect_right(TIMES,t)-1)
    old,_,caption=CUTS[i];local=t-TIMES[i];p=local/(TIMES[i+1]-TIMES[i])
    STATE.update(scene=M.STORY[old][0],p=p,local=local)
    src=M.TIMES[old]+min(.999,p)*(M.TIMES[old+1]-M.TIMES[old])
    im=S.frame(src)
    # Reframe only the stage; captions and headings remain stable and readable.
    stage=im.crop((0,185,1920,930))
    emphasis=old in (6,10,16,21,30)
    z=1+(.055 if emphasis else .022)*math.sin(p*math.pi/2)
    sw,sh=int(1920/z),int(745/z)
    cx=850 if old==16 else 960
    left=max(0,min(1920-sw,int(cx-sw/2)));top=(745-sh)//2
    stage=stage.crop((left,top,left+sw,top+sh)).resize((1920,745),Image.Resampling.NEAREST)
    im.paste(stage,(0,185))
    d=ImageDraw.Draw(im)
    # Cover old counters, replace with one quiet chapter label.
    im.paste(S.BG.crop((0,0,1920,75)),(0,0))
    chapter='01 生存循环' if i<4 else '02 换一种方法' if i<9 else '03 积累与投入' if i<14 else '04 效率带来选择' if i<21 else '05 你的那张网'
    S.txt(d,70,26,'小岛经济学',25,S.WHITE,'lt',stroke=2)
    S.txt(d,1850,26,chapter,25,S.WHITE,'rt',stroke=2)
    # Short impact accent at the successful catch, no whole-screen flash.
    if old==16 and local<.55:
        for k in range(12):
            ang=k*math.pi/6;r=95+local*220
            x=1180+math.cos(ang)*r;y=445+math.sin(ang)*r
            d.rectangle((x,y,x+9,y+9),fill=S.YELLOW)
    d.rectangle((0,930,1920,1080),fill='#061a49')
    d=ImageDraw.Draw(im)
    S.txt(d,960,956+int(10*max(0,1-local/.18)),caption,45,S.WHITE,stroke=1)
    note='故事设定：1 条 / 人天 → 2 条 / 人天' if 14<=i<=16 else '两种选择不同时实现；半天产出假设与时间成正比' if i in (17,18) else '改编自《小岛经济学》 · 简化模型，非现实统计' if i==26 else ''
    if note:S.txt(d,960,1015,note,22,'#a4dff1',stroke=0)
    d.rectangle((70,1061,1850,1066),fill='#247acc')
    d.rectangle((70,1061,70+1780*t/LENGTH,1066),fill=S.YELLOW)
    return im
def audio():
    raw=ROOT/'audio/music.wav'
    if M.BGM.is_file():
        subprocess.run([M.FF,'-y','-v','error','-i',str(M.BGM),'-t',str(LENGTH),'-ac','1','-ar','44100',str(raw)],check=True)
    else:
        with wave.open(str(raw),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(44100);f.writeframes(bytes(round(LENGTH*44100)*2))
    with wave.open(str(raw),'rb') as f:data=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float64)/32768
    sr=44100;data=data[:round(LENGTH*sr)]*.64
    # New accents are timed to the new edit, not inherited from the old 132s cut.
    for i,start in enumerate(TIMES[:-1]):
        success=CUTS[i][0]==16
        dur=.32 if success else .085
        x=np.arange(int(sr*dur))/sr
        tone=np.sin(2*np.pi*(784 if success else 440)*x)*np.exp(-x*(11 if success else 48))*.09
        if success:tone+=np.sin(2*np.pi*1176*x)*np.exp(-x*12)*.05
        a=round((start+.035)*sr);b=min(len(data),a+len(tone));data[a:b]+=tone[:b-a]
    fade=min(len(data),int(sr*1.1));data[-fade:]*=np.linspace(1,0,fade)
    data[:int(sr*.15)]*=np.linspace(0,1,int(sr*.15))
    data=np.clip(data,-.95,.95)
    with wave.open(str(ROOT/'audio/mix.wav'),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((data*32767).astype('<i2').tobytes())
def timestamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def run():
    audio()
    (ROOT/'字幕.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(TIMES[i])} --> {timestamp(TIMES[i+1])}\n{cut[2]}' for i,cut in enumerate(CUTS)),encoding='utf-8')
    (ROOT/'节奏分镜.json').write_text(json.dumps({'duration':LENGTH,'cuts':CUTS,'times':TIMES},ensure_ascii=False,indent=2),encoding='utf-8')
    sheet=Image.new('RGB',(1920,1080))
    for j,i in enumerate([0,3,4,6,9,12,14,15,17,18,21,26]):
        im=frame(TIMES[i]+.65);sheet.paste(im.resize((480,360)),((j%4)*480,(j//4)*360))
    sheet.save(ROOT/'review/contact-sheet.jpg')
    frame(TIMES[14]+.6).save(ROOT/'封面.png')
    out=ROOT/'renders/小岛经济学-海蓝像素-节奏增强-无旁白.mp4'
    cmd=[M.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-i',str(ROOT/'audio/mix.wav'),'-t',str(LENGTH),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
    with open(ROOT/'review/render.log','w') as log:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        for n in range(round(LENGTH*30)):
            p.stdin.write(frame(n/30).tobytes())
            if n%300==0:print(f'Render {n/30:.0f}/{LENGTH:.1f}s',flush=True)
        p.stdin.close()
        if p.wait():raise RuntimeError('Render failed')
    silent=out.with_name('小岛经济学-海蓝像素-节奏增强-纯画面.mp4')
    subprocess.run([M.FF,'-y','-v','error','-i',str(out),'-c:v','copy','-an',str(silent)],check=True)
    for f in [out,silent]:
        subprocess.run([M.FF,'-v','error','-i',str(f),'-f','null','-'],check=True)
    (ROOT/'review/verification.json').write_text(json.dumps({'duration':LENGTH,'frames':round(LENGTH*30),'resolution':'1920x1080','fps':30,'narration':False,'full_decode':'passed','outputs':[str(out),str(silent)]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',out,flush=True)
if __name__=='__main__':run()
