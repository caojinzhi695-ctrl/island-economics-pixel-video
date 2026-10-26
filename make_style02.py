"""Selected simple blue-ocean pixel film, original art, deterministic frames.
Usage: python make_style02.py review|sample|full|verify
"""
from pathlib import Path
import sys,math,bisect,subprocess,json,hashlib
from functools import lru_cache
from PIL import Image,ImageDraw
import make_film as M
ROOT=Path(__file__).parent/'style02';W,H=1920,1080;FPS=30;LENGTH=132
for folder in ['renders','review']:(ROOT/folder).mkdir(exist_ok=True)
BG=Image.open(ROOT/'assets/background.png').convert('RGB').resize((W,H),Image.Resampling.NEAREST)
ATLAS=Image.open(ROOT/'assets/sprites.png').convert('RGBA')
SPR=[]
for row in range(2):
    for col in range(3):
        a=ATLAS.crop((col*512,row*512,(col+1)*512,(row+1)*512))
        bb=a.getchannel('A').point(lambda v:255 if v>180 else 0).getbbox()
        SPR.append(a.crop(bb))
BLUE='#081a50';WHITE='#fffbe7';YELLOW='#ffdf6b';INK='#113c76';TEAL='#8df3ef'

def txt(d,x,y,s,size=43,color=WHITE,anchor='mt',bold=True,stroke=3):
    d.text((x,y),s,font=M.fnt(size,bold),fill=color,anchor=anchor,stroke_width=stroke,stroke_fill=BLUE)
def headline(d,s,size=57):
    while d.textlength(s,font=M.fnt(size,True))>W-180:size-=1
    txt(d,W/2,100,s,size,YELLOW,stroke=4)
@lru_cache(maxsize=90)
def sprite(index,height,flip=False):
    a=SPR[index];a=a.resize((round(a.width*height/a.height),height),Image.Resampling.NEAREST)
    return a.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else a
def actor(im,index,x,t,height=360,foot=769,flip=False):
    a=sprite(index,int(height),flip);bob=round(math.sin(t*2)*2)
    d=ImageDraw.Draw(im);d.ellipse((x-a.width*.26,foot-5,x+a.width*.26,foot+9),fill='#b7954f')
    im.paste(a,(round(x-a.width/2),round(foot-height+bob)),a)
def fish(im,x,y,size=1):
    a=Image.new('RGBA',(96,54));d=ImageDraw.Draw(a)
    d.polygon([(8,14),(8,40),(29,32),(29,20)],fill=BLUE)
    d.rectangle((27,9,77,44),fill=BLUE);d.rectangle((35,3,66,50),fill=BLUE)
    d.rectangle((30,14,76,38),fill='#17b7ef');d.rectangle((38,8,64,44),fill='#17b7ef')
    d.rectangle((33,24,74,33),fill='#e0ffff');d.rectangle((65,17,70,23),fill=BLUE)
    a=a.resize((round(96*size),round(54*size)),Image.Resampling.NEAREST)
    im.paste(a,(round(x-a.width/2),round(y-a.height/2)),a)
def badge(im,x,y,words,size=40,width=None,color=WHITE):
    d=ImageDraw.Draw(im);tw=d.textlength(words,font=M.fnt(size,True))
    bw=width or tw+55
    d.rectangle((x-bw/2,y-14,x+bw/2,y+size+30),fill=BLUE,outline='#9defff',width=4)
    txt(d,x,y,words,size,color,stroke=0)
def net(im,x,y,progress=1):
    d=ImageDraw.Draw(im);w,h=230,170
    for k in range(9):
        xx=x-w/2+w*k/8
        d.line((xx,y-h,xx+(x-xx)*.23*progress,y-h+h*progress),fill=BLUE,width=6)
        d.line((xx,y-h,xx+(x-xx)*.23*progress,y-h+h*progress),fill=YELLOW,width=3)
    for k in range(7):
        p=k/6
        if p<=progress:
            half=w/2*(1-.23*p)
            d.line((x-half,y-h+h*p,x+half,y-h+h*p),fill=YELLOW,width=4)
    d.line((x-w/2-9,y-h,x+w/2+9,y-h),fill=BLUE,width=10)
    d.line((x-w/2-9,y-h,x+w/2+9,y-h),fill=YELLOW,width=5)
def inventory(im,t,count):
    d=ImageDraw.Draw(im)
    for j in range(4):
        x=940+j*150
        d.rectangle((x-62,286,x+62,383),fill='#0a50bd',outline='#96edff',width=4)
        if j<count:fish(im,x,334,.9)
    txt(d,1165,240,'存下的口粮',32,WHITE)
def arrow(d,x,y):
    d.polygon([(x-28,y-9),(x+7,y-9),(x+7,y-24),(x+36,y),(x+7,y+24),(x+7,y+9),(x-28,y+9)],fill=YELLOW)

def frame(t):
    idx=min(32,max(0,bisect.bisect_right(M.TIMES,t)-1))
    scene,sub,title,kicker=M.STORY[idx];u=(t-M.TIMES[idx])/(M.TIMES[idx+1]-M.TIMES[idx]);im=BG.copy();d=ImageDraw.Draw(im)
    # Tiny moving waves add life without changing the selected simple art style.
    for j in range(10):
        x=(j*223-t*(12+j%3))%W;y=897+(j%3)*39
        d.rectangle((x,y,x+17+j%2*12,y+5),fill='#7deeff')
    if scene=='hook':
        headline(d,'每天忙到天黑，为什么还是没有余裕？' if idx==0 else '捕鱼 → 吃鱼 → 明天再来')
        actor(im,1 if u<.60 else 4,650,t,400)
        badge(im,1160,330,'1 天 → 1 条鱼',48,color=YELLOW)
        if u>.6:fish(im,1150,490-170*M.smooth((u-.6)/.4),1)
    elif scene=='title':
        headline(d,'小 岛 经 济 学',88)
        txt(d,960,241,'一张渔网，如何改变生活',40)
        actor(im,0,630,t,390)
    elif scene=='island':
        headline(d,'故事，从三个人开始')
        actor(im,0,400,t,340);actor(im,4,800,t+.7,340);actor(im,1,1210,t+1.4,340,flip=True)
    elif scene in ['fishing','eat']:
        headline(d,'工作一整天，只够吃一天')
        actor(im,1 if scene=='fishing' and u<.72 else 4 if u<.65 else 0,630,t,400)
        badge(im,1180,315,'1 条鱼 / 人天' if scene=='fishing' else '今日余粮：1 → 0',45,color=YELLOW)
        if scene=='fishing':
            fish(im,1060,520-90*math.sin(u*math.pi),1.1)
    elif scene in ['idea','blueprint']:
        headline(d,'如果，我有一张网呢？')
        actor(im,0 if scene=='idea' else 3,640,t,385)
        net(im,1150,523,.95 if scene=='idea' else .15+.85*M.smooth(u))
        badge(im,1150,568,'把好点子，变成工具',30)
    elif scene in ['choice','cost']:
        headline(d,'织网的这一天，就不能去捕鱼')
        actor(im,0,450,t,350)
        fish(im,920,380,1.5);net(im,1285,465)
        badge(im,920,540,'捕鱼',34);badge(im,1285,540,'织网',34)
        if scene=='cost':
            d=ImageDraw.Draw(im);d.line((805,285,1035,478),fill='#ff755f',width=9)
            badge(im,1060,214,'机会成本：放弃的最佳替代选择',33,color=YELLOW)
    elif scene=='risk':
        headline(d,'付出了，也不一定成功')
        actor(im,0,650,t,390)
        badge(im,1200,320,'织不好？',47);badge(im,1200,468,'捕不到鱼？',47)
    elif scene in ['save','reserve']:
        headline(d,'储蓄：没有被当期消费掉的部分' if idx==12 else '先留一点点，为未来腾出时间')
        actor(im,4 if scene=='save' else 0,600,t,385)
        count=min(4,1+int(max(0,t-44)/2)) if scene=='save' else 4
        inventory(im,t,count)
        badge(im,1170,463,'余粮 → 不用捕鱼的时间',32,color=YELLOW)
        txt(ImageDraw.Draw(im),1170,558,'食物可以保存；数量为示意',24,WHITE)
    elif scene=='weave':
        headline(d,'鱼支持生活，劳动和材料变成渔网')
        actor(im,3,640,t,365+round(math.sin(t*4)*2))
        net(im,1170,514,.15+.85*M.smooth((t-56)/8))
        badge(im,1170,566,'投资：把资源用于生产工具',30,color=YELLOW)
    elif scene=='net':
        headline(d,'这一次，一天捕到了两条鱼！')
        actor(im,2,700,t,420)
        badge(im,1180,319,'1 条 → 2 条',59,color=YELLOW)
        for k in range(6):
            ang=k*math.pi/3;xx=1120+math.cos(ang)*(80+u*25);yy=470+math.sin(ang)*(80+u*25)
            d=ImageDraw.Draw(im);d.rectangle((xx,yy,xx+8,yy+8),fill=YELLOW)
    elif scene in ['compare','productivity','optionfish','optiontime']:
        headline(d,'同样的劳动，得到更多产出' if scene in ['compare','productivity'] else '多出来的效率，你可以怎么用？')
        actor(im,4,470,t,355);actor(im,5 if scene=='optiontime' else 2,1110,t,355)
        badge(im,470,300,'徒手：1 条 / 人天',34)
        badge(im,1110,300,'用网：2 条 / 人天',34,color=YELLOW)
        if scene=='productivity':badge(im,830,203,'劳动生产率 = 产出 ÷ 劳动投入',34,color=YELLOW)
        elif scene=='optionfish':badge(im,1130,820,'选择 A：吃 1 条，留 1 条',28)
        elif scene=='optiontime':badge(im,1110,820,'选择 B：半天劳动，半天空闲',27)
    elif scene in ['capital','chain']:
        headline(d,'渔网，是帮助生产的实物资本')
        actor(im,3,520,t,350);net(im,1000,530)
        if scene=='chain':
            for j,(x,word) in enumerate([(500,'储蓄'),(880,'投入'),(1240,'工具')]):badge(im,x,260,word,37)
            d=ImageDraw.Draw(im);arrow(d,690,280);arrow(d,1070,280)
        else:badge(im,1040,245,'资本品，不只是一笔钱',39,color=YELLOW)
    elif scene in ['work','learn','rest']:
        headline(d,'你的日常，有没有那条鱼？' if scene=='work' else '寻找自己的那张网' if scene=='learn' else '储蓄，是为了更好地生活')
        actor(im,0 if scene=='work' else 3 if scene=='learn' else 5,650,t,395)
        words=['每天的任务','自己的时间'] if scene=='work' else ['技能','工具','工作方法'] if scene=='learn' else ['休息','健康','生活体验']
        for j,word in enumerate(words):badge(im,1190,260+j*120,word,39,color=YELLOW if j==0 else WHITE)
    elif scene in ['wealth','assets','skills','money']:
        headline(d,'财富 = 钱？' if scene=='wealth' else '财富，不只有货币' if scene=='assets' else '还有看不见的积累' if scene=='skills' else '钱和网，各有作用')
        actor(im,0 if scene=='wealth' else 3 if scene=='skills' else 4,530,t,380)
        words=['先别急着回答'] if scene=='wealth' else ['存粮 · 渔网 · 房屋','资产价值 − 负债'] if scene=='assets' else ['知识 · 技能 · 经验','人力资本'] if scene=='skills' else ['钱：让交换更方便','网：让生产更有效']
        for j,word in enumerate(words):badge(im,1130,280+j*145,word,36,color=YELLOW if j==0 else WHITE)
    elif scene in ['question','next','sources']:
        actor(im,5,600,t,370)
        headline(d,'你自己的那张网，是什么？' if scene=='question' else '小岛经济学 · 第一章' if scene=='next' else '故事是模型，生活更复杂')
        words=['除了下一条鱼','你正在积累什么？'] if scene=='question' else ['下一章','鱼、借贷与货币'] if scene=='next' else ['故事：Peter D. Schiff / Andrew J. Schiff','概念：CORE Econ · OpenStax','鱼数为叙事设定，不是现实统计']
        for j,word in enumerate(words):badge(im,1150,250+j*110,word,27 if scene=='sources' else 38,color=YELLOW if j==0 else WHITE)
    # A small quiet subtitle strip keeps the selected sea palette visible.
    overlay=Image.new('RGBA',(W,150),(6,26,73,190));im.paste(overlay,(0,930),overlay)
    d=ImageDraw.Draw(im)
    size=41
    while d.textlength(sub,font=M.fnt(size,True))>W-160:size-=1
    txt(d,960,965,sub,size,WHITE,stroke=1)
    d.rectangle((85,1040,1835,1043),fill='#247acc');d.rectangle((85,1040,85+1750*t/LENGTH,1043),fill=YELLOW)
    txt(d,84,35,'小岛经济学 / 01',24,WHITE,'lt',False,2)
    txt(d,1835,35,f'{idx+1:02d} / 33',23,WHITE,'rt',False,2)
    return im

def review():
    ts=[1.4,9.4,13.4,17.4,25.4,33.4,41.4,49.4,57.4,65.4,73.4,81.4,97.4,109.4,117.4,125.4]
    sheet=Image.new('RGB',(1920,1080))
    for i,t in enumerate(ts):
        im=frame(t);im.save(ROOT/f'review/{t:05.1f}.png');thumb=im.resize((480,270),Image.Resampling.LANCZOS)
        sheet.paste(thumb,((i%4)*480,(i//4)*270))
    sheet.save(ROOT/'review/contact-sheet.jpg',quality=94)
    frame(65.4).save(ROOT/'封面.png')
    assert frame(65.4).tobytes()==frame(65.4).tobytes()
    print('Selected style review saved, deterministic rendering checked',flush=True)
def encode(a,b,name):
    out=ROOT/'renders'/name;log=open(ROOT/'renders'/(name+'.log'),'w',encoding='utf-8')
    cmd=[M.FF,'-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',FPS,'-i','-','-ss',a,'-i',M.ROOT/'audio/mix.wav','-map','0:v','-map','1:a','-t',b-a,'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out]
    p=subprocess.Popen([str(v) for v in cmd],stdin=subprocess.PIPE,stderr=log)
    try:
        for n in range(round(a*FPS),round(b*FPS)):
            p.stdin.write(frame(n/FPS).tobytes())
            if n%300==0:print(f'02 rendering {n/FPS:.0f}s / {b:.0f}s',flush=True)
        p.stdin.close()
        if p.wait():raise RuntimeError('Encoding failed')
    except Exception:p.kill();raise
    finally:log.close()
    print('Saved',out,flush=True)
def verify():
    result={}
    for f in (ROOT/'renders').glob('*.mp4'):
        p=subprocess.run([M.FF,'-hide_banner','-i',str(f),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True)
        if p.returncode:raise RuntimeError('Decode failed: '+str(f))
        result[f.name]={'size':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'decode_exit':0,'log':p.stderr.decode('utf-8','replace')[-2400:]}
    (ROOT/'review/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('All selected style video and audio fully decoded',flush=True)
if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else 'review'
    if cmd=='review':review()
    elif cmd=='sample':encode(0,12,'小岛经济学-02风格-12秒样片.mp4')
    elif cmd=='full':encode(0,LENGTH,'小岛经济学-02海蓝像素-完整版.mp4');verify()
    elif cmd=='verify':verify()
