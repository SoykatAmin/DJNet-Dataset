#!/usr/bin/env python3
"""
Dataset Generation Script

This script generates the complete DJNet transition dataset from analyzed tracks.
"""

import sys
import yaml
import os
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


def main():
    """Main function."""
    print("DJNet Dataset Generator")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    
    # Check if analysis directory exists
    analysis_dir = config['data']['analysis_dir']
    if not os.path.exists(analysis_dir):
        print(f"Error: Analysis directory not found: {analysis_dir}")
        print("Please run analyze_tracks.py first to analyze the audio tracks.")
        sys.exit(1)
    
    # Check if we have analysis files
    analysis_files = [f for f in os.listdir(analysis_dir) if f.endswith('.json')]
    if not analysis_files:
        print(f"Error: No analysis files found in {analysis_dir}")
        print("Please run analyze_tracks.py first to analyze the audio tracks.")
        sys.exit(1)
    
    print(f"Found {len(analysis_files)} analysis files")
    print(f"Target dataset size: {config['dataset']['num_transitions']} transitions")
    print(f"Output directory: {config['data']['output_dir']}")
    
    # Initialize dataset generator
    generator = DatasetGenerator(config)
    
    # Load analysis data
    print("\nLoading analysis data...")
    analysis_file_paths = [os.path.join(analysis_dir, f) for f in analysis_files]
    tracks_data = generator.analyzer.load_analysis_data(analysis_file_paths)
    
    # Find compatible pairs
    print("Finding compatible track pairs...")
    compatible_pairs = generator.pairer.find_compatible_pairs(tracks_data)
    print(f"Found {len(compatible_pairs)} compatible pairs")
    
    if len(compatible_pairs) == 0:
        print("Error: No compatible pairs found. Try adjusting the compatibility thresholds in config.yaml")
        sys.exit(1)
    
    # Check if we have enough pairs for the target dataset size
    if len(compatible_pairs) < config['dataset']['num_transitions']:
        print(f"Warning: Only {len(compatible_pairs)} pairs available, "
              f"but {config['dataset']['num_transitions']} transitions requested.")
        response = input("Continue with available pairs? (y/N): ")
        if response.lower() != 'y':
            print("Generation cancelled.")
            sys.exit(0)
    
    # Generate dataset
    print("\nGenerating dataset...")
    metadata = generator.generate_dataset(compatible_pairs)
    
    print(f"\nDataset generation complete!")
    print(f"Generated {len(metadata)} transitions")
    print(f"Dataset saved in: {config['data']['output_dir']}")


if __name__ == "__main__":
    main()
