"""Produce the TV-news remix using FFmpeg and the Python standard library.

Requires the separately delivered original artifacts/video.mp4; no network calls.
Generated presenter plates are retained in assets/. Intermediate media is scratch.
"""
from pathlib import Path
import array
import json
import math
import subprocess
import textwrap
import wave

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / 'test/scratch/news'
SCRATCH.mkdir(parents=True, exist_ok=True)


def run(args):
    subprocess.run(args, check=True, cwd=ROOT)


def ff(*args):
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *args])


def mouth_clip(name, x, y, top, bottom):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i',
        f'assets/news-{name}.png', '-vf', 'scale=1280:720',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], cwd=ROOT)
    rows = [raw[((y+j)*1280+x)*3:((y+j)*1280+x+64)*3] for j in range(64)]
    with wave.open(str(SCRATCH / 'audio.wav')) as wav:
        samples = array.array('h', wav.readframes(wav.getnframes()))
    caps = json.loads((ROOT / 'captions.json').read_text())
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo',
        '-pixel_format', 'rgb24', '-video_size', '64x64', '-framerate', '24',
        '-i', '-', '-c:v', 'ffv1', str(SCRATCH / f'{name}-mouth.mkv')],
        stdin=subprocess.PIPE, cwd=ROOT)
    center = (top+bottom)/2
    for frame in range(2880):
        t = frame/24
        active = any(c['start'] <= t <= c['end'] for c in caps)
        chunk = samples[frame*1000:(frame+1)*1000]
        rms = math.sqrt(sum(s*s for s in chunk)/max(1,len(chunk)))/32768
        openness = min(1, max(0, (rms-.008)*13)) if active else 0
        openness *= .55 + .45*abs(math.sin(t*15.5))
        half = 2 + (bottom-top-4)/2 * openness
        a, b = center-half, center+half
        out = []
        for yy in range(64):
            if yy < a:
                sy = yy/a*top
            elif yy <= b:
                sy = top+(yy-a)/(b-a)*(bottom-top)
            else:
                sy = bottom+(yy-b)/(63-b)*(63-bottom)
            out.append(rows[max(0,min(63,round(sy)))])
        proc.stdin.write(b''.join(out))
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError('Mouth animation encoding failed')


def stamp(t):
    ms = round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def main():
    ff('-i', 'artifacts/video.mp4', '-vn', '-ac', '1', '-ar', '24000',
       '-c:a', 'pcm_s16le', str(SCRATCH/'audio.wav'))
    mouth_clip('anchor', 294, 208, 13, 43)
    mouth_clip('correspondent', 284, 183, 21, 49)
    caps = json.loads((ROOT/'captions.json').read_text())
    subtitle = '\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n' +
        '\n'.join(textwrap.wrap(c['text'], 87)) for i,c in enumerate(caps))+'\n'
    (ROOT/'news-captions.srt').write_text(subtitle)
    titles = [
        ('NIGHTSHIFT: THE AI COMPANY STATION', 'A technology project built on the IMD swarm'),
        ('FROM AN IDEA TO A COMPANY BRIEF', 'Define the product, audience and spending limits'),
        ('INSIDE THE CEO AGENT WORK CYCLE', 'Research / build / ship / learn'),
        ('SPECIALIST AGENTS, CONNECTED BY IMD', 'Research, writing, websites and contract audits'),
        ('TURNING COMPLETED WORK INTO PRODUCTS', 'Digital tools, research and public storefronts'),
        ('COMMERCE FOR PEOPLE AND AI AGENTS', 'Project design: x402 payments and USDC on Base'),
        ('THE OWNER SETS THE BOUNDARIES', 'Budgets, approvals and company controls'),
        ('A RECORD OF EACH COMPANY SHIFT', 'Decisions, work orders and spending'),
        ('INSIDE THE NIGHTSHIFT STATION', 'Five rooms connect the wider project'),
        ('TOOLS FOR AGENTS AND THEIR OWNERS', 'MCP connections, Swarm Mind and crews'),
        ('THE ECOSYSTEM AND THE RISKS', 'Companies can lose money; review the current terms'),
        ('EXPLORE THE PROJECT', 'getnightshift.tech / built on imd.fun'),
    ]
    font = 'assets/SpaceGrotesk.ttf'
    def text(s,x,y,size,color='white',extra=''):
        # Text is read from files, so punctuation never becomes filter syntax.
        p = SCRATCH/f'text-{len(list(SCRATCH.glob("text-*.txt"))):03}.txt'
        p.write_text(s)
        return f"drawtext=fontfile={font}:textfile={p.relative_to(ROOT)}:x={x}:y={y}:fontsize={size}:fontcolor={color}{extra}"
    filters = [
        '[0:v]scale=1280:720,setsar=1[a]',
        '[1:v]scale=1280:720,setsar=1[b]',
        '[a][2:v]overlay=294:208[a1]',
        '[b][3:v]overlay=284:183[b1]',
        "[a1][b1]overlay=enable='between(t,60,99.999)'[people]",
        '[people]scale=320:180:flags=area,scale=1280:720:flags=neighbor[pixel]',
        '[4:v]split=2[monitor][cut]',
        '[monitor]scale=640:360[screen]',
        '[pixel]drawbox=x=588:y=78:w=664:h=398:color=0x10152d:t=fill[set]',
        '[set][screen]overlay=600:98[studio]',
        '[cut]scale=1280:720[broll]',
        "[studio][broll]overlay=enable='between(t,16,19.99)+between(t,36,39.99)+between(t,56,59.99)+between(t,76,79.99)+between(t,96,99.99)+between(t,106,109.99)'[program]",
    ]
    layers = [
        'drawbox=x=24:y=22:w=302:h=44:color=0x08132c@0.95:t=fill',
        'drawbox=x=24:y=22:w=7:h=44:color=0x81ebd5:t=fill',
        text('SHIFT / TECH REPORT',43,30,25),
        'drawbox=x=846:y=22:w=410:h=36:color=0x08132c@0.95:t=fill',
        text('SYNTHETIC NEWS-STYLE PRESENTATION',859,31,17),
        'drawbox=x=0:y=514:w=1280:h=186:color=0x08132c@0.98:t=fill',
        'drawbox=x=24:y=489:w=227:h=29:color=0x80e4ce:t=fill',
        text('TECHNOLOGY / EXPLAINED',36,495,17,'0x07162c'),
        'drawbox=x=24:y=531:w=6:h=91:color=0xa78bfa:t=fill',
    ]
    for i,(title,deck) in enumerate(titles):
        extra = f":enable='gte(t,{i*10})*lt(t,{(i+1)*10})'"
        layers += [text(title,46,535,32,extra=extra), text(deck,46,581,23,'0xb9cadf',extra)]
    layers += [
        'drawbox=x=0:y=700:w=1280:h=20:color=0x214168:t=fill',
        text('NIGHTSHIFT  /  getnightshift.tech     |     IMD  /  imd.fun     |     PROJECT EXPLAINER  /  NOT A LIVE BROADCAST',28,702,13),
        "subtitles=news-captions.srt:fontsdir=assets:force_style='FontName=Space Grotesk,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00201308,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=12'",
        'fade=t=in:st=0:d=0.35,fade=t=out:st=119.5:d=0.5',
    ]
    filters.append('[program]'+','.join(layers)+'[out]')
    graph = SCRATCH/'filters.txt'
    graph.write_text(';\n'.join(filters))
    ff('-loop','1','-framerate','24','-i','assets/news-anchor.png',
       '-loop','1','-framerate','24','-i','assets/news-correspondent.png',
       '-i',str(SCRATCH/'anchor-mouth.mkv'),'-i',str(SCRATCH/'correspondent-mouth.mkv'),
       '-i','artifacts/video.mp4','-filter_complex_threads','2',
       '-filter_complex_script',str(graph),'-map','[out]','-map','4:a:0',
       '-t','120','-r','24','-c:v','libx264','-preset','fast','-crf','20',
       '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',
       '-movflags','+faststart','-metadata','title=NIGHTSHIFT | The technology report',
       '-metadata','comment=Fictional synthetic presenters; original project narration; animated pixelated newsroom.',
       'artifacts/video-v2.mp4')


if __name__ == '__main__':
    main()
