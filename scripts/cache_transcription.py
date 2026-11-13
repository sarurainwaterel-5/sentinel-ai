"""Prepare the local multilingual CPU speech model during image construction."""
import os
from faster_whisper.utils import download_model

directory = os.getenv('SENTINEL_WHISPER_MODEL_DIR', '/opt/sentinel-models/whisper-base')
download_model('base', output_dir=directory)
print('Local speech transcription model cached.')
