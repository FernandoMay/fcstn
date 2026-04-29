"""
NeuroDigital Adaptive Network (NDAN) Interface
Brain-Computer Interface signal processing and cognitive state estimation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import mne
    from scipy import signal
    from sklearn.decomposition import FastICA
    MNE_AVAILABLE = True
except ImportError:
    MNE_AVAILABLE = False
    logging.warning("MNE not available. BCI features limited.")


class CognitiveState(Enum):
    """Cognitive state categories"""
    FOCUSED = "focused"
    RELAXED = "relaxed"
    ENGAGED = "engaged"
    FATIGUED = "fatigued"
    STRESSED = "stressed"
    NEUTRAL = "neutral"


@dataclass
class BCISignal:
    """Raw BCI signal data"""
    data: np.ndarray  # Shape: (n_channels, n_samples)
    sampling_rate: float
    channel_names: List[str]
    timestamp: float


@dataclass
class CognitiveFeatures:
    """Extracted cognitive features from neural signals"""
    alpha_power: float  # 8-13 Hz
    beta_power: float   # 13-30 Hz
    theta_power: float  # 4-8 Hz
    gamma_power: float  # 30-100 Hz
    attention_index: float  # 0-1
    engagement_level: float  # 0-1
    workload: float  # 0-1
    emotional_valence: float  # -1 to 1
    cognitive_state: CognitiveState


class BCIProcessor:
    """
    Processes raw BCI signals (EEG, fNIRS) into cognitive features.
    """
    
    def __init__(self, sampling_rate: float = 250.0):
        """
        Initialize BCI processor.
        
        Args:
            sampling_rate: Signal sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
        self.filters_initialized = False
        
        if MNE_AVAILABLE:
            self._initialize_filters()
        
        logging.info(f"BCI Processor initialized (sampling rate: {sampling_rate} Hz)")
    
    def _initialize_filters(self):
        """Initialize bandpass filters for different frequency bands"""
        self.filters = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100)
        }
        self.filters_initialized = True
    
    def preprocess(self, raw_signal: BCISignal) -> np.ndarray:
        """
        Preprocess raw BCI signal.
        
        Steps:
        1. Remove baseline drift
        2. Notch filter (50/60 Hz)
        3. Bandpass filter (0.5-100 Hz)
        4. Artifact removal (ICA)
        
        Args:
            raw_signal: Raw BCI signal data
            
        Returns:
            Preprocessed signal
        """
        data = raw_signal.data.copy()
        
        # Remove DC offset
        data = data - np.mean(data, axis=1, keepdims=True)
        
        # Notch filter for powerline noise (60 Hz)
        if self.sampling_rate > 120:
            b_notch, a_notch = signal.iirnotch(60.0, 30.0, self.sampling_rate)
            data = signal.filtfilt(b_notch, a_notch, data, axis=1)
        
        # Bandpass filter (0.5-100 Hz)
        nyquist = self.sampling_rate / 2
        low = 0.5 / nyquist
        high = min(100.0, nyquist - 1) / nyquist
        
        b_bp, a_bp = signal.butter(4, [low, high], btype='band')
        data = signal.filtfilt(b_bp, a_bp, data, axis=1)
        
        # Simple artifact removal (amplitude threshold)
        threshold = 5 * np.std(data)
        artifact_mask = np.abs(data) > threshold
        data[artifact_mask] = np.median(data)

        # Recenter after filtering and artifact suppression so downstream features
        # operate on a baseline-corrected signal.
        data = data - np.mean(data, axis=1, keepdims=True)
        
        return data
    
    def extract_band_power(self, signal_data: np.ndarray, freq_band: Tuple[float, float]) -> float:
        """
        Extract power in specific frequency band using Welch's method.
        
        Args:
            signal_data: Preprocessed signal (n_channels, n_samples)
            freq_band: (low_freq, high_freq) in Hz
            
        Returns:
            Mean band power across channels
        """
        powers = []
        
        for channel_data in signal_data:
            freqs, psd = signal.welch(
                channel_data,
                fs=self.sampling_rate,
                nperseg=min(256, len(channel_data))
            )
            
            # Find frequency band indices
            idx_band = np.logical_and(freqs >= freq_band[0], freqs <= freq_band[1])
            
            # Integrate power in band
            band_power = np.trapezoid(psd[idx_band], freqs[idx_band])
            powers.append(band_power)
        
        return float(np.mean(powers))
    
    def compute_attention_index(self, features: Dict[str, float]) -> float:
        """
        Compute attention index from band powers.
        
        Attention ∝ (beta + gamma) / (theta + alpha)
        
        Args:
            features: Dictionary of band powers
            
        Returns:
            Attention index (0-1)
        """
        numerator = features['beta'] + features['gamma']
        denominator = features['theta'] + features['alpha']
        
        if denominator > 0:
            attention_raw = numerator / denominator
            # Normalize to 0-1 (assumes typical range 0-10)
            attention = np.clip(attention_raw / 10.0, 0, 1)
        else:
            attention = 0.5
        
        return float(attention)
    
    def compute_engagement(self, features: Dict[str, float]) -> float:
        """
        Compute engagement level from band powers.
        
        Engagement ∝ beta / (alpha + theta)
        
        Args:
            features: Dictionary of band powers
            
        Returns:
            Engagement level (0-1)
        """
        numerator = features['beta']
        denominator = features['alpha'] + features['theta']
        
        if denominator > 0:
            engagement_raw = numerator / denominator
            engagement = np.clip(engagement_raw / 5.0, 0, 1)
        else:
            engagement = 0.5
        
        return float(engagement)
    
    def compute_workload(self, features: Dict[str, float]) -> float:
        """
        Compute mental workload from band powers.
        
        Workload ∝ theta / alpha
        
        Args:
            features: Dictionary of band powers
            
        Returns:
            Workload (0-1)
        """
        if features['alpha'] > 0:
            workload_raw = features['theta'] / features['alpha']
            workload = np.clip(workload_raw / 2.0, 0, 1)
        else:
            workload = 0.5
        
        return float(workload)
    
    def classify_cognitive_state(self, features: CognitiveFeatures) -> CognitiveState:
        """
        Classify overall cognitive state from features.
        
        Args:
            features: Cognitive features
            
        Returns:
            Classified cognitive state
        """
        # Simple rule-based classification
        if features.attention_index > 0.7 and features.engagement_level > 0.6:
            return CognitiveState.FOCUSED
        elif features.workload > 0.7:
            return CognitiveState.STRESSED
        elif features.attention_index < 0.3 and features.engagement_level < 0.3:
            return CognitiveState.FATIGUED
        elif features.engagement_level > 0.5:
            return CognitiveState.ENGAGED
        elif features.alpha_power > features.beta_power:
            return CognitiveState.RELAXED
        else:
            return CognitiveState.NEUTRAL
    
    def extract_features(self, raw_signal: BCISignal) -> CognitiveFeatures:
        """
        Extract full cognitive feature set from raw signal.
        
        Args:
            raw_signal: Raw BCI signal
            
        Returns:
            Cognitive features
        """
        # Preprocess
        preprocessed = self.preprocess(raw_signal)
        
        # Extract band powers
        band_powers = {}
        for band_name, freq_range in self.filters.items():
            band_powers[band_name] = self.extract_band_power(preprocessed, freq_range)
        
        # Compute derived metrics
        attention = self.compute_attention_index(band_powers)
        engagement = self.compute_engagement(band_powers)
        workload = self.compute_workload(band_powers)
        
        # Emotional valence (simplified - based on asymmetry in real systems)
        valence = 0.0  # Placeholder
        
        # Create feature object
        features = CognitiveFeatures(
            alpha_power=band_powers['alpha'],
            beta_power=band_powers['beta'],
            theta_power=band_powers['theta'],
            gamma_power=band_powers['gamma'],
            attention_index=attention,
            engagement_level=engagement,
            workload=workload,
            emotional_valence=valence,
            cognitive_state=CognitiveState.NEUTRAL  # Will be set below
        )
        
        # Classify state
        features.cognitive_state = self.classify_cognitive_state(features)
        
        return features


class NDANInterface:
    """
    Main NDAN interface coordinating BCI processing and environment feedback.
    """
    
    def __init__(self, sampling_rate: float = 250.0):
        """
        Initialize NDAN interface.
        
        Args:
            sampling_rate: BCI sampling rate
        """
        self.processor = BCIProcessor(sampling_rate)
        self.cognitive_history: List[CognitiveFeatures] = []
        self.max_history = 100
        
        logging.info("NDAN Interface initialized")
    
    def process_signal(self, raw_signal: BCISignal) -> CognitiveFeatures:
        """
        Process incoming BCI signal.
        
        Args:
            raw_signal: Raw BCI signal
            
        Returns:
            Extracted cognitive features
        """
        features = self.processor.extract_features(raw_signal)
        
        # Store in history
        self.cognitive_history.append(features)
        if len(self.cognitive_history) > self.max_history:
            self.cognitive_history.pop(0)
        
        return features
    
    def get_environment_parameters(self, features: CognitiveFeatures) -> Dict[str, float]:
        """
        Convert cognitive features to environment control parameters.
        
        Args:
            features: Cognitive features
            
        Returns:
            Dictionary of environment parameters
        """
        params = {
            'complexity_level': features.attention_index,
            'curvature_scale': 1.0 + 2.0 * features.engagement_level,
            'color_intensity': features.emotional_valence,
            'geometry_smoothness': 1.0 - features.workload,
            'fractal_zoom': 1.0 + features.attention_index,
            'detail_level': features.engagement_level
        }
        
        return params
    
    def get_cognitive_trend(self, window: int = 10) -> Dict[str, float]:
        """
        Compute trends in cognitive state over recent history.
        
        Args:
            window: Number of recent samples to analyze
            
        Returns:
            Dictionary of trend values (-1 to 1, negative = decreasing)
        """
        if len(self.cognitive_history) < 2:
            return {
                'attention_trend': 0.0,
                'engagement_trend': 0.0,
                'workload_trend': 0.0
            }
        
        recent = self.cognitive_history[-window:]
        
        # Compute linear trends
        attention_vals = [f.attention_index for f in recent]
        engagement_vals = [f.engagement_level for f in recent]
        workload_vals = [f.workload for f in recent]
        
        def compute_trend(values):
            if len(values) < 2:
                return 0.0
            # Simple linear regression slope
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            return np.clip(slope * 10, -1, 1)  # Scale and clip
        
        return {
            'attention_trend': compute_trend(attention_vals),
            'engagement_trend': compute_trend(engagement_vals),
            'workload_trend': compute_trend(workload_vals)
        }


def generate_synthetic_eeg(
    duration: float = 10.0,
    sampling_rate: float = 250.0,
    n_channels: int = 8
) -> BCISignal:
    """
    Generate synthetic EEG signal for testing.
    
    Args:
        duration: Signal duration in seconds
        sampling_rate: Sampling rate in Hz
        n_channels: Number of EEG channels
        
    Returns:
        Synthetic BCI signal
    """
    n_samples = int(duration * sampling_rate)
    t = np.linspace(0, duration, n_samples)
    
    # Generate synthetic EEG with multiple frequency components
    data = np.zeros((n_channels, n_samples))
    
    for ch in range(n_channels):
        # Alpha rhythm (10 Hz)
        data[ch] += 20 * np.sin(2 * np.pi * 10 * t + ch * 0.5)
        
        # Beta activity (20 Hz)
        data[ch] += 10 * np.sin(2 * np.pi * 20 * t + ch * 0.3)
        
        # Theta (6 Hz)
        data[ch] += 5 * np.sin(2 * np.pi * 6 * t + ch * 0.7)
        
        # Noise
        data[ch] += np.random.randn(n_samples) * 2
    
    channel_names = [f"EEG{i+1}" for i in range(n_channels)]
    
    return BCISignal(
        data=data,
        sampling_rate=sampling_rate,
        channel_names=channel_names,
        timestamp=0.0
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Generate synthetic signal
    signal_data = generate_synthetic_eeg(duration=10.0)
    print(f"Generated signal: {signal_data.data.shape}")
    
    # Initialize NDAN
    ndan = NDANInterface()
    
    # Process signal
    features = ndan.process_signal(signal_data)
    
    print(f"\nExtracted Features:")
    print(f"  Alpha Power: {features.alpha_power:.2f}")
    print(f"  Beta Power: {features.beta_power:.2f}")
    print(f"  Attention Index: {features.attention_index:.3f}")
    print(f"  Engagement: {features.engagement_level:.3f}")
    print(f"  Cognitive State: {features.cognitive_state.value}")
    
    # Get environment parameters
    env_params = ndan.get_environment_parameters(features)
    print(f"\nEnvironment Parameters:")
    for key, value in env_params.items():
        print(f"  {key}: {value:.3f}")
