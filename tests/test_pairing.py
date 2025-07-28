"""
Tests for TrackPairer class
"""

import unittest
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.pairing import TrackPairer


class TestTrackPairer(unittest.TestCase):
    """Test cases for TrackPairer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pairer = TrackPairer(tempo_threshold=10.0, key_threshold=1)
        
        # Sample track data for testing
        self.test_tracks = [
            {"path": "track1.mp3", "tempo": 120.0, "key": 0},
            {"path": "track2.mp3", "tempo": 125.0, "key": 1},
            {"path": "track3.mp3", "tempo": 140.0, "key": 0},
            {"path": "track4.mp3", "tempo": 122.0, "key": 11},
            {"path": "track5.mp3", "tempo": None, "key": 0},  # Invalid tempo
        ]
    
    def test_find_compatible_pairs_tempo_threshold(self):
        """Test tempo compatibility filtering."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        # Check that tempo differences respect the threshold
        for track_a, track_b in pairs:
            if track_a['tempo'] is not None and track_b['tempo'] is not None:
                tempo_diff = abs(track_a['tempo'] - track_b['tempo'])
                self.assertLessEqual(tempo_diff, self.pairer.tempo_threshold)
    
    def test_find_compatible_pairs_key_threshold(self):
        """Test key compatibility filtering."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        # Check that key differences respect the threshold
        for track_a, track_b in pairs:
            key_diff = abs(track_a['key'] - track_b['key'])
            key_diff_wrapped = min(key_diff, 12 - key_diff)
            self.assertLessEqual(key_diff_wrapped, self.pairer.key_threshold)
    
    def test_find_compatible_pairs_no_self_pairing(self):
        """Test that tracks are not paired with themselves."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        # Check no self-pairing
        for track_a, track_b in pairs:
            self.assertNotEqual(track_a['path'], track_b['path'])
    
    def test_find_compatible_pairs_excludes_none_tempo(self):
        """Test that tracks with None tempo are excluded."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        # Check that no pairs contain tracks with None tempo
        for track_a, track_b in pairs:
            self.assertIsNotNone(track_a['tempo'])
            self.assertIsNotNone(track_b['tempo'])
    
    def test_filter_by_tempo_range(self):
        """Test tempo range filtering."""
        filtered = self.pairer.filter_by_tempo_range(
            self.test_tracks, min_tempo=115.0, max_tempo=130.0
        )
        
        # Check all returned tracks are within range
        for track in filtered:
            self.assertGreaterEqual(track['tempo'], 115.0)
            self.assertLessEqual(track['tempo'], 130.0)
    
    def test_group_by_key(self):
        """Test grouping tracks by key."""
        key_groups = self.pairer.group_by_key(self.test_tracks)
        
        # Check that tracks are properly grouped
        self.assertIn(0, key_groups)
        self.assertIn(1, key_groups)
        self.assertIn(11, key_groups)
        
        # Check group contents
        self.assertEqual(len(key_groups[0]), 3)  # tracks 1, 3, and 5
        self.assertEqual(len(key_groups[1]), 1)  # track 2
        self.assertEqual(len(key_groups[11]), 1)  # track 4
    
    def test_group_by_tempo(self):
        """Test grouping tracks by tempo."""
        tempo_groups = self.pairer.group_by_tempo(self.test_tracks, tempo_bins=5)
        
        # Check that we get tempo groups
        self.assertGreater(len(tempo_groups), 0)
        
        # Check that tracks with None tempo are excluded
        all_grouped_tracks = []
        for tracks in tempo_groups.values():
            all_grouped_tracks.extend(tracks)
        
        for track in all_grouped_tracks:
            self.assertIsNotNone(track['tempo'])
    
    def test_shuffle_pairs(self):
        """Test pair shuffling."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        if len(pairs) > 1:  # Only test if we have multiple pairs
            shuffled1 = self.pairer.shuffle_pairs(pairs, seed=42)
            shuffled2 = self.pairer.shuffle_pairs(pairs, seed=42)
            shuffled3 = self.pairer.shuffle_pairs(pairs, seed=123)
            
            # Same seed should produce same result
            self.assertEqual(shuffled1, shuffled2)
            
            # Different seed should produce different result (with high probability)
            if len(pairs) > 2:
                self.assertNotEqual(shuffled1, shuffled3)
    
    def test_get_pairing_stats(self):
        """Test pairing statistics calculation."""
        pairs = self.pairer.find_compatible_pairs(self.test_tracks)
        
        if pairs:  # Only test if we have pairs
            stats = self.pairer.get_pairing_stats(pairs)
            
            # Check required stats are present
            required_keys = [
                'total_pairs', 'avg_tempo_diff', 'max_tempo_diff', 
                'min_tempo_diff', 'avg_key_diff', 'max_key_diff', 'min_key_diff'
            ]
            for key in required_keys:
                self.assertIn(key, stats)
            
            # Check stats make sense
            self.assertEqual(stats['total_pairs'], len(pairs))
            self.assertGreaterEqual(stats['max_tempo_diff'], stats['min_tempo_diff'])
            self.assertGreaterEqual(stats['max_key_diff'], stats['min_key_diff'])
        else:
            # If no pairs, should return minimal stats
            stats = self.pairer.get_pairing_stats(pairs)
            self.assertEqual(stats['total_pairs'], 0)
    
    def test_empty_input(self):
        """Test behavior with empty input."""
        empty_pairs = self.pairer.find_compatible_pairs([])
        self.assertEqual(len(empty_pairs), 0)
        
        stats = self.pairer.get_pairing_stats(empty_pairs)
        self.assertEqual(stats['total_pairs'], 0)


if __name__ == '__main__':
    unittest.main()
