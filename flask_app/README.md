# Rolex Detector Flask Web Application

A sophisticated web application that uses machine learning to detect authentic vs. fake Rolex watches through audio analysis of their movement sounds.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Virtual environment (recommended)
- All dependencies from `requirements.txt`

### Setup & Run

1. **Navigate to the flask_app directory:**
   ```bash
   cd flask_app
   ```

2. **Run the startup script:**
   ```bash
   python run_app.py
   ```

3. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
flask_app/
├── app.py              # Main Flask application
├── run_app.py          # Startup script with checks
├── test_model.py       # Model testing utility
├── templates/
│   └── index.html      # Main web interface
├── static/
│   ├── style.css       # Styling
│   ├── script_new.js   # JavaScript functionality
│   └── favicon.ico     # App icon
└── uploads/            # Temporary file storage (auto-created)
```

## 🔧 Technical Details

### Path Configuration
The app uses absolute paths to ensure correct file location:
- **Model Path**: `../model/rolex_model.pkl`
- **Upload Folder**: `./uploads/`
- **Static Files**: `./static/`

### Feature Extraction
The app extracts the same 30 features used in training:
- **MFCC Features**: 13 mean + 13 std = 26 features
- **Zero Crossing Rate**: mean + std = 2 features  
- **Spectral Centroid**: mean + std = 2 features
- **Total**: 30 features

### Audio Processing
- **Supported formats**: WAV, MP3, M4A, FLAC, OGG, WebM
- **Sampling rate**: 16kHz (matches training)
- **Auto-conversion**: Non-WAV files converted automatically
- **Cleanup**: Temporary files removed after processing

### Model Predictions
- **Real Rolex**: Prediction = 1, Label = "Real"
- **Fake Rolex**: Prediction = 0, Label = "Fake"
- **Confidence**: Probability score (0-100%)

## 🛠️ Troubleshooting

### Common Issues

1. **Model not found:**
   ```
   ❌ Model file not found at: ../model/rolex_model.pkl
   ```
   **Solution**: Ensure the model has been trained using `scripts/train_model.py`

2. **Missing dependencies:**
   ```
   ❌ Missing packages: librosa, flask
   ```
   **Solution**: Install requirements: `pip install -r ../requirements.txt`

3. **Audio processing errors:**
   - Ensure audio file is not corrupted
   - Try converting to WAV format manually
   - Check file permissions

### Testing the Model

Run the test script to verify everything works:
```bash
python test_model.py
```

Expected output:
```
🔍 Testing Rolex Detector Model...
✅ Model loaded successfully!
✅ Test prediction successful!
🎉 All tests passed! Flask app should work correctly.
```

## 🌟 Features

### Web Interface
- **Responsive design** with modern UI
- **File upload** with drag-and-drop support
- **Audio recording** directly in browser
- **Real-time feedback** and progress indicators
- **Confidence scoring** with visual indicators

### Audio Analysis
- **Multi-format support** (WAV, MP3, M4A, etc.)
- **Automatic preprocessing** and feature extraction
- **Machine learning prediction** using trained Random Forest model
- **Confidence estimation** for reliability assessment

### Error Handling
- **Comprehensive validation** of input files
- **Graceful error messages** for users
- **Automatic cleanup** of temporary files
- **Logging** for debugging

## 📊 Model Performance

The underlying machine learning model achieves:
- **High accuracy** on test data
- **Robust feature extraction** from audio signals
- **Cross-validation** for reliability
- **Feature importance analysis** for interpretability

## 🔒 Security Considerations

- **File validation** prevents malicious uploads
- **Temporary storage** with automatic cleanup
- **Input sanitization** for all user inputs
- **Error handling** prevents information leakage

## 🚀 Deployment

For production deployment:
1. Set `debug=False` in `app.py`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure proper logging
4. Set up SSL/HTTPS
5. Implement rate limiting

## 📝 API Usage

The app provides a simple POST endpoint:
```
POST /
Content-Type: multipart/form-data
Body: file=<audio_file>
```

Response:
```json
{
  "result": "Real" | "Fake",
  "confidence": 85.5,
  "filename": "audio.wav"
}
```

## 🤝 Contributing

To extend the application:
1. Add new audio formats in `ALLOWED_EXTENSIONS`
2. Modify feature extraction in `extract_features()`
3. Update the UI in `templates/index.html`
4. Add new routes in `app.py`

## 📄 License

This project is part of the Rolex Detector AI system for educational and research purposes. 