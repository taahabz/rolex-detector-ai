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

This application is configured for Heroku deployment with audio processing capabilities using the standard buildpack approach.

### Important for Audio Processing:

The app uses `Aptfile` to install system dependencies required for audio processing:
- `ffmpeg` - For audio format conversion
- `libsndfile1` - For audio file reading
- `libsndfile1-dev` - Development headers for soundfile
- Additional audio codec libraries for WebM and other formats

### Deployment Steps:

1. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

2. **Add buildpacks** (in this order):
   ```bash
   heroku buildpacks:add --index 1 heroku-community/apt
   heroku buildpacks:add --index 2 heroku/python
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY="your-secure-secret-key"
   heroku config:set FLASK_ENV=production
   ```

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy with audio processing fixes"
   git push heroku main
   ```

### Troubleshooting Audio Issues:

If you encounter "Error processing audio file" errors:

1. **Check logs**: `heroku logs --tail`
2. **Test audio setup**: Use the `/health` endpoint to verify setup
3. **Run audio test**: `heroku run python test_audio.py`
4. **Check buildpack order**: Ensure apt buildpack is first, python second

### Common Issues and Solutions:

- **WebM recording fails**: Usually due to missing ffmpeg or codec libraries
- **Feature extraction fails**: Check if librosa can load the audio file
- **Empty audio files**: Verify the recording actually contains audio data
- **Timeout errors**: Increase worker timeout in Procfile if needed

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



**New Name: CORE**
**Full Form: Central Operational Resource Engine**

This name is strong, memorable, gender-neutral, single-syllable, and the full form perfectly captures its central, active, and fundamental role in HR, implying intelligence and efficiency.

Here's that 4-line explanation again, ready for your non-tech audience:

---

1.  **CORE is like the central engine for managing your company's entire team**, handling everything from hiring to their daily work.
2.  You can easily use it through a **simple website or just by texting on WhatsApp**, making HR tasks quick and convenient for everyone.
3.  This **smart agent** (the "engine" part) is clever enough to **understand your natural messages**, whether you're noting something about an employee or securely sharing important company passwords like the Wi-Fi.
4.  This means **less paperwork, smarter decisions** for your **human** resources, and a more organized, efficient business built on a strong **CORE**.