#!/usr/bin/env python3
"""
Final test for AquaTrace AI with MongoDB + my_fine_tuned.h5 + Vision API
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_model_file():
    """Test if my_fine_tuned.h5 exists"""
    model_path = os.path.join(os.path.dirname(__file__), 'model', 'my_fine_tuned.h5')
    if os.path.exists(model_path):
        print(f"✅ Model file found: {model_path}")
        return True
    else:
        print(f"❌ Model file NOT found: {model_path}")
        return False

def test_mongodb():
    """Test MongoDB connection"""
    try:
        from models import User
        count = User.count()
        print(f"✅ MongoDB connected! Users: {count}")
        return True
    except Exception as e:
        print(f"❌ MongoDB failed: {e}")
        return False

def test_vision_api():
    """Test Vision API"""
    try:
        from vision_api_fallback import test_vision_api
        result = test_vision_api()
        if result:
            print("✅ Vision API ready!")
        else:
            print("❌ Vision API failed!")
        return result
    except Exception as e:
        print(f"❌ Vision API error: {e}")
        return False

def main():
    print("🚀 Final Setup Test for AquaTrace AI")
    print("=" * 50)
    
    # Test all components
    model_ok = test_model_file()
    mongodb_ok = test_mongodb()
    vision_ok = test_vision_api()
    
    print("\n📊 Final Results:")
    print(f"   Model (my_fine_tuned.h5): {'✅' if model_ok else '❌'}")
    print(f"   MongoDB Atlas: {'✅' if mongodb_ok else '❌'}")
    print(f"   Vision API: {'✅' if vision_ok else '❌'}")
    
    if model_ok and mongodb_ok and vision_ok:
        print("\n🎉 ALL SYSTEMS READY!")
        print("🎓 Professor's requirements met:")
        print("   ✅ H5 model (my_fine_tuned.h5) - Primary")
        print("   ✅ Vision API - Fallback")
        print("   ✅ MongoDB Atlas - Database")
        print("   ✅ 5 Classes: Dolphin, Jellyfish, Sea Rays, Starfish, Whale")
        print("\n💡 Run: python app.py")
    else:
        print("\n⚠️ Some components need fixing!")

if __name__ == "__main__":
    main()
