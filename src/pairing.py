"""
Track Pairing Module

This module provides functionality to find compatible pairs of tracks
based on tempo and key compatibility for creating smooth transitions.
"""

from typing import List, Dict, Tuple
import random


class TrackPairer:
    """Finds compatible pairs of tracks for DJ transitions."""
    
    def __init__(self, tempo_threshold: float = 10.0, key_threshold: int = 1):
        """
        Initialize the TrackPairer.
        
        Args:
            tempo_threshold: Maximum BPM difference for compatibility
            key_threshold: Maximum key difference for compatibility
        """
        self.tempo_threshold = tempo_threshold
        self.key_threshold = key_threshold
    
    def find_compatible_pairs(self, tracks_data: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """
        Find pairs of tracks with compatible tempo and key.
        
        Args:
            tracks_data: List of track analysis data dictionaries
            
        Returns:
            List of compatible track pairs (tuples)
        """
        pairs = []
        
        for i in range(len(tracks_data)):
            for j in range(len(tracks_data)):
                if i == j:  # Don't pair a song with itself
                    continue
                
                track_a = tracks_data[i]
                track_b = tracks_data[j]
                
                # Skip if tempo data is missing
                if track_a['tempo'] is None or track_b['tempo'] is None:
                    continue
                
                # Rule 1: Tempo compatibility
                tempo_diff = abs(track_a['tempo'] - track_b['tempo'])
                if tempo_diff > self.tempo_threshold:
                    continue
                
                # Rule 2: Key compatibility
                key_diff = abs(track_a['key'] - track_b['key'])
                # Keys are 0-11. Compatible if diff is 0, 1, or 11 (wrap-around)
                if key_diff > self.key_threshold and key_diff < (12 - self.key_threshold):
                    continue
                
                pairs.append((track_a, track_b))
        
        return pairs
    
    def filter_by_tempo_range(self, tracks_data: List[Dict], 
                             min_tempo: float = 60.0, 
                             max_tempo: float = 200.0) -> List[Dict]:
        """
        Filter tracks by tempo range.
        
        Args:
            tracks_data: List of track analysis data
            min_tempo: Minimum acceptable tempo
            max_tempo: Maximum acceptable tempo
            
        Returns:
            Filtered list of tracks within tempo range
        """
        filtered_tracks = []
        for track in tracks_data:
            if (track['tempo'] is not None and 
                min_tempo <= track['tempo'] <= max_tempo):
                filtered_tracks.append(track)
        
        return filtered_tracks
    
    def group_by_key(self, tracks_data: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Group tracks by their estimated key.
        
        Args:
            tracks_data: List of track analysis data
            
        Returns:
            Dictionary mapping keys to lists of tracks
        """
        key_groups = {}
        for track in tracks_data:
            key = track['key']
            if key not in key_groups:
                key_groups[key] = []
            key_groups[key].append(track)
        
        return key_groups
    
    def group_by_tempo(self, tracks_data: List[Dict], 
                      tempo_bins: int = 10) -> Dict[int, List[Dict]]:
        """
        Group tracks by tempo ranges.
        
        Args:
            tracks_data: List of track analysis data
            tempo_bins: Number of tempo bins to create
            
        Returns:
            Dictionary mapping tempo bin indices to lists of tracks
        """
        # Find tempo range
        valid_tempos = [t['tempo'] for t in tracks_data if t['tempo'] is not None]
        if not valid_tempos:
            return {}
        
        min_tempo = min(valid_tempos)
        max_tempo = max(valid_tempos)
        bin_size = (max_tempo - min_tempo) / tempo_bins
        
        tempo_groups = {}
        for track in tracks_data:
            if track['tempo'] is not None:
                bin_idx = int((track['tempo'] - min_tempo) / bin_size)
                bin_idx = min(bin_idx, tempo_bins - 1)  # Handle edge case
                
                if bin_idx not in tempo_groups:
                    tempo_groups[bin_idx] = []
                tempo_groups[bin_idx].append(track)
        
        return tempo_groups
    
    def shuffle_pairs(self, pairs: List[Tuple[Dict, Dict]], 
                     seed: int = None) -> List[Tuple[Dict, Dict]]:
        """
        Shuffle the list of pairs for diversity.
        
        Args:
            pairs: List of track pairs
            seed: Random seed for reproducibility
            
        Returns:
            Shuffled list of pairs
        """
        if seed is not None:
            random.seed(seed)
        
        shuffled_pairs = pairs.copy()
        random.shuffle(shuffled_pairs)
        return shuffled_pairs
    
    def get_pairing_stats(self, pairs: List[Tuple[Dict, Dict]]) -> Dict:
        """
        Get statistics about the track pairings.
        
        Args:
            pairs: List of track pairs
            
        Returns:
            Dictionary containing pairing statistics
        """
        if not pairs:
            return {"total_pairs": 0}
        
        tempo_diffs = []
        key_diffs = []
        
        for track_a, track_b in pairs:
            tempo_diffs.append(abs(track_a['tempo'] - track_b['tempo']))
            key_diff = abs(track_a['key'] - track_b['key'])
            # Handle wrap-around for keys
            key_diff = min(key_diff, 12 - key_diff)
            key_diffs.append(key_diff)
        
        stats = {
            "total_pairs": len(pairs),
            "avg_tempo_diff": sum(tempo_diffs) / len(tempo_diffs),
            "max_tempo_diff": max(tempo_diffs),
            "min_tempo_diff": min(tempo_diffs),
            "avg_key_diff": sum(key_diffs) / len(key_diffs),
            "max_key_diff": max(key_diffs),
            "min_key_diff": min(key_diffs)
        }
        
        return stats
