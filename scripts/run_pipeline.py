#!/usr/bin/env python3
"""
Full Pipeline Script

This script runs the complete DJNet dataset generation pipeline:
1. Download data (if needed)
2. Analyze tracks
3. Generate dataset
"""

import sys
import yaml
import os
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.dataset_generator import DatasetGenerator


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)


def run_script(script_name: str) -> bool:
    """Run a Python script and return success status."""
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False


def main():
    """Main function."""
    print("DJNet Complete Pipeline")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Step 1: Check if data needs to be downloaded
    music_dir = config['data']['music_dir']
    if not os.path.exists(music_dir):
        print("Step 1: Downloading dataset...")
        script_path = os.path.join(os.path.dirname(__file__), "download_data.py")
        if not run_script(script_path):
            print("Failed to download data. Exiting.")
            sys.exit(1)
        print("✓ Data download complete")
    else:
        print("Step 1: Dataset already exists, skipping download")
    
    # Step 2: Check if tracks need to be analyzed
    analysis_dir = config['data']['analysis_dir']
    analysis_files = []
    if os.path.exists(analysis_dir):
        analysis_files = [f for f in os.listdir(analysis_dir) if f.endswith('.json')]
    
    if not analysis_files:
        print("\nStep 2: Analyzing tracks...")
        script_path = os.path.join(os.path.dirname(__file__), "analyze_tracks.py")
        if not run_script(script_path):
            print("Failed to analyze tracks. Exiting.")
            sys.exit(1)
        print("✓ Track analysis complete")
    else:
        print(f"\nStep 2: Found {len(analysis_files)} existing analysis files, skipping analysis")
    
    # Step 3: Generate dataset
    print("\nStep 3: Generating dataset...")
    script_path = os.path.join(os.path.dirname(__file__), "generate_dataset.py")
    if not run_script(script_path):
        print("Failed to generate dataset. Exiting.")
        sys.exit(1)
    print("✓ Dataset generation complete")
    
    print("\n" + "=" * 40)
    print("Pipeline completed successfully!")
    print(f"Dataset available in: {config['data']['output_dir']}")


if __name__ == "__main__":
    main()
