#!/usr/bin/env python3
"""
Upload Dataset to Google Drive

This script uploads the generated DJNet dataset to Google Drive.
Designed for use on vast.ai or other cloud hardware.
"""

import os
import sys
import time
import shutil
import zipfile
from pathlib import Path
import subprocess

def install_dependencies():
    """Install required packages for Google Drive upload."""
    print("📦 Installing Google Drive dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pydrive2', 'google-auth', 'google-auth-oauthlib'], check=True, capture_output=True)
        print("Dependencies installed!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    return True

def authenticate_gdrive():
    """Set up Google Drive authentication."""
    print("🔐 Setting up Google Drive authentication...")
    
    # Create credentials file template
    credentials_template = '''
{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost:8080"]
}
'''
    
    settings_template = '''
client_config_backend: settings
client_config:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET

save_credentials: True
save_credentials_backend: file
save_credentials_file: credentials.json

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive.file
'''
    
    # Write templates if they don't exist
    if not os.path.exists('client_secrets.json'):
        with open('client_secrets.json', 'w') as f:
            f.write(credentials_template)
        print("   Created client_secrets.json template")
        print("   Please update it with your Google Drive API credentials")
        print("   Get credentials at: https://console.developers.google.com/")
        return False
    
    if not os.path.exists('settings.yaml'):
        with open('settings.yaml', 'w') as f:
            f.write(settings_template)
        print(" Created settings.yaml template")
    
    return True

def create_zip_archive(dataset_dir, output_path, progress_callback=None):
    """Create a zip archive of the dataset with progress tracking."""
    print(f" Creating zip archive: {output_path}")
    
    # Count total files for progress
    total_files = 0
    for root, dirs, files in os.walk(dataset_dir):
        total_files += len(files)
    
    processed_files = 0
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(dataset_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, dataset_dir)
                zipf.write(file_path, arc_name)
                
                processed_files += 1
                if progress_callback and processed_files % 100 == 0:
                    progress = (processed_files / total_files) * 100
                    progress_callback(f"Zipping: {progress:.1f}% ({processed_files}/{total_files})")
    
    file_size = os.path.getsize(output_path)
    print(f" Archive created: {file_size / (1024**3):.2f} GB")
    return output_path

def upload_to_gdrive_with_rclone(file_path, remote_path="gdrive:DJNet_Dataset/"):
    """Upload using rclone (alternative method - more reliable for large files)."""
    print(" Using rclone for upload (recommended for large files)")
    print(" Setup instructions:")
    print("1. Install rclone: curl https://rclone.org/install.sh | sudo bash")
    print("2. Configure Google Drive: rclone config")
    print("3. Run the upload command below:")
    print()
    
    filename = os.path.basename(file_path)
    upload_cmd = f"rclone copy '{file_path}' '{remote_path}' --progress --transfers 4 --checkers 8"
    
    print(f"Upload command:")
    print(f"  {upload_cmd}")
    print()
    print("Optional: Monitor upload progress in another terminal:")
    print(f"  watch -n 5 'rclone size {remote_path}'")
    
    return upload_cmd

def upload_to_gdrive_pydrive(file_path):
    """Upload using PyDrive2."""
    try:
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
    except ImportError:
        print(" PyDrive2 not installed. Installing...")
        if not install_dependencies():
            return False
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
    
    print(" Authenticating with Google Drive...")
    
    try:
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # This will open a browser for authentication
        drive = GoogleDrive(gauth)
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"📤 Uploading {filename} ({file_size / (1024**3):.2f} GB)...")
        print("⚠️  This may take several hours for large files...")
        
        # Create file in Drive
        gfile = drive.CreateFile({'title': filename})
        gfile.SetContentFile(file_path)
        
        # Upload with progress (limited progress info available)
        start_time = time.time()
        gfile.Upload()
        
        elapsed_time = time.time() - start_time
        upload_speed = file_size / elapsed_time / (1024**2)  # MB/s
        
        print(f"✅ Upload completed!")
        print(f"   Time: {elapsed_time/3600:.1f} hours")
        print(f"   Speed: {upload_speed:.1f} MB/s")
        print(f"   File ID: {gfile['id']}")
        print(f"   Share link: https://drive.google.com/file/d/{gfile['id']}/view")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    """Main upload process."""
    print("🎵 DJNet Dataset Google Drive Upload")
    print("=" * 50)
    
    # Configuration
    dataset_dir = "/tmp/djnet_dataset_20k"  # Adjust path as needed
    zip_filename = "djnet_dataset_20k.zip"
    zip_path = f"/tmp/{zip_filename}"
    
    # Check if dataset exists
    if not os.path.exists(dataset_dir):
        print(f"❌ Dataset directory not found: {dataset_dir}")
        print("Please update the dataset_dir path in the script")
        return
    
    # Count transitions
    transitions = [d for d in os.listdir(dataset_dir) 
                  if d.startswith('transition_') and os.path.isdir(os.path.join(dataset_dir, d))]
    print(f"📊 Found {len(transitions)} transitions in dataset")
    
    # Estimate sizes
    sample_size = 0
    if transitions:
        sample_dir = os.path.join(dataset_dir, transitions[0])
        for f in os.listdir(sample_dir):
            if f.endswith('.wav'):
                sample_size += os.path.getsize(os.path.join(sample_dir, f))
    
    estimated_total = sample_size * len(transitions) / (1024**3)  # GB
    estimated_zip = estimated_total * 0.7  # Assume 70% compression
    
    print(f"📏 Estimated dataset size: {estimated_total:.2f} GB")
    print(f"📦 Estimated zip size: {estimated_zip:.2f} GB")
    print()
    
    # Choose upload method
    print("🚀 Choose upload method:")
    print("1. rclone (recommended for large files)")
    print("2. PyDrive2 (direct Python upload)")
    print("3. Create zip only (upload manually)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    # Create zip archive
    def progress_print(msg):
        print(f"\r{msg}", end="", flush=True)
    
    if not os.path.exists(zip_path):
        create_zip_archive(dataset_dir, zip_path, progress_print)
        print()  # New line after progress
    else:
        print(f"📦 Using existing zip file: {zip_path}")
    
    # Handle upload based on choice
    if choice == "1":
        upload_cmd = upload_to_gdrive_with_rclone(zip_path)
        print("\n🎯 To execute upload, run:")
        print(f"   {upload_cmd}")
        
    elif choice == "2":
        if not authenticate_gdrive():
            print("❌ Authentication setup required first")
            return
        upload_to_gdrive_pydrive(zip_path)
        
    elif choice == "3":
        print(f"✅ Zip file created: {zip_path}")
        print(f"📤 Upload manually to Google Drive")
        print(f"💡 You can also use Google Drive desktop app to sync the file")
        
    else:
        print("❌ Invalid choice")
        return
    
    print("\n🎉 Process completed!")
    print("\n📋 Next steps:")
    print("1. Verify upload completed successfully")
    print("2. Test download a sample to ensure integrity")
    print("3. Clean up local files if needed")
    print("4. Share dataset or keep private as needed")

if __name__ == "__main__":
    main()
