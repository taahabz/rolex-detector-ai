from flask import Flask, render_template, request, redirect, jsonify, flash
from pydub import AudioSegment
from sklearn.ensemble import RandomForestClassifier
import os, uuid
import joblib
import numpy as np
import librosa
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Fixed paths - using absolute paths relative to the flask_app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Use temporary directory for Vercel serverless environment
UPLOAD_FOLDER = tempfile.mkdtemp()

# Model path for Vercel deployment
MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "rolex_model.pkl")
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg', 'webm'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the model
try:
    # Try multiple paths for different deployment environments
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        # Alternative path for Vercel
        alt_model_path = os.path.join(BASE_DIR, "..", "model", "rolex_model.pkl")
        if os.path.exists(alt_model_path):
            model = joblib.load(alt_model_path)
        else:
            # Try relative to current directory
            rel_model_path = os.path.join("model", "rolex_model.pkl")
            model = joblib.load(rel_model_path)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    print(f"Tried paths: {MODEL_PATH}")
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_path):
    """Convert audio file to WAV format if needed"""
    try:
        print(f"Converting audio file: {input_path}")
        
        # Check if file exists
        if not os.path.exists(input_path):
            print(f"Input file does not exist: {input_path}")
            return input_path
        
        # Load audio file with pydub
        if input_path.endswith('.webm'):
            # For WebM files, we need to be more explicit
            audio = AudioSegment.from_file(input_path, format="webm")
        else:
            audio = AudioSegment.from_file(input_path)
        
        # Create output path
        output_path = input_path.rsplit('.', 1)[0] + '_converted.wav'
        
        # Export as WAV with specific parameters for consistency
        audio.export(output_path, format="wav", parameters=["-ar", "44100", "-ac", "1"])
        
        print(f"Successfully converted to: {output_path}")
        
        # Verify the output file was created
        if not os.path.exists(output_path):
            print(f"Conversion failed - output file not created: {output_path}")
            return input_path
            
        return output_path
    except Exception as e:
        print(f"Error converting audio from {input_path}: {e}")
        import traceback
        traceback.print_exc()
        return input_path

def extract_features(filepath):
    """Extract features matching the training format exactly"""
    try:
        print(f"Processing file: {filepath}")
        
        # Always convert WebM and other non-WAV files to WAV
        if not filepath.endswith('.wav'):
            print(f"Converting {filepath} to WAV...")
            converted_path = convert_to_wav(filepath)
            if not os.path.exists(converted_path):
                print(f"Conversion failed - file does not exist: {converted_path}")
                return None
            filepath = converted_path
        
        # Load audio with same parameters as training (16kHz sampling rate)
        print(f"Loading audio with librosa: {filepath}")
        y, sr = librosa.load(filepath, sr=16000)  # Match training sr=16000
        
        if len(y) == 0:
            print("Audio file is empty or corrupted")
            return None
            
        print(f"Audio loaded: {len(y)} samples at {sr} Hz")
        
        # Extract features exactly like training script
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        zcr = librosa.feature.zero_crossing_rate(y)
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)

        # Combine features in same order as training
        features = np.hstack([
            np.mean(mfcc, axis=1),     # mfcc_mean_0 to mfcc_mean_12 (13 features)
            np.std(mfcc, axis=1),      # mfcc_std_0 to mfcc_std_12 (13 features)
            np.mean(zcr),              # zcr_mean (1 feature)
            np.std(zcr),               # zcr_std (1 feature)
            np.mean(spec_cent),        # spec_cent_mean (1 feature)
            np.std(spec_cent)          # spec_cent_std (1 feature)
        ])
        
        print(f"Extracted features shape: {features.shape} (expected: 30)")
        
        # Clean up converted file if it was created
        if filepath.endswith('_converted.wav'):
            try:
                os.remove(filepath)
                print(f"Cleaned up converted file: {filepath}")
            except:
                pass
            
        return features
    except Exception as e:
        print(f"Error extracting features from {filepath}: {e}")
        import traceback
        traceback.print_exc()
        
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
            
            # Extract features
            features = extract_features(filepath)
            
            if features is None:
                flash("Error processing audio file. Please try a different file.", "error")
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
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return render_template("index.html", 
                                 result=result, 
                                 confidence=confidence_score,
                                 filename=file.filename)
                                 
        except Exception as e:
            print(f"Error processing file: {e}")
            flash("Error processing audio file. Please try again.", "error")
            # Clean up uploaded file
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return render_template("index.html")
    
    return render_template("index.html")

if __name__ == "__main__":
    # For local development
    app.run(debug=True)
else:
    # For Vercel deployment, create the app instance
    application = app
