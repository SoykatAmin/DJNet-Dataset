# DJNet Local Dataset Generation

Generate your 20k DJNet transition dataset locally on your own system.

## Quick Start

1. **Create virtual environment (recommended):**
   ```bash
   python -m venv djnet-env
   source djnet-env/bin/activate  # Linux/Mac
   # djnet-env\Scripts\activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate dataset:**
   ```bash
   python generate_local_dataset.py
   ```

4. **Monitor progress (optional):**
   ```bash
   # In a separate terminal (activate environment first!)
   source djnet-env/bin/activate
   python monitor_local_progress.py
   ```

That's it! No cloud instances, no uploads needed.

## What It Does

### Automatic Process:
1. **Downloads FMA dataset** (~8GB, one-time download)
2. **Analyzes audio tracks** (tempo, key, etc.)
3. **Finds compatible pairs** for smooth transitions
4. **Generates 20k transitions** with:
   - 20-second source segments (A & B)
   - Natural-length transitions (2-8 seconds)
   - Multiple transition types (fade, cut, etc.)

### Output Structure:
```
output/djnet_dataset_20k/
├── transition_00000/
│   ├── source_a.wav      # 20 seconds
│   ├── source_b.wav      # 20 seconds  
│   ├── target.wav        # Natural length transition
│   └── conditioning.json # Metadata
├── transition_00001/
│   └── ...
├── metadata.csv          # Summary of all transitions
└── progress.json         # Generation progress
```

## System Requirements

- **Python 3.7+**
- **~50-100 GB free space** (for dataset)
- **8 GB RAM minimum** (16 GB recommended)
- **Good internet connection** (for initial FMA download)

## Configuration Options

When you run the script, you can choose:

1. **Default locations:**
   - Data: `./data/` (FMA dataset)
   - Output: `./output/djnet_dataset_20k/`

2. **Custom locations:**
   - Specify your own directories
   - Useful for external drives, etc.

## Expected Timeline

| System | Generation Time | Notes |
|--------|----------------|-------|
| Fast Desktop (16+ GB RAM) | 4-8 hours | Recommended |
| Average Laptop (8 GB RAM) | 8-16 hours | Works fine |
| Slow System (4 GB RAM) | 16+ hours | May struggle |

Initial FMA download: 30-60 minutes (one-time only)

## Monitoring Progress

### Real-time Monitor
```bash
python monitor_local_progress.py
```

Shows:
- Current progress (X/20,000)
- Generation rate (transitions/sec)
- Dataset size (GB)
- Estimated completion time
- Success/failure rates

### Manual Checks
```bash
# Count generated transitions
ls output/djnet_dataset_20k/ | grep transition | wc -l

# Check dataset size
du -sh output/djnet_dataset_20k/

# View progress file
cat output/djnet_dataset_20k/progress.json
```

## Customization

Edit the config in `generate_local_dataset.py`:

```python
'dataset': {
    'num_transitions': 20000,  # Change this number
    'shuffle_pairs': True,
    'minimum_valid_starts': 3
},
'audio': {
    'source_segment_length_sec': 20.0,  # Source length
    'tempo_threshold': 15.0,  # Compatibility
    'key_compatibility_threshold': 2,
}
```

## Troubleshooting

### Not Enough Compatible Pairs
```
⚠️ Warning: Only X pairs available for 20000 requested transitions
```

**Solutions:**
- Relax tempo threshold (increase from 15.0 to 20.0)
- Relax key threshold (increase from 2 to 3)
- Add more audio files to FMA dataset
- Reduce target number (e.g., 10k instead of 20k)

### Out of Disk Space
```
❌ No space left on device
```

**Solutions:**
- Use external drive for output directory
- Clean up other files
- Generate smaller dataset first

### Memory Issues
```
❌ Out of memory
```

**Solutions:**
- Close other applications
- Process fewer files at once
- Use system with more RAM

### Slow Generation
**Tips:**
- Close unnecessary applications
- Use SSD instead of HDD
- Ensure good CPU cooling
- Run overnight for large datasets

## What You Get

After successful completion:
- **20,000 transition samples** ready for ML training
- **Consistent format:** All transitions use same sample rate, format
- **Metadata:** Full information about each transition
- **Natural durations:** No artificial padding or blank audio
- **Local storage:** Everything on your system, no cloud needed

## Next Steps

1. **Verify dataset:**
   ```bash
   # Check metadata
   head output/djnet_dataset_20k/metadata.csv
   
   # Test a few samples
   play output/djnet_dataset_20k/transition_00000/target.wav
   ```

2. **Use for training:**
   - Load metadata.csv in your ML framework
   - Point to audio files for training
   - Use conditioning.json for advanced features

3. **Share or backup:**
   - Archive: `tar -czf djnet_dataset_20k.tar.gz output/djnet_dataset_20k/`
   - Upload to cloud storage if needed
   - Share with collaborators

Happy training! 🚀
