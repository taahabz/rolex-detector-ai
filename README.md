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
- **Audio Processing**: pydub, librosa
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Heroku

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Open your browser to `http://localhost:5000`

## Deployment

This application is configured for Heroku deployment. See deployment instructions below.

## Model Information

The application uses a Random Forest classifier trained on audio features including:
- MFCC (Mel-frequency cepstral coefficients)
- Zero-crossing rate
- Spectral centroid

The model analyzes these features to classify audio as either authentic or fake Rolex sounds.
