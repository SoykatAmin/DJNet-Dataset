"""
Transitions Module

This module provides various audio transition techniques for creating
smooth DJ-style transitions between tracks.
"""

import librosa
import numpy as np
import random
from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter
from typing import Dict, Tuple, Optional


class TransitionGenerator:
    """Generates various types of audio transitions between tracks."""
    
    def __init__(self, target_sr: int = 44100):
        """
        Initialize the TransitionGenerator.
        
        Args:
            target_sr: Target sample rate for audio processing
        """
        self.target_sr = target_sr
    
    def apply_custom_fade(self, segment: AudioSegment, curve_type: str = 'in', 
                         power: float = 1.0) -> AudioSegment:
        """
        Apply a non-linear (exponential) fade to an audio segment.
        
        Args:
            segment: Audio segment to fade
            curve_type: 'in' for fade in, 'out' for fade out
            power: Power curve exponent
            
        Returns:
            Faded audio segment
        """
        gain_curve = np.linspace(0.0, 1.0, len(segment))
        
        if curve_type == 'in':
            gain_curve = gain_curve ** power
        elif curve_type == 'out':
            gain_curve = 1.0 - (gain_curve ** power)
        
        samples = np.array(segment.get_array_of_samples()).astype(np.float32)
        
        if segment.channels == 2:
            gain_matrix = np.array([gain_curve, gain_curve]).T
            faded_samples = (samples.reshape(-1, 2) * gain_matrix).astype(np.int16)
        else:
            faded_samples = (samples * gain_curve).astype(np.int16)
        
        return segment._spawn(faded_samples.tobytes())
    
    def eq_bass_swap_transition(self, seg_a: AudioSegment, seg_b: AudioSegment, 
                               crossover_freq: int = 250) -> AudioSegment:
        """
        Create a transition by swapping bass frequencies and crossfading mids/highs.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            crossover_freq: Frequency crossover point in Hz
            
        Returns:
            Mixed audio segment with bass swap transition
        """
        # Split into low and high frequency components
        lows_a = seg_a.low_pass_filter(crossover_freq)
        highs_a = seg_a.high_pass_filter(crossover_freq)
        lows_b = seg_b.low_pass_filter(crossover_freq)
        highs_b = seg_b.high_pass_filter(crossover_freq)
        
        fade_duration = len(seg_a)
        halfway_point = fade_duration // 2
        
        # Fade out the highs of Song A
        highs_a_faded = highs_a.fade_out(fade_duration)
        # Fade in the highs of Song B
        highs_b_faded = highs_b.fade_in(fade_duration)
        
        # Bass A plays for the first half, then fades out
        bass_a_swap = lows_a[:halfway_point].append(
            AudioSegment.silent(duration=fade_duration - halfway_point), 
            crossfade=10
        )
        # Silence for the first half, then Bass B fades in
        bass_b_swap = AudioSegment.silent(duration=halfway_point).append(
            lows_b[halfway_point:], crossfade=10
        )
        
        # Combine all layers
        final_mix = (highs_a_faded.overlay(bass_a_swap)
                    .overlay(bass_b_swap)
                    .overlay(highs_b_faded))
        
        return final_mix
    
    def low_pass_sweep_transition(self, seg_a: AudioSegment, seg_b: AudioSegment,
                                 start_freq: int = 20000, end_freq: int = 100,
                                 chunk_size_ms: int = 50) -> AudioSegment:
        """
        Apply a sweeping low-pass filter to fade out track A while fading in track B.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            start_freq: Starting frequency for the sweep
            end_freq: Ending frequency for the sweep
            chunk_size_ms: Size of processing chunks in milliseconds
            
        Returns:
            Mixed audio segment with filter sweep transition
        """
        num_chunks = len(seg_a) // chunk_size_ms
        filtered_a = AudioSegment.empty()
        freq_curve = np.linspace(start_freq, end_freq, num_chunks)
        
        for i in range(num_chunks):
            chunk = seg_a[i * chunk_size_ms:(i + 1) * chunk_size_ms]
            filtered_chunk = chunk.low_pass_filter(int(freq_curve[i]))
            filtered_a += filtered_chunk
        
        return filtered_a.overlay(seg_b.fade_in(len(seg_b)))
    
    def echo_fade_transition(self, seg_a: AudioSegment, seg_b: AudioSegment,
                           beat_duration_ms: int = 500, num_echos: int = 4,
                           decay_db: int = 6) -> AudioSegment:
        """
        Fade out A while overlaying echoes of its last beat onto B's intro.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            beat_duration_ms: Duration of one beat in milliseconds
            num_echos: Number of echo repetitions
            decay_db: Volume decay per echo in dB
            
        Returns:
            Mixed audio segment with echo fade transition
        """
        faded_a = seg_a.fade_out(len(seg_a))
        mix = faded_a.overlay(seg_b.fade_in(len(seg_b)))
        
        last_beat_a = seg_a[-beat_duration_ms:]
        
        for i in range(num_echos):
            echo = last_beat_a - (i * decay_db)
            start_pos = len(seg_a) - beat_duration_ms + (i * beat_duration_ms)
            if start_pos < len(mix):
                mix = mix.overlay(echo, position=start_pos)
        
        return mix
    
    def hard_cut_transition(self, seg_a: AudioSegment, seg_b: AudioSegment) -> AudioSegment:
        """
        Perform a hard cut in the middle of the transition period.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            
        Returns:
            Audio segment with hard cut transition
        """
        halfway_point = len(seg_a) // 2
        return seg_a[:halfway_point] + seg_b[halfway_point:]
    
    def linear_fade_transition(self, seg_a: AudioSegment, seg_b: AudioSegment) -> AudioSegment:
        """
        Create a simple linear crossfade transition.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            
        Returns:
            Mixed audio segment with linear fade transition
        """
        return seg_a.fade_out(len(seg_a)).overlay(seg_b.fade_in(len(seg_b)))
    
    def exponential_fade_transition(self, seg_a: AudioSegment, seg_b: AudioSegment,
                                  power_out_range: Tuple[float, float] = (1.5, 3.0),
                                  power_in_range: Tuple[float, float] = (0.3, 0.8)) -> AudioSegment:
        """
        Create an exponential fade transition with random curve parameters.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            power_out_range: Range for fade out power curve
            power_in_range: Range for fade in power curve
            
        Returns:
            Mixed audio segment with exponential fade transition
        """
        power_out = random.uniform(*power_out_range)
        power_in = random.uniform(*power_in_range)
        
        faded_a = self.apply_custom_fade(seg_a, 'out', power=power_out)
        faded_b = self.apply_custom_fade(seg_b, 'in', power=power_in)
        
        return faded_a.overlay(faded_b)
    
    def create_transition(self, seg_a: AudioSegment, seg_b: AudioSegment,
                         transition_type: str, **kwargs) -> AudioSegment:
        """
        Create a transition using the specified technique.
        
        Args:
            seg_a: First audio segment
            seg_b: Second audio segment
            transition_type: Type of transition to create
            **kwargs: Additional parameters for specific transition types
            
        Returns:
            Mixed audio segment with the specified transition
        """
        if transition_type == 'linear_fade':
            return self.linear_fade_transition(seg_a, seg_b)
        elif transition_type == 'exp_fade':
            return self.exponential_fade_transition(seg_a, seg_b, **kwargs)
        elif transition_type == 'bass_swap_eq':
            return self.eq_bass_swap_transition(seg_a, seg_b, **kwargs)
        elif transition_type == 'filter_sweep':
            return self.low_pass_sweep_transition(seg_a, seg_b, **kwargs)
        elif transition_type == 'hard_cut':
            return self.hard_cut_transition(seg_a, seg_b)
        elif transition_type == 'echo_fade':
            return self.echo_fade_transition(seg_a, seg_b, **kwargs)
        else:
            # Default to linear fade
            return self.linear_fade_transition(seg_a, seg_b)
    
    @staticmethod
    def float_to_int16(arr: np.ndarray) -> np.ndarray:
        """
        Convert float audio array to 16-bit integer format.
        
        Args:
            arr: Float audio array
            
        Returns:
            16-bit integer audio array
        """
        return (arr * 32767).astype(np.int16)
