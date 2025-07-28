"""
Tests for AudioAnalyzer class
"""

import unittest
import tempfile
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.audio_analysis import AudioAnalyzer


class TestAudioAnalyzer(unittest.TestCase):
    """Test cases for AudioAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = AudioAnalyzer(target_sr=22050)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.audio_analysis.librosa.load')
    @patch('src.audio_analysis.librosa.beat.beat_track')
    @patch('src.audio_analysis.librosa.frames_to_time')
    @patch('src.audio_analysis.librosa.feature.chroma_stft')
    def test_analyze_track_success(self, mock_chroma, mock_frames_to_time, 
                                  mock_beat_track, mock_load):
        """Test successful track analysis."""
        # Mock librosa functions
        mock_load.return_value = (np.random.randn(44100), 44100)
        mock_beat_track.return_value = (120.0, np.array([100, 200, 300]))
        mock_frames_to_time.return_value = np.array([1.0, 2.0, 3.0])
        mock_chroma.return_value = np.random.randn(12, 100)
        
        # Test analysis
        result = self.analyzer.analyze_track("test_audio.mp3")
        
        # Assert results
        self.assertIsNotNone(result)
        self.assertEqual(result['path'], "test_audio.mp3")
        self.assertEqual(result['tempo'], 120.0)
        self.assertIsInstance(result['beat_times'], list)
        self.assertIsInstance(result['downbeat_times'], list)
        self.assertIsInstance(result['key'], int)
    
    @patch('src.audio_analysis.librosa.load')
    def test_analyze_track_failure(self, mock_load):
        """Test track analysis failure handling."""
        # Mock librosa to raise an exception
        mock_load.side_effect = Exception("File not found")
        
        # Test analysis
        result = self.analyzer.analyze_track("nonexistent.mp3")
        
        # Assert failure
        self.assertIsNone(result)
    
    def test_get_beat_duration_ms(self):
        """Test beat duration calculation."""
        # Test normal tempo
        duration = AudioAnalyzer.get_beat_duration_ms(120.0)
        self.assertEqual(duration, 500.0)  # 60000 / 120
        
        # Test zero tempo (edge case)
        duration = AudioAnalyzer.get_beat_duration_ms(0.0)
        self.assertEqual(duration, 500.0)  # Default value
    
    @patch('src.audio_analysis.AudioAnalyzer.analyze_track')
    def test_analyze_directory(self, mock_analyze):
        """Test directory analysis."""
        # Create test audio files
        test_files = ["track1.mp3", "track2.wav", "track3.txt"]
        for filename in test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write("dummy content")
        
        # Mock analyze_track to return dummy data
        mock_analyze.return_value = {
            "path": "dummy_path",
            "tempo": 120.0,
            "beat_times": [1.0, 2.0],
            "downbeat_times": [1.0],
            "key": 0
        }
        
        # Test directory analysis
        analysis_dir = os.path.join(self.temp_dir, "analysis")
        result_files = self.analyzer.analyze_directory(self.temp_dir, analysis_dir)
        
        # Assert results
        self.assertEqual(len(result_files), 2)  # Only .mp3 and .wav files
        self.assertTrue(os.path.exists(analysis_dir))
    
    def test_load_analysis_data(self):
        """Test loading analysis data from JSON files."""
        # Create test JSON files
        test_data = [
            {"path": "track1.mp3", "tempo": 120.0, "key": 0},
            {"path": "track2.mp3", "tempo": 130.0, "key": 1}
        ]
        
        json_files = []
        for i, data in enumerate(test_data):
            json_path = os.path.join(self.temp_dir, f"analysis_{i}.json")
            with open(json_path, 'w') as f:
                json.dump(data, f)
            json_files.append(json_path)
        
        # Test loading
        loaded_data = self.analyzer.load_analysis_data(json_files)
        
        # Assert results
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]['tempo'], 120.0)
        self.assertEqual(loaded_data[1]['tempo'], 130.0)


if __name__ == '__main__':
    unittest.main()
