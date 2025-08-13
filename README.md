# DJNet Dataset Generator

## Overview

The DJNet Dataset Generator addresses the challenge of creating comprehensive training data for AI-powered DJ systems. By analyzing musical features such as tempo, key, and harmonic content, the system automatically identifies compatible track pairs and generates professional-quality transitions using various mixing techniques. This enables researchers and developers to train neural networks on realistic DJ mixing scenarios without manually creating thousands of transition examples.

## Project Architecture

```
DJNet-Dataset/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation script
├── generate_local_dataset.py    # Local dataset generation script
├── monitor_local_progress.py    # Real-time progress monitoring
├── colab_setup.py              # Google Colab configuration
├── upload_to_gdrive.py         # Cloud storage integration
├── config/
│   ├── config.yaml             # Main configuration file
│   └── colab_config.yaml       # Colab-specific settings
├── src/                        # Core library modules
│   ├── __init__.py
│   ├── audio_analysis.py       # Audio feature extraction
│   ├── pairing.py              # Track compatibility algorithms
│   ├── transitions.py          # Transition generation engine
│   └── dataset_generator.py    # Main dataset orchestration
├── scripts/                    # Modular pipeline components
│   ├── download_data.py        # FMA dataset acquisition
│   ├── analyze_tracks.py       # Batch audio analysis
│   ├── generate_dataset.py     # Transition generation
│   └── run_pipeline.py         # Complete automated pipeline
├── tests/                      # Unit and integration tests
│   ├── __init__.py
│   ├── test_audio_analysis.py
│   ├── test_pairing.py
│   └── test_transitions.py
└── data/                       # Data storage structure
    ├── fma_small.zip           # Downloaded FMA dataset
    ├── track_analysis/         # Processed audio features
    └── output/                 # Generated dataset samples
        └── djnet_dataset_20k/  # Default output directory
```

## Quick Start Guide

### Option 1: Google Colab (Recommended for Beginners)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SoykatAmin/DJNet-Dataset/blob/main/DJNet_Colab.ipynb)

### Option 2: Local Installation

For users who prefer local execution or need custom configurations:

1. **Clone the repository:**
```bash
git clone https://github.com/SoykatAmin/DJNet-Dataset.git
cd DJNet-Dataset
```

2. **Set up Python environment:**
```bash
# Create virtual environment (recommended)
python -m venv djnet_env
source djnet_env/bin/activate  # On Windows: djnet_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Install the package:**
```bash
pip install -e .
```

### Option 3: One-Command Local Generation

For immediate dataset generation with default settings:

```bash
python generate_local_dataset.py
```

This script will:
- Download the FMA dataset (~8GB)
- Analyze all audio tracks
- Generate 20,000 transition samples
- Save everything to `output/djnet_dataset_20k/`

## Dataset Output Structure

The generated dataset follows a structured format optimized for machine learning workflows:

### Directory Structure
```
output/djnet_dataset_20k/
├── transition_00000/           # Individual transition samples
│   ├── source_a.wav           # First track segment (20s, 22kHz)
│   ├── source_b.wav           # Second track segment (20s, 22kHz)
│   ├── target.wav             # Generated transition (2-8s, 22kHz)
│   └── conditioning.json      # Metadata and parameters
├── transition_00001/
│   └── ...
├── metadata.csv               # Master dataset index
├── dataset_stats.json         # Generation statistics
└── progress.json              # Generation progress tracking
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.