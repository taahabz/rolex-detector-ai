# Rolex Authenticity Detector AI

An AI-powered web application that analyzes audio files to detect authentic Rolex watches from fakes using machine learning. The application uses Flask for the web interface and scikit-learn for audio feature extraction and classification.

## Features

- **Audio Upload**: Upload various audio formats (WAV, MP3, M4A, FLAC, OGG, WebM)
- **Live Recording**: Record audio directly in the browser
- **AI Analysis**: Machine learning model analyzes audio features to determine authenticity
- **Confidence Score**: Provides confidence percentage for predictions
- **Modern UI**: Clean, responsive interface with real-time feedback

## Technology Stack

- **Backend**: Flask (Python)
- **Machine Learning**: scikit-learn, librosa
- **Audio Processing**: pydub, librosa, soundfile
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Heroku

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Open your browser to `http://localhost:5000`

## Heroku Deployment

This application is configured for Heroku deployment with audio processing capabilities.

### Important for Audio Processing:

The app uses `heroku.yml` to install system dependencies required for audio processing:
- `ffmpeg` - For audio format conversion
- `libsndfile1` - For audio file reading
- `libsndfile1-dev` - Development headers for soundfile

### Deployment Steps:

1. **Enable heroku.yml builds** in your Heroku app:
   ```bash
   heroku stack:set container -a your-app-name
   ```

2. **Or use heroku.yml** by setting the stack:
   ```bash
   heroku stack:set heroku-22 -a your-app-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY="your-secure-secret-key"
   heroku config:set FLASK_ENV=production
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Troubleshooting Audio Issues:

If you encounter "Error processing audio file" errors:

1. **Check logs**: `heroku logs --tail`
2. **Test audio setup**: Use the `/health` endpoint to verify setup
3. **Run audio test**: `heroku run python test_audio.py`

## Model Information

The application uses a Random Forest classifier trained on audio features including:
- MFCC (Mel-frequency cepstral coefficients)
- Zero-crossing rate
- Spectral centroid

The model analyzes these features to classify audio as either authentic or fake Rolex sounds.

## System Dependencies

- Python 3.11+
- ffmpeg (for audio conversion)
- libsndfile1 (for audio file reading)
- Various Python packages (see requirements.txt)
