# DJNet Dataset Setup Guide

## Virtual Environment Setup (Recommended)

Creating a virtual environment is **highly recommended** to avoid conflicts with other Python projects and keep your system clean.

### Option 1: Using venv (Built-in)

```bash
# Create virtual environment
python -m venv djnet-env

# Activate it
# On Linux/Mac:
source djnet-env/bin/activate
# On Windows:
djnet-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Your prompt should now show (djnet-env) at the beginning
```

### Option 2: Using conda (If you have Anaconda/Miniconda)

```bash
# Create conda environment
conda create -n djnet-env python=3.9

# Activate it
conda activate djnet-env

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

After activating your environment:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Test key libraries
python -c "import librosa, pydub, numpy; print('All dependencies working!')"
```

## Quick Start (With Virtual Environment)

```bash
# 1. Create and activate virtual environment
python -m venv djnet-env
source djnet-env/bin/activate  # Linux/Mac
# djnet-env\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate dataset
python generate_local_dataset.py

# 4. Monitor progress (optional, in new terminal)
# First activate environment in new terminal:
source djnet-env/bin/activate
python monitor_local_progress.py
```

## Why Use Virtual Environment?

✅ **Isolates dependencies** - No conflicts with other projects  
✅ **Reproducible setup** - Same versions across systems  
✅ **Easy cleanup** - Delete folder to remove everything  
✅ **System protection** - Doesn't modify system Python  
✅ **Project portability** - Easy to share exact setup  

## Important Notes

### Always Activate First
Before running any DJNet scripts, make sure your environment is activated:
```bash
# You should see (djnet-env) in your prompt
(djnet-env) $ python generate_local_dataset.py
```

### Deactivating Environment
When you're done:
```bash
deactivate
```

### Reactivating Later
To work on the project again:
```bash
cd /path/to/DJNet-Dataset
source djnet-env/bin/activate  # Linux/Mac
# djnet-env\Scripts\activate   # Windows
```

### Requirements File
The `requirements.txt` includes all necessary dependencies:
- librosa (audio analysis)
- pydub (audio processing)  
- numpy (numerical computing)
- pandas (data handling)
- tqdm (progress bars)
- requests (downloading)
- matplotlib (plotting)
- scikit-learn (machine learning utilities)
- pyyaml (configuration files)

## Troubleshooting

### "python -m venv not found"
```bash
# Install venv (Ubuntu/Debian)
sudo apt install python3-venv

# Or use pip
pip install virtualenv
virtualenv djnet-env
```

### Permission Issues
```bash
# Use --user flag if needed
pip install --user -r requirements.txt
```

### Environment Not Activating
Make sure you're in the right directory:
```bash
cd /path/to/DJNet-Dataset
ls djnet-env/  # Should show bin/ lib/ etc.
source djnet-env/bin/activate
```

### Old Environment
If you need to start fresh:
```bash
# Remove old environment
rm -rf djnet-env

# Create new one
python -m venv djnet-env
source djnet-env/bin/activate
pip install -r requirements.txt
```

## Alternative: Docker (Advanced)

For even more isolation, you could use Docker:

```dockerfile
# Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "generate_local_dataset.py"]
```

But for most users, a simple virtual environment is perfect!

## Next Steps

Once your virtual environment is set up:

1. **Test the setup:**
   ```bash
   python -c "import librosa; print('Setup successful!')"
   ```

2. **Start generation:**
   ```bash
   python generate_local_dataset.py
   ```

3. **Monitor progress:**
   ```bash
   # In another terminal (activate environment first!)
   python monitor_local_progress.py
   ```

Happy dataset generation! 🚀
