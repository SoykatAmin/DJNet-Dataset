#!/usr/bin/env python3
"""
Progress Monitor for Dataset Generation

Run this in a separate terminal to monitor progress.
"""

import os
import time
import json
from pathlib import Path

def monitor_progress():
    """Monitor dataset generation progress."""
    output_dir = "/tmp/djnet_dataset_20k"
    target_count = 20000
    
    print("DJNet Dataset Generation Monitor")
    print("=" * 40)
    print(f"Target: {target_count} transitions")
    print(f"Monitoring: {output_dir}")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    start_time = time.time()
    
    try:
        while True:
            if os.path.exists(output_dir):
                # Count generated transitions
                transition_dirs = [d for d in os.listdir(output_dir) 
                                 if d.startswith('transition_') and os.path.isdir(os.path.join(output_dir, d))]
                current_count = len(transition_dirs)
                
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
                
                # Check for partial metadata file
                partial_meta = os.path.join(output_dir, "metadata_partial.csv")
                status = "RUNNING" if os.path.exists(partial_meta) else "INITIALIZING"
                
                print(f"\r{status} | Progress: {current_count:,}/{target_count:,} ({progress_pct:.1f}%) | "
                      f"Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f}h", end="", flush=True)
            else:
                print(f"\rWaiting for output directory to be created...", end="", flush=True)
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_progress()
