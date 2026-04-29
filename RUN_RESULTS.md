# FCSTN Run Results

Date: 2026-04-29
Workspace: `/Users/fmf/Downloads/fcstn`
Python: `venv/bin/python` -> Python 3.9.6

## Scope

This validation run covered:

- End-to-end test suite execution
- Main platform demo execution
- Neurogaming demo execution
- Basic document cross-check against `fcstn (1).pdf`

## Commands Executed

```bash
venv/bin/python -m pytest tests/ -v --tb=short
venv/bin/python fcstn_platform.py
venv/bin/python neurogaming_demo.py
```

## Test Results

Command:

```bash
venv/bin/python -m pytest tests/ -v --tb=short
```

Outcome:

- `22 passed in 458.39s (0:07:38)`
- No test failures

Coverage by behavior:

- Fractal generation
- Metric tensor construction and curvature
- NDAN/BCI preprocessing and feature extraction
- Coalition formation and utility calculations
- Platform integration
- End-to-end pipeline behavior

## Platform Demo Results

Command:

```bash
venv/bin/python fcstn_platform.py
```

Observed output summary:

- Cognitive attention: `0.026`
- Engagement: `0.049`
- Classified state: `fatigued`
- Adapted fractal zoom: `1.03`
- Adapted curvature scale: `1.10`
- Environment generation time: `20706.20 ms`
- Fractal field shape: `(1920, 1080)`
- NDAN latency: `29.77 ms`
- Coalition count: `3`
- Total coalition value: `385.00`
- Coalition types: `{'infrastructure': 2, 'compute': 1}`

Interpretation:

- The platform demo runs successfully from start to finish.
- Neural-side latency is within the `< 100 ms` target described in the project docs.
- Rendering/generation performance is not yet near the README target of `60 FPS`.
- With the current CPU-only path, the observed environment generation time corresponds to roughly `0.05 FPS` for the demo frame.

## Neurogaming Demo Results

Command:

```bash
venv/bin/python neurogaming_demo.py
```

Observed runtime behavior:

- Session initialized correctly
- 60-second simulated gameplay session completed
- Logged checkpoints were emitted at `0s`, `5s`, `10s`, `15s`, `20s`, `25s`, `30s`, `35s`, `40s`, `45s`, `50s`, and `55s`
- Repeated cognitive state in this run was predominantly `fatigued`
- Difficulty converged to the minimum bound `0.50`
- Attention remained around `0.02-0.03`

Artifacts present in `outputs/`:

- [neurogame_session.png](/Users/fmf/Downloads/fcstn/outputs/neurogame_session.png)
  - PNG, `1800x1500`
- [cognitive_environments.png](/Users/fmf/Downloads/fcstn/outputs/cognitive_environments.png)
  - PNG, `2250x750`

Notes:

- The demo is computationally heavy on CPU because it generates fractals repeatedly over a simulated 60-second session.
- A Matplotlib cache warning appeared because `/Users/fmf/.matplotlib` is not writable in this environment. The run still proceeded.

## Document Cross-Check

Referenced document:

- `fcstn (1).pdf`

What was verified locally:

- PDF metadata indicates title `fcstn`
- PDF page count appears to be `11`

Limitations:

- `pdftotext` was not installed in this environment
- `textutil` and `strings` exposed metadata and raw PDF internals, but not a clean readable text extraction
- Because of that, this cross-check was limited to file metadata and not a full semantic comparison

## Alignment With Repo Documentation

Confirmed:

- The project concept in `README.md` matches the implemented modules:
  - fractal engine
  - metric geometry engine
  - NDAN/BCI processing
  - coalition network
- The test suite validates all four major areas plus integration

Observed gaps:

- The README performance target of `60 FPS` is not met in the current CPU run
- The docs describe a richer directory layout (`docs/`, `examples/`, `config/`, `scripts/`) than the current repo layout actually contains at runtime
- The neurogaming simulation currently trends toward a low-attention, fatigued regime because the synthetic signal generator is not yet modulated strongly enough to produce varied cognitive states during the session

## Practical Conclusion

Current status:

- Codebase is runnable
- Test suite passes completely
- Main demo runs successfully
- Neurogaming demo completes and produces visual artifacts

Current caveats:

- Performance is far from real-time on CPU
- PDF verification was only partial because local extraction tools were unavailable
- Documentation still overstates some structure and maturity compared with the actual executable layout and observed runtime characteristics

## Recommended Next Steps

1. Add a dedicated `MPLCONFIGDIR` in the project workspace for cleaner Matplotlib runs.
2. Refine synthetic EEG generation so the neurogaming demo produces more varied cognitive states.
3. Add a lightweight benchmark script that records generation time and effective FPS explicitly.
4. Reconcile `README.md` project structure with the actual repo layout.
5. If full paper/document verification is important, install a PDF text extraction tool and compare claims section by section.
