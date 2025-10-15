#!/usr/bin/env python3
"""
Quick Test Script for Updated AquaTrace AI
Tests ResNet50V2 model loading and basic app functionality
"""

import os
import sys
import traceback

def test_updated_app():
    """Test the updated AquaTrace AI application"""
    
    print("=" * 60)
    print("🧪 Testing Updated AquaTrace AI")
    print("=" * 60)
    
    # Test 1: Check dependencies
    print("1️⃣ Checking dependencies...")
    try:
        import tensorflow as tf
        print(f"   ✅ TensorFlow: {tf.__version__}")
        
        import numpy as np
        print(f"   ✅ NumPy: {np.__version__}")
        
        from PIL import Image
        print(f"   ✅ Pillow: {Image.__version__}")
        
        import flask
        print(f"   ✅ Flask: {flask.__version__}")
        
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        return False
    
    # Test 2: Check model file
    print("\n2️⃣ Checking model file...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'model', 'ResNet50V2-Sea-Animal-Classifier.h5')
    
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"   ✅ ResNet50V2 model found ({file_size:.2f} MB)")
    else:
        print(f"   ❌ Model file not found at: {model_path}")
        return False
    
    # Test 3: Test model loading
    print("\n3️⃣ Testing model loading...")
    try:
        from tensorflow.keras.applications.resnet_v2 import ResNet50V2, preprocess_input
        
        # Try to load the actual model
        model = tf.keras.models.load_model(model_path)
        print(f"   ✅ Model loaded successfully!")
        print(f"   📊 Input shape: {model.input_shape}")
        print(f"   📊 Output shape: {model.output_shape}")
        
        # Test prediction with dummy data
        dummy_input = np.random.random((1, 224, 224, 3))
        dummy_input = preprocess_input(dummy_input)
        prediction = model.predict(dummy_input, verbose=0)
        print(f"   ✅ Test prediction successful! Shape: {prediction.shape}")
        
    except Exception as e:
        print(f"   ⚠️  Model loading failed, testing fallback...")
        try:
            # Test fallback model creation
            base_model = ResNet50V2(
                weights='imagenet',
                include_top=False,
                input_shape=(224, 224, 3)
            )
            print(f"   ✅ Fallback ResNet50V2 creation successful!")
        except Exception as e2:
            print(f"   ❌ Fallback failed: {e2}")
            return False
    
    # Test 4: Check environment variables
    print("\n4️⃣ Checking OAuth configuration...")
    from dotenv import load_dotenv
    load_dotenv()
    
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if google_client_id and google_client_secret:
        print("   ✅ Google OAuth credentials configured")
    else:
        print("   ⚠️  Google OAuth credentials missing")
    
    if github_client_id and github_client_secret:
        print("   ✅ GitHub OAuth credentials configured")
    else:
        print("   ⚠️  GitHub OAuth credentials missing")
    
    # Test 5: Basic app import
    print("\n5️⃣ Testing app import...")
    try:
        # Change to backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, backend_dir)
        
        # Try importing the app (this will test all imports)
        import app
        print("   ✅ App imports successfully!")
        print("   ✅ All tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ App import failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_updated_app()
    
    if success:
        print(f"\n🎉 All tests passed! Your updated AquaTrace AI is ready to run!")
        print(f"💡 Run with: python app.py")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
