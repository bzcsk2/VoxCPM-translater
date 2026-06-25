# Roadmap

This repository is currently a research release. The code is useful as a local workflow, but several areas should mature before it is treated as a polished end-user tool.

## Completed foundation

- Documented adapter contract for `scripts/05_generate_audio_chunks.py`.
- Added `manual`, `custom_command`, and `voxcpm` adapter backend modes.
- Added preflight checks for required local files, tools, environment variables, and model directories.
- Added video-to-WAV extraction as stage 00.
- Added a dry-run capable pipeline orchestrator.
- Added lightweight CI with compile, pytest, and dry-run checks.
- Added unit tests for timestamps, subtitle escaping, JSON alignment, LLM JSON parsing, and assembly chunk discovery.
- Added a fixture-free smoke test for manual TTS validation and audio assembly.

## Near-term

- Fill in `docs/KNOWN_GOOD_ENV.md` after a complete local GPU run.
- Add a concrete VoxCPM adapter example once a stable local VoxCPM API/CLI shape is confirmed.
- Add shell checks for `scripts/01_process_vocals.sh`.
- Add stronger resumability checks so users can restart after failures without rerunning completed stages.

## Project quality

- Pin or constrain dependency versions once a known-good environment is tested.
- Separate optional dependency groups for ASR, translation, TTS, subtitles, and LatentSync.
- Add tests for speed-adjustment decisions that monkeypatch FFmpeg calls.
- Add sample ASR/refined JSON fixtures for documentation examples.

## User experience

- Consider packaging the scripts behind a single installable CLI.
- Improve failure messages for malformed model output and invalid subtitle text.
- Add progress summaries for long-running stages.

## Release readiness

- Add versioned releases when the pipeline has a reproducible setup.
- Add screenshots or short demo clips only if the media can be redistributed.
- Keep model weights, generated media, and source content outside the repository.
