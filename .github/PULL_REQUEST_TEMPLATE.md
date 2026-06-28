## Summary

<!-- Briefly describe what changed and why. -->

-
-
-

## Change type

<!-- Check the boxes that apply. -->

- [ ] Documentation only
- [ ] Tests only
- [ ] Runtime / pipeline logic
- [ ] Model setup or backend adapter
- [ ] CI / developer tooling
- [ ] Other:

## Model, media, and secret safety

<!-- This repository must not include private or non-redistributable artifacts. -->

- [ ] I did not commit model weights.
- [ ] I did not commit private media, copyrighted media, generated audio, or generated video.
- [ ] I did not commit `.env`, API keys, tokens, or secrets.
- [ ] I did not commit `configs/local.yaml` or machine-specific private paths.

## Validation

### Lightweight checks

<!-- These are the same checks run by CI and should work without GPU models or media files. -->

- [ ] `python -m compileall scripts`
- [ ] `pytest -q`
- [ ] Not run; reason:

### Full local pipeline checks

<!-- Required when the change affects media processing, ASR, translation, TTS, assembly, subtitles, or lip sync. -->

- [ ] `python scripts/check_env.py --config configs/local.yaml`
- [ ] `python scripts/run_pipeline.py --config configs/local.yaml --from-stage 0 --to-stage 6`
- [ ] Optional LatentSync / subtitles checked
- [ ] Not applicable; reason:
- [ ] Not run; reason:

## Local environment, if a full run was performed

<!-- Fill this section only for model-dependent or media-dependent validation. -->

- OS:
- Python:
- CUDA / GPU:
- FFmpeg:
- ASR model paths or IDs:
- TTS backend:
- TTS model path or adapter:
- Pipeline stages run:

## Notes for reviewers

<!-- Mention known limitations, follow-up issues, screenshots/log snippets, or anything reviewers should inspect carefully. -->

