"""Isolated local Whisper worker. No application state or network downloads."""
import json
import os
import sys
import wave

def read_audio(path):
    """Read only our bounded, normalized PCM; avoid third-party media decoding."""
    import numpy as np
    with wave.open(str(path), 'rb') as source:
        if (source.getnchannels() != 1 or source.getsampwidth() != 2
                or source.getframerate() != 16000 or source.getcomptype() != 'NONE'
                or not 0 < source.getnframes() <= 16000 * 7200):
            raise ValueError('invalid_normalized_audio')
        frames = source.getnframes()
        pcm = source.readframes(frames)
        if len(pcm) != frames * 2:
            raise ValueError('truncated_normalized_audio')
    audio = np.frombuffer(pcm, dtype='<i2').astype(np.float32)
    audio /= 32768.0
    return audio


def main():
    # Bound native thread pools before importing the inference libraries.
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[variable] = '2'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    from faster_whisper import WhisperModel
    model = WhisperModel(sys.argv[2], device='cpu', compute_type='int8',
                         cpu_threads=2, num_workers=1, local_files_only=True)
    segments, info = model.transcribe(read_audio(sys.argv[1]), beam_size=5, temperature=0,
                                     vad_filter=True, condition_on_previous_text=False)
    limit = int(sys.argv[3])
    size = 0
    # JSON lines permit bounded output without accumulating a long recording.
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        line = json.dumps({'start': segment.start, 'end': segment.end, 'text': text,
                           'language': info.language}, ensure_ascii=False).encode('utf-8') + b'\n'
        size += len(line)
        if size > limit:
            raise ValueError('transcription_output_limit')
        sys.stdout.buffer.write(line)


if __name__ == '__main__':
    main()
