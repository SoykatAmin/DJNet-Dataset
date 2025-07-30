#!/usr/bin/env python3
"""
Full Dataset Generation Script for vast.ai

This script generates a large DJNet transition dataset optimized for cloud hardware.
Designed to run efficiently on rented GPU/CPU instances.
"""

import os
import sys
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


def create_vast_config():
    """Create configuration optimized for vast.ai hardware."""
    return {
        'data': {
            'music_dir': '/tmp/fma_small',
            'analysis_dir': '/tmp/track_analysis',
            'output_dir': '/tmp/djnet_dataset_20k',
            'fma_url': 'https://os.unil.cloud.switch.ch/fma/fma_small.zip'
        },
        'audio': {
            'target_sample_rate': 22050,  # Optimized for speed
            'mono': True,
            'tempo_threshold': 15.0,  # More lenient for larger dataset
            'key_compatibility_threshold': 2,
            'source_segment_length_sec': 20.0
        },
        'transitions': {
            'transition_bars': 4,
            'beats_per_bar': 4,
            'types': [
                {'name': 'linear_fade', 'weight': 0.35},
                {'name': 'exp_fade', 'weight': 0.25}, 
                {'name': 'bass_swap_eq', 'weight': 0.20},
                {'name': 'filter_sweep', 'weight': 0.10},
                {'name': 'hard_cut', 'weight': 0.05},
                {'name': 'echo_fade', 'weight': 0.05}
            ]
        },
        'dataset': {
            'num_transitions': 20000,  # Target 20k transitions
            'shuffle_pairs': True,
            'minimum_valid_starts': 3,
            'batch_size': 100  # Process in batches for memory efficiency
        },
        'echo_fade': {'num_echos': 3, 'decay_db': 5},
        'filter_sweep': {'start_freq': 15000, 'end_freq': 200, 'chunk_size_ms': 100},
        'eq': {'crossover_freq': 300},
        'exp_fade': {'power_out_range': [1.2, 2.5], 'power_in_range': [0.4, 0.9]}
    }


def download_and_extract_fma(config):
    """Download and extract FMA dataset."""
    print("=" * 60)
    print("DOWNLOADING FMA DATASET")
    print("=" * 60)
    
    music_dir = config['data']['music_dir']
    if os.path.exists(music_dir):
        print(f"Dataset already exists at {music_dir}")
        return
    
    fma_url = config['data']['fma_url']
    zip_path = '/tmp/fma_small.zip'
    
    print(f"Downloading from: {fma_url}")
    
    def download_with_progress(url, filename):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    download_with_progress(fma_url, zip_path)
    
    print("Extracting dataset...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp/')
    
    os.remove(zip_path)
    print(f"Dataset ready at: {music_dir}")


def analyze_all_tracks(config):
    """Analyze all audio tracks."""
    print("=" * 60)
    print("ANALYZING AUDIO TRACKS")
    print("=" * 60)
    
    music_dir = config['data']['music_dir']
    analysis_dir = config['data']['analysis_dir']
    
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Find all audio files
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.flac']:
        audio_files.extend(glob.glob(os.path.join(music_dir, '**', ext), recursive=True))
    
    print(f"Found {len(audio_files)} audio files")
    
    # Initialize analyzer
    analyzer = AudioAnalyzer(target_sr=config['audio']['target_sample_rate'])
    
    analysis_files = []
    failed_count = 0
    
    for audio_file in tqdm(audio_files, desc="Analyzing tracks"):
        try:
            analysis_data = analyzer.analyze_track(audio_file)
            if analysis_data:
                base_name = os.path.splitext(os.path.basename(audio_file))[0]
                output_path = os.path.join(analysis_dir, f"{base_name}.json")
                
                with open(output_path, 'w') as f:
                    json.dump(analysis_data, f, indent=2)
                analysis_files.append(output_path)
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # Only show first few errors
                print(f"Error analyzing {audio_file}: {str(e)[:100]}...")
    
    print(f"Analysis complete!")
    print(f"Successfully analyzed: {len(analysis_files)} tracks")
    print(f"Failed: {failed_count} tracks")
    
    return analysis_files


def generate_natural_transition(pair, output_dir, config):
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
        
        # Extract segments
        max_start_a = len(y_a) - source_samples_a
        max_start_b = len(y_b) - source_samples_b
        
        if max_start_a <= 0 or max_start_b <= 0:
            return None
        
        start_a = random.randint(0, max_start_a)
        start_b = random.randint(0, max_start_b)
        
        segment_a = y_a[start_a:start_a + source_samples_a]
        segment_b = y_b[start_b:start_b + source_samples_b]
        
        # Resample if needed
        if sr_a != target_sr:
            segment_a = librosa.resample(segment_a, orig_sr=sr_a, target_sr=target_sr)
        if sr_b != target_sr:
            segment_b = librosa.resample(segment_b, orig_sr=sr_b, target_sr=target_sr)
        
        # Ensure exact length
        target_samples = int(source_length_sec * target_sr)
        
        if len(segment_a) < target_samples:
            segment_a = np.pad(segment_a, (0, target_samples - len(segment_a)))
        else:
            segment_a = segment_a[:target_samples]
            
        if len(segment_b) < target_samples:
            segment_b = np.pad(segment_b, (0, target_samples - len(segment_b)))
        else:
            segment_b = segment_b[:target_samples]
        
        # Convert to AudioSegment
        segment_a_int = (segment_a * 32767).astype(np.int16)
        segment_b_int = (segment_b * 32767).astype(np.int16)
        
        seg_a = AudioSegment(
            segment_a_int.tobytes(), 
            frame_rate=target_sr, 
            sample_width=2, 
            channels=1
        )
        seg_b = AudioSegment(
            segment_b_int.tobytes(), 
            frame_rate=target_sr, 
            sample_width=2, 
            channels=1
        )
        
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
        if chosen_type == 'linear_fade':
            fade_duration = natural_transition_ms
            part_a = seg_a[-fade_duration:].fade_out(fade_duration)
            part_b = seg_b[:fade_duration].fade_in(fade_duration)
            target_transition = part_a.overlay(part_b)
        elif chosen_type == 'exp_fade':
            fade_duration = natural_transition_ms
            part_a = seg_a[-fade_duration:].fade_out(fade_duration)
            part_b = seg_b[:fade_duration].fade_in(fade_duration)
            target_transition = part_a.overlay(part_b)
        elif chosen_type == 'hard_cut':
            cut_duration = 100
            part_a = seg_a[-cut_duration//2:]
            part_b = seg_b[:cut_duration//2]
            target_transition = part_a + part_b
        else:  # Default to fade for other types
            fade_duration = natural_transition_ms
            part_a = seg_a[-fade_duration:].fade_out(fade_duration)
            part_b = seg_b[:fade_duration].fade_in(fade_duration)
            target_transition = part_a.overlay(part_b)
        
        # Save files
        os.makedirs(output_dir, exist_ok=True)
        
        seg_a.export(os.path.join(output_dir, "source_a.wav"), format="wav")
        seg_b.export(os.path.join(output_dir, "source_b.wav"), format="wav")
        target_transition.export(os.path.join(output_dir, "target.wav"), format="wav")
        
        # Save metadata
        actual_transition_sec = len(target_transition) / 1000.0
        conditioning = {
            "source_a_path": track_a_data['path'],
            "source_b_path": track_b_data['path'],
            "source_segment_length_sec": source_length_sec,
            "transition_length_sec": actual_transition_sec,
            "sample_rate": target_sr,
            "transition_type": chosen_type,
            "avg_tempo": avg_tempo,
            "start_position_a_sec": start_a / sr_a,
            "start_position_b_sec": start_b / sr_b
        }
        
        with open(os.path.join(output_dir, "conditioning.json"), 'w') as f:
            json.dump(conditioning, f, indent=2)
        
        return output_dir
        
    except Exception as e:
        return None


def generate_full_dataset(config, analysis_files):
    """Generate the complete dataset."""
    print("=" * 60)
    print("GENERATING DATASET")
    print("=" * 60)
    
    # Load analysis data
    print("Loading track analysis data...")
    analyzer = AudioAnalyzer(target_sr=config['audio']['target_sample_rate'])
    tracks_data = analyzer.load_analysis_data(analysis_files)
    print(f"Loaded {len(tracks_data)} track analyses")
    
    # Find compatible pairs
    print("Finding compatible pairs...")
    pairer = TrackPairer(
        tempo_threshold=config['audio']['tempo_threshold'],
        key_threshold=config['audio']['key_compatibility_threshold']
    )
    compatible_pairs = pairer.find_compatible_pairs(tracks_data)
    print(f"Found {len(compatible_pairs)} compatible pairs")
    
    if len(compatible_pairs) == 0:
        print("ERROR: No compatible pairs found!")
        return []
    
    # Prepare for generation
    target_transitions = config['dataset']['num_transitions']
    if len(compatible_pairs) < target_transitions:
        print(f"WARNING: Only {len(compatible_pairs)} pairs available for {target_transitions} requested transitions")
        print("Will generate with repetition...")
        # Repeat pairs to reach target
        multiplier = (target_transitions // len(compatible_pairs)) + 1
        compatible_pairs = (compatible_pairs * multiplier)[:target_transitions]
    
    random.shuffle(compatible_pairs)
    
    print(f"Generating {target_transitions} transitions...")
    print(f"Source segments: {config['audio']['source_segment_length_sec']} seconds each")
    print(f"Output directory: {config['data']['output_dir']}")
    
    # Generate in batches for memory efficiency
    batch_size = config['dataset']['batch_size']
    metadata = []
    generated_count = 0
    failed_count = 0
    
    os.makedirs(config['data']['output_dir'], exist_ok=True)
    
    for i in tqdm(range(0, len(compatible_pairs), batch_size), desc="Processing batches"):
        batch_pairs = compatible_pairs[i:i + batch_size]
        
        for pair in tqdm(batch_pairs, desc=f"Batch {i//batch_size + 1}", leave=False):
            transition_id = f"transition_{generated_count:05d}"
            output_dir = os.path.join(config['data']['output_dir'], transition_id)
            
            result_path = generate_natural_transition(pair, output_dir, config)
            
            if result_path:
                # Load conditioning info
                conditioning_path = os.path.join(result_path, "conditioning.json")
                with open(conditioning_path, 'r') as f:
                    conditioning = json.load(f)
                
                metadata.append({
                    "id": transition_id,
                    "path": result_path,
                    "transition_type": conditioning['transition_type'],
                    "transition_length_sec": conditioning['transition_length_sec'],
                    "avg_tempo": conditioning['avg_tempo']
                })
                generated_count += 1
            else:
                failed_count += 1
            
            # Save metadata periodically
            if generated_count % 1000 == 0:
                print(f"Generated {generated_count} transitions so far...")
                df = pd.DataFrame(metadata)
                df.to_csv(os.path.join(config['data']['output_dir'], "metadata_partial.csv"), index=False)
    
    # Save final metadata
    if metadata:
        df = pd.DataFrame(metadata)
        metadata_path = os.path.join(config['data']['output_dir'], "metadata.csv")
        df.to_csv(metadata_path, index=False)
        
        # Remove partial file
        partial_path = os.path.join(config['data']['output_dir'], "metadata_partial.csv")
        if os.path.exists(partial_path):
            os.remove(partial_path)
    
    print(f"\nDataset generation complete!")
    print(f"Successfully generated: {generated_count} transitions")
    print(f"Failed: {failed_count} transitions")
    print(f"Success rate: {generated_count/(generated_count+failed_count)*100:.1f}%")
    
    # Show statistics
    if metadata:
        print(f"\nDataset Statistics:")
        print(f"Total transitions: {len(metadata)}")
        
        transition_lengths = [item['transition_length_sec'] for item in metadata]
        print(f"Transition lengths - Min: {np.min(transition_lengths):.2f}s, Max: {np.max(transition_lengths):.2f}s, Avg: {np.mean(transition_lengths):.2f}s")
        
        type_counts = {}
        for item in metadata:
            t_type = item['transition_type']
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
        
        print("\nTransition types:")
        for t_type, count in type_counts.items():
            print(f"  {t_type}: {count}")
    
    return metadata


def create_download_package(config):
    """Create a downloadable package of the dataset."""
    print("=" * 60)
    print("CREATING DOWNLOAD PACKAGE")
    print("=" * 60)
    
    output_dir = config['data']['output_dir']
    if not os.path.exists(output_dir):
        print("No dataset to package!")
        return
    
    print("Creating compressed archive...")
    archive_path = "/tmp/djnet_dataset_20k"
    shutil.make_archive(archive_path, 'zip', output_dir)
    
    archive_file = f"{archive_path}.zip"
    size_mb = os.path.getsize(archive_file) / (1024 * 1024)
    
    print(f"Dataset packaged: {archive_file}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Ready for download!")
    
    return archive_file


def create_upload_instructions(dataset_dir, archive_file):
    """Create scripts and instructions for uploading to Google Drive."""
    
    # Create rclone upload script
    rclone_script = f'''#!/bin/bash
# Upload DJNet dataset to Google Drive using rclone

ARCHIVE_FILE="{archive_file}"
GDRIVE_PATH="gdrive:DJNet_Dataset/"

echo "📤 Starting upload to Google Drive..."
echo "📋 File: $ARCHIVE_FILE"
echo "🎯 Destination: $GDRIVE_PATH"
echo "⚠️  This will take several hours for large datasets"

# Upload with progress and resume capability
rclone copy "$ARCHIVE_FILE" "$GDRIVE_PATH" \\
    --progress \\
    --transfers 4 \\
    --checkers 8 \\
    --retries 3 \\
    --low-level-retries 10 \\
    --stats 30s \\
    --stats-one-line

echo "✅ Upload complete!"
echo "📋 File uploaded to: $GDRIVE_PATH$(basename "$ARCHIVE_FILE")"

# Clean up local archive file after successful upload
read -p "🗑️  Delete local archive file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f "$ARCHIVE_FILE"
    echo "✅ Local archive deleted"
fi

echo "🎉 All done!"
'''
    
    upload_script_path = '/tmp/upload_to_gdrive.sh'
    with open(upload_script_path, 'w') as f:
        f.write(rclone_script)
    os.chmod(upload_script_path, 0o755)
    
    # Create comprehensive instructions
    archive_size_gb = os.path.getsize(archive_file) / (1024**3)
    
    instructions = f'''
🎉 DJNet Dataset Generation Complete!

📊 Dataset Information:
   Dataset Location: {dataset_dir}
   Archive Location: {archive_file}
   Archive Size: {archive_size_gb:.2f} GB
   Upload Estimated Time: {archive_size_gb * 0.5:.1f} - {archive_size_gb * 2:.1f} hours

🚀 UPLOAD TO GOOGLE DRIVE - Choose Your Method:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 METHOD 1: RCLONE (RECOMMENDED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install rclone:
   curl https://rclone.org/install.sh | sudo bash

2. Configure Google Drive:
   rclone config
   
   When prompted:
   - Choose "n" for new remote
   - Name: gdrive
   - Storage type: drive (Google Drive)
   - Leave client_id and client_secret blank
   - Choose "1" for full access
   - Leave root_folder_id blank
   - Leave service_account_file blank
   - Choose "n" for advanced config
   - Complete OAuth in browser

3. Run upload script:
   {upload_script_path}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 METHOD 2: MANUAL WEB UPLOAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to drive.google.com
2. Click "New" → "File upload"  
3. Select: {archive_file}
4. Wait for upload completion

⚠️  IMPORTANT NOTES:
• Keep vast.ai instance running during upload
• Archive size: {archive_size_gb:.2f} GB  
• Upload time: {archive_size_gb * 0.5:.1f}-{archive_size_gb * 2:.1f} hours

🎯 QUICK START (RECOMMENDED):
1. curl https://rclone.org/install.sh | sudo bash
2. rclone config  # Set up Google Drive  
3. {upload_script_path}

📄 Full instructions saved to: /tmp/upload_instructions.txt
'''
    
    print("\n" + "="*60)
    print("📤 GOOGLE DRIVE UPLOAD READY!")  
    print("="*60)
    print(f"Archive size: {archive_size_gb:.2f} GB")
    print(f"Estimated upload time: {archive_size_gb * 0.5:.1f}-{archive_size_gb * 2:.1f} hours")
    print()
    print("🚀 Quick start:")
    print("1. curl https://rclone.org/install.sh | sudo bash")
    print("2. rclone config")
    print(f"3. {upload_script_path}")
    
    # Save instructions to file
    with open('/tmp/upload_instructions.txt', 'w') as f:
        f.write(instructions)


def main():
    """Main execution function."""
    print("DJNet Full Dataset Generator for vast.ai")
    print("Target: 20,000 transitions")
    print("=" * 60)
    
    # Create configuration
    config = create_vast_config()
    
    try:
        # Step 1: Download dataset
        download_and_extract_fma(config)
        
        # Step 2: Analyze tracks
        analysis_files = analyze_all_tracks(config)
        
        if not analysis_files:
            print("ERROR: No tracks were successfully analyzed!")
            return
        
        # Step 3: Generate full dataset
        metadata = generate_full_dataset(config, analysis_files)
        
        if not metadata:
            print("ERROR: No transitions were generated!")
            return
        
        # Step 4: Create download package
        archive_file = create_download_package(config)
        
        # Step 5: Create upload instructions
        create_upload_instructions(config['data']['output_dir'], archive_file)
        
        print("\n" + "=" * 60)
        print("GENERATION COMPLETE!")
        print("=" * 60)
        print(f"Generated {len(metadata)} transitions")
        print(f"Dataset location: {config['data']['output_dir']}")
        print(f"Archive: {archive_file}")
        print("Check /tmp/upload_instructions.txt for Google Drive upload options!")
        print("Ready for download from vast.ai instance!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
