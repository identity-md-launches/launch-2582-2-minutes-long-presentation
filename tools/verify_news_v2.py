"""Verify the delivered remix without changing the original v1 inspection records."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess


if __name__ == '__main__':
    video = Path('artifacts/video-v2.mp4')
    def command(args):
        return subprocess.run(args, capture_output=True, text=True, check=True)
    meta = json.loads(command(['ffprobe','-v','error','-show_streams',
        '-show_format','-of','json',str(video)]).stdout)
    Path('review/news-v2-ffprobe.json').write_text(json.dumps(meta,indent=2)+'\n')
    v = next(s for s in meta['streams'] if s['codec_type']=='video')
    a = next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
    assert (v['width'],v['height'])==(1280,720)
    assert v['r_frame_rate']=='24/1' and int(v['nb_frames'])==2880
    assert abs(float(meta['format']['duration'])-120)<.05
    assert a['codec_name']=='aac' and a['channels']==2 and a['sample_rate']=='48000'
    assert video.stat().st_size < 64*1024*1024
    atoms=[]
    with video.open('rb') as stream:
        while True:
            offset=stream.tell()
            header=stream.read(8)
            if not header:
                break
            size,kind=struct.unpack('>I4s',header)
            if size==1:
                size=struct.unpack('>Q',stream.read(8))[0]
            if size==0:
                size=video.stat().st_size-offset
            assert size>=8
            atoms.append({'type':kind.decode('ascii'),'offset':offset,'size':size})
            stream.seek(offset+size)
    kinds=[atom['type'] for atom in atoms]
    assert kinds.index('moov')<kinds.index('mdat')
    decode=command(['ffmpeg','-v','error','-i',str(video),'-map','0:v:0',
        '-map','0:a:0','-f','null','-'])
    assert not decode.stderr.strip(), decode.stderr
    volume=command(['ffmpeg','-hide_banner','-i',str(video),'-vn','-af',
        'volumedetect','-f','null','-']).stderr
    mean=float(re.search(r'mean_volume: ([\-\d.]+) dB',volume)[1])
    peak=float(re.search(r'max_volume: ([\-\d.]+) dB',volume)[1])
    assert -30<mean<-8 and peak<0
    data={
        'output':str(video),'media_type':'video/mp4',
        'duration_seconds':float(meta['format']['duration']),
        'width':v['width'],'height':v['height'],'fps':24,'frame_count':int(v['nb_frames']),
        'video_codec':v['codec_name'],'pixel_format':v['pix_fmt'],
        'audio_codec':a['codec_name'],'audio_sample_rate':int(a['sample_rate']),
        'audio_channels':a['channels'],'audio_mean_dbfs':mean,'audio_peak_dbfs':peak,
        'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'faststart':True,'mp4_atoms':atoms,
        'full_decode':'passed; all video and audio decoded without errors',
    }
    data['limitations'] = [
        'Fictional generated human presenters; not filmed people or a real news broadcast.',
        'Speech-energy mouth animation is approximate, not phoneme-accurate lip synchronization.',
        'The single original synthetic narrator is retained across both presenter shots.',
        'Original project descriptions and music retained; no new live product verification.',
        'Browser compatibility checked by codecs, pixel format, faststart and full decode; no interactive browser playback check.',
    ]
    Path('review/news-v2-verification.json').write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(data,indent=2))
