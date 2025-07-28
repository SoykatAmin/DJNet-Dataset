#!/usr/bin/env python3
"""
Track Analysis Script

This script analyzes audio tracks to extract features like tempo, beats,
downbeats, and key information for DJ transition generation.
"""

import sys
import yaml
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.audio_analysis import AudioAnalyzer


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)


def main():
    """Main function."""
    print("DJNet Track Analyzer")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Initialize analyzer
    analyzer = AudioAnalyzer(
        target_sr=config['audio']['target_sample_rate']
    )
    
    # Check if music directory exists
    music_dir = config['data']['music_dir']
    if not os.path.exists(music_dir):
        print(f"Error: Music directory not found: {music_dir}")
        print("Please run download_data.py first to download the dataset.")
        sys.exit(1)
    
    # Analyze tracks
    print(f"Analyzing tracks in: {music_dir}")
    print(f"Saving analysis to: {config['data']['analysis_dir']}")
    
    analysis_files = analyzer.analyze_directory(
        music_dir=music_dir,
        analysis_dir=config['data']['analysis_dir']
    )
    
    print(f"\nAnalysis complete!")
    print(f"Generated {len(analysis_files)} analysis files")
    print(f"Analysis files saved in: {config['data']['analysis_dir']}")


if __name__ == "__main__":
    main()
