"""
Tests for TransitionGenerator class
"""

import unittest
import os
import sys
import numpy as np
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.transitions import TransitionGenerator


class TestTransitionGenerator(unittest.TestCase):
    """Test cases for TransitionGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = TransitionGenerator(target_sr=22050)
    
    @patch('src.transitions.AudioSegment')
    def test_apply_custom_fade_in(self, mock_audio_segment):
        """Test custom fade in application."""
        # Mock audio segment
        mock_segment = MagicMock()
        mock_segment.get_array_of_samples.return_value = np.random.randint(-32768, 32767, 1000)
        mock_segment.channels = 1
        mock_segment.__len__.return_value = 1000
        mock_segment._spawn.return_value = mock_segment
        
        # Test fade in
        result = self.generator.apply_custom_fade(mock_segment, curve_type='in', power=2.0)
        
        # Assert methods were called
        mock_segment.get_array_of_samples.assert_called_once()
        mock_segment._spawn.assert_called_once()
    
    @patch('src.transitions.AudioSegment')
    def test_apply_custom_fade_out(self, mock_audio_segment):
        """Test custom fade out application."""
        # Mock audio segment
        mock_segment = MagicMock()
        mock_segment.get_array_of_samples.return_value = np.random.randint(-32768, 32767, 1000)
        mock_segment.channels = 1
        mock_segment.__len__.return_value = 1000
        mock_segment._spawn.return_value = mock_segment
        
        # Test fade out
        result = self.generator.apply_custom_fade(mock_segment, curve_type='out', power=2.0)
        
        # Assert methods were called
        mock_segment.get_array_of_samples.assert_called_once()
        mock_segment._spawn.assert_called_once()
    
    @patch('src.transitions.AudioSegment')
    def test_linear_fade_transition(self, mock_audio_segment):
        """Test linear fade transition."""
        # Mock audio segments
        mock_seg_a = MagicMock()
        mock_seg_b = MagicMock()
        mock_seg_a.__len__.return_value = 1000
        mock_seg_b.__len__.return_value = 1000
        mock_seg_a.fade_out.return_value = mock_seg_a
        mock_seg_b.fade_in.return_value = mock_seg_b
        mock_seg_a.overlay.return_value = mock_seg_a
        
        # Test transition
        result = self.generator.linear_fade_transition(mock_seg_a, mock_seg_b)
        
        # Assert methods were called
        mock_seg_a.fade_out.assert_called_once_with(1000)
        mock_seg_b.fade_in.assert_called_once_with(1000)
        mock_seg_a.overlay.assert_called_once_with(mock_seg_b)
    
    @patch('src.transitions.AudioSegment')
    def test_hard_cut_transition(self, mock_audio_segment):
        """Test hard cut transition."""
        # Mock audio segments
        mock_seg_a = MagicMock()
        mock_seg_b = MagicMock()
        mock_seg_a.__len__.return_value = 1000
        mock_seg_b.__len__.return_value = 1000
        mock_seg_a.__getitem__.return_value = mock_seg_a
        mock_seg_b.__getitem__.return_value = mock_seg_b
        mock_seg_a.__add__.return_value = mock_seg_a
        
        # Test transition
        result = self.generator.hard_cut_transition(mock_seg_a, mock_seg_b)
        
        # Assert slicing and concatenation
        mock_seg_a.__getitem__.assert_called_once_with(slice(None, 500))
        mock_seg_b.__getitem__.assert_called_once_with(slice(500, None))
    
    def test_float_to_int16(self):
        """Test float to int16 conversion."""
        # Test normal range
        float_array = np.array([0.0, 0.5, -0.5, 1.0, -1.0])
        int16_array = TransitionGenerator.float_to_int16(float_array)
        
        expected = np.array([0, 16383, -16383, 32767, -32767], dtype=np.int16)
        np.testing.assert_array_equal(int16_array, expected)
    
    @patch('src.transitions.AudioSegment')
    def test_create_transition_dispatch(self, mock_audio_segment):
        """Test transition type dispatching."""
        # Mock audio segments
        mock_seg_a = MagicMock()
        mock_seg_b = MagicMock()
        mock_seg_a.__len__.return_value = 1000
        mock_seg_b.__len__.return_value = 1000
        mock_seg_a.fade_out.return_value = mock_seg_a
        mock_seg_b.fade_in.return_value = mock_seg_b
        mock_seg_a.overlay.return_value = mock_seg_a
        
        # Test different transition types
        transition_types = [
            'linear_fade',
            'exp_fade', 
            'bass_swap_eq',
            'filter_sweep',
            'hard_cut',
            'echo_fade',
            'unknown_type'  # Should default to linear fade
        ]
        
        for transition_type in transition_types:
            with self.subTest(transition_type=transition_type):
                result = self.generator.create_transition(
                    mock_seg_a, mock_seg_b, transition_type
                )
                self.assertIsNotNone(result)
    
    @patch('src.transitions.AudioSegment')
    def test_eq_bass_swap_transition(self, mock_audio_segment):
        """Test EQ bass swap transition."""
        # Mock audio segments with required methods
        mock_seg_a = MagicMock()
        mock_seg_b = MagicMock()
        
        # Mock filter methods
        mock_lows_a = MagicMock()
        mock_highs_a = MagicMock()
        mock_lows_b = MagicMock()
        mock_highs_b = MagicMock()
        
        mock_seg_a.low_pass_filter.return_value = mock_lows_a
        mock_seg_a.high_pass_filter.return_value = mock_highs_a
        mock_seg_b.low_pass_filter.return_value = mock_lows_b
        mock_seg_b.high_pass_filter.return_value = mock_highs_b
        
        # Mock fade methods
        mock_highs_a.fade_out.return_value = mock_highs_a
        mock_highs_b.fade_in.return_value = mock_highs_b
        
        # Mock length and slicing
        mock_seg_a.__len__.return_value = 1000
        mock_lows_a.__getitem__.return_value = mock_lows_a
        mock_lows_b.__getitem__.return_value = mock_lows_b
        
        # Mock append and overlay
        mock_lows_a.append.return_value = mock_lows_a
        mock_highs_a.overlay.return_value = mock_highs_a
        
        # Mock AudioSegment.silent
        with patch('src.transitions.AudioSegment.silent') as mock_silent:
            mock_silent.return_value = MagicMock()
            
            # Test transition
            result = self.generator.eq_bass_swap_transition(mock_seg_a, mock_seg_b)
            
            # Assert filter methods were called
            mock_seg_a.low_pass_filter.assert_called_once_with(250)
            mock_seg_a.high_pass_filter.assert_called_once_with(250)
            mock_seg_b.low_pass_filter.assert_called_once_with(250)
            mock_seg_b.high_pass_filter.assert_called_once_with(250)


if __name__ == '__main__':
    unittest.main()
