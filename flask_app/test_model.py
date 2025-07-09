#!/usr/bin/env python3
"""
Simple test script to verify the model loads and works correctly
"""
import os
import joblib
import numpy as np

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "rolex_model.pkl")

def test_model():
    print("🔍 Testing Rolex Detector Model...")
    print(f"Model path: {MODEL_PATH}")
    
    # Test model loading
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Model loaded successfully!")
        print(f"Model type: {type(model)}")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False
    
    # Test prediction with dummy data (30 features as expected)
    try:
        # Create dummy feature vector (30 features to match training)
        dummy_features = np.random.rand(1, 30)
        
        # Make prediction
        prediction = model.predict(dummy_features)[0]
        confidence = model.predict_proba(dummy_features)[0]
        
        result = "Fake" if prediction == 0 else "Real"
        confidence_score = max(confidence) * 100
        
        print(f"✅ Test prediction successful!")
        print(f"   Prediction: {result}")
        print(f"   Confidence: {confidence_score:.2f}%")
        print(f"   Raw prediction: {prediction}")
        print(f"   Probabilities: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model()
    if success:
        print("\n🎉 All tests passed! Flask app should work correctly.")
    else:
        print("\n💥 Tests failed! Check the model and paths.") 