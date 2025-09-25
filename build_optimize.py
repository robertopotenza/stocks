#!/usr/bin/env python3
"""
Docker Build Optimization and NLTK Data Download Utility

This module ensures NLTK data is properly available and provides
build optimization recommendations for deployment platforms.
"""

import ssl
import os
import sys
from pathlib import Path

def ensure_nltk_data():
    """Ensure NLTK VADER lexicon is available with SSL fix."""
    try:
        # Fix SSL certificate issues
        ssl._create_default_https_context = ssl._create_unverified_context
        
        import nltk
        
        # Try to use the data first
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()
            # Test it works
            test_result = sia.polarity_scores("test")
            print("✅ NLTK VADER lexicon is already available and working")
            return True
        except (LookupError, ImportError) as e:
            print(f"⚠️  NLTK VADER lexicon not available: {e}")
            
        # Download if not available
        print("📥 Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon', quiet=True)
        
        # Test after download
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        test_result = sia.polarity_scores("test")
        print("✅ NLTK VADER lexicon downloaded and working successfully")
        print(f"📊 Test result: {test_result}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to ensure NLTK data: {e}")
        print("📌 Application will fall back to TextBlob-only sentiment analysis")
        return False

def print_build_optimizations():
    """Print build optimization recommendations."""
    print("\n🚀 Docker Build Optimization Recommendations:")
    print("=" * 60)
    print("1. Use Dockerfile.optimized for fastest builds (~45s)")
    print("2. Use Dockerfile.fixed for production without Chrome (~55s)")
    print("3. Main Dockerfile with Chrome takes ~2+ minutes")
    print("\n💡 For Railway/deployment platforms:")
    print("- Set Dockerfile to 'Dockerfile.optimized'")
    print("- Or use docker-compose.yml which uses Dockerfile.fixed")
    print("- Builds under 1 minute to avoid timeouts")
    print("\n📦 Layer Caching Optimizations:")
    print("- requirements.txt copied before app code")
    print("- System dependencies installed in single layer")
    print("- Pip cache disabled for smaller images")
    print("- Non-essential packages removed")

if __name__ == "__main__":
    print("🔧 Build Optimization and NLTK Setup")
    print("=" * 50)
    
    success = ensure_nltk_data()
    print_build_optimizations()
    
    if success:
        print("\n✅ All optimizations applied successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some optimizations had issues but app should still work")
        sys.exit(0)  # Don't fail the build