import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from app.services import audio_transcription as audio, media_extraction as media


def test_transcript_preserves_words_languages_and_recording_timestamps():
    raw = b'{"start":1.25,"end":2.5,"text":"Restart the service.","language":"en"}\n'
    text, metadata = audio.parse_transcript(raw, 10)
    assert text == '[Speech 1.250–2.500 seconds]\nRestart the service.'
    assert metadata['status'] == 'completed' and metadata['segments'] == 1
    assert metadata['languages'] == ['en']


@pytest.mark.parametrize('row', [
    {'start': -1, 'end': 2, 'text': 'bad'},
    {'start': 2, 'end': 1, 'text': 'bad'},
    {'start': 0, 'end': 12, 'text': 'past recording'},
    {'start': float('nan'), 'end': 2, 'text': 'bad'},
    {'start': True, 'end': 2, 'text': 'bad'},
    {'start': 0, 'end': 1, 'text': ''},
    {'start': 0, 'end': 1, 'text': 'bad\x00data'},
    {'start': 0, 'end': 1, 'text': 'hi', 'language': '../secret'},
])
def test_invalid_transcription_is_not_indexable(row):
    with pytest.raises(HTTPException) as error:
        audio.parse_transcript(json.dumps(row).encode(), 10)
    assert error.value.status_code == 422


def test_partial_worker_output_is_not_accepted():
    raw = b'{"start":0,"end":1,"text":"valid"}\n{"start":'
    with pytest.raises(HTTPException): audio.parse_transcript(raw, 10)


def test_empty_transcript_does_not_invent_speech():
    text, metadata = audio.parse_transcript(b'', 5)
    assert text == '' and metadata['segments'] == 0


def test_transcript_output_bounds(monkeypatch):
    monkeypatch.setattr(audio, 'MAX_TRANSCRIPT_BYTES', 5)
    with pytest.raises(HTTPException): audio.parse_transcript(b'123456', 10)


def test_unavailable_model_never_launches_transcription(monkeypatch):
    monkeypatch.setattr(audio, 'available', lambda: False)
    with pytest.raises(HTTPException) as error: audio.transcribe_video('source.mp4', 30)
    assert error.value.status_code == 503


def test_local_audio_processes_are_bounded_and_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(audio, 'available', lambda: True)
    monkeypatch.setattr(audio, 'model_directory', lambda: tmp_path / 'local-model')
    commands, progress = [], []
    def run(command, **options):
        commands.append((command, options))
        if command[0] == 'ffmpeg':
            Path(command[-1]).write_bytes(b'WAVE' + b'0'*50)
            return b''
        return b'{"start":0,"end":1,"text":"Spoken instructions","language":"en"}\n'
    monkeypatch.setattr(media, '_run', run)
    text, metadata = audio.transcribe_video(tmp_path / 'video.mp4', 30, progress.append)
    assert 'Spoken instructions' in text
    assert progress == [{'phase': 'audio_transcription'}]
    decode, inference = commands
    assert decode[0][decode[0].index('-protocol_whitelist') + 1] == 'file,pipe'
    assert decode[0][decode[0].index('-map') + 1] == '0:a:0'
    assert decode[0][decode[0].index('-ar') + 1] == '16000'
    assert decode[1]['output_limit'] == audio.MAX_PCM_BYTES
    assert inference[0][1] == '-I'
    assert inference[1]['cpu_seconds'] == 7200 and inference[1]['memory_bytes'] == 4*1024**3
    assert metadata['status'] == 'completed'
    assert not Path(decode[0][-1]).exists()


def test_failed_decoder_does_not_run_speech_or_leak_temporary_files(tmp_path, monkeypatch):
    monkeypatch.setattr(audio, 'available', lambda: True)
    paths = []
    def fail(command, **options):
        paths.append(Path(command[-1]))
        raise HTTPException(422, 'failed')
    monkeypatch.setattr(media, '_run', fail)
    with pytest.raises(HTTPException): audio.transcribe_video(tmp_path/'source.mp4', 30)
    assert len(paths) == 1 and not paths[0].parent.exists()


def video_fixture(tmp_path, monkeypatch, tracks=1):
    path = tmp_path / 'video.mp4'; path.write_bytes(b'video')
    monkeypatch.setattr(media, '_video', lambda *args: ('visible instructions', {
        'duration_seconds': 30, 'sampled_frames': 1, 'visual_text_unavailable': False, 'audio_tracks': tracks}))
    return path


def test_video_indexes_spoken_and_visible_words(tmp_path, monkeypatch):
    path = video_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(media, 'transcribe_video', lambda *args: ('[Speech 0.000–1.000 seconds]\nRestart safely.', {'status':'completed', 'segments':1}))
    result = media.extract_source_text(path, path.name)
    assert 'Restart safely.' in result['text'] and 'visible instructions' in result['text']
    assert result['extraction_method'] == 'sampled_video_frame_ocr_and_local_speech'
    assert 'audio_not_transcribed' not in result['warnings']


@pytest.mark.parametrize('status', [422, 503])
def test_partial_video_keeps_visual_text_with_explicit_audio_failure(tmp_path, monkeypatch, status):
    path = video_fixture(tmp_path, monkeypatch)
    def fail(*args): raise HTTPException(status, 'private inference details')
    monkeypatch.setattr(media, 'transcribe_video', fail)
    result = media.extract_source_text(path, path.name)
    assert result['text'] == 'visible instructions'
    assert result['metadata']['audio_transcription']['status'] == ('unavailable' if status == 503 else 'failed')
    assert 'audio_not_transcribed' in result['warnings']
    assert 'private' not in str(result)


def test_no_audio_track_does_not_invoke_transcription(tmp_path, monkeypatch):
    path = video_fixture(tmp_path, monkeypatch, tracks=0)
    monkeypatch.setattr(media, 'transcribe_video', lambda *args: pytest.fail('no audio track'))
    result = media.extract_source_text(path, path.name)
    assert result['metadata']['audio_transcription']['status'] == 'no_audio'
    assert 'video_has_no_audio_track' in result['warnings']


def test_silent_audio_and_multiple_tracks_are_explicit(tmp_path, monkeypatch):
    path = video_fixture(tmp_path, monkeypatch, tracks=2)
    monkeypatch.setattr(media, 'transcribe_video', lambda *args: ('', {'status':'completed', 'segments':0}))
    result = media.extract_source_text(path, path.name)
    assert 'no_speech_detected' in result['warnings']
    assert 'only_first_audio_track_processed' in result['warnings']


def test_audio_processing_survives_unavailable_visual_ocr(tmp_path, monkeypatch):
    source = tmp_path/'recording.mp4'; source.write_bytes(b'video')
    monkeypatch.setattr(media, '_require', lambda *args: None)
    monkeypatch.setattr(media, '_run', lambda *args, **kwargs: json.dumps({'format':{'duration':2}, 'streams':[{'codec_type':'video','width':32,'height':32}, {'codec_type':'audio'}]}).encode())
    def no_ocr(*args): raise HTTPException(503, 'OCR unavailable')
    monkeypatch.setattr(media, '_ocr', no_ocr)
    monkeypatch.setattr(media, 'transcribe_video', lambda *args: ('[Speech 0.000–1.000 seconds]\nSpoken evidence.', {'status':'completed', 'segments':1}))
    result = media.extract_source_text(source, source.name)
    assert 'Spoken evidence.' in result['text']
    assert 'video_visual_text_processing_unavailable' in result['warnings']
    assert 'audio_not_transcribed' not in result['warnings']


def test_capability_requires_installed_model_and_tools(tmp_path, monkeypatch):
    monkeypatch.setattr(audio, 'model_directory', lambda: tmp_path)
    monkeypatch.setattr(audio.shutil, 'which', lambda name: '/usr/bin/'+name)
    monkeypatch.setattr(audio.importlib.util, 'find_spec', lambda name: object())
    assert audio.available() is False
    for name in ('config.json', 'model.bin', 'tokenizer.json'):
        (tmp_path/name).write_bytes(b'fixture')
    assert audio.available() is True
    monkeypatch.setattr(audio.shutil, 'which', lambda name: None)
    assert audio.available() is False


def test_worker_normalized_audio_decodes_without_pyav(tmp_path):
    import wave
    import struct
    from app.services.audio_worker import read_audio
    path = tmp_path/'normalized.wav'
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
        output.writeframes(struct.pack('<hhh', -32768, 0, 16384))
    samples = read_audio(path)
    assert samples.tolist() == [-1.0, 0.0, 0.5]
    assert str(samples.dtype) == 'float32'


@pytest.mark.parametrize('channels,rate,width', [(2,16000,2), (1,8000,2), (1,16000,1)])
def test_worker_rejects_unexpected_audio_format(tmp_path, channels, rate, width):
    import wave
    from app.services.audio_worker import read_audio
    path = tmp_path/'invalid.wav'
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(channels); output.setsampwidth(width); output.setframerate(rate)
        output.writeframes(b'\0' * 100)
    with pytest.raises(ValueError): read_audio(path)
