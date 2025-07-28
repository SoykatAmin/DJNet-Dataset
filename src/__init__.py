"""
DJNet Dataset Generator Package

This package provides tools for generating datasets of DJ transitions
for training neural networks to create smooth audio transitions between songs.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .audio_analysis import AudioAnalyzer
from .pairing import TrackPairer
from .transitions import TransitionGenerator
from .dataset_generator import DatasetGenerator

__all__ = [
    "AudioAnalyzer",
    "TrackPairer", 
    "TransitionGenerator",
    "DatasetGenerator"
]
