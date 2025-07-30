#!/bin/bash
# Setup script for vast.ai instances
# Run this first on your rented hardware

echo "Setting up DJNet Dataset Generator on vast.ai..."
echo "================================================"

# Update system
apt-get update -qq
apt-get install -y -qq ffmpeg git

# Install Python dependencies
pip install --upgrade pip
pip install librosa soundfile pydub tqdm pandas numpy requests pyyaml

# Clone repository
git clone https://github.com/SoykatAmin/DJNet-Dataset.git
cd DJNet-Dataset

# Install package
pip install -e .

echo "Setup complete!"
echo "Run: python generate_full_dataset.py"
