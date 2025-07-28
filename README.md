# DJNet Dataset Generator

This project generates a dataset of synthetic DJ transitions for training neural networks to create smooth audio transitions between songs. The dataset includes various transition types such as linear fades, exponential fades, bass swaps, filter sweeps, hard cuts, and echo fades.

## Project Structure

```
DJNet-Dataset/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── audio_analysis.py
│   ├── pairing.py
│   ├── transitions.py
│   └── dataset_generator.py
├── scripts/
│   ├── download_data.py
│   ├── analyze_tracks.py
│   ├── generate_dataset.py
│   └── run_pipeline.py
├── tests/
│   ├── __init__.py
│   ├── test_audio_analysis.py
│   ├── test_pairing.py
│   └── test_transitions.py
└── data/
    ├── raw/
    ├── processed/
    └── output/
```

## Features

- **Audio Analysis**: Extract BPM, beats, downbeats, and key information from audio tracks
- **Intelligent Pairing**: Find compatible track pairs based on tempo and key compatibility
- **Multiple Transition Types**:
  - Linear fade
  - Exponential fade
  - Bass swap with EQ
  - Filter sweep
  - Hard cut
  - Echo fade
- **Dataset Generation**: Generate thousands of transition samples with metadata

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd DJNet-Dataset
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Quick Start

1. Download the FMA dataset:
```bash
python scripts/download_data.py
```

2. Analyze audio tracks:
```bash
python scripts/analyze_tracks.py
```

3. Generate the dataset:
```bash
python scripts/generate_dataset.py
```

### Full Pipeline

Run the complete pipeline:
```bash
python scripts/run_pipeline.py
```

## Configuration

Edit `config/config.yaml` to customize:
- Dataset size
- Transition types and probabilities
- Audio processing parameters
- Output directories

## Requirements

- Python 3.7+
- librosa
- pydub
- numpy
- pandas
- tqdm
- PyYAML

## Output

The generated dataset includes:
- `source_a.wav`: First track segment
- `source_b.wav`: Second track segment  
- `target.wav`: Generated transition
- `conditioning.json`: Metadata and parameters
- `metadata.csv`: Master dataset index
