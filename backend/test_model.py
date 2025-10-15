#!/usr/bin/env python3
"""
Model Testing Script for AquaTrace AI
This script helps diagnose issues with loading Kaggle H5 models
"""

import os
import sys
import traceback

def test_model_loading():
    """Test H5 model loading with detailed diagnostics"""
    
    # Get the model path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'model', 'animals_eff.h5')
    
    print("=" * 60)
    print("🔍 AquaTrace AI Model Diagnostic Tool")
    print("=" * 60)
    
    # Step 1: Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Step 2: Check if model file exists
    print(f"\n📁 Model path: {model_path}")
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✅ Model file exists ({file_size:.2f} MB)")
    else:
        print("❌ Model file not found!")
        return False
    
    # Step 3: Check TensorFlow installation
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow version: {tf.__version__}")
    except ImportError as e:
        print(f"❌ TensorFlow not installed: {e}")
        return False
    
    # Step 4: Check other dependencies
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except ImportError:
        print("❌ NumPy not installed")
        return False
    
    try:
        import h5py
        print(f"✅ h5py version: {h5py.__version__}")
    except ImportError:
        print("⚠️  h5py not installed (may cause issues)")
    
    # Step 5: Try to load the model
    print(f"\n🔄 Attempting to load model...")
    
    try:
        # Method 1: Standard loading
        print("   Method 1: Standard tf.keras.models.load_model...")
        model = tf.keras.models.load_model(model_path)
        print("   ✅ Success!")
        
        # Print model details
        print(f"\n📊 Model Details:")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output shape: {model.output_shape}")
        print(f"   Total parameters: {model.count_params():,}")
        print(f"   Number of layers: {len(model.layers)}")
        
        # Test prediction with dummy data
        print(f"\n🧪 Testing prediction...")
        import numpy as np
        dummy_input = np.random.random((1, 224, 224, 3))
        prediction = model.predict(dummy_input, verbose=0)
        print(f"   ✅ Prediction successful! Output shape: {prediction.shape}")
        print(f"   Sample prediction: {prediction[0][:5]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Method 1 failed: {str(e)}")
        
        try:
            # Method 2: Load without compilation
            print("   Method 2: Loading without compilation...")
            model = tf.keras.models.load_model(model_path, compile=False)
            print("   ✅ Success without compilation!")
            return True
            
        except Exception as e2:
            print(f"   ❌ Method 2 failed: {str(e2)}")
            
            try:
                # Method 3: Check if it's an HDF5 file
                print("   Method 3: Checking HDF5 file structure...")
                import h5py
                with h5py.File(model_path, 'r') as f:
                    print(f"   HDF5 keys: {list(f.keys())}")
                    if 'model_config' in f.attrs:
                        print("   ✅ Contains model configuration")
                    if 'model_weights' in f:
                        print("   ✅ Contains model weights")
                
            except Exception as e3:
                print(f"   ❌ Method 3 failed: {str(e3)}")
                print(f"\n🔍 Full error traceback:")
                traceback.print_exc()
                
                print(f"\n💡 Troubleshooting suggestions:")
                print(f"   1. The model might be saved with a different TensorFlow version")
                print(f"   2. Try installing the exact TensorFlow version used to create the model")
                print(f"   3. The model might have custom layers not available in your environment")
                print(f"   4. Consider converting the model to a compatible format")
                
                return False

if __name__ == "__main__":
    success = test_model_loading()
    
    if success:
        print(f"\n🎉 Model loading successful! Your AquaTrace AI should work properly.")
    else:
        print(f"\n❌ Model loading failed. Please check the suggestions above.")
    
    print("=" * 60)
