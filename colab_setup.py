#!/usr/bin/env python3
"""
Colab Setup Script for DJNet Dataset Generator

This script sets up the environment for running DJNet in Google Colab.
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path


def install_dependencies():
    """Install required packages for Colab."""
    print("📦 Installing dependencies...")
    
    # Install system dependencies
    subprocess.run(['apt-get', 'update', '-qq'], check=True)
    subprocess.run(['apt-get', 'install', '-y', '-qq', 'ffmpeg'], check=True)
    
    # Install Python packages
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'librosa', 'soundfile'], check=True)
    
    print("✅ Dependencies installed!")


def setup_google_drive():
    """Mount Google Drive and create necessary directories."""
    print("💾 Setting up Google Drive...")
    
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        
        # Create directories
        dirs = [
            '/content/drive/MyDrive/DJNet_Data',
            '/content/drive/MyDrive/DJNet_Data/raw',
            '/content/drive/MyDrive/DJNet_Data/processed',
            '/content/drive/MyDrive/DJNet_Data/output'
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        print("✅ Google Drive setup complete!")
        return True
        
    except ImportError:
        print("⚠️ Not running in Colab, skipping Google Drive setup")
        return False


def create_colab_config():
    """Create Colab-specific configuration."""
    print("⚙️ Creating Colab configuration...")
    
    # Load the colab config template
    with open('config/colab_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("✅ Configuration ready!")
    return config


def download_sample_data(config):
    """Download and extract FMA dataset."""
    print("📥 Downloading FMA dataset...")
    
    import requests
    import zipfile
    from tqdm import tqdm
    
    def download_with_progress(url, filename):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    music_dir = config['data']['music_dir']
    if not os.path.exists(music_dir):
        fma_url = config['data']['fma_url']
        zip_path = '/content/fma_small.zip'
        
        # Download
        download_with_progress(fma_url, zip_path)
        
        # Extract
        print("📦 Extracting dataset...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('/content/drive/MyDrive/DJNet_Data/raw/')
        
        # Cleanup
        os.remove(zip_path)
        print("✅ Dataset ready!")
    else:
        print("✅ Dataset already exists!")


def main():
    """Main setup function."""
    print("🚀 DJNet Colab Setup")
    print("=" * 40)
    
    # Check if running in Colab
    try:
        import google.colab
        print("✅ Running in Google Colab")
    except ImportError:
        print("⚠️ Not running in Google Colab")
        print("This script is optimized for Colab environment")
        return
    
    # Setup steps
    install_dependencies()
    drive_mounted = setup_google_drive()
    config = create_colab_config()
    
    if drive_mounted:
        download_sample_data(config)
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Run the analysis: from src.audio_analysis import AudioAnalyzer")
    print("2. Generate dataset: from src.dataset_generator import DatasetGenerator") 
    print("3. Or follow the Colab notebook for guided experience")


if __name__ == "__main__":
    main()
