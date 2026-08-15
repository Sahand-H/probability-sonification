# Probability Sonification

An interactive Streamlit experiment for sampling a few basic probability distributions,
mapping sample values to MIDI pitch, and comparing the results visually and by
ear. Part of a little project to investigate sonification methods.

## Run locally

```bash
uv sync
uv run streamlit run app.py
```

FluidSynth is used to render distinguishable General MIDI instruments. On
macOS, install it with `brew install fluid-synth`. The Streamlit Community Cloud
deployment installs it from `packages.txt`.

## Attribution

This project uses [pretty-midi](https://github.com/craffel/pretty-midi) to
construct instruments and notes, manage MIDI timing, and generate downloadable
MIDI files. Instrument audio is rendered from those MIDI sequences using the
[pyFluidSynth](https://github.com/nwhitehead/pyfluidsynth) Python bindings and
[FluidSynth](https://www.fluidsynth.org/). The rendered instrument sounds use
the TimGM6mb SoundFont bundled with `pretty-midi`.
