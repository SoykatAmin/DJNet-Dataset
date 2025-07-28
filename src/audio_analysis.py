"""
Audio Analysis Module

This module provides functionality to analyze audio tracks and extract
features like tempo, beats, downbeats, and key information.
"""

import librosa
import numpy as np
import json
import os
from typing import Dict, List, Optional, Tuple


class AudioAnalyzer:
    """Analyzes audio files to extract musical features."""
    
    def __init__(self, target_sr: int = 44100):
        """
        Initialize the AudioAnalyzer.
        
        Args:
            target_sr: Target sample rate for audio processing
        """
        self.target_sr = target_sr
    
    def analyze_track(self, audio_path: str) -> Optional[Dict]:
        """
        Analyze a single audio file to extract BPM, beats, and key.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary containing analysis results or None if analysis fails
        """
        try:
            # Load audio with original sample rate
            y, sr = librosa.load(audio_path, sr=None)
            
            # Estimate tempo and get beat frames
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            
            # Convert beat frames to beat times
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Get downbeats (approximate by taking every 4th beat)
            downbeat_times = beat_times[::4]
            
            # Estimate key (simplified approach)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            key_corr = np.corrcoef(chroma)
            key_est = np.argmax(np.sum(key_corr, axis=1))
            
            return {
                "path": audio_path,
                "tempo": float(tempo),
                "beat_times": beat_times.tolist(),
                "downbeat_times": downbeat_times.tolist(),
                "key": int(key_est)
            }
            
        except Exception as e:
            print(f"Error processing {audio_path}: {e}")
            return None
    
    def analyze_directory(self, music_dir: str, analysis_dir: str) -> List[str]:
        """
        Analyze all audio files in a directory and save results.
        
        Args:
            music_dir: Directory containing audio files
            analysis_dir: Directory to save analysis results
            
        Returns:
            List of paths to analysis files
        """
        from tqdm import tqdm
        
        os.makedirs(analysis_dir, exist_ok=True)
        
        # Find all audio files
        all_files = []
        for root, dirs, files in os.walk(music_dir):
            for file in files:
                if file.endswith(('.mp3', '.wav', '.flac', '.m4a')):
                    all_files.append(os.path.join(root, file))
        
        analysis_files = []
        
        # Analyze each file
        for audio_file in tqdm(all_files, desc="Analyzing Tracks"):
            analysis_data = self.analyze_track(audio_file)
            if analysis_data:
                # Save analysis as JSON file
                base_name = os.path.splitext(os.path.basename(audio_file))[0]
                output_path = os.path.join(analysis_dir, f"{base_name}.json")
                
                with open(output_path, 'w') as f:
                    json.dump(analysis_data, f, indent=2)
                
                analysis_files.append(output_path)
        
        print(f"Analysis complete! Processed {len(analysis_files)} tracks.")
        return analysis_files
    
    def load_analysis_data(self, analysis_files: List[str]) -> List[Dict]:
        """
        Load analysis data from JSON files.
        
        Args:
            analysis_files: List of paths to analysis JSON files
            
        Returns:
            List of analysis data dictionaries
        """
        all_tracks_data = []
        for file_path in analysis_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    all_tracks_data.append(data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        return all_tracks_data
    
    @staticmethod
    def get_beat_duration_ms(tempo: float) -> float:
        """
        Calculate beat duration in milliseconds from BPM.
        
        Args:
            tempo: Tempo in beats per minute
            
        Returns:
            Beat duration in milliseconds
        """
        return 60000.0 / tempo if tempo > 0 else 500.0  # Default to 500ms
