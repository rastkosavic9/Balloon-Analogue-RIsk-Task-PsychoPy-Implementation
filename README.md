# Balloon-Analogue-RIsk-Task-PsychoPy-Implementation
A PsychoPy (Python) implementation of the Balloon Analogue Risk Task (BART; Lejuez et al., 2002), adapted with multiple balloon types and explicit risk parameters. Designed for behavioral research and future EEG integration and implementations.
**Citation / DOI:** Savic R. (2026). * Balloon Analogue Risk Task (BART) in PsychoPy* [Computer software]. Zenodo. [https://doi.org/10.5281/zenodo.18121801](https://doi.org/10.5281/zenodo.18121801)


## Features
- Single-page intro (centered, concise; black text on light-grey background)
- Practice (3) and main (60) trials
- Left-side balloon (no outline); gradual growth per pump (visible +1 px minimum), clamped to a panel
- Right-side HUD on dark-grey cards (white text)
- Bottom command prompts on dark-grey boxes (white text) for visibility
- Deterministic explosion threshold per trial (reproducible; correct counterfactual potential)
- Block summaries after 20 and 40 trials; final summary after 60 trials
- CSV outputs suitable for analysis: `subjects.csv`, `trials.csv`, `blocks.csv`

## Requirements

**Option A (recommended): PsychoPy Standalone (2024+)**

**Option B (Python environment):**
```bash
pip install -r requirements.txt
