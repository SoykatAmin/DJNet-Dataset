#!/usr/bin/env python3
"""
Upload Progress Monitor

Monitor Google Drive upload progress when using rclone.
Run this in a separate terminal while upload is running.
"""

import os
import time
import subprocess
import re
from datetime import datetime, timedelta

def get_upload_progress():
    """Check rclone progress and Google Drive folder size."""
    try:
        # Check if rclone is running
        result = subprocess.run(['pgrep', 'rclone'], capture_output=True, text=True)
        rclone_running = bool(result.stdout.strip())
        
        if rclone_running:
            status = "🚀 UPLOADING"
        else:
            status = "⏸️  NOT RUNNING"
        
        return status, rclone_running
        
    except Exception as e:
        return f"❌ ERROR: {e}", False

def check_gdrive_folder():
    """Check Google Drive folder size using rclone."""
    try:
        result = subprocess.run(['rclone', 'size', 'gdrive:DJNet_Dataset/'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse output: "Total objects: X, Total size: Y"
            output = result.stdout.strip()
            size_match = re.search(r'Total size: ([\d.]+\s*\w+)', output)
            count_match = re.search(r'Total objects: (\d+)', output)
            
            if size_match and count_match:
                size = size_match.group(1)
                count = count_match.group(1)
                return f"📁 Google Drive: {count} files, {size}"
            else:
                return "📁 Google Drive: Connected"
        else:
            return "📁 Google Drive: Not accessible"
            
    except subprocess.TimeoutExpired:
        return "📁 Google Drive: Checking..."
    except Exception as e:
        return f"📁 Google Drive: Error - {e}"

def estimate_completion(start_time, current_size_gb, target_size_gb):
    """Estimate completion time based on progress."""
    if current_size_gb <= 0 or target_size_gb <= 0:
        return "Unknown"
    
    elapsed_time = time.time() - start_time
    if elapsed_time <= 0:
        return "Calculating..."
    
    upload_rate = current_size_gb / elapsed_time  # GB/second
    remaining_gb = target_size_gb - current_size_gb
    
    if upload_rate <= 0:
        return "Unknown"
    
    eta_seconds = remaining_gb / upload_rate
    eta_time = datetime.now() + timedelta(seconds=eta_seconds)
    
    return f"{eta_time.strftime('%H:%M')} ({eta_seconds/3600:.1f}h remaining)"

def monitor_upload():
    """Main monitoring function."""
    print("📤 DJNet Google Drive Upload Monitor")
    print("=" * 50)
    print("Monitoring upload progress...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    start_time = time.time()
    target_size_gb = 80.0  # Estimated dataset size
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("📤 DJNet Google Drive Upload Monitor")
            print("=" * 50)
            print(f"Started: {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}")
            print(f"Current: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Elapsed: {(time.time() - start_time)/3600:.1f} hours")
            print()
            
            # Check rclone status
            status, is_running = get_upload_progress()
            print(f"Status: {status}")
            
            # Check Google Drive folder
            gdrive_status = check_gdrive_folder()
            print(gdrive_status)
            
            print()
            print("💡 Tips:")
            if is_running:
                print("• Upload is running - keep this terminal open")
                print("• Don't close the vast.ai instance")
                print("• Check rclone terminal for detailed progress")
            else:
                print("• rclone not detected - start upload with:")
                print("  /tmp/upload_to_gdrive.sh")
            
            print()
            print("🔧 Useful commands:")
            print("• Check rclone processes: ps aux | grep rclone")
            print("• Check Google Drive size: rclone size gdrive:DJNet_Dataset/")
            print("• Resume upload: /tmp/upload_to_gdrive.sh")
            
            print("\nPress Ctrl+C to exit monitor")
            
            time.sleep(30)  # Update every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n📊 Upload monitoring stopped.")
        print("Upload may still be running in background.")
        print("Check with: ps aux | grep rclone")

if __name__ == "__main__":
    monitor_upload()
