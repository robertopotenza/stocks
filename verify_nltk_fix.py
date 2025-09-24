#!/usr/bin/env python3
"""
NLTK VADER Fix Verification Script

This script can be run inside the Docker container to verify that the
NLTK VADER lexicon fix is working correctly.

Usage in Docker container:
    docker exec <container_name> python /app/verify_nltk_fix.py

Expected output when fix is working:
    ✅ All checks passed - NLTK VADER is working correctly

Expected output when fix is not working:
    ❌ NLTK VADER lexicon not available (falls back to TextBlob only)
"""

import sys
import os
from pathlib import Path

def verify_nltk_vader_fix():
    """Verify that NLTK VADER lexicon is available and working."""
    print("🔍 Verifying NLTK VADER fix in Docker container...")
    print("=" * 50)
    
    # Check 1: User context
    print(f"👤 Current user: {os.getenv('USER', 'unknown')}")
    print(f"🏠 Home directory: {os.path.expanduser('~')}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check 2: NLTK import
    try:
        import nltk
        print("✅ NLTK import successful")
        print(f"📂 NLTK data paths: {nltk.data.path}")
    except ImportError as e:
        print(f"❌ NLTK import failed: {e}")
        return False
    
    # Check 3: NLTK data directory
    nltk_data_dirs = [
        os.path.expanduser('~/nltk_data'),
        '/app/nltk_data',
        '/usr/nltk_data',
        '/usr/share/nltk_data'
    ]
    
    found_nltk_data = False
    for data_dir in nltk_data_dirs:
        if os.path.exists(data_dir):
            print(f"📁 Found NLTK data directory: {data_dir}")
            
            # Check for VADER lexicon specifically
            vader_paths = [
                os.path.join(data_dir, 'sentiment', 'vader_lexicon.zip'),
                os.path.join(data_dir, 'sentiment', 'vader_lexicon', 'vader_lexicon.txt')
            ]
            
            for vader_path in vader_paths:
                if os.path.exists(vader_path):
                    print(f"✅ Found VADER lexicon: {vader_path}")
                    found_nltk_data = True
                    break
    
    if not found_nltk_data:
        print("❌ VADER lexicon not found in any NLTK data directory")
    
    # Check 4: SentimentIntensityAnalyzer initialization
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        print("✅ SentimentIntensityAnalyzer initialized successfully")
        
        # Test sentiment analysis
        test_result = sia.polarity_scores("This is a great stock investment!")
        print(f"📊 Test sentiment result: {test_result}")
        
        if test_result and 'compound' in test_result:
            print("✅ VADER sentiment analysis working correctly")
        else:
            print("❌ VADER sentiment analysis not returning expected results")
            return False
            
    except Exception as e:
        print(f"❌ SentimentIntensityAnalyzer failed: {e}")
        return False
    
    # Check 5: Application sentiment analysis
    try:
        from sentiment_analysis import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        if analyzer.sia is None:
            print("❌ Application SentimentAnalyzer failed to initialize VADER")
            return False
        else:
            print("✅ Application SentimentAnalyzer with VADER initialized")
            
        # Test application sentiment analysis
        result = analyzer.analyze_text("This stock is performing amazingly well!")
        print(f"📈 Application sentiment result: {result}")
        
        required_keys = ['polarity', 'subjectivity', 'compound', 'classification', 'pos', 'neu', 'neg']
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"❌ Missing keys in sentiment result: {missing_keys}")
            return False
        else:
            print("✅ All expected sentiment keys present")
            
    except Exception as e:
        print(f"❌ Application sentiment analysis failed: {e}")
        return False
    
    return True

def main():
    """Main verification function."""
    success = verify_nltk_vader_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ NLTK VADER lexicon is working correctly")
        print("🚀 Sentiment analysis will use both TextBlob and VADER")
    else:
        print("💥 VERIFICATION FAILED!")
        print("❌ NLTK VADER lexicon is not working properly")
        print("⚠️  Application will fall back to TextBlob-only sentiment analysis")
    print("=" * 50)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)