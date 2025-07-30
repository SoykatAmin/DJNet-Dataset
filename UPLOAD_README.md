# DJNet Dataset Upload to Google Drive

This guide helps you upload your generated 20k DJNet dataset to Google Drive from vast.ai.

## Quick Start

1. **Generate the dataset:**
   ```bash
   python generate_full_dataset.py
   ```

2. **Set up rclone:**
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   rclone config
   ```

3. **Upload to Google Drive:**
   ```bash
   /tmp/upload_to_gdrive.sh
   ```

4. **Monitor progress (optional):**
   ```bash
   python upload_monitor.py
   ```

## Detailed Instructions

### 1. rclone Configuration

When running `rclone config`:

1. Choose `n` for new remote
2. Name: `gdrive`
3. Storage type: `drive` (Google Drive)
4. Leave client_id and client_secret **blank**
5. Choose `1` for full access
6. Leave root_folder_id **blank**
7. Leave service_account_file **blank**
8. Choose `n` for advanced config
9. Complete OAuth in browser (will open automatically)

### 2. Upload Options

#### Option A: Automated Script (Recommended)
```bash
/tmp/upload_to_gdrive.sh
```

Features:
- Progress tracking
- Resume capability
- Automatic cleanup option
- Optimized settings

#### Option B: Manual rclone
```bash
rclone copy /tmp/djnet_dataset_20k.zip gdrive:DJNet_Dataset/ --progress
```

#### Option C: Web Upload
- Go to drive.google.com
- Upload `/tmp/djnet_dataset_20k.zip` manually
- ⚠️ May timeout for large files

### 3. Monitoring Upload

#### Real-time Monitor
```bash
python upload_monitor.py
```

#### Manual Checks
```bash
# Check if rclone is running
ps aux | grep rclone

# Check Google Drive folder size
rclone size gdrive:DJNet_Dataset/

# Check local file
ls -lh /tmp/djnet_dataset_20k.zip
```

## Expected Timeline

| Dataset Size | Upload Time | Bandwidth Needed |
|-------------|-------------|------------------|
| 20 GB       | 2-4 hours   | 2-4 MB/s        |
| 50 GB       | 4-8 hours   | 2-4 MB/s        |
| 100 GB      | 8-16 hours  | 2-4 MB/s        |

## Troubleshooting

### Upload Fails/Stops
```bash
# Resume upload
rclone copy /tmp/djnet_dataset_20k.zip gdrive:DJNet_Dataset/ --progress
```

### Authentication Issues
```bash
# Reconfigure Google Drive
rclone config delete gdrive
rclone config  # Set up again
```

### Check Upload Progress
```bash
# Compare sizes
ls -lh /tmp/djnet_dataset_20k.zip
rclone size gdrive:DJNet_Dataset/djnet_dataset_20k.zip
```

### Vast.ai Instance Issues
- Keep instance running during upload
- Monitor instance time remaining
- Extend instance if needed before upload completes

## After Upload

1. **Verify upload:**
   - Check file appears in Google Drive
   - Verify file size matches local file
   
2. **Test download:**
   - Download a small portion to test
   - Or download full file to verify integrity

3. **Clean up:**
   - Delete local files from vast.ai instance
   - Terminate vast.ai instance

## Files Created

- `/tmp/upload_to_gdrive.sh` - Upload script
- `/tmp/upload_instructions.txt` - Detailed instructions
- `upload_monitor.py` - Progress monitor
- `/tmp/djnet_dataset_20k.zip` - Dataset archive

## Tips for Success

- **Stable connection:** Use vast.ai instances with good network
- **Monitor progress:** Don't let vast.ai expire during upload
- **Resume capability:** rclone can resume interrupted uploads
- **Multiple attempts:** If upload fails, try again
- **Backup plan:** Consider downloading locally first if upload repeatedly fails

Happy uploading! 🚀
