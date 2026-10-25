"""Check the submitted media bytes, fully decode them, and record the result."""
import hashlib
import json
from pathlib import Path
import re
import struct
import shutil
import subprocess

VIDEO=Path('artifacts/video.mp4')
PROBE=shutil.which('ffprobe') or '.build/ffmpeg/ffprobe'
FFMPEG=shutil.which('ffmpeg') or '.build/ffmpeg/ffmpeg'


def main():
    probe=subprocess.run([PROBE,'-v','error','-show_streams','-show_format','-of','json',str(VIDEO)],
                         capture_output=True,text=True,check=True)
    meta=json.loads(probe.stdout)
    Path('review/ffprobe.json').write_text(json.dumps(meta,indent=2)+'\n')
    video=next(s for s in meta['streams'] if s['codec_type']=='video')
    audio=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert video['codec_name']=='h264'
    assert video['pix_fmt']=='yuv420p'
    assert (video['width'],video['height'])==(1920,1080)
    assert video['r_frame_rate']=='24/1'
    assert int(video['nb_frames'])==2880
    assert abs(float(meta['format']['duration'])-120)<.05
    assert audio['codec_name']=='aac'
    assert audio['channels']==2 and audio['sample_rate']=='48000'
    assert VIDEO.stat().st_size < 64*1024*1024
    atoms=[]
    with VIDEO.open('rb') as stream:
        while True:
            offset=stream.tell()
            header=stream.read(8)
            if not header:break
            size,kind=struct.unpack('>I4s',header)
            if size==1:size=struct.unpack('>Q',stream.read(8))[0]
            if size==0:size=VIDEO.stat().st_size-offset
            assert size>=8
            atoms.append({'type':kind.decode('ascii'),'offset':offset,'size':size})
            stream.seek(offset+size)
    types=[a['type'] for a in atoms]
    assert types.index('moov')<types.index('mdat'),'MP4 needs faststart'
    decode=subprocess.run([FFMPEG,'-hide_banner','-v','error','-i',str(VIDEO),
                           '-map','0:v:0','-map','0:a:0','-f','null','-'],
                          capture_output=True,text=True,check=True)
    assert not decode.stderr.strip(), decode.stderr
    volume=subprocess.run([FFMPEG,'-hide_banner','-i',str(VIDEO),'-vn',
                           '-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True)
    mean=float(re.search(r'mean_volume: ([\-\d.]+) dB',volume.stderr)[1])
    peak=float(re.search(r'max_volume: ([\-\d.]+) dB',volume.stderr)[1])
    assert -30<mean<-8, 'Unexpectedly quiet or loud audio'
    assert peak<0, 'Audio peak has no headroom'
    loudness=subprocess.run([FFMPEG,'-hide_banner','-i',str(VIDEO),'-vn',
                             '-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json',
                             '-f','null','-'],capture_output=True,text=True,check=True)
    measured,_=json.JSONDecoder().raw_decode(loudness.stderr[loudness.stderr.rfind('{'):])
    result={
        'output':'artifacts/video.mp4','media_type':'video/mp4','duration_seconds':float(meta['format']['duration']),
        'width':video['width'],'height':video['height'],'fps':24,'frame_count':int(video['nb_frames']),
        'video_codec':'h264','profile':video['profile'],'pixel_format':video['pix_fmt'],
        'audio_codec':'aac','audio_sample_rate':int(audio['sample_rate']),'audio_channels':audio['channels'],
        'bytes':VIDEO.stat().st_size,'mib':round(VIDEO.stat().st_size/(1024*1024),2),
        'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'faststart':True,'mp4_atoms':atoms,
        'full_decode':'passed: every audio and video packet decoded, no errors',
        'audio_mean_dbfs':mean,'audio_peak_dbfs':peak,'integrated_loudness_lufs':float(measured['input_i']),
        'true_peak_dbtp':float(measured['input_tp']),'loudness_range_lu':float(measured['input_lra']),
        'limitations':['Motion graphics are explanatory illustrations, not a recording of live product interactions.',
                        'Project functionality and financial claims were not independently audited.',
                        'Narration uses a synthetic voice; source information is a 2026-10-25 snapshot.',
                        'No browser playback session was available; compatibility was checked through codecs, pixel format, MP4 structure and full decoding.']}
    Path('review/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
