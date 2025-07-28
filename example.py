#!/usr/bin/env python3
"""
Example usage of the DJNet Dataset Generator

This script demonstrates how to use the DJNet dataset generation tools
with a small example dataset.
"""

import os
import sys
import yaml
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.audio_analysis import AudioAnalyzer
from src.pairing import TrackPairer
from src.transitions import TransitionGenerator
from src.dataset_generator import DatasetGenerator


def create_example_config():
    """Create an example configuration for testing."""
    return {
        'data': {
            'music_dir': 'data/raw/fma_small',
            'analysis_dir': 'data/processed/track_analysis',
            'output_dir': 'data/output/djnet_dataset_example',
            'fma_url': 'https://os.unil.cloud.switch.ch/fma/fma_small.zip'
        },
        'audio': {
            'target_sample_rate': 22050,  # Lower for faster processing
            'mono': True,
            'tempo_threshold': 15.0,  # More lenient for small dataset
            'key_compatibility_threshold': 2
        },
        'transitions': {
            'transition_bars': 4,  # Shorter transitions for demo
            'beats_per_bar': 4,
            'types': [
                {'name': 'linear_fade', 'weight': 0.4},
                {'name': 'exp_fade', 'weight': 0.3},
                {'name': 'bass_swap_eq', 'weight': 0.2},
                {'name': 'hard_cut', 'weight': 0.1}
            ]
        },
        'dataset': {
            'num_transitions': 10,  # Small number for demo
            'shuffle_pairs': True,
            'minimum_valid_starts': 3
        },
        'echo_fade': {
            'num_echos': 3,
            'decay_db': 5
        },
        'filter_sweep': {
            'start_freq': 15000,
            'end_freq': 200,
            'chunk_size_ms': 100
        },
        'eq': {
            'crossover_freq': 300
        },
        'exp_fade': {
            'power_out_range': [1.2, 2.5],
            'power_in_range': [0.4, 0.9]
        }
    }


def demo_individual_components():
    """Demonstrate individual components of the system."""
    print("=" * 50)
    print("Individual Component Demo")
    print("=" * 50)
    
    # Demo AudioAnalyzer
    print("\n1. Audio Analysis Demo")
    print("-" * 30)
    analyzer = AudioAnalyzer(target_sr=22050)
    print(f"Created AudioAnalyzer with target sample rate: {analyzer.target_sr}")
    
    # Demo TrackPairer  
    print("\n2. Track Pairing Demo")
    print("-" * 30)
    pairer = TrackPairer(tempo_threshold=10.0, key_threshold=1)
    
    # Create sample track data
    sample_tracks = [
        {"path": "track1.mp3", "tempo": 120.0, "key": 0, "beat_times": [1, 2, 3], "downbeat_times": [1]},
        {"path": "track2.mp3", "tempo": 125.0, "key": 1, "beat_times": [1, 2, 3], "downbeat_times": [1]},
        {"path": "track3.mp3", "tempo": 140.0, "key": 0, "beat_times": [1, 2, 3], "downbeat_times": [1]},
    ]
    
    pairs = pairer.find_compatible_pairs(sample_tracks)
    print(f"Found {len(pairs)} compatible pairs from {len(sample_tracks)} tracks")
    
    stats = pairer.get_pairing_stats(pairs)
    print(f"Pairing stats: {stats}")
    
    # Demo TransitionGenerator
    print("\n3. Transition Generator Demo")
    print("-" * 30)
    transition_gen = TransitionGenerator(target_sr=22050)
    print(f"Created TransitionGenerator with target sample rate: {transition_gen.target_sr}")
    print("Available transition types:")
    transition_types = ['linear_fade', 'exp_fade', 'bass_swap_eq', 'filter_sweep', 'hard_cut', 'echo_fade']
    for i, t_type in enumerate(transition_types, 1):
        print(f"  {i}. {t_type}")


def demo_full_pipeline():
    """Demonstrate the full pipeline (requires actual audio data)."""
    print("\n" + "=" * 50)
    print("Full Pipeline Demo")
    print("=" * 50)
    
    config = create_example_config()
    
    # Check if we have audio data
    if not os.path.exists(config['data']['music_dir']):
        print("Note: Full pipeline demo requires audio data.")
        print(f"Please run 'python scripts/download_data.py' first to download the FMA dataset.")
        print(f"Expected music directory: {config['data']['music_dir']}")
        return
    
    print("Creating DatasetGenerator...")
    generator = DatasetGenerator(config)
    
    print("Running full pipeline...")
    try:
        metadata = generator.run_full_pipeline()
        print(f"Successfully generated {len(metadata)} transitions!")
        
        # Show some statistics
        transition_types = {}
        for item in metadata:
            t_type = item['transition_type']
            transition_types[t_type] = transition_types.get(t_type, 0) + 1
        
        print("\nGenerated transition types:")
        for t_type, count in transition_types.items():
            print(f"  {t_type}: {count}")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")
        print("This is normal if you don't have the audio dataset downloaded.")


def main():
    """Main demo function."""
    print("DJNet Dataset Generator - Example Usage")
    print("=" * 60)
    
    # Demo individual components
    demo_individual_components()
    
    # Demo full pipeline (if data is available)
    demo_full_pipeline()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nTo run the full system:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Download data: python scripts/download_data.py")
    print("3. Run pipeline: python scripts/run_pipeline.py")
    print("\nOr use individual scripts:")
    print("- python scripts/analyze_tracks.py")
    print("- python scripts/generate_dataset.py")


if __name__ == "__main__":
    main()
