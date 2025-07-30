#!/usr/bin/env python3
"""
Local Dataset Generation Progress Monitor

Monitor the progress of local dataset generation.
Run this in a separate terminal while generation is running.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

def monitor_local_progress(output_dir="./output/djnet_dataset_20k"):
    """Monitor local dataset generation progress."""
    print("🎵 DJNet Local Generation Monitor")
    print("=" * 40)
    print(f"Monitoring: {output_dir}")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    start_time = time.time()
    target_count = 20000  # Default target
    
    try:
        while True:
            if os.path.exists(output_dir):
                # Count generated transitions
                transition_dirs = [d for d in os.listdir(output_dir) 
                                 if d.startswith('transition_') and os.path.isdir(os.path.join(output_dir, d))]
                current_count = len(transition_dirs)
                
                # Try to read progress file for more info
                progress_file = os.path.join(output_dir, "progress.json")
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            progress_data = json.load(f)
                        target_count = progress_data.get('target', 20000)
                        failed_count = progress_data.get('failed', 0)
                        status = "RUNNING"
                    except:
                        failed_count = 0
                        status = "RUNNING"
                else:
                    failed_count = 0
                    status = "INITIALIZING"
                
                # Calculate progress
                progress_pct = (current_count / target_count) * 100
                elapsed_time = time.time() - start_time
                
                if current_count > 0:
                    rate = current_count / elapsed_time
                    eta_seconds = (target_count - current_count) / rate if rate > 0 else 0
                    eta_hours = eta_seconds / 3600
                else:
                    rate = 0
                    eta_hours = 0
                
                # Calculate dataset size
                total_size = 0
                try:
                    for root, dirs, files in os.walk(output_dir):
                        for file in files:
                            if file.endswith('.wav'):
                                total_size += os.path.getsize(os.path.join(root, file))
                    size_gb = total_size / (1024**3)
                except:
                    size_gb = 0
                
                # Clear screen and display info
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("🎵 DJNet Local Generation Monitor")
                print("=" * 50)
                print(f"Started: {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}")
                print(f"Current: {datetime.now().strftime('%H:%M:%S')}")
                print(f"Elapsed: {elapsed_time/3600:.1f} hours")
                print()
                
                print(f"Status: {status}")
                print(f"Progress: {current_count:,}/{target_count:,} ({progress_pct:.1f}%)")
                print(f"Failed: {failed_count}")
                print(f"Success Rate: {(current_count/(current_count+failed_count)*100) if (current_count+failed_count) > 0 else 0:.1f}%")
                print(f"Generation Rate: {rate:.1f} transitions/sec")
                print(f"Dataset Size: {size_gb:.2f} GB")
                print(f"ETA: {eta_hours:.1f} hours")
                
                # Progress bar
                bar_width = 40
                filled = int(bar_width * progress_pct / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"\n[{bar}] {progress_pct:.1f}%")
                
                # Show file structure sample
                if current_count > 0:
                    print(f"\n📁 Sample structure:")
                    sample_dir = os.path.join(output_dir, transition_dirs[0])
                    if os.path.exists(sample_dir):
                        files = os.listdir(sample_dir)
                        for file in sorted(files):
                            file_path = os.path.join(sample_dir, file)
                            if os.path.isfile(file_path):
                                size = os.path.getsize(file_path)
                                size_str = f"{size/(1024*1024):.1f}MB" if size > 1024*1024 else f"{size/1024:.1f}KB"
                                print(f"   {file}: {size_str}")
                
                print(f"\n💡 Tip: Check generated samples in {output_dir}")
                print("Press Ctrl+C to exit monitor")
                
            else:
                print(f"\rWaiting for generation to start...", end="", flush=True)
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n📊 Monitoring stopped.")
        if os.path.exists(output_dir):
            final_count = len([d for d in os.listdir(output_dir) 
                             if d.startswith('transition_') and os.path.isdir(os.path.join(output_dir, d))])
            print(f"Final count: {final_count} transitions generated")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor local DJNet dataset generation')
    parser.add_argument('--output-dir', default='./output/djnet_dataset_20k', 
                       help='Output directory to monitor')
    
    args = parser.parse_args()
    
    monitor_local_progress(args.output_dir)

if __name__ == "__main__":
    main()
