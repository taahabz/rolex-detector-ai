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
    """Convert audio file to WAV format if needed"""
    try:
        logger.info(f"Converting audio file: {input_path}")
        
        # Check if file exists
        if not os.path.exists(input_path):
            logger.error(f"Input file does not exist: {input_path}")
            return input_path
        
        # Check file size
        file_size = os.path.getsize(input_path)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Input file is empty")
            return input_path
        
        # Test if ffmpeg is available
        ffmpeg_test = os.system("which ffmpeg > /dev/null 2>&1")
        if ffmpeg_test != 0:
            logger.error("ffmpeg is not available - this is required for audio conversion")
            return input_path
        
        # Load audio file with pydub - enhanced WebM handling
        try:
            if input_path.endswith('.webm'):
                # For WebM files from browser MediaRecorder, try multiple approaches
                logger.info("Loading WebM file with pydub")
                try:
                    # First try: Standard WebM
                    audio = AudioSegment.from_file(input_path, format="webm")
                    logger.info("Successfully loaded WebM with standard method")
                except Exception as e1:
                    logger.info(f"Standard WebM failed: {e1}, trying alternative methods")
                    try:
                        # Second try: WebM with opus codec
                        audio = AudioSegment.from_file(input_path, format="webm", codec="opus")
                        logger.info("Successfully loaded WebM with opus codec")
                    except Exception as e2:
                        logger.info(f"WebM with opus failed: {e2}, trying auto-detect")
                        try:
                            # Third try: Let pydub auto-detect format
                            audio = AudioSegment.from_file(input_path)
                            logger.info("Successfully loaded WebM with auto-detection")
                        except Exception as e3:
                            logger.error(f"All WebM methods failed: {e3}")
                            # Last resort: try with different parameters
                            try:
                                audio = AudioSegment.from_file(input_path, format="webm", parameters=["-acodec", "libopus"])
                                logger.info("Successfully loaded WebM with libopus parameters")
                            except Exception as e4:
                                logger.error(f"Final WebM attempt failed: {e4}")
                                return input_path
            else:
                logger.info(f"Loading {input_path} with pydub")
                audio = AudioSegment.from_file(input_path)
        except Exception as e:
            logger.error(f"pydub failed to load audio file: {e}")
            return input_path
        
        # Check if audio was loaded successfully
        if len(audio) == 0:
            logger.error("Loaded audio is empty")
            return input_path
        
        logger.info(f"Audio loaded successfully: {len(audio)}ms duration, {audio.channels} channels, {audio.frame_rate}Hz")
        
        # Create output path
        output_path = input_path.rsplit('.', 1)[0] + '_converted.wav'
        
        # Export as WAV with specific parameters for consistency
        try:
            audio.export(output_path, format="wav", parameters=["-ar", "44100", "-ac", "1"])
            logger.info(f"Successfully exported to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export audio: {e}")
            return input_path
        
        # Verify the output file was created and has content
        if not os.path.exists(output_path):
            logger.error(f"Conversion failed - output file not created: {output_path}")
            return input_path
        
        output_size = os.path.getsize(output_path)
        if output_size == 0:
            logger.error(f"Conversion failed - output file is empty: {output_path}")
            return input_path
            
        logger.info(f"Conversion successful - output file size: {output_size} bytes")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting audio from {input_path}: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return input_path

def extract_features(filepath):
    """Extract features matching the training format exactly"""
    try:
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
        
        # Fast path for WAV files - skip all conversion
        if filepath.endswith('.wav'):
            logger.info("WAV file detected - loading directly with librosa")
            try:
                y, sr = librosa.load(filepath, sr=16000)  # Match training sr=16000
                logger.info(f"WAV file loaded directly: {len(y)} samples at {sr}Hz")
            except Exception as e:
                logger.error(f"Error loading WAV file with librosa: {e}")
                return None
        else:
            # For non-WAV files, try loading directly with librosa first
            logger.info(f"Non-WAV file - trying direct librosa loading: {filepath}")
            
            try:
                # First attempt: Load directly with librosa (works with most formats)
                y, sr = librosa.load(filepath, sr=16000)  # Match training sr=16000
                logger.info(f"Librosa loaded {len(y)} samples at {sr}Hz directly")
            except Exception as e:
                logger.info(f"Direct librosa loading failed: {e}, trying conversion method")
                
                # Fallback: Convert to WAV first (only if direct loading fails)
                logger.info(f"Converting {filepath} to WAV...")
                converted_path = convert_to_wav(filepath)
                
                # Check if conversion actually worked
                if not os.path.exists(converted_path):
                    logger.error(f"Conversion failed - file does not exist: {converted_path}")
                    return None
                
                # Check if conversion returned the original path (indicating failure)
                if converted_path == filepath:
                    logger.error("Conversion returned original path - conversion likely failed")
                    return None
                    
                # Verify the converted file is actually a WAV file
                if not converted_path.endswith('.wav'):
                    logger.error(f"Conversion did not produce a WAV file: {converted_path}")
                    return None
                    
                filepath = converted_path
                logger.info(f"Successfully converted to WAV: {filepath}")
                
                # Try loading the converted file
                try:
                    y, sr = librosa.load(filepath, sr=16000)  # Match training sr=16000
                    logger.info(f"Librosa loaded {len(y)} samples at {sr}Hz after conversion")
                except Exception as e2:
                    logger.error(f"Error loading converted audio with librosa: {e2}")
                    # Try alternative loading methods
                    try:
                        logger.info("Trying alternative loading method...")
                        y, sr = librosa.load(filepath, sr=None)  # Load with original sample rate first
                        if sr != 16000:
                            logger.info(f"Resampling from {sr}Hz to 16000Hz")
                            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                            sr = 16000
                        logger.info(f"Alternative method loaded {len(y)} samples at {sr}Hz")
                    except Exception as e3:
                        logger.error(f"Alternative loading method also failed: {e3}")
                        return None
        
        if len(y) == 0:
            logger.error("Audio file is empty or corrupted")
            return None
            
        logger.info(f"Audio loaded: {len(y)} samples at {sr} Hz")
        
        # Extract features exactly like training script
        try:
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            zcr = librosa.feature.zero_crossing_rate(y)
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
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
        
        logger.info(f"Extracted features shape: {features.shape} (expected: 30)")
        
        # Clean up converted file if it was created
        if filepath.endswith('_converted.wav'):
            try:
                os.remove(filepath)
                logger.info(f"Cleaned up converted file: {filepath}")
            except:
                pass
            
        return features
    except Exception as e:
        logger.error(f"Error extracting features from {filepath}: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Clean up converted file if it exists
        if filepath.endswith('_converted.wav'):
            try:
                os.remove(filepath)
            except:
                pass
        
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
