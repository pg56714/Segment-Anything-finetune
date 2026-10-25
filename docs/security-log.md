# Security Log

English | [繁體中文](security-log.zh-TW.md)

- Date: 2026-10-25
- Branch: `fix/security-upgrades`
- Scope: `requirements.txt`

## Summary

gradio now requires a patched release. pillow still has open advisories because gradio caps its version.

## Changes

| Item | Before | After | Reason |
|---|---|---|---|
| gradio | unpinned | >=6.16 | File read, SSRF and path traversal advisories (fixed in 6.16) |

## Remaining issues

### Dependency versions held back upstream

| Package | Version | Advisories | Why it is not fixed | Impact and mitigation |
|---|---|---|---|---|
| pillow | 12.3.0 | 41 (fixed in 13.0.0) | gradio >= 6.16 requires `pillow<13`; no gradio release allows Pillow 13 yet. | Crafted image files (for example TIFF or PDF) can crash the process or read out-of-bounds memory when decoded. Run the Gradio app locally only (no `share=True`, no public port) and open only images you trust. Upgrade once gradio allows Pillow 13. |

## How it was verified

- osv-scanner on the resolved `requirements.txt`; only pillow remains.
- `demo_app.py` builds and serves its UI on gradio 6.30.0 with the SAM model stubbed out.

## Not verified

- Inference on a GPU with the real model weights (the test environment has no GPU and no weights).
- Fine-tuning, test and eval scripts on real datasets.
