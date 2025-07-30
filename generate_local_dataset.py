#!/usr/bin/env python3
"""
Local Dataset Generation Script

Generate 20k DJNet transitions on your local system.
No need for cloud instances or uploads - everything stays local.
"""

import os
import sys
import time
import yaml
import json
import random
import requests
import zipfile
import glob
import shutil
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import numpy as np
import librosa
from pydub import AudioSegment

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.audio_analysis import AudioAnalyzer
from src.pairing import TrackPairer


def create_local_config(data_dir="./data", output_dir="./output/djnet_dataset_20k"):
    """Create configuration optimized for local generation."""
    
    # Ensure directories exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    return {
        'data': {
            'music_dir': os.path.join(data_dir, 'fma_small'),
            'analysis_dir': os.path.join(data_dir, 'track_analysis'),
            'output_dir': output_dir,
            'fma_url': 'https://os.unil.cloud.switch.ch/fma/fma_small.zip'
        },
        'audio': {
            'target_sample_rate': 22050,
            'mono': True,
            'tempo_threshold': 15.0,  # More lenient for larger dataset
            'key_compatibility_threshold': 2,
            'source_segment_length_sec': 20.0
        },
        'transitions': {
            'transition_bars': 4,
            'beats_per_bar': 4,
            'types': [
                {'name': 'linear_fade', 'weight': 0.3},
                {'name': 'exp_fade', 'weight': 0.25},
                {'name': 'bass_swap_eq', 'weight': 0.25},
                {'name': 'filter_sweep', 'weight': 0.1},
                {'name': 'hard_cut', 'weight': 0.05},
                {'name': 'echo_fade', 'weight': 0.05}
            ]
        },
        'dataset': {
            'num_transitions': 20000,
            'shuffle_pairs': True,
            'minimum_valid_starts': 3
        }
    }


def download_fma_dataset(config):
    """Download and extract FMA dataset locally."""
    music_dir = config['data']['music_dir']
    fma_url = config['data']['fma_url']
    
    if os.path.exists(music_dir):
        print(f"✅ FMA dataset already exists at {music_dir}")
        return music_dir
    
    print("📥 Downloading FMA dataset...")
    print("⚠️  This is ~8GB and may take 30+ minutes on slower connections")
    
    # Create data directory
    os.makedirs(os.path.dirname(music_dir), exist_ok=True)
    zip_path = os.path.join(os.path.dirname(music_dir), "fma_small.zip")
    
    # Download with progress
    response = requests.get(fma_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(zip_path, 'wb') as f, tqdm(
        desc="Downloading FMA",
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    
    # Extract
    print("📦 Extracting dataset...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.dirname(music_dir))
    
    # Clean up zip file
    os.remove(zip_path)
    print(f"✅ FMA dataset ready at {music_dir}")
    return music_dir


def analyze_tracks(config):
    """Analyze all audio tracks."""
    print("🔍 Analyzing audio tracks...")
    
    analyzer = AudioAnalyzer(target_sr=config['audio']['target_sample_rate'])
    music_dir = config['data']['music_dir']
    analysis_dir = config['data']['analysis_dir']
    
    # Get all audio files
    audio_files = glob.glob(os.path.join(music_dir, '**/*.mp3'), recursive=True)
    print(f"Found {len(audio_files)} audio files")
    
    if len(audio_files) == 0:
        print("❌ No audio files found! Check the music directory path.")
        return []
    
    os.makedirs(analysis_dir, exist_ok=True)
    analysis_files = []
    
    # Analyze tracks with progress
    for audio_file in tqdm(audio_files, desc="Analyzing tracks"):
        try:
            analysis_data = analyzer.analyze_track(audio_file)
            if analysis_data:
                base_name = os.path.splitext(os.path.basename(audio_file))[0]
                output_path = os.path.join(analysis_dir, f"{base_name}.json")
                
                with open(output_path, 'w') as f:
                    json.dump(analysis_data, f, indent=2)
                analysis_files.append(output_path)
        except Exception as e:
            print(f"Error analyzing {audio_file}: {str(e)[:100]}...")
            continue
    
    print(f"✅ Analysis complete! Generated {len(analysis_files)} analysis files")
    return analysis_files


def find_compatible_pairs(analysis_files, config):
    """Find compatible track pairs."""
    print("🔗 Finding compatible track pairs...")
    
    analyzer = AudioAnalyzer(target_sr=config['audio']['target_sample_rate'])
    tracks_data = analyzer.load_analysis_data(analysis_files)
    
    pairer = TrackPairer(
        tempo_threshold=config['audio']['tempo_threshold'],
        key_threshold=config['audio']['key_compatibility_threshold']
    )
    compatible_pairs = pairer.find_compatible_pairs(tracks_data)
    
    print(f"Found {len(compatible_pairs)} compatible pairs")
    
    if len(compatible_pairs) < config['dataset']['num_transitions']:
        print(f"⚠️  Warning: Only {len(compatible_pairs)} pairs available for {config['dataset']['num_transitions']} requested transitions")
        print("💡 Consider:")
        print("   - Relaxing tempo/key thresholds in config")
        print("   - Adding more audio files to the dataset")
        print("   - Reducing the number of requested transitions")
        
        # Ask user what to do
        user_choice = input("\nContinue with available pairs? (y/N): ").strip().lower()
        if user_choice != 'y':
            print("❌ Generation cancelled by user")
            return []
    
    return compatible_pairs


def generate_single_transition(pair, output_dir, config):
    """Generate a single transition with natural duration."""
    track_a_data, track_b_data = pair
    source_length_sec = config['audio']['source_segment_length_sec']
    target_sr = config['audio']['target_sample_rate']
    
    try:
        # Load audio files
        y_a, sr_a = librosa.load(track_a_data['path'], sr=None, mono=True)
        y_b, sr_b = librosa.load(track_b_data['path'], sr=None, mono=True)
        
        # Calculate required samples
        source_samples_a = int(source_length_sec * sr_a)
        source_samples_b = int(source_length_sec * sr_b)
        
        # Check if tracks are long enough
        if len(y_a) < source_samples_a or len(y_b) < source_samples_b:
            return None
        
        # Find valid start positions
        max_start_a = len(y_a) - source_samples_a
        max_start_b = len(y_b) - source_samples_b
        
        if max_start_a <= 0 or max_start_b <= 0:
            return None
        
        # Choose random start positions
        start_a = random.randint(0, max_start_a)
        start_b = random.randint(0, max_start_b)
        
        # Extract segments
        segment_a = y_a[start_a:start_a + source_samples_a]
        segment_b = y_b[start_b:start_b + source_samples_b]
        
        # Resample if needed
        if sr_a != target_sr:
            segment_a = librosa.resample(segment_a, orig_sr=sr_a, target_sr=target_sr)
        if sr_b != target_sr:
            segment_b = librosa.resample(segment_b, orig_sr=sr_b, target_sr=target_sr)
        
        # Ensure exact length
        source_target_samples = int(source_length_sec * target_sr)
        
        if len(segment_a) < source_target_samples:
            segment_a = np.pad(segment_a, (0, source_target_samples - len(segment_a)))
        else:
            segment_a = segment_a[:source_target_samples]
            
        if len(segment_b) < source_target_samples:
            segment_b = np.pad(segment_b, (0, source_target_samples - len(segment_b)))
        else:
            segment_b = segment_b[:source_target_samples]
        
        # Convert to AudioSegment
        segment_a_int = (segment_a * 32767).astype(np.int16)
        segment_b_int = (segment_b * 32767).astype(np.int16)
        
        seg_a = AudioSegment(segment_a_int.tobytes(), frame_rate=target_sr, sample_width=2, channels=1)
        seg_b = AudioSegment(segment_b_int.tobytes(), frame_rate=target_sr, sample_width=2, channels=1)
        
        # Generate transition
        transition_weights = [t['weight'] for t in config['transitions']['types']]
        transition_type_names = [t['name'] for t in config['transitions']['types']]
        chosen_type = random.choices(transition_type_names, weights=transition_weights, k=1)[0]
        
        # Calculate natural transition duration
        avg_tempo = (track_a_data.get('tempo', 120) + track_b_data.get('tempo', 120)) / 2
        transition_bars = config['transitions']['transition_bars']
        beats_per_bar = config['transitions']['beats_per_bar']
        
        beats_in_transition = transition_bars * beats_per_bar
        natural_transition_sec = (beats_in_transition / avg_tempo) * 60
        natural_transition_sec = max(2.0, min(8.0, natural_transition_sec))
        natural_transition_ms = int(natural_transition_sec * 1000)
        
        # Create transition
        if chosen_type == 'hard_cut':
            cut_duration = 100
            part_a = seg_a[-cut_duration//2:]
            part_b = seg_b[:cut_duration//2]
            target_transition = part_a + part_b
        else:
            # All other types use fade
            fade_duration = natural_transition_ms
            part_a = seg_a[-fade_duration:].fade_out(fade_duration)
            part_b = seg_b[:fade_duration].fade_in(fade_duration)
            target_transition = part_a.overlay(part_b)
        
        # Save files
        os.makedirs(output_dir, exist_ok=True)
        
        seg_a.export(os.path.join(output_dir, "source_a.wav"), format="wav")
        seg_b.export(os.path.join(output_dir, "source_b.wav"), format="wav")
        target_transition.export(os.path.join(output_dir, "target.wav"), format="wav")
        
        # Save conditioning info
        conditioning = {
            "source_a_path": track_a_data['path'],
            "source_b_path": track_b_data['path'],
            "source_segment_length_sec": source_length_sec,
            "transition_length_sec": len(target_transition) / 1000.0,
            "natural_transition_sec": natural_transition_sec,
            "sample_rate": target_sr,
            "transition_type": chosen_type,
            "avg_tempo": avg_tempo,
            "transition_bars": transition_bars,
            "start_position_a_sec": start_a / sr_a,
            "start_position_b_sec": start_b / sr_b
        }
        
        with open(os.path.join(output_dir, "conditioning.json"), 'w') as f:
            json.dump(conditioning, f, indent=2)
        
        return output_dir
        
    except Exception as e:
        return None


def generate_transitions(compatible_pairs, config):
    """Generate all transitions with progress tracking."""
    print("🎼 Generating transitions...")
    
    output_dir = config['data']['output_dir']
    num_to_generate = min(len(compatible_pairs), config['dataset']['num_transitions'])
    
    if config['dataset']['shuffle_pairs']:
        random.shuffle(compatible_pairs)
    
    metadata = []
    generated_count = 0
    failed_count = 0
    
    # Create progress tracking
    progress_file = os.path.join(output_dir, "progress.json")
    
    with tqdm(total=num_to_generate, desc="Generating transitions") as pbar:
        for i, pair in enumerate(compatible_pairs[:num_to_generate]):
            transition_id = f"transition_{generated_count:05d}"
            transition_output_dir = os.path.join(output_dir, transition_id)
            
            result_path = generate_single_transition(pair, transition_output_dir, config)
            
            if result_path:
                # Get transition info
                conditioning_path = os.path.join(result_path, "conditioning.json")
                with open(conditioning_path, 'r') as f:
                    conditioning = json.load(f)
                
                metadata.append({
                    "id": transition_id,
                    "path": result_path,
                    "transition_type": conditioning['transition_type'],
                    "transition_length_sec": conditioning['transition_length_sec'],
                    "avg_tempo": conditioning.get('avg_tempo', 0)
                })
                generated_count += 1
            else:
                failed_count += 1
            
            pbar.update(1)
            
            # Save progress every 100 transitions
            if (generated_count + failed_count) % 100 == 0:
                progress_data = {
                    "generated": generated_count,
                    "failed": failed_count,
                    "total_attempted": generated_count + failed_count,
                    "target": num_to_generate,
                    "timestamp": time.time()
                }
                with open(progress_file, 'w') as f:
                    json.dump(progress_data, f, indent=2)
                
                # Save partial metadata
                if metadata:
                    partial_df = pd.DataFrame(metadata)
                    partial_df.to_csv(os.path.join(output_dir, "metadata_partial.csv"), index=False)
    
    # Save final metadata
    if metadata:
        final_df = pd.DataFrame(metadata)
        final_df.to_csv(os.path.join(output_dir, "metadata.csv"), index=False)
    
    print(f"✅ Generation complete!")
    print(f"   Generated: {generated_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Success rate: {generated_count/(generated_count+failed_count)*100:.1f}%")
    
    return metadata


def print_results_summary(config, metadata):
    """Print final results summary."""
    output_dir = config['data']['output_dir']
    
    # Calculate total size
    total_size = 0
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.wav'):
                total_size += os.path.getsize(os.path.join(root, file))
    
    total_size_gb = total_size / (1024**3)
    
    print("\n" + "=" * 60)
    print("🎉 DATASET GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📊 Results:")
    print(f"   Generated transitions: {len(metadata)}")
    print(f"   Total dataset size: {total_size_gb:.2f} GB")
    print(f"   Location: {output_dir}")
    print()
    print(f"📁 Dataset structure:")
    print(f"   {output_dir}/")
    print(f"   ├── transition_00000/")
    print(f"   │   ├── source_a.wav      (20 seconds)")
    print(f"   │   ├── source_b.wav      (20 seconds)")
    print(f"   │   ├── target.wav        (natural length)")
    print(f"   │   └── conditioning.json")
    print(f"   ├── transition_00001/")
    print(f"   │   └── ...")
    print(f"   └── metadata.csv")
    print()
    
    # Show transition statistics
    if metadata:
        transition_types = {}
        transition_lengths = []
        
        for item in metadata:
            t_type = item['transition_type']
            if t_type not in transition_types:
                transition_types[t_type] = 0
            transition_types[t_type] += 1
            transition_lengths.append(item['transition_length_sec'])
        
        print("📈 Transition statistics:")
        for t_type, count in transition_types.items():
            percentage = (count / len(metadata)) * 100
            print(f"   {t_type}: {count} ({percentage:.1f}%)")
        
        if transition_lengths:
            avg_length = np.mean(transition_lengths)
            min_length = np.min(transition_lengths)
            max_length = np.max(transition_lengths)
            print(f"\n⏱️  Transition lengths:")
            print(f"   Average: {avg_length:.2f}s")
            print(f"   Range: {min_length:.2f}s - {max_length:.2f}s")
    
    print(f"\n🎯 Next steps:")
    print(f"   1. Explore dataset: ls {output_dir}")
    print(f"   2. Check metadata: head {output_dir}/metadata.csv")
    print(f"   3. Test samples: play some .wav files")
    print(f"   4. Use for training your neural network!")
    print()
    print("Happy training! 🚀")


def main():
    """Main execution function."""
    import time
    
    print("🎵 DJNet Local Dataset Generation")
    print("=" * 50)
    print("Generating 20k transitions with 20-second source segments")
    print("All files will be saved locally - no cloud needed!")
    print()
    
    # Get user preferences
    print("📁 Dataset location options:")
    print("1. Current directory (./data and ./output)")
    print("2. Custom location")
    
    choice = input("Choose option (1-2, default=1): ").strip()
    
    if choice == "2":
        data_dir = input("Data directory (for FMA dataset): ").strip()
        output_dir = input("Output directory (for generated dataset): ").strip()
    else:
        data_dir = "./data"
        output_dir = "./output/djnet_dataset_20k"
    
    print(f"\n📍 Using locations:")
    print(f"   Data: {os.path.abspath(data_dir)}")
    print(f"   Output: {os.path.abspath(output_dir)}")
    
    try:
        # Step 1: Create configuration
        print("\n" + "=" * 50)
        print("STEP 1: CONFIGURATION")
        print("=" * 50)
        config = create_local_config(data_dir, output_dir)
        
        # Step 2: Download FMA dataset
        print("\n" + "=" * 50)
        print("STEP 2: DOWNLOAD DATASET")
        print("=" * 50)
        music_dir = download_fma_dataset(config)
        
        # Step 3: Analyze tracks
        print("\n" + "=" * 50)
        print("STEP 3: ANALYZE TRACKS")
        print("=" * 50)
        analysis_files = analyze_tracks(config)
        
        if not analysis_files:
            print("❌ No tracks analyzed successfully!")
            return
        
        # Step 4: Find compatible pairs
        print("\n" + "=" * 50)
        print("STEP 4: FIND COMPATIBLE PAIRS")
        print("=" * 50)
        compatible_pairs = find_compatible_pairs(analysis_files, config)
        
        if not compatible_pairs:
            print("❌ No compatible pairs found!")
            return
        
        # Step 5: Generate transitions
        print("\n" + "=" * 50)
        print("STEP 5: GENERATE TRANSITIONS")
        print("=" * 50)
        metadata = generate_transitions(compatible_pairs, config)
        
        if not metadata:
            print("❌ No transitions generated!")
            return
        
        # Step 6: Show results
        print_results_summary(config, metadata)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Generation stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
