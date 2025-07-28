"""
Dataset Generator Module

This module orchestrates the complete dataset generation process,
combining audio analysis, track pairing, and transition generation.
"""

import os
import json
import random
import pandas as pd
import librosa
import numpy as np
from pydub import AudioSegment
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional

from .audio_analysis import AudioAnalyzer
from .pairing import TrackPairer
from .transitions import TransitionGenerator


class DatasetGenerator:
    """Main class for generating DJ transition datasets."""
    
    def __init__(self, config: Dict):
        """
        Initialize the DatasetGenerator.
        
        Args:
            config: Configuration dictionary with all parameters
        """
        self.config = config
        self.analyzer = AudioAnalyzer(
            target_sr=config['audio']['target_sample_rate']
        )
        self.pairer = TrackPairer(
            tempo_threshold=config['audio']['tempo_threshold'],
            key_threshold=config['audio']['key_compatibility_threshold']
        )
        self.transition_gen = TransitionGenerator(
            target_sr=config['audio']['target_sample_rate']
        )
    
    def generate_transition(self, pair: Tuple[Dict, Dict], output_dir: str,
                          transition_bars: int = 8, transition_type: str = 'linear_fade') -> Optional[str]:
        """
        Generate a transition between two tracks using a specified technique.
        
        Args:
            pair: Tuple of two track analysis dictionaries
            output_dir: Directory to save the generated files
            transition_bars: Number of bars for the transition
            transition_type: Type of transition to generate
            
        Returns:
            Path to output directory if successful, None otherwise
        """
        track_a_data, track_b_data = pair
        
        try:
            # Calculate target tempo and duration
            if track_a_data['tempo'] is None or track_b_data['tempo'] is None:
                return None
            
            target_tempo = (track_a_data['tempo'] + track_b_data['tempo']) / 2
            if target_tempo == 0:
                return None
            
            beats_per_bar = self.config['transitions']['beats_per_bar']
            transition_beats = transition_bars * beats_per_bar
            transition_duration_sec = transition_beats / (target_tempo / 60.0)
            
            # Load and time-stretch audio
            y_a, _ = librosa.load(track_a_data['path'], sr=self.analyzer.target_sr, mono=True)
            y_b, _ = librosa.load(track_b_data['path'], sr=self.analyzer.target_sr, mono=True)
            
            rate_a = target_tempo / track_a_data['tempo']
            rate_b = target_tempo / track_b_data['tempo']
            
            y_a_warped = librosa.effects.time_stretch(y_a, rate=rate_a)
            y_b_warped = librosa.effects.time_stretch(y_b, rate=rate_b)
            
            # Find slice points
            downbeats_a = np.array(track_a_data['downbeat_times']) * rate_a
            end_time_a_warped = len(y_a_warped) / self.analyzer.target_sr
            
            valid_starts_a = downbeats_a[downbeats_a < end_time_a_warped - transition_duration_sec]
            if len(valid_starts_a) < self.config['dataset']['minimum_valid_starts']:
                return None
            
            start_a_sec = np.random.choice(valid_starts_a[-5:])
            end_a_sec = start_a_sec + transition_duration_sec
            
            downbeats_b = np.array(track_b_data['downbeat_times']) * rate_b
            if len(downbeats_b) == 0:
                return None
            
            start_b_sec = downbeats_b[0]  # Start from the first downbeat
            end_b_sec = start_b_sec + transition_duration_sec
            
            # Slice the audio
            slice_a_float = y_a_warped[int(start_a_sec * self.analyzer.target_sr):
                                     int(end_a_sec * self.analyzer.target_sr)]
            slice_b_float = y_b_warped[int(start_b_sec * self.analyzer.target_sr):
                                     int(end_b_sec * self.analyzer.target_sr)]
            
            if len(slice_a_float) == 0 or len(slice_b_float) == 0:
                return None
            
            # Ensure equal length
            min_len = min(len(slice_a_float), len(slice_b_float))
            slice_a_float = slice_a_float[:min_len]
            slice_b_float = slice_b_float[:min_len]
            
            # Convert to 16-bit integer format
            slice_a_int = self.transition_gen.float_to_int16(slice_a_float)
            slice_b_int = self.transition_gen.float_to_int16(slice_b_float)
            
            # Create AudioSegment objects
            seg_a = AudioSegment(
                slice_a_int.tobytes(), 
                frame_rate=self.analyzer.target_sr, 
                sample_width=2, 
                channels=1
            )
            seg_b = AudioSegment(
                slice_b_int.tobytes(), 
                frame_rate=self.analyzer.target_sr, 
                sample_width=2, 
                channels=1
            )
            
            # Generate transition based on type
            transition_kwargs = self._get_transition_kwargs(transition_type, target_tempo)
            target_transition = self.transition_gen.create_transition(
                seg_a, seg_b, transition_type, **transition_kwargs
            )
            
            # Save files
            os.makedirs(output_dir, exist_ok=True)
            seg_a.export(os.path.join(output_dir, "source_a.wav"), format="wav")
            seg_b.export(os.path.join(output_dir, "source_b.wav"), format="wav")
            target_transition.export(os.path.join(output_dir, "target.wav"), format="wav")
            
            # Generate conditioning info
            conditioning = {
                "source_a_path": track_a_data['path'],
                "source_b_path": track_b_data['path'],
                "target_tempo": target_tempo,
                "transition_duration_sec": transition_duration_sec,
                "transition_type": transition_type,
                "transition_bars": transition_bars
            }
            
            with open(os.path.join(output_dir, "conditioning.json"), 'w') as f:
                json.dump(conditioning, f, indent=2)
            
            return output_dir
            
        except Exception as e:
            # Skip pairs that cause errors
            return None
    
    def _get_transition_kwargs(self, transition_type: str, target_tempo: float) -> Dict:
        """
        Get keyword arguments for specific transition types.
        
        Args:
            transition_type: Type of transition
            target_tempo: Target tempo for the transition
            
        Returns:
            Dictionary of keyword arguments
        """
        kwargs = {}
        
        if transition_type == 'echo_fade':
            beat_dur_ms = 60000 / target_tempo
            kwargs.update({
                'beat_duration_ms': int(beat_dur_ms),
                'num_echos': self.config['echo_fade']['num_echos'],
                'decay_db': self.config['echo_fade']['decay_db']
            })
        elif transition_type == 'filter_sweep':
            kwargs.update({
                'start_freq': self.config['filter_sweep']['start_freq'],
                'end_freq': self.config['filter_sweep']['end_freq'],
                'chunk_size_ms': self.config['filter_sweep']['chunk_size_ms']
            })
        elif transition_type == 'bass_swap_eq':
            kwargs.update({
                'crossover_freq': self.config['eq']['crossover_freq']
            })
        elif transition_type == 'exp_fade':
            kwargs.update({
                'power_out_range': self.config['exp_fade']['power_out_range'],
                'power_in_range': self.config['exp_fade']['power_in_range']
            })
        
        return kwargs
    
    def generate_dataset(self, compatible_pairs: List[Tuple[Dict, Dict]]) -> List[Dict]:
        """
        Generate the complete dataset from compatible pairs.
        
        Args:
            compatible_pairs: List of compatible track pairs
            
        Returns:
            List of metadata dictionaries for generated transitions
        """
        # Shuffle pairs for diversity
        if self.config['dataset']['shuffle_pairs']:
            random.shuffle(compatible_pairs)
        
        # Setup transition types and weights
        transition_types = [t['name'] for t in self.config['transitions']['types']]
        transition_weights = [t['weight'] for t in self.config['transitions']['types']]
        
        # Generate transitions
        metadata = []
        generated_count = 0
        pair_iterator = iter(compatible_pairs)
        
        num_transitions = self.config['dataset']['num_transitions']
        dataset_root = self.config['data']['output_dir']
        os.makedirs(dataset_root, exist_ok=True)
        
        with tqdm(total=num_transitions, desc="Generating Transitions") as pbar:
            while generated_count < num_transitions:
                try:
                    pair = next(pair_iterator)
                except StopIteration:
                    print("Ran out of compatible pairs.")
                    break
                
                # Choose transition type randomly based on weights
                chosen_type = random.choices(transition_types, weights=transition_weights, k=1)[0]
                
                transition_id = f"transition_{generated_count:05d}"
                output_dir = os.path.join(dataset_root, transition_id)
                
                result_path = self.generate_transition(
                    pair, output_dir, 
                    transition_bars=self.config['transitions']['transition_bars'],
                    transition_type=chosen_type
                )
                
                if result_path:
                    metadata.append({
                        "id": transition_id,
                        "path": result_path,
                        "transition_type": chosen_type
                    })
                    generated_count += 1
                    pbar.update(1)
        
        # Save master metadata file
        metadata_df = pd.DataFrame(metadata)
        metadata_path = os.path.join(dataset_root, "metadata.csv")
        metadata_df.to_csv(metadata_path, index=False)
        
        print(f"Dataset generation complete! Generated {generated_count} transitions.")
        print(f"Metadata saved to: {metadata_path}")
        
        return metadata
    
    def run_full_pipeline(self) -> List[Dict]:
        """
        Run the complete dataset generation pipeline.
        
        Returns:
            List of metadata dictionaries for generated transitions
        """
        print("Starting DJNet dataset generation pipeline...")
        
        # Step 1: Analyze tracks
        print("Step 1: Analyzing audio tracks...")
        analysis_files = self.analyzer.analyze_directory(
            self.config['data']['music_dir'],
            self.config['data']['analysis_dir']
        )
        
        # Step 2: Load analysis data
        print("Step 2: Loading analysis data...")
        tracks_data = self.analyzer.load_analysis_data(analysis_files)
        
        # Step 3: Find compatible pairs
        print("Step 3: Finding compatible track pairs...")
        compatible_pairs = self.pairer.find_compatible_pairs(tracks_data)
        print(f"Found {len(compatible_pairs)} compatible pairs.")
        
        # Step 4: Generate dataset
        print("Step 4: Generating transition dataset...")
        metadata = self.generate_dataset(compatible_pairs)
        
        print("Pipeline complete!")
        return metadata
