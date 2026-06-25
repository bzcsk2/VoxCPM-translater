# Model setup

This repository does not include model weights. You must download models from their official sources and follow their usage terms.

## Required models

### 1. Vocal separation model

Used by `audio-separator` in `scripts/01_process_vocals.sh`.

Config keys:

```yaml
models:
  audio_separator_model: "Kim_Vocal_2.onnx"
  audio_separator_model_dir: "/path/to/audio-separator-models"
```

### 2. VibeVoice-ASR

Used by `scripts/02_transcribe_vibe.py` for timestamped ASR and speaker IDs.

Config keys:

```yaml
models:
  vibevoice_repo: "/path/to/VibeVoice"
  vibevoice_asr_path: "/path/to/VibeVoice-ASR"
  qwen_asr_path: "/path/to/Qwen3-ASR-1.7B"
```

`vibevoice_repo` should be the local source repository path that exposes the `vibevoice` Python package imports used by the script.

### 3. Local audio generation backend

Used by `scripts/05_generate_audio_chunks.py` for per-segment dubbed audio generation or validation.

Config key:

```yaml
models:
  voxcpm_model_path: "/path/to/VoxCPM2"

tts:
  backend: "manual"
```

The repository defines a stable file contract:

```text
paths.dub_chunk_dir/
  raw_0.wav
  raw_1.wav
  raw_2.wav
```

Each spoken segment in `paths.refined_json` must produce one WAV file named `raw_<id>.wav`. `dub_<id>.wav` is accepted for compatibility.

Supported backend modes:

#### `manual`

Validates that required chunks already exist.

```yaml
tts:
  backend: "manual"
```

#### `custom_command`

Calls a local CLI command once per segment. Available template variables are `$id`, `$speaker`, `$text`, `$output`, `$start`, and `$end`.

```yaml
tts:
  backend: "custom_command"
  custom_command: "python my_tts.py --text '$text' --speaker '$speaker' --output '$output'"
  overwrite: false
```

#### `voxcpm`

Calls a Python adapter module that you provide. This keeps VoxCPM import details outside the repository while giving the project a first-class backend slot.

```yaml
tts:
  backend: "voxcpm"
  voxcpm_adapter: "my_voxcpm_adapter"
  voxcpm_adapter_function: "generate_audio"
  overwrite: false
```

The adapter function must have this signature:

```python
def generate_audio(segment: dict, output_path: Path, config: dict) -> None:
    ...
```

The function should write a WAV file to `output_path`. It can read `models.voxcpm_model_path`, `tts.cfg_value`, `tts.inference_timesteps`, `tts.voice_prompt_prefix`, and any extra keys from `config`.

### 4. LatentSync, optional

Used by `scripts/07_latentsync_lipsync.py`.

Config key:

```yaml
models:
  latentsync_dir: "/path/to/LatentSync"
```

The LatentSync step is experimental. It may require separate dependency isolation because its torch / diffusers / CUDA requirements can conflict with the ASR or TTS environment.

## Recommended model storage

Do not store models inside this Git repository. Use a separate local directory, for example:

```text
~/models/
  audio-separator/
  VibeVoice-ASR/
  Qwen3-ASR-1.7B/
  VoxCPM2/
  LatentSync/
```

Then reference those paths from `configs/local.yaml`.
