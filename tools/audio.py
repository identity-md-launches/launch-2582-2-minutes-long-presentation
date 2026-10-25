"""Create a timed neural narration and an original, deterministic electronic score."""
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

FFMPEG = '.build/ffmpeg/ffmpeg'
WORK = Path('.build/audio')
WORK.mkdir(parents=True, exist_ok=True)
SCENES = json.loads(Path('storyboard.json').read_text())
RATE = 48000


def write_wav(path, data, rate=RATE):
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1 if data.ndim == 1 else data.shape[1])
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes((np.clip(data, -1, 1) * 32767).astype('<i2').tobytes())


def load_wav(path):
    with wave.open(str(path), 'rb') as wav:
        return np.frombuffer(wav.readframes(wav.getnframes()), '<i2').astype(np.float32) / 32768, wav.getframerate()


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def main():
    voice = PiperVoice.load('.build/en_US-ljspeech-high.onnx', 'vendor/en_US-ljspeech-high.onnx.json')
    config = SynthesisConfig(length_scale=0.96, noise_scale=0.5, noise_w_scale=0.65)
    narration = np.zeros(120 * RATE, dtype=np.float32)
    captions = []
    for i, scene in enumerate(SCENES):
        parts = []
        for j, sentence in enumerate(scene['voice']):
            raw = WORK / f'{i:02}-{j}-raw.wav'
            if not raw.exists():
                with wave.open(str(raw), 'wb') as wav:
                    voice.synthesize_wav(sentence, wav, config)
            data, rate = load_wav(raw)
            # Remove long generated tails, retain a little breath room.
            active = np.flatnonzero(np.abs(data) > .006)
            if len(active):
                data = data[max(0, active[0]-int(rate*.04)):min(len(data), active[-1]+int(rate*.14))]
            parts.append((sentence, data, rate))
        natural = sum(len(a)/r for _, a, r in parts) + .18*(len(parts)-1)
        speed = max(1.0, natural / 8.75)
        cursor = i * 10 + .65
        for j, (sentence, data, rate) in enumerate(parts):
            trimmed = WORK / f'{i:02}-{j}-trim.wav'
            write_wav(trimmed, data, rate)
            fitted = WORK / f'{i:02}-{j}.wav'
            subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(trimmed),
                            '-af', f'atempo={speed:.6f},loudnorm=I=-18:TP=-2:LRA=7',
                            '-ar', str(RATE), '-ac', '1', str(fitted)], check=True)
            sample, rate = load_wav(fitted)
            start = round(cursor * RATE)
            assert start + len(sample) <= (i+1)*10*RATE, f'Voice overflow in scene {i+1}'
            narration[start:start+len(sample)] += sample
            end = cursor + len(sample)/RATE
            display = sentence.replace('I M D', 'IMD').replace('M C P', 'MCP').replace('H R', 'HR')
            display = display.replace('X four oh two', 'x402').replace('U S D C', 'USDC')
            display = display.replace('Get Nightshift dot tech.', 'getnightshift.tech.').replace('I M D dot fun', 'imd.fun')
            display = display.replace('IMD dot fun', 'imd.fun')
            captions.append({'start':cursor, 'end':end, 'text':display, 'scene':i})
            cursor = end + .18
        print(f'Scene {i+1:02}: natural {natural:.2f}s; tempo {speed:.3f}; last word at {cursor-.18-i*10:.2f}s', flush=True)
    write_wav(WORK/'narration.wav', narration)
    Path('captions.json').write_text(json.dumps(captions, indent=2)+'\n')
    Path('captions.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(c["start"])} --> {timestamp(c["end"])}\n{c["text"]}' for i,c in enumerate(captions))+'\n')
    # An original 80 BPM D-minor bed, designed to sit under speech.
    rng = np.random.default_rng(42)
    score = np.zeros((120*RATE, 2), dtype=np.float32)
    chords = [(50,57,62,65), (46,53,58,62), (48,55,60,64), (43,50,57,62)]
    for bar in range(12):
        chord = chords[bar % 4]
        local = np.arange(10*RATE, dtype=np.float32)/RATE
        envelope = np.minimum(local/1.8, 1)*np.minimum((10-local)/2.2, 1)
        for n, midi in enumerate(chord):
            freq = 440*2**((midi-69)/12)
            for channel, detune in enumerate((.9988, 1.0012)):
                tone = np.sin(2*math.pi*freq*detune*local+n*.73)
                tone += .2*np.sin(2*math.pi*freq*2*detune*local+n)
                score[bar*10*RATE:(bar+1)*10*RATE,channel] += tone*envelope*.0075
    for beat in np.arange(0, 120, .75):
        start = int(beat*RATE)
        duration = min(int(.4*RATE), len(score)-start)
        local = np.arange(duration)/RATE
        kick = np.sin(2*math.pi*(44*local + 3.5*(1-np.exp(-local*28))))*np.exp(-local*16)*.026
        score[start:start+duration] += kick[:,None]
        # Airy offbeat, softly panned; no sample library.
        off = start + int(.375*RATE)
        length = min(int(.13*RATE), len(score)-off)
        if length > 0:
            tt = np.arange(length)/RATE
            noise = rng.normal(0,1,length).astype(np.float32)
            noise[1:] -= noise[:-1]*.85
            hat = noise*np.exp(-tt*58)*.0022
            score[off:off+length,0] += hat
            score[off:off+length,1] += hat*.6
    # Bell-like arpeggio: gentle lift after the opening and into the finale.
    for k, moment in enumerate(np.arange(1.5,119,.75)):
        chord = chords[int(moment//10)%4]
        freq = 440*2**((chord[k%4]+12-69)/12)
        n = min(int(2.2*RATE),len(score)-int(moment*RATE))
        local = np.arange(n)/RATE
        env = (1-np.exp(-local*100))*np.exp(-local*2.6)
        pluck = (np.sin(2*math.pi*freq*local)+.25*np.sin(2*math.pi*freq*2.003*local))*env*.009
        start = int(moment*RATE)
        score[start:start+n,k%2] += pluck
        score[start:start+n,1-k%2] += pluck*.45
    # Smooth manual ducking keyed to the known voice timing.
    duck = np.ones(120*RATE, dtype=np.float32)
    for cap in captions:
        a,b = int(max(0,cap['start']-.2)*RATE),int(min(120,cap['end']+.35)*RATE)
        duck[a:b] = .53
    smooth = np.convolve(duck[::480], np.ones(31)/31, mode='same')
    duck = np.interp(np.arange(len(duck)), np.arange(len(smooth))*480, smooth)
    fade = np.minimum(np.arange(120*RATE)/(RATE*2),1)*np.minimum((120*RATE-1-np.arange(120*RATE))/(RATE*2.5),1)
    score *= (duck*fade)[:,None]
    write_wav(WORK/'music.wav', score)
    mix = score + narration[:,None]*.88
    write_wav(WORK/'mix.wav', mix)
    subprocess.run([FFMPEG,'-hide_banner','-loglevel','error','-y','-i',str(WORK/'mix.wav'),
                    '-af','loudnorm=I=-16:TP=-1.5:LRA=8','-ar','48000',str(WORK/'master.wav')],check=True)
    print('Audio master and timed captions complete.', flush=True)


if __name__ == '__main__':
    main()
