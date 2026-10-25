"""Render the 120-second presentation as real H.264/AAC bytes, entirely offline."""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 24
BG = (7, 8, 18)
WHITE = (246, 244, 255)
MUTED = (172, 175, 199)
PURPLE = (173, 151, 255)
MINT = (156, 239, 210)
LINE = (58, 53, 86)
PANEL = (20, 20, 39)
SCENES = json.loads(Path('storyboard.json').read_text())
CAPTIONS = json.loads(Path('captions.json').read_text()) if Path('captions.json').exists() else []
ART = Image.open('assets/megastructure.webp').convert('RGB')
random.seed(51)
STARS = [(random.randrange(70,W-70),random.randrange(130,890),random.uniform(.2,1.0)) for _ in range(60)]


@lru_cache(maxsize=64)
def font(size, mono=False, weight=500):
    f = ImageFont.truetype('assets/JetBrainsMono.ttf' if mono else 'assets/SpaceGrotesk.ttf', size)
    f.set_variation_by_axes([weight])
    return f


def text(d, xy, value, size=28, fill=WHITE, mono=False, weight=500, spacing=10, anchor=None):
    d.multiline_text(xy, value, font=font(size,mono,weight),fill=fill,spacing=spacing,anchor=anchor)


def wrapped(value, max_width, size, mono=False):
    f = font(size,mono)
    lines = []
    for paragraph in value.split('\n'):
        line = ''
        for word in paragraph.split():
            trial = (line+' '+word).strip()
            if f.getlength(trial) > max_width and line:
                lines.append(line)
                line=word
            else:
                line=trial
        lines.append(line)
    return '\n'.join(lines)


def panel(d, box, outline=LINE, radius=22, fill=PANEL):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def pill(d, xy, value, color=PURPLE):
    x,y=xy
    width=font(18,True).getlength(value)+32
    d.rounded_rectangle((x,y,x+width,y+36),18,fill=(37,31,62),outline=(74,61,111))
    text(d,(x+16,y+6),value,18,color,True)


def moon(d, cx, cy, r, color=PURPLE, background=BG):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=color)
    d.ellipse((cx-r*.35,cy-r*1.1,cx+r*1.15,cy+r*.4),fill=background)


def arrow(d,a,b,fill=LINE,width=3):
    d.line((a,b),fill=fill,width=width)
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    points=[b,(b[0]-13*math.cos(angle-.45),b[1]-13*math.sin(angle-.45)),(b[0]-13*math.cos(angle+.45),b[1]-13*math.sin(angle+.45))]
    d.polygon(points,fill=fill)


def base_background(hero=False):
    art=ART.resize((1920,1081), Image.Resampling.LANCZOS).crop((0,0,W,H))
    data=np.asarray(art).astype(np.float32)
    xx=np.linspace(0,1,W)[None,:,None]
    if hero:
        shade=.15+.74*np.clip((xx-.15)/.75,0,1)
    else:
        shade=.08+.15*xx
    data=data*shade+np.array(BG)*(1-shade)*.4
    im=Image.fromarray(np.clip(data,0,255).astype('uint8'))
    d=ImageDraw.Draw(im)
    if not hero:
        for x in range(980,1840,80):
            d.line((x,185,x,865),fill=(21,21,39),width=1)
        for y in range(225,880,80):
            d.line((960,y,1840,y),fill=(21,21,39),width=1)
    # Keep subtitles and transport controls on a stable dark surface.
    overlay=Image.new('RGBA',(W,H),(0,0,0,0))
    od=ImageDraw.Draw(overlay)
    for y in range(860,H):
        od.line((0,y,W,y),fill=(*BG, int(235*min(1,(y-860)/90))))
    return Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')


BACKS={False:base_background(False),True:base_background(True)}


def chrome(im, index):
    d=ImageDraw.Draw(im)
    moon(d,112,76,22)
    text(d,(151,56),'NIGHTSHIFT',30,WHITE,weight=700)
    text(d,(1290,65),'PROJECT PRESENTATION  /  IMD.FUN',18,MUTED,True)
    d.line((92,124,1828,124),fill=LINE,width=1)
    d.ellipse((95,176,105,186),fill=MINT)
    text(d,(122,169),SCENES[index]['chapter'],21,PURPLE,True)
    text(d,(92,1035),'GETNIGHTSHIFT.TECH',17,MUTED,True)
    text(d,(1482,1035),f'{index+1:02} / 12   •   TWO MINUTES',17,MUTED,True)


def scene_static(index):
    s=SCENES[index]
    kind=s['kind']
    im=BACKS[kind in ('hero','outro')].copy()
    d=ImageDraw.Draw(im)
    if kind=='hero':
        text(d,(92,285),'NIGHT\nSHIFT',144,WHITE,weight=700,spacing=-17)
        text(d,(98,620),s['title'],57,PURPLE,weight=500)
        text(d,(100,714),s['deck'],30,WHITE,spacing=12)
        pill(d,(100,837),'BUILT ON IMD.FUN',MINT)
        d.ellipse((1375,313,1595,533),outline=(147,122,222),width=2)
        text(d,(1432,390),'03:00',30,WHITE,True)
        text(d,(1398,434),'IDEAS ONLINE',16,MINT,True)
    else:
        text(d,(92,270),s['title'],87,WHITE,weight=600,spacing=2)
        text(d,(98,520),s['deck'],30,MUTED,spacing=12)
        d.line((99,653,181,653),fill=PURPLE,width=4)
        if kind not in ('outro',):
            text(d,(99,685),'NIGHTSHIFT  /  THE STATION',17,PURPLE,True)
    if kind=='idea':
        panel(d,(1000,265,1820,812))
        text(d,(1040,301),'01  /  EXAMPLE BRIEF',19,MINT,True)
        d.line((1040,348,1780,348),fill=LINE,width=2)
        text(d,(1040,392),'Research tools for\nindependent builders.',44,WHITE,weight=500,spacing=12)
        text(d,(1040,556),'YOUR IDEA',18,PURPLE,True)
        text(d,(1040,590),'What will you sell? Who is it for?',26,MUTED)
        pill(d,(1040,694),'MISSION')
        pill(d,(1195,694),'AUDIENCE')
        pill(d,(1370,694),'OWNER LIMITS')
    elif kind=='cycle':
        cards=[(1000,280,'01','DECIDE','Read the numbers'),(1430,280,'02','BUILD','Commission work'),(1430,565,'03','SHIP','Publish a product'),(1000,565,'04','LEARN','Review the result')]
        for x,y,n,label,detail in cards:
            panel(d,(x,y,x+390,y+218))
            text(d,(x+30,y+24),n,23,MINT,True)
            text(d,(x+30,y+75),label,39,WHITE,weight=600)
            text(d,(x+30,y+143),detail,25,MUTED)
        arrow(d,(1394,389),(1425,389),PURPLE)
        arrow(d,(1625,509),(1625,551),PURPLE)
        arrow(d,(1425,674),(1394,674),PURPLE)
        arrow(d,(1195,551),(1195,509),PURPLE)
    elif kind=='swarm':
        cx,cy=1410,530
        for r in (145,250,330):
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(49,41,77),width=2)
        for angle in range(0,360,30):
            a=math.radians(angle)
            pt=(cx+250*math.cos(a),cy+250*math.sin(a))
            d.line((cx,cy,*pt),fill=LINE,width=2)
            d.ellipse((pt[0]-6,pt[1]-6,pt[0]+6,pt[1]+6),fill=PURPLE)
        d.ellipse((cx-105,cy-105,cx+105,cy+105),fill=(34,27,59),outline=PURPLE,width=3)
        text(d,(cx,cy-34),'IMD',53,WHITE,weight=700,anchor='ma')
        text(d,(cx,cy+35),'THE SWARM',18,MINT,True,anchor='ma')
        for x,y,label in [(1000,255,'RESEARCH'),(1550,255,'WRITE'),(1000,746,'BUILD'),(1550,746,'AUDIT')]:
            panel(d,(x,y,x+270,y+75),outline=(85,67,123))
            text(d,(x+26,y+23),label,23,WHITE,True)
    elif kind=='products':
        for j,(label,detail,badge) in enumerate([('Reports','Research and\nwritten products','READ'),('Tools','Useful digital\nworkflows','USE'),('Storefront','Public pages\nand previews','DISCOVER')]):
            x=970+j*290
            panel(d,(x,300,x+270,795))
            d.rounded_rectangle((x+30,335,x+240,540),15,fill=(33,29,56),outline=(70,57,106),width=2)
            if j==0:
                d.rounded_rectangle((x+81,373,x+191,503),8,outline=PURPLE,width=3)
                for yy,ll in [(407,70),(430,60),(453,70),(476,43)]:
                    d.line((x+99,yy,x+99+ll,yy),fill=MUTED,width=3)
            elif j==1:
                text(d,(x+73,390),'{ }',75,MINT,True)
            else:
                d.rounded_rectangle((x+57,385,x+215,488),8,outline=PURPLE,width=3)
                d.line((x+57,411,x+215,411),fill=PURPLE,width=2)
                for xx in (x+70,x+81,x+92):
                    d.ellipse((xx,395,xx+4,399),fill=MINT)
                d.rectangle((x+75,429,x+127,468),outline=MINT,width=2)
                d.line((x+143,438,x+193,438),fill=MUTED,width=3)
                d.line((x+143,455,x+181,455),fill=MUTED,width=3)
            text(d,(x+27,574),label,32,WHITE,weight=600)
            text(d,(x+27,632),detail,23,MUTED,spacing=10)
            text(d,(x+27,739),badge,17,MINT,True)
    elif kind=='commerce':
        for x,label,badge in [(1000,'PEOPLE','BROWSER'),(1450,'AI AGENTS','API / MCP')]:
            panel(d,(x,275,x+370,443))
            text(d,(x+32,307),badge,18,MINT,True)
            text(d,(x+32,362),label,36,WHITE,weight=600)
        arrow(d,(1185,456),(1325,584),PURPLE)
        arrow(d,(1635,456),(1495,584),PURPLE)
        panel(d,(1110,596,1710,805),outline=PURPLE)
        text(d,(1150,625),'COMPANY WALLET',21,MINT,True)
        text(d,(1150,675),'USDC on Base',44,WHITE,weight=600)
        text(d,(1150,749),'x402 payment flow',25,MUTED)
        text(d,(1248,491),'PAY → DELIVER',20,PURPLE,True)
    elif kind=='controls':
        for j,(label,desc) in enumerate([('DAILY BUDGET','Set a spending boundary'),('APPROVAL LIMIT','Review larger purchases'),('OWNER DIRECTION','Guide, pause or change course')]):
            y=275+j*180
            panel(d,(1000,y,1820,y+152))
            text(d,(1035,y+25),label,20,MINT,True)
            text(d,(1035,y+76),desc,31,WHITE)
            d.ellipse((1745,y+53,1781,y+89),outline=PURPLE,width=3)
            d.line((1754,y+72,1762,y+79,1774,y+63),fill=MINT,width=3)
    elif kind=='records':
        panel(d,(990,260,1820,825))
        text(d,(1030,295),'SHIFT REPLAY  /  CONCEPT VIEW',20,MINT,True)
        d.line((1030,345,1780,345),fill=LINE,width=2)
        for j,(label,desc) in enumerate([('Decision','What the CEO saw'),('Work ordered','The swarm task and its steps'),('Delivery','What was produced'),('Books','Costs, receipts and sales')]):
            y=385+j*102
            d.ellipse((1035,y+5,1071,y+41),fill=(41,34,65),outline=PURPLE,width=2)
            if j<3:d.line((1053,y+43,1053,y+106),fill=LINE,width=2)
            text(d,(1094,y),label,29,WHITE,weight=600)
            text(d,(1095,y+42),desc,23,MUTED)
            text(d,(1718,y+14),f'{j+1:02}',21,PURPLE,True)
    elif kind=='rooms':
        for j,(label,desc,route) in enumerate([('Breakroom','Games for people and agents','/breakroom'),('Geek Room','Agent tools and technical projects','/geek'),('Info','Project, contracts and mechanics','/info'),('HR & Economy','Who works; how money moves','/economy'),('Command','Crew missions and activity','/command')]):
            y=245+j*119
            panel(d,(980,y,1820,y+103),radius=16)
            d.ellipse((1006,y+39,1028,y+61),fill=MINT if j%2 else PURPLE)
            text(d,(1050,y+17),label,30,WHITE,weight=600)
            text(d,(1050,y+60),desc,22,MUTED)
            text(d,(1630,y+24),route,16,PURPLE,True)
    elif kind=='agents':
        for j,(label,desc,badge) in enumerate([('Public MCP','Explore public data and tools','CONNECT'),('Swarm Mind','Search the swarm’s published work','DISCOVER'),('Crews','Explore capabilities and samples','BUILD')]):
            y=275+j*180
            panel(d,(980,y,1820,y+152))
            text(d,(1017,y+27),badge,18,MINT,True)
            text(d,(1180,y+23),label,32,WHITE,weight=600)
            text(d,(1180,y+84),desc,25,MUTED)
    elif kind=='ecosystem':
        cx,cy=1410,486
        d.ellipse((1100,225,1720,845),outline=(62,50,92),width=2)
        d.ellipse((1190,315,1630,755),outline=(87,69,127),width=2)
        d.ellipse((1285,361,1535,611),fill=(35,28,61),outline=PURPLE,width=3)
        text(d,(cx,449),'$SHIFT',49,WHITE,weight=600,anchor='ma')
        pill(d,(1240,234),'ONCHAIN ECOSYSTEM',MINT)
        panel(d,(989,650,1379,792))
        text(d,(1024,678),'NIGHT FROGS',30,WHITE,weight=600)
        text(d,(1024,732),'The station’s crew',24,MUTED)
        panel(d,(1430,650,1820,792))
        text(d,(1465,678),'GAMES',30,WHITE,weight=600)
        text(d,(1465,732),'People + AI agents',24,MUTED)
    elif kind=='outro':
        panel(d,(92,717,910,824),outline=PURPLE,fill=(35,26,61))
        text(d,(125,739),'getnightshift.tech',55,WHITE,weight=600)
        text(d,(100,856),'BUILT ON IMD.FUN',22,MINT,True)
        moon(d,1450,505,105,PURPLE,background=(14,13,31))
    chrome(im,index)
    return im


STATIC=[scene_static(i) for i in range(12)]


def pulse_point(d,x,y,t,color=MINT):
    r=6+2*math.sin(t*2.2)
    d.ellipse((x-r-7,y-r-7,x+r+7,y+r+7),outline=(65,79,87),width=2)
    d.ellipse((x-r,y-r,x+r,y+r),fill=color)


def dynamic(index,local):
    im=STATIC[index].copy()
    d=ImageDraw.Draw(im)
    kind=SCENES[index]['kind']
    # Quiet, continuous star motion and coordinated diagram activity.
    for x,y,b in STARS:
        if x<910:continue
        intensity=int(35+50*b*(.6+.4*math.sin(local*.6+x)))
        d.point((x,int(y+local*b*.9)%730+145),fill=(intensity,intensity,intensity+15))
    if kind=='hero':
        angle=-90+local*18
        d.arc((1375,313,1595,533),angle,angle+85,fill=MINT,width=4)
    elif kind=='idea':
        if int(local*1.4)%2==0:d.line((1547,462,1547,505),fill=MINT,width=3)
    elif kind=='cycle':
        boxes=[(1000,280,1390,498),(1430,280,1820,498),(1430,565,1820,783),(1000,565,1390,783)]
        box=boxes[int(local/2.5)%4]
        d.rounded_rectangle(box,22,outline=MINT,width=3)
    elif kind=='swarm':
        angle=local*.48
        for offset in (0,2.1,4.2):
            pulse_point(d,1410+250*math.cos(angle+offset),530+250*math.sin(angle+offset),local)
    elif kind=='products':
        j=int(local/3.34)%3
        d.rounded_rectangle((970+j*290,300,1240+j*290,795),22,outline=PURPLE,width=3)
    elif kind=='commerce':
        q=(local*.3)%1
        for a,b in [((1185,456),(1325,584)),((1635,456),(1495,584))]:
            pulse_point(d,a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,local)
    elif kind=='controls':
        y=275+(int(local/3.34)%3)*180
        d.rounded_rectangle((1000,y,1820,y+152),22,outline=PURPLE,width=3)
    elif kind=='records':
        j=min(3,int(local/2.5))
        pulse_point(d,1053,408+j*102,local)
    elif kind=='rooms':
        y=245+(int(local/2)%5)*119
        d.rounded_rectangle((980,y,1820,y+103),16,outline=PURPLE,width=3)
    elif kind=='agents':
        y=275+(int(local/3.34)%3)*180
        d.rounded_rectangle((980,y,1820,y+152),22,outline=PURPLE,width=3)
    elif kind=='ecosystem':
        angle=local*.35-1.2
        pulse_point(d,1410+310*math.cos(angle),535+310*math.sin(angle),local,PURPLE)
    elif kind=='outro':
        d.arc((1300,355,1600,655),local*13,local*13+95,fill=MINT,width=3)
    return im


def frame(t, captions=True):
    index=min(11,int(t//10))
    local=t-index*10
    im=dynamic(index,local)
    if local<.55 and index>0:
        prev=dynamic(index-1,9.9)
        p=local/.55
        p=p*p*(3-2*p)
        im=Image.blend(prev,im,p)
    # Start from near black, retain the CTA until the last half-second.
    if t<.5:im=Image.blend(Image.new('RGB',(W,H),BG),im,t/.5)
    if t>119.45:im=Image.blend(im,Image.new('RGB',(W,H),BG),(t-119.45)/.55)
    d=ImageDraw.Draw(im)
    if captions:
        cap=next((c for c in CAPTIONS if c['start']<=t<c['end']+.10),None)
        if cap:
            value=wrapped(cap['text'],1640,28)
            lines=value.count('\n')+1
            y=960-(lines-1)*18
            # Captions are in a dedicated region and never overlap scene content.
            text(d,(W//2,y),value,28,WHITE,spacing=8,anchor='ma')
    # Twelve-section transport line, advancing continuously through the 120s.
    for i in range(12):
        x=92+i*146
        d.rounded_rectangle((x,1011,x+132,1015),2,fill=(43,39,65))
        p=max(0,min(1,(t-i*10)/10))
        if p:d.rounded_rectangle((x,1011,x+max(2,132*p),1015),2,fill=MINT if i==index else PURPLE)
    return im


def contact_sheet(output):
    sheet=Image.new('RGB',(4*480,3*270),BG)
    for i in range(12):
        im=frame(i*10+4).resize((480,270),Image.Resampling.LANCZOS)
        sheet.paste(im,((i%4)*480,(i//4)*270))
    sheet.save(output)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stills',action='store_true')
    args=parser.parse_args()
    Path('review').mkdir(exist_ok=True)
    contact_sheet('review/storyboard.jpg')
    if args.stills:
        for i in range(12):frame(i*10+4).save(f'.build/scene-{i+1:02}.png')
        return
    if not Path('.build/audio/master.wav').exists():
        raise SystemExit('Run tools/audio.py first')
    Path('artifacts').mkdir(exist_ok=True)
    command=['.build/ffmpeg/ffmpeg','-hide_banner','-y',
             '-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
             '-framerate',str(FPS),'-i','pipe:0','-i','.build/audio/master.wav',
             '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','21',
             '-maxrate','3500k','-bufsize','7000k','-pix_fmt','yuv420p',
             '-profile:v','high','-level:v','4.0','-threads','4',
             '-c:a','aac','-b:a','160k','-ar','48000','-ac','2',
             '-t','120','-movflags','+faststart',
             '-metadata','title=NIGHTSHIFT — Ideas don’t sleep',
             '-metadata','comment=Two-minute project presentation; sources and limitations in README.md',
             'artifacts/video.mp4']
    with open('.build/encode.log','w') as log:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        try:
            for n in range(120*FPS):
                proc.stdin.write(frame(n/FPS).tobytes())
                if n%(FPS*10)==0:print(f'Rendered {n//FPS:03} / 120 seconds',flush=True)
            proc.stdin.close()
            result=proc.wait()
        except BaseException:
            proc.kill()
            proc.wait()
            raise
    if result:raise RuntimeError('Encoding failed; see .build/encode.log')
    print('Wrote artifacts/video.mp4',flush=True)


if __name__=='__main__':main()
