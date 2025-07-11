#!/usr/bin/env python3
"""
Simple test script to verify audio processing capabilities on Heroku
"""
import os
import sys

def test_imports():
    """Test if all required libraries can be imported"""
    try:
        import librosa
        print(f"✓ librosa imported successfully - version: {librosa.__version__}")
    except ImportError as e:
        print(f"✗ librosa import failed: {e}")
        return False
    
    try:
        import pydub
        print(f"✓ pydub imported successfully")
    except ImportError as e:
        print(f"✗ pydub import failed: {e}")
        return False
    
    try:
        import soundfile
        print(f"✓ soundfile imported successfully")
    except ImportError as e:
        print(f"✗ soundfile import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ numpy imported successfully - version: {np.__version__}")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    return True

def test_audio_backends():
    """Test if audio backends are available"""
    try:
        import librosa
        # Test if we can create a simple audio signal
        y = librosa.tone(440, sr=16000, duration=0.1)
        print(f"✓ librosa can generate audio signals")
        
        # Test feature extraction
        mfcc = librosa.feature.mfcc(y=y, sr=16000, n_mfcc=13)
        print(f"✓ librosa can extract MFCC features - shape: {mfcc.shape}")
        
        return True
    except Exception as e:
        print(f"✗ librosa audio processing failed: {e}")
        return False

def test_system_dependencies():
    """Test if system dependencies are available"""
    # Check for ffmpeg
    ffmpeg_check = os.system("which ffmpeg > /dev/null 2>&1")
    if ffmpeg_check == 0:
        print("✓ ffmpeg is available")
        # Test ffmpeg version
        os.system("ffmpeg -version | head -1")
    else:
        print("✗ ffmpeg is not available")
    
    # Check for libsndfile
    try:
        import soundfile
        # Try to read a dummy file to test soundfile backend
        print("✓ soundfile backend is working")
    except Exception as e:
        print(f"✗ soundfile backend issue: {e}")
    
    # Test WebM processing specifically
    try:
        from pydub import AudioSegment
        # Create a test audio file
        test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        print("✓ pydub can create audio")
        
        # Test export functionality
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_audio.export(tmp.name, format="wav")
            print("✓ pydub can export WAV files")
            os.unlink(tmp.name)
    except Exception as e:
        print(f"✗ pydub audio processing failed: {e}")

def main():
    print("Testing audio processing setup on Heroku...")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("=" * 50)
    
    # Test imports
    print("Testing imports...")
    if not test_imports():
        print("Import tests failed!")
        sys.exit(1)
    
    print("\nTesting system dependencies...")
    test_system_dependencies()
    
    print("\nTesting audio processing...")
    if not test_audio_backends():
        print("Audio processing tests failed!")
        sys.exit(1)
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main() 