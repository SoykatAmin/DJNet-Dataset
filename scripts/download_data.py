#!/usr/bin/env python3
"""
Download FMA Dataset Script

This script downloads and extracts the FMA small dataset for use in
DJ transition generation.
"""

import os
import sys
import wget
import zipfile
import yaml
from pathlib import Path


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)


def download_fma_dataset(config: dict) -> None:
    """Download and extract the FMA small dataset."""
    fma_url = config['data']['fma_url']
    music_dir = config['data']['music_dir']
    
    # Create data directory
    os.makedirs(os.path.dirname(music_dir), exist_ok=True)
    
    zip_filename = "fma_small.zip"
    
    print("Downloading FMA small dataset...")
    print(f"URL: {fma_url}")
    
    try:
        # Download the dataset
        wget.download(fma_url, zip_filename)
        print(f"\nDownload complete: {zip_filename}")
        
        # Extract the dataset
        print("Extracting dataset...")
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall("data/raw/")
        
        print("Extraction complete!")
        
        # Clean up zip file
        os.remove(zip_filename)
        print("Cleanup complete!")
        
        # Verify extraction
        if os.path.exists(music_dir):
            num_files = sum(1 for _, _, files in os.walk(music_dir) 
                          for f in files if f.endswith(('.mp3', '.wav')))
            print(f"Found {num_files} audio files in {music_dir}")
        else:
            print(f"Warning: Expected directory {music_dir} not found after extraction")
            
    except Exception as e:
        print(f"Error downloading/extracting dataset: {e}")
        sys.exit(1)


def main():
    """Main function."""
    print("DJNet Dataset Downloader")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Check if dataset already exists
    music_dir = config['data']['music_dir']
    if os.path.exists(music_dir):
        response = input(f"Dataset directory {music_dir} already exists. "
                        "Do you want to re-download? (y/N): ")
        if response.lower() != 'y':
            print("Download cancelled.")
            return
    
    # Download dataset
    download_fma_dataset(config)
    
    print("\nDataset download complete!")
    print(f"Music files are available in: {music_dir}")


if __name__ == "__main__":
    main()
