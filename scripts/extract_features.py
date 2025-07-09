import os
import numpy as np
import pandas as pd
import librosa

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
FEATURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'features')
os.makedirs(FEATURES_DIR, exist_ok=True)

def extract_features_from_file(file_path):
    y, sr = librosa.load(file_path, sr=16000)  #   Already resampled by pydub
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    zcr = librosa.feature.zero_crossing_rate(y)
    spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)

    features = np.hstack([
        np.mean(mfcc, axis=1),
        np.std(mfcc, axis=1),
        np.mean(zcr),
        np.std(zcr),
        np.mean(spec_cent),
        np.std(spec_cent)
    ])
    return features

def process_dataset():
    dataset = []
    for label in ['real', 'fake']:
        label_dir = os.path.join(DATA_DIR, label)
        for file_name in os.listdir(label_dir):
            if file_name.endswith('.wav'):
                file_path = os.path.join(label_dir, file_name)
                print(f" Extracting from: {file_path}")
                features = extract_features_from_file(file_path)
                dataset.append(np.append(features, label))
    
    # Create DataFrame
    feature_names = [f'mfcc_mean_{i}' for i in range(13)] + \
                    [f'mfcc_std_{i}' for i in range(13)] + \
                    ['zcr_mean', 'zcr_std', 'spec_cent_mean', 'spec_cent_std'] + \
                    ['label']
    df = pd.DataFrame(dataset, columns=feature_names)
    df.to_csv(os.path.join(FEATURES_DIR, 'dataset.csv'), index=False)
    print("  Features saved to features/dataset.csv")

if __name__ == "__main__":
    process_dataset()
