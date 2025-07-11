from flask import Flask, render_template, request, redirect, jsonify, flash
from pydub import AudioSegment
from sklearn.ensemble import RandomForestClassifier
import os, uuid
import joblib
import numpy as np
import librosa
import tempfile
import shutil
import logging
import sys

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure environment for PulseAudio libraries (Heroku fix)
if 'LD_LIBRARY_PATH' in os.environ:
    os.environ['LD_LIBRARY_PATH'] += ':/usr/lib/x86_64-linux-gnu/pulseaudio'
else:
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib/x86_64-linux-gnu/pulseaudio'

# Also set PULSE_RUNTIME_PATH to avoid PulseAudio runtime issues
os.environ['PULSE_RUNTIME_PATH'] = '/tmp/pulse'

logger.info(f"LD_LIBRARY_PATH set to: {os.environ.get('LD_LIBRARY_PATH')}")
logger.info(f"PULSE_RUNTIME_PATH set to: {os.environ.get('PULSE_RUNTIME_PATH')}")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this')

# Fixed paths for Heroku deployment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Use temporary directory for uploads (Heroku has ephemeral filesystem)
UPLOAD_FOLDER = tempfile.mkdtemp()

# Model path - prioritize Heroku-friendly paths
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "rolex_model.pkl")
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg', 'webm'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the model with better error handling for Heroku
try:
    # Primary path for Heroku
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        logger.info("✓ Model loaded successfully from primary path")
    else:
        # Alternative relative path
        alt_model_path = os.path.join(BASE_DIR, "..", "model", "rolex_model.pkl")
        if os.path.exists(alt_model_path):
            model = joblib.load(alt_model_path)
            logger.info("✓ Model loaded successfully from alternative path")
        else:
            # Try current directory
            current_model_path = os.path.join("model", "rolex_model.pkl")
            if os.path.exists(current_model_path):
                model = joblib.load(current_model_path)
                logger.info("✓ Model loaded successfully from current directory")
            else:
                raise FileNotFoundError("Model file not found in any expected location")
except Exception as e:
    logger.error(f"✗ Error loading model: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('model'):
        logger.error(f"Files in model directory: {os.listdir('model')}")
    else:
        logger.error("Model directory not found")
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_path):
    """Simplified - just return original path since we handle all formats directly"""
    return input_path

def extract_features(filepath):
    """Extract features matching the training format exactly"""
    try:
        logger.info(f"=== EXTRACT FEATURES DEBUG START ===")
        logger.info(f"Processing file: {filepath}")
        
        # Check if file exists and is readable
        if not os.path.exists(filepath):
            logger.error(f"File does not exist: {filepath}")
            return None
            
        file_size = os.path.getsize(filepath)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("File is empty")
            return None

        # ROBUST SOLUTION: Use FFmpeg directly to convert WebM to WAV
        # This handles the WebM codec issue on Heroku more reliably
        temp_wav_path = None
        try:
            # Check if file is WebM format
            if filepath.lower().endswith('.webm'):
                logger.info("WebM file detected, converting to WAV using FFmpeg...")
                
                # Create temporary WAV file path
                temp_wav_path = filepath.replace('.webm', '_temp.wav')
                
                # Use FFmpeg directly to convert WebM to WAV
                # FFmpeg is more reliable than pydub for WebM conversion on Heroku
                import subprocess
                ffmpeg_cmd = [
                    'ffmpeg', '-i', filepath,
                    '-acodec', 'pcm_s16le',  # 16-bit PCM
                    '-ar', '16000',          # 16kHz sample rate
                    '-ac', '1',              # Mono
                    '-y',                    # Overwrite output file
                    temp_wav_path
                ]
                
                logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"FFmpeg conversion successful: {temp_wav_path}")
                    
                    # Verify the WAV file was created and has content
                    if os.path.exists(temp_wav_path) and os.path.getsize(temp_wav_path) > 0:
                        logger.info(f"WAV file created successfully, size: {os.path.getsize(temp_wav_path)} bytes")
                        
                        # Use the converted WAV file for librosa
                        y, sr = librosa.load(temp_wav_path, sr=16000)
                        logger.info(f"SUCCESS: Audio loaded from converted WAV - {len(y)} samples at {sr}Hz")
                    else:
                        raise Exception("FFmpeg conversion failed - no output file created")
                else:
                    logger.error(f"FFmpeg failed with return code {result.returncode}")
                    logger.error(f"FFmpeg stderr: {result.stderr}")
                    raise Exception(f"FFmpeg conversion failed: {result.stderr}")
            else:
                # For non-WebM files, try direct loading with librosa
                logger.info("Non-WebM file, trying direct librosa loading...")
                y, sr = librosa.load(filepath, sr=16000)
                logger.info(f"SUCCESS: Audio loaded directly - {len(y)} samples at {sr}Hz")
                
        except Exception as e:
            logger.error(f"Primary loading method failed: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            
            # Fallback 1: Try pydub conversion if FFmpeg failed
            if filepath.lower().endswith('.webm') and temp_wav_path:
                try:
                    logger.info("FFmpeg failed, trying pydub as fallback...")
                    audio = AudioSegment.from_file(filepath, format="webm")
                    audio.export(temp_wav_path, format="wav")
                    logger.info(f"Pydub conversion successful: {temp_wav_path}")
                    
                    y, sr = librosa.load(temp_wav_path, sr=16000)
                    logger.info(f"SUCCESS: Audio loaded from pydub-converted WAV - {len(y)} samples at {sr}Hz")
                except Exception as e_pydub:
                    logger.error(f"Pydub fallback also failed: {str(e_pydub)}")
                    
                    # Fallback 2: Try direct librosa loading without resampling
                    try:
                        logger.info("Trying final fallback: direct librosa loading without resampling...")
                        y, sr = librosa.load(filepath, sr=None)
                        logger.info(f"Loaded at original rate: {len(y)} samples at {sr}Hz")
                        
                        # Resample to 16kHz if needed
                        if sr != 16000:
                            logger.info(f"Resampling from {sr}Hz to 16000Hz")
                            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                            sr = 16000
                            logger.info(f"Resampled: {len(y)} samples at {sr}Hz")
                    except Exception as e2:
                        logger.error(f"All loading methods failed: {str(e2)}")
                        logger.error(f"Exception type: {type(e2).__name__}")
                        return None
            else:
                # For non-WebM files, try loading without resampling
                try:
                    logger.info("Trying fallback: loading without resampling...")
                    y, sr = librosa.load(filepath, sr=None)
                    logger.info(f"Loaded at original rate: {len(y)} samples at {sr}Hz")
                    
                    # Resample to 16kHz if needed
                    if sr != 16000:
                        logger.info(f"Resampling from {sr}Hz to 16000Hz")
                        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                        sr = 16000
                        logger.info(f"Resampled: {len(y)} samples at {sr}Hz")
                except Exception as e2:
                    logger.error(f"All loading methods failed: {str(e2)}")
                    logger.error(f"Exception type: {type(e2).__name__}")
                    return None
        finally:
            # Clean up temporary WAV file if created
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    logger.info(f"Cleaned up temporary file: {temp_wav_path}")
                except:
                    pass
        
        if len(y) == 0:
            logger.error("Audio file is empty or corrupted")
            return None
            
        logger.info(f"Audio successfully loaded: {len(y)} samples at {sr} Hz")
        
        # Extract features exactly like training script
        try:
            logger.info("Starting feature extraction...")
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            logger.info(f"MFCC extracted: shape {mfcc.shape}")
            zcr = librosa.feature.zero_crossing_rate(y)
            logger.info(f"ZCR extracted: shape {zcr.shape}")
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
            logger.info(f"Spectral centroid extracted: shape {spec_cent.shape}")
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

        # Combine features in same order as training
        features = np.hstack([
            np.mean(mfcc, axis=1),     # mfcc_mean_0 to mfcc_mean_12 (13 features)
            np.std(mfcc, axis=1),      # mfcc_std_0 to mfcc_std_12 (13 features)
            np.mean(zcr),              # zcr_mean (1 feature)
            np.std(zcr),               # zcr_std (1 feature)
            np.mean(spec_cent),        # spec_cent_mean (1 feature)
            np.std(spec_cent)          # spec_cent_std (1 feature)
        ])
        
        logger.info(f"SUCCESS: Extracted features shape: {features.shape} (expected: 30)")
        logger.info(f"=== EXTRACT FEATURES DEBUG END - SUCCESS ===")
        return features
        
    except Exception as e:
        logger.error(f"=== EXTRACT FEATURES DEBUG END - ERROR ===")
        logger.error(f"Error extracting features from {filepath}: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if model is loaded
        if model is None:
            flash("Model not available. Please try again later.", "error")
            logger.error("Model not available")
            return render_template("index.html")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            flash("No file uploaded. Please select an audio file.", "error")
            return render_template("index.html")
        
        file = request.files["file"]
        
        # Check if file is selected
        if file.filename == '':
            flash("No file selected. Please choose an audio file.", "error")
            return render_template("index.html")
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload WAV, MP3, M4A, FLAC, OGG, or WebM files.", "error")
            return render_template("index.html")
        
        try:
            # Save uploaded file
            filename = str(uuid.uuid4()) + "_" + file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            logger.info(f"=== FILE UPLOAD DEBUG ===")
            logger.info(f"Original filename: {file.filename}")
            logger.info(f"File content type: {file.content_type}")
            logger.info(f"Saved as: {filename}")
            logger.info(f"Full path: {filepath}")
            logger.info(f"File uploaded: {filename}, size: {os.path.getsize(filepath)} bytes")
            
            # Extract features
            features = extract_features(filepath)
            
            if features is None:
                flash("Error processing audio file. Please try a different file.", "error")
                logger.error("Feature extraction failed")
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                return render_template("index.html")
            
            # Make prediction
            features_reshaped = features.reshape(1, -1)
            prediction = model.predict(features_reshaped)[0]
            confidence = model.predict_proba(features_reshaped)[0]
            
            # Get result - check training data to confirm label mapping
            # Based on dataset.csv: 'real' and 'fake' are string labels
            # Model likely encodes: 'fake' = 0, 'real' = 1 (alphabetical order)
            result = "Fake" if prediction == 0 else "Real"
            confidence_score = max(confidence) * 100
            
            logger.info(f"=== PREDICTION SUCCESS ===")
            logger.info(f"Prediction: {result}, Confidence: {confidence_score}%")
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return render_template("index.html", 
                                 result=result, 
                                 confidence=confidence_score,
                                 filename=file.filename)
                                 
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(traceback.format_exc())
            flash("Error processing audio file. Please try again.", "error")
            # Clean up uploaded file
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return render_template("index.html")
    
    return render_template("index.html")

# Health check endpoint for Heroku
@app.route("/health")
def health_check():
    """Comprehensive health check endpoint for Heroku"""
    import sys
    
    # Test system dependencies
    ffmpeg_available = os.system("which ffmpeg > /dev/null 2>&1") == 0
    
    # Test audio libraries
    librosa_test = False
    soundfile_test = False
    pydub_test = False
    
    try:
        import librosa
        # Test basic librosa functionality
        test_audio = librosa.tone(440, sr=16000, duration=0.1)
        mfcc_test = librosa.feature.mfcc(y=test_audio, sr=16000, n_mfcc=13)
        librosa_test = True
    except Exception as e:
        logger.error(f"Librosa test failed: {e}")
    
    try:
        import soundfile as sf
        # Test if soundfile can work
        soundfile_test = True
    except Exception as e:
        logger.error(f"Soundfile test failed: {e}")
    
    try:
        from pydub import AudioSegment
        # Test basic pydub functionality
        test_audio = AudioSegment.silent(duration=100)  # 100ms of silence
        pydub_test = True
    except Exception as e:
        logger.error(f"Pydub test failed: {e}")
    
    overall_status = "healthy" if all([model is not None, ffmpeg_available, librosa_test, soundfile_test, pydub_test]) else "degraded"
    
    return jsonify({
        "status": overall_status,
        "model_loaded": model is not None,
        "upload_folder": os.path.exists(UPLOAD_FOLDER),
        "system_dependencies": {
            "ffmpeg": ffmpeg_available,
            "python_version": sys.version
        },
        "audio_libraries": {
            "librosa": librosa_test,
            "soundfile": soundfile_test,
            "pydub": pydub_test
        },
        "environment": {
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }
    })

@app.route("/test-webm")
def test_webm():
    """Test endpoint to verify WebM processing capabilities"""
    try:
        from pydub import AudioSegment
        import tempfile
        
        # Create a test audio file
        test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        
        # Test WebM creation and conversion
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_webm:
            try:
                # Try to export as WebM
                test_audio.export(tmp_webm.name, format="webm")
                webm_created = os.path.exists(tmp_webm.name) and os.path.getsize(tmp_webm.name) > 0
                
                if webm_created:
                    # Test conversion back to WAV
                    converted_path = convert_to_wav(tmp_webm.name)
                    conversion_success = converted_path != tmp_webm.name and os.path.exists(converted_path)
                    
                    # Clean up
                    if os.path.exists(tmp_webm.name):
                        os.unlink(tmp_webm.name)
                    if os.path.exists(converted_path):
                        os.unlink(converted_path)
                    
                    return jsonify({
                        "webm_creation": webm_created,
                        "webm_conversion": conversion_success,
                        "status": "success" if conversion_success else "conversion_failed"
                    })
                else:
                    return jsonify({
                        "webm_creation": False,
                        "webm_conversion": False,
                        "status": "webm_creation_failed"
                    })
                    
            except Exception as e:
                return jsonify({
                    "webm_creation": False,
                    "webm_conversion": False,
                    "status": "error",
                    "error": str(e)
                })
                
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        })

if __name__ == "__main__":
    # For local development
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
