"""Original procedural pixel animation. Every frame is a pure function of time.
Usage: python make_film.py review|sample|full|verify
Output 1920x1080 / 30 fps / 132 sec, no narration.
"""
from pathlib import Path
import sys, math, json, subprocess, hashlib, shutil, wave, bisect, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
sys.path.insert(0,str(BASE/'.tools'))
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
STORY=json.loads((ROOT/'story.json').read_text(encoding='utf-8'))
FPS=30; LENGTH=len(STORY)*4; W,H=1920,1080; PW,PH=640,360
GOLD='#f2cf87'; WHITE='#f2edda'; MUTED='#94b3b9'; TEAL='#6ed5c2'; RED='#e68c82'
BGM=Path(os.environ.get('BGM_PATH', str(ROOT/'audio/bgm.mp3')))
for folder in ['renders','review','audio']:(ROOT/folder).mkdir(exist_ok=True)
TIMES=[i*4.0 for i in range(len(STORY)+1)]
if (ROOT/'audio/analysis.json').exists():
    onsets=json.loads((ROOT/'audio/analysis.json').read_text(encoding='utf-8'))['onsets']
    for i in range(1,len(STORY)):
        close=[s for s in onsets if abs(s-i*4)<.22]
        if close:TIMES[i]=min(close,key=lambda s:abs(s-i*4))

def clamp(x,a=0,b=1):return max(a,min(b,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def mix(a,b,x):return a+(b-a)*x
def phase(t,period=1):return (t%period)/period
@lru_cache(None)
def fnt(size,bold=False):
    return ImageFont.truetype(os.environ.get('CHINESE_FONT_BOLD' if bold else 'CHINESE_FONT', 'C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,words,size=30,fill=WHITE,bold=False,anchor=None):
    d.text(xy,str(words),font=fnt(size,bold),fill=fill,anchor=anchor)
def ct(d,y,words,size=40,fill=WHITE,bold=False):
    text(d,(W/2,y),words,size,fill,bold,'mt')
def label(d,x,y,words,size=28,fill=MUTED):text(d,(x,y),words,size,fill,False,'mt')
def rect(d,box,fill):d.rectangle(tuple(round(v) for v in box),fill=fill)
def poly(d,points,fill):d.polygon([(round(x),round(y)) for x,y in points],fill=fill)

def fish(d,x,y,s=1,color='#9cddd7',flip=False,alpha=1):
    # Eleven-pixel fish, deliberately drawn with square edges.
    def r(a,b,c,e,col):
        xx=x+(-c if flip else a)*s; xxx=x+(-a if flip else c)*s
        rect(d,(xx,y+b*s,xxx,y+e*s),col)
    r(-5,-2,3,2,color);r(-3,-3,1,3,color);r(3,-1,5,1,color)
    r(-8,-3,-6,3,color);r(-6,-2,-5,2,color)
    r(1,-1,2,0,'#132c3c');r(-3,-2,-1,-1,'#d8f3dd')

def person(d,x,y,t=0,shirt=TEAL,action='idle',scale=1,flip=False):
    # y is feet. local 14x29 sprite.
    s=scale; bob=0 if action=='rest' else (int(t*4)%2 if action in ['walk','fish','weave'] else 0)
    y-=bob*s
    def r(a,b,c,e,col):
        aa=-c if flip else a; cc=-a if flip else c
        rect(d,(x+aa*s,y+b*s,x+cc*s,y+e*s),col)
    dark='#243341'; skin='#e8b48a'; hair='#513d35'
    r(-5,-27,4,-18,hair);r(-4,-25,4,-17,skin);r(-5,-28,4,-25,hair)
    r(-5,-24,-3,-21,hair);r(2,-23,3,-22,dark)
    r(-4,-16,4,-7,shirt);r(-5,-16,-4,-9,shirt)
    r(-4,-7,4,-3,dark)
    if action=='walk':
        stride=2 if int(t*5)%2 else -2
        r(-4,-3,-1,0+stride,dark);r(1,-3,4,0-stride,dark)
    elif action=='rest':
        r(-4,-3,8,0,dark);r(7,-2,11,0,skin)
    else:r(-4,-3,-1,0,dark);r(1,-3,4,0,dark)
    if action in ['fish','weave']:
        yy=-13+(int(t*5)%2)*2
        r(4,yy,9,yy+3,skin)
    else:r(4,-14,6,-7,skin)

def palm(d,x,y,s=1):
    for j in range(20):rect(d,(x+j*.18*s,y-j*2*s,x+3*s+j*.18*s,y-j*2*s+3*s),'#b58c5b')
    top=(x+4*s,y-39*s)
    for dx,dy in [(-26,-5),(-21,-17),(-3,-24),(20,-18),(27,-4),(19,6)]:
        poly(d,[top,(top[0]+dx*s*.5,top[1]+dy*s-3*s),(top[0]+dx*s,top[1]+dy*s),(top[0]+dx*s*.45,top[1]+dy*s+4*s)],'#397a65')
    rect(d,(top[0]-1*s,top[1]+2*s,top[0]+6*s,top[1]+7*s),'#b58c5b')

def hut(d,x,y,s=1):
    rect(d,(x-18*s,y-25*s,x+19*s,y),'#9d7853')
    rect(d,(x-13*s,y-22*s,x+14*s,y),'#b69563')
    poly(d,[(x-27*s,y-24*s),(x-7*s,y-47*s),(x+9*s,y-47*s),(x+27*s,y-24*s)],'#d0af72')
    for j in range(-18,20,6):d.line((int(x+j*s),int(y-25*s),int(x+(j*.4)*s),int(y-43*s)),fill='#9d8055',width=max(1,int(s)))
    rect(d,(x-4*s,y-18*s,x+6*s,y),'#263c3c');rect(d,(x-15*s,y-18*s,x-9*s,y-11*s),'#476969')

def basket(d,x,y,amount=0,s=1):
    rect(d,(x-17*s,y-8*s,x+17*s,y+12*s),'#785d42')
    rect(d,(x-19*s,y-10*s,x+19*s,y-6*s),'#c7a471')
    for j in range(-14,17,7):rect(d,(x+j*s,y-5*s,x+(j+2)*s,y+10*s),'#ac8959')
    if amount>0:
        for j in range(amount):fish(d,x+((j%2)*15-7)*s,y-(j//2)*6*s-10*s,.9*s)

def net(d,x,y,w=60,h=50,progress=1):
    col='#dcca97'; height=h*progress
    d.line((int(x-w/2),int(y-height),int(x+w/2),int(y-height)),fill=col,width=2)
    for i in range(9):
        xx=x-w/2+w*i/8
        d.line((int(xx),int(y-height),int(x+(xx-x)*.7),int(y)),fill=col,width=1)
    for j in range(7):
        p=j/6; yy=y-height+height*p; half=w/2*(1-.3*p)
        d.line((int(x-half),int(yy),int(x+half),int(yy)),fill=col,width=1)
    rect(d,(x-w/2-3,y-height-2,x-w/2+2,y-height+2),GOLD)
    rect(d,(x+w/2-2,y-height-2,x+w/2+3,y-height+2),GOLD)

def waves(d,t,top=130):
    for j in range(11):
        y=top+j*14
        for i in range(9):
            x=((i*88+j*37-t*(5+j%3))%730)-40
            width=9+(i*13+j*7)%24
            rect(d,(x,y,x+width,y+1),'#275565' if j%2 else '#366a75')
            if j%3==0:rect(d,(x+3,y+2,x+width-3,y+2),'#204a5d')

@lru_cache(None)
def sky():
    im=Image.new('RGB',(PW,PH),'#0d1d2b'); d=ImageDraw.Draw(im)
    for y in range(128):
        u=y/128; col=tuple(int(mix(a,b,u)) for a,b in zip((12,23,38),(35,61,73)))
        rect(d,(0,y,PW,y),col)
    rect(d,(0,128,640,360),'#183f53')
    rect(d,(0,128,640,130),'#64878a')
    return im

def landscape(t,kind='wide'):
    im=sky().copy();d=ImageDraw.Draw(im)
    for j in range(42):
        x=(j*137+29)%640;y=22+(j*71)%85
        if j%4:rect(d,(x,y,x+1,y+1),'#63818a')
    # Pixel moon and wind-driven cloud banks.
    rect(d,(501,38,515,55),'#e9dfb3');rect(d,(498,42,518,52),'#e9dfb3')
    for j in range(4):
        x=((j*173+t*.8)%750)-65;y=69+j%2*23
        rect(d,(x,y,x+61,y+7),'#354f60');rect(d,(x+13,y-5,x+39,y+9),'#354f60')
    waves(d,t)
    if kind=='wide':
        poly(d,[(107,235),(153,201),(244,188),(337,190),(435,209),(507,238),(485,266),(377,285),(237,286),(143,269)],'#325961')
        poly(d,[(116,228),(157,195),(244,183),(337,185),(440,204),(507,233),(480,259),(377,277),(237,277),(145,260)],'#c2a978')
        poly(d,[(144,220),(190,195),(280,189),(363,195),(428,213),(454,236),(405,250),(254,260),(182,249)],'#71906b')
        poly(d,[(157,217),(199,199),(286,194),(370,203),(420,220),(422,233),(352,246),(227,247)],'#53775b')
        hut(d,250,229,.85);hut(d,330,218,.7);palm(d,177,222,1.05);palm(d,402,238,1.15)
        for x,y in [(164,246),(365,257),(460,236),(302,265)]:rect(d,(x,y,x+4,y+2),'#d8c28e')
    else:
        poly(d,[(0,229),(130,218),(260,232),(360,217),(510,229),(640,220),(640,360),(0,360)],'#bba477')
        poly(d,[(0,231),(130,220),(260,234),(360,219),(510,231),(640,222),(640,235),(510,243),(360,231),(260,246),(130,232),(0,243)],'#dac393')
        poly(d,[(0,292),(95,278),(212,292),(360,269),(520,282),(640,270),(640,360),(0,360)],'#59745c')
        hut(d,88,288,1.3);palm(d,559,283,1.5);palm(d,610,295,1)
        for j in range(24):
            x=(j*73)%640;y=249+(j*31)%61
            rect(d,(x,y,x+3,y+1),'#9b8f68')
    return im

def close_canvas(t):
    im=landscape(t,'beach'); return im,ImageDraw.Draw(im)

def fish_catch(d,t,x=340,y=220,shirt=TEAL,use_net=False):
    person(d,x,y,t,shirt,'fish',2)
    if use_net:
        bob=math.sin(t*3)*3
        net(d,x+81,y-10+bob,70,49)
        fish(d,x+66,y-30+bob,1.3);fish(d,x+91,y-36+bob,1.3)
        d.line((x+15,y-27,x+46,y-59),fill='#c9ae7b',width=2)
    else:
        d.line((x+16,y-25,x+57,y-65),fill='#c9ae7b',width=2)
        d.line((x+57,y-65,x+76,y-6),fill='#9bb5b7',width=1)
        if phase(t,2)>0.5:
            rise=math.sin((phase(t,2)-.5)*math.pi*2)*27
            fish(d,x+76,y-6-rise,1.5)
        for j in range(3):rect(d,(x+65+j*8,y+2+(j%2)*2,x+69+j*8,y+2+(j%2)*2),'#91c6c6')

def card_scene(t):
    im=Image.new('RGB',(PW,PH),'#112734');d=ImageDraw.Draw(im)
    for x in range(20,640,24):
        for y in range(22,350,24):rect(d,(x,y,x+1,y+1),'#223e4a')
    return im,d

def draw_world(t,scene,local):
    u=local/4
    if scene in ['hook','island','title','next','question','sources']:
        im=landscape(t);d=ImageDraw.Draw(im)
        if scene not in ['sources','title']:
            for j,(x,y) in enumerate([(305,249),(355,239),(380,259)]):
                person(d,x,y,t+j,['#6ed5c2','#e68c82','#e0bd70'][j],'fish' if scene=='hook' else 'idle',1.3)
                if scene=='hook':
                    d.line((x+12,y-17,x+31,y-46),fill='#d3b886',width=1)
                    d.line((x+31,y-46,x+42,y-4),fill='#b2cdcd',width=1)
                    fish(d,x+42,y-5-abs(math.sin((t+j)*2))*8,1)
            if scene=='hook':
                for j in range(3):fish(d,270+j*54,270,1)
        if scene=='question':net(d,319,255,45,35)
        return im
    if scene in ['fishing','eat','idea','save','reserve','weave','net','work','learn','rest']:
        im,d=close_canvas(t)
        if scene=='fishing':
            fish_catch(d,t,300,235)
            person(d,193,255,t+1,RED,'fish',1.2);person(d,433,248,t+2,GOLD,'fish',1.2)
        elif scene=='eat':
            person(d,320,273,t,TEAL,'idle',2)
            if u<.65:fish(d,350-mix(0,20,smooth(u/.65)),241,1.8)
            basket(d,420,274,0,1.2)
        elif scene=='idea':
            person(d,287,270,t,TEAL,'idle',2)
            rect(d,(320,165,409,218),'#e3d5b0');rect(d,(318,168,411,215),'#e3d5b0')
            poly(d,[(325,215),(325,226),(335,215)],'#e3d5b0');net(d,365,207,49,30)
        elif scene in ['save','reserve']:
            person(d,223,271,t,TEAL,'fish',2)
            amount=min(4,1+int(clamp((t-44)/8)*4)) if scene=='save' else 4
            basket(d,401,273,amount,1.8)
            if scene=='save':
                xx=mix(265,395,smooth(phase(local,1.3)))
                fish(d,xx,235-19*math.sin(phase(local,1.3)*math.pi),1.5)
            else:
                net(d,306,268,57,39,.35)
        elif scene=='weave':
            basket(d,209,271,2 if t<60 else 1,1.5)
            person(d,310,270,t,TEAL,'weave',2)
            progress=mix(.25,1,clamp((t-56)/8))
            net(d,381,272,95,60,progress)
            rect(d,(354,273,358,294),'#8e704e');rect(d,(420,273,424,294),'#8e704e')
        elif scene=='net':
            fish_catch(d,t,270,237,use_net=True)
            basket(d,442,280,2,1.6)
        elif scene=='work':
            person(d,309,279,t,TEAL,'walk',2)
            for j in range(3):
                x=110+j*164
                rect(d,(x,187,x+79,235),'#8a775d');rect(d,(x+4,191,x+75,230),'#b7b19b')
                for k in range(3):rect(d,(x+12,200+k*8,x+64,202+k*8),'#667b76')
            # treadmill-like repeating footprints, still firmly on the island.
            for j in range(7):rect(d,((j*57-t*18)%430+100,291,(j*57-t*18)%430+107,294),'#c4b58b')
        elif scene=='learn':
            person(d,283,273,t,TEAL,'weave',2)
            rect(d,(326,245,387,250),'#a67d52');rect(d,(332,250,337,282),'#8a6549');rect(d,(377,250,382,282),'#8a6549')
            poly(d,[(330,231),(353,234),(353,247),(330,242)],'#e4d7b2');poly(d,[(353,234),(378,230),(378,242),(353,247)],'#d1c293')
            net(d,437,268,48,39)
        elif scene=='rest':
            person(d,320,275,t,TEAL,'rest',2)
            d.line((255,274,382,274),fill='#bda175',width=2)
            basket(d,441,275,2,1.4)
        return im
    im,d=card_scene(t)
    if scene in ['blueprint','choice','cost','risk']:
        if scene=='blueprint':
            net(d,320,260,190,135,smooth(u*.8+.2))
            person(d,200,292,t,TEAL,'weave',1.6)
        elif scene in ['choice','cost']:
            rect(d,(80,164,281,291),'#183d4b');rect(d,(359,164,560,291),'#284744')
            person(d,136,271,t,TEAL,'fish',1.4);fish(d,215,233,3)
            net(d,465,270,90,70);person(d,389,273,t,TEAL,'weave',1.3)
            if scene=='cost':
                overlay=Image.new('RGB',(PW,PH),'black');od=ImageDraw.Draw(overlay)
                # diagonal slash on the fishing alternative.
                d.line((92,285,270,174),fill=RED,width=3)
        else:
            net(d,235,267,100,77)
            net(d,425,267,100,77)
            rect(d,(421,231,428,249),'#112734')
            d.line((394,213,410,230,425,220,442,240),fill=RED,width=3)
            fish(d,240,240,1.7)
    elif scene in ['compare','productivity','optionfish','optiontime']:
        rect(d,(69,158,303,298),'#193844');rect(d,(337,158,571,298),'#204a4d')
        person(d,129,270,t,RED,'fish',1.65);fish(d,232,233,2)
        person(d,397,270,t,TEAL,'fish' if scene!='optiontime' else 'rest',1.65)
        net(d,462,270,69,59)
        fish(d,519,220,1.8)
        if scene!='optiontime':fish(d,519,247,1.8)
        if scene=='optionfish':basket(d,529,288,2,1)
        if scene=='optiontime':
            rect(d,(473,284,552,289),GOLD)
    elif scene in ['capital','chain']:
        person(d,136,274,t,TEAL,'weave',2)
        basket(d,241,267,3,1.4);net(d,376,270,92,74)
        for j in range(3):fish(d,507+j%2*25,228+j//2*20,1.5)
        for a in [284,430]:
            x=a+int(phase(t,1)*8)
            poly(d,[(x,230),(x+17,230),(x+17,224),(x+26,234),(x+17,244),(x+17,238),(x,238)],GOLD)
    elif scene in ['wealth','assets','skills','money']:
        centers=[170,320,470]
        for x in centers:rect(d,(x-64,175,x+64,290),'#1c3c47')
        if scene=='wealth':
            for j in range(5):
                rect(d,(286+j*7,230-j*5,338+j*7,239-j*5),'#c7a363')
                rect(d,(290+j*7,231-j*5,334+j*7,233-j*5),'#f0ce88')
        elif scene=='skills':
            basket(d,170,264,3,1.5);net(d,320,269,75,57)
            person(d,468,274,t,TEAL,'weave',2)
            for j in range(3):rect(d,(456+j*9,197-j*9,461+j*9,203-j*9),GOLD)
        elif scene=='money':
            rect(d,(130,216,208,254),'#87a88a');rect(d,(137,222,201,247),'#527c72')
            rect(d,(165,227,175,242),'#a9c39b');net(d,320,270,74,58)
            fish(d,470,234,3.2)
        else:
            basket(d,170,264,3,1.5);net(d,320,269,75,57)
            hut(d,470,270,1.2)
    return im

def render_frame(t):
    idx=min(len(STORY)-1,max(0,bisect.bisect_right(TIMES,t)-1));scene,subtitle,title,kicker=STORY[idx]
    local=(t-TIMES[idx])/(TIMES[idx+1]-TIMES[idx])*4
    low=draw_world(t,scene,local)
    im=low.resize((W,H),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
    # Editorial frame: generous clean subtitle area, restrained amber accents.
    d.rectangle((0,0,W,56),fill='#0b1824');d.rectangle((0,926,W,H),fill='#0b1824')
    text(d,(77,18),'小岛经济学',20,MUTED)
    text(d,(1840,18),'01 / 从一条鱼开始',20,MUTED,anchor='rt')
    if scene not in ['hook','title','sources','question','next']:
        ct(d,105,title,52,GOLD,True)
        ct(d,179,kicker,25,MUTED)
    elif scene=='hook':
        ct(d,121,title,62,GOLD,True);ct(d,210,kicker,23,MUTED)
    elif scene=='title':
        ct(d,126,'小 岛 经 济 学',91,GOLD,True)
        ct(d,251,kicker,35,WHITE)
        ct(d,312,'ISLAND ECONOMICS / CHAPTER 01',23,MUTED)
    elif scene in ['question','next']:
        ct(d,125,title,62,GOLD,True);ct(d,222,kicker,29,WHITE)
    elif scene=='sources':
        ct(d,100,title,51,GOLD,True)
        for j,line in enumerate(kicker.split('\n')):ct(d,182+j*45,line,27,WHITE)
    if scene in ['choice','cost']:
        label(d,540,462,'捕鱼',30,RED);label(d,1380,462,'织网',30,TEAL)
    if scene in ['compare','productivity','optionfish','optiontime']:
        label(d,558,456,'徒手：1 条 / 人天',29,RED)
        label(d,1362,456,'用网：2 条 / 人天',29,TEAL)
        if scene=='optiontime':
            label(d,1530,874,'半天劳动 + 半天空闲',22,GOLD)
    if scene in ['wealth','assets','skills','money'] and scene!='wealth':
        vals=['存粮','渔网','技能' if scene=='skills' else '房屋']
        if scene=='money':vals=['货币','生产工具','消费品']
        for x,val in zip([510,960,1410],vals):label(d,x,886,val,26,GOLD)
    if scene=='chain':
        for x,val in [(720,'储蓄'),(1130,'资本品'),(1550,'产出')]:label(d,x,876,val,25,GOLD)
    if scene=='risk':label(d,710,843,'可能成功',27,TEAL);label(d,1270,843,'也可能失败',27,RED)
    # Fixed footer: one sentence, no tiny text competing with story.
    ct(d,959,subtitle,42,WHITE,True)
    text(d,(78,1040),'寓言改编 · 数量为示意',19,MUTED)
    text(d,(1840,1040),f'{idx+1:02d} / {len(STORY):02d}',19,MUTED,anchor='rt')
    d.rectangle((78,1023,1840,1025),fill='#243e49')
    d.rectangle((78,1023,78+1762*t/LENGTH,1025),fill=GOLD)
    # Brief dark dip joins shots; frames remain deterministic.
    edge=min(local,4-local)
    if edge<.15:
        im=Image.blend(Image.new('RGB',(W,H),'#0b1824'),im,.55+.45*smooth(edge/.15))
    return im

def run(cmd,**kw):return subprocess.run([str(v) for v in cmd],check=True,**kw)
def analyze_audio():
    pcm=ROOT/'audio/music-analysis.wav'
    run([FF,'-y','-v','error','-i',BGM,'-vn','-ac','1','-ar','22050','-c:a','pcm_s16le',pcm])
    with wave.open(str(pcm),'rb') as w:
        sr=w.getframerate();arr=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
    hop=220;win=441
    energy=np.array([np.sqrt(np.mean(arr[i:i+win]**2)) for i in range(0,len(arr)-win,hop)])
    novelty=np.maximum(0,np.diff(energy,prepend=energy[0]))
    lags=range(int(60/150*sr/hop),int(60/65*sr/hop))
    corr=[float(np.dot(novelty[k:],novelty[:-k])) for k in lags]
    lag=list(lags)[int(np.argmax(corr))];bpm=60*sr/hop/lag
    peaks=[]
    for i in range(2,len(novelty)-2):
        if novelty[i]==max(novelty[i-2:i+3]) and novelty[i]>np.quantile(novelty,.88):
            sec=i*hop/sr
            if not peaks or sec-peaks[-1]>.28:peaks.append(round(sec,3))
    report={'source':str(BGM),'duration':len(arr)/sr,'estimated_bpm':round(bpm,2),'method':'RMS positive-difference autocorrelation, approximate; not a musical transcription','onsets':peaks,'music_sha256':hashlib.sha256(BGM.read_bytes()).hexdigest()}
    (ROOT/'audio/analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Audio analyzed:',round(bpm,2),'BPM (estimate),',len(peaks),'onsets',flush=True)
    return report

def make_audio():
    report=analyze_audio(); sr=44100
    events=np.zeros(int(LENGTH*sr),dtype=np.float32)
    rng=np.random.default_rng(20261026)
    # Quiet sea and short, original game-like action sounds.
    for sec,freq in [(s,440 if s<64 else 660) for s in range(0,LENGTH,4)]:
        n=int(sr*.15); tt=np.arange(n)/sr
        ping=(np.sin(2*np.pi*freq*tt)+.18*np.sin(4*np.pi*freq*tt))*np.exp(-tt*35)*.065
        start=int((sec+.18)*sr);events[start:start+n]+=ping
    for sec in [17.3,21.3,48.8,50.1,52.9,56.6,58.6,60.7,64.8,66.8,69.2,77.4,81.1]:
        n=int(sr*.25);tt=np.arange(n)/sr
        noise=rng.normal(0,1,n)*np.exp(-tt*20)*.022
        start=int(sec*sr);events[start:start+n]+=noise.astype(np.float32)
    wav=ROOT/'audio/events.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((np.clip(events,-1,1)*32767).astype('<i2').tobytes())
    run([FF,'-y','-v','error','-i',BGM,'-i',wav,'-filter_complex',f'[0:a]atrim=0:{LENGTH},asetpts=PTS-STARTPTS,volume=0.70,afade=t=in:d=1,afade=t=out:st={LENGTH-3}:d=3[m];[m][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.94[a]','-map','[a]','-c:a','pcm_s16le',ROOT/'audio/mix.wav'])

def srt():
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
    (ROOT/'字幕.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(TIMES[i])} --> {stamp(TIMES[i+1])}\n{row[1]}' for i,row in enumerate(STORY)),encoding='utf-8')
    lines=['# 小岛经济学 · 分镜表','\n132 秒 / 16:9 / 1920×1080 / 30fps / 像素动画 / 无旁白','\n| 时间 | 镜头 | 字幕 | 画面概念 |','|---|---|---|---|']
    for i,row in enumerate(STORY):lines.append(f'| {TIMES[i]:.3f}–{TIMES[i+1]:.3f}s | {row[0]} | {row[1]} | {row[2]} |')
    (ROOT/'storyboard.md').write_text('\n'.join(lines),encoding='utf-8')

def review():
    times=[1.5,9.5,17.5,29.5,37.5,45.5,49.5,57.5,65.5,69.5,81.5,89.5,101.5,109.5,117.5,125.5]
    sheet=Image.new('RGB',(1920,1080))
    for i,t in enumerate(times):
        im=render_frame(t); im.save(ROOT/f'review/frame-{t:05.1f}.png')
        thumb=im.resize((480,270),Image.Resampling.LANCZOS)
        td=ImageDraw.Draw(thumb);td.rectangle((0,0,65,23),fill='black');td.text((5,1),str(t)+'s',font=fnt(16),fill='white')
        sheet.paste(thumb,((i%4)*480,(i//4)*270))
    sheet.save(ROOT/'review/contact-sheet.jpg',quality=94)
    render_frame(65.5).save(ROOT/'封面预览.png')
    assert render_frame(65.5).tobytes()==render_frame(65.5).tobytes()
    for row in STORY:
        assert ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(row[1],font=fnt(42,True))<W-160,row[1]
    print('Review sheet, stills and caption width checks complete',flush=True)

def encode(start,end,name):
    out=ROOT/'renders'/name
    log=open(ROOT/'renders'/f'{name}.log','w',encoding='utf-8')
    cmd=[FF,'-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',FPS,'-i','-','-ss',start,'-i',ROOT/'audio/mix.wav','-map','0:v','-map','1:a','-t',end-start,'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out]
    p=subprocess.Popen([str(c) for c in cmd],stdin=subprocess.PIPE,stderr=log)
    try:
        for i in range(round(start*FPS),round(end*FPS)):
            p.stdin.write(render_frame(i/FPS).tobytes())
            if i%300==0:print(f'rendering {i/FPS:.0f}s / {end:.0f}s',flush=True)
        p.stdin.close()
        if p.wait()!=0:raise RuntimeError('ffmpeg failed; read log')
    except Exception:
        p.kill();raise
    finally:log.close()
    print('Completed:',out.name,flush=True)
    return out

def verify():
    files=list((ROOT/'renders').glob('*.mp4'))
    result={}
    for file in files:
        p=subprocess.run([FF,'-hide_banner','-i',str(file),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True)
        if p.returncode:raise RuntimeError('decode validation failed: '+file.name)
        stderr=p.stderr.decode('utf-8','replace')
        result[file.name]={'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'decode_exit':p.returncode,'log':stderr[-2200:]}
    (ROOT/'review/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Full video/audio decode verified:',len(files),'files',flush=True)

if __name__=='__main__':
    srt();cmd=sys.argv[1] if len(sys.argv)>1 else 'review'
    if cmd=='review':review()
    elif cmd=='audio':make_audio()
    elif cmd=='sample':
        if not (ROOT/'audio/mix.wav').exists():make_audio()
        encode(0,30,'小岛经济学-30秒样片.mp4')
    elif cmd=='full':
        if not (ROOT/'audio/mix.wav').exists():make_audio()
        encode(0,LENGTH,'小岛经济学-像素风-完整版.mp4');verify()
    elif cmd=='verify':verify()
