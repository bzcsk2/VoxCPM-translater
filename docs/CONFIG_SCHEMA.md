# Config schema validation

VoxCPM Translator has two layers of configuration checks:

1. **Schema validation**: checks YAML structure, required keys, value types, enum values, numeric ranges, and cross-field rules.
2. **Environment validation**: checks local files, directories, executables, importable adapter modules, API-key environment variables, and model paths.

Schema validation is intentionally lightweight. It does not touch local media, models, FFmpeg, GPUs, or APIs.

## Run schema-only validation

```bash
python scripts/check_config_schema.py --config configs/default.yaml
```

For machine-readable output:

```bash
python scripts/check_config_schema.py --config configs/default.yaml --json
```

The command exits with status `1` when schema errors are present.

## Run full preflight validation

```bash
python scripts/check_env.py --config configs/local.yaml
```

`check_env.py` includes schema issues as `schema.<path>` rows, then continues with executable, path, model, LLM, and TTS backend checks.

## What the schema checks

The schema layer validates:

- required core paths such as `paths.input_video`, `paths.refined_json`, and `paths.final_video`
- model path fields such as `models.vibevoice_repo` and `models.qwen_asr_path`
- LLM fields such as `llm.api_base`, `llm.model`, `llm.batch_size`, and `llm.max_tokens`
- TTS backend values: `manual`, `custom_command`, or `voxcpm`
- TTS cross-field rules:
  - `tts.custom_command` is required when `tts.backend` is `custom_command`
  - `tts.voxcpm_adapter` and `models.voxcpm_model_path` are required when `tts.backend` is `voxcpm`
- runtime values such as `runtime.tts_devices`
- audio extraction and vocal extraction numeric ranges
- ASR generation numeric ranges
- assembly values such as `assembly.min_speed_ratio` and `assembly.missing_chunk_policy`
- subtitle numeric and string fields

## What the schema does not check

Schema validation does not verify:

- whether a path exists
- whether a file is a valid audio/video file
- whether FFmpeg is installed
- whether a Python adapter module is importable
- whether an API key is present
- whether CUDA or a GPU is available
- whether model licenses permit your use case

Use `check_env.py`, `diagnose.py`, and real pipeline runs for those checks.

## Development policy

The default development check suite includes schema validation:

```bash
python scripts/dev_check.py
```

Focused schema check:

```bash
python scripts/dev_check.py --check config-schema
```

When adding or renaming config keys:

1. Update the committed config templates.
2. Update `scripts/config_schema.py`.
3. Update docs that describe the key.
4. Add or adjust tests in `tests/test_config_schema.py`.
5. Run `python scripts/dev_check.py --check config-schema`.

## Interpreting results

Examples:

```text
[ERROR] tts.backend: unsupported value 'bad'; expected one of: manual, custom_command, voxcpm
[ERROR] assembly.min_speed_ratio: value 1.5 is above maximum 1.0
[ERROR] runtime.tts_devices: all device entries must be non-empty strings
```

`ERROR` rows fail the command. `WARN` rows indicate suspicious but not always fatal values.
