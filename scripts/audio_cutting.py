from pydub import AudioSegment, effects, silence
import os

# Define base directories relative to current file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUDIO_INPUT_DIR = os.path.join(BASE_DIR, "audio_samples")
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "data")

def preprocess_audio(audio: AudioSegment):
    #   Convert to mono
    audio = audio.set_channels(1)

    #   Normalize volume
    audio = effects.normalize(audio)

    #   Trim silence using detect_nonsilent
    nonsilent_ranges = silence.detect_nonsilent(audio, min_silence_len=300, silence_thresh=-40)

    if not nonsilent_ranges:
        return audio  # return as-is if no nonsilent parts found

    #   Merge all nonsilent parts
    trimmed_audio = AudioSegment.empty()
    for start, end in nonsilent_ranges:
        trimmed_audio += audio[start:end]

    #   Resample to 16kHz for ML
    trimmed_audio = trimmed_audio.set_frame_rate(16000)

    return trimmed_audio


def slice_audio(filename, label, chunk_length_ms=2000):
    input_path = os.path.join(AUDIO_INPUT_DIR, filename)
    print(f" Processing: {input_path}")

    if not os.path.exists(input_path):
        print(f" File not found: {input_path}")
        return

    audio = AudioSegment.from_file(input_path)
    audio = preprocess_audio(audio)

    output_dir = os.path.join(OUTPUT_BASE_DIR, label)
    os.makedirs(output_dir, exist_ok=True)

    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk.export(os.path.join(output_dir, f"{label}_{i // chunk_length_ms}.wav"), format="wav")

#  Process both real and fake
slice_audio("Real Submariner Date Movement (1).m4a", "real")
slice_audio("Fake Submariner Date Movement (1).m4a", "fake")
