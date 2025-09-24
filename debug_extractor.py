#!/usr/bin/env python3
"""
Debug helper script for technical indicators extractor.

This script provides an easy way to test and debug the technical indicators
extractor with immediate output and detailed logging.

Usage examples:
  python debug_extractor.py                    # Quick test with 3 tickers
  python debug_extractor.py --limit 1         # Test with just 1 ticker  
  python debug_extractor.py --check-files     # Just validate file structure
  python debug_extractor.py --no-headless     # Run with visible browser (if available)

Expected log messages when working:
  - "Loading URL mappings from ..."
  - "Processing X/Y: TICKER"
  - "Extracted indicators for TICKER with quality: ..."
  - "Successfully saved N ticker results to ..."

Common issues and solutions:
  - Network issues: Extractor will use mock data (quality: 'mock')
  - Selenium disabled: Will fallback to requests-only mode
  - File permission errors: Check write permissions on output file
  - Missing columns: Ensure URL.xlsx has 'Ticker' and 'URL' columns
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

def main():
    """Main function for debugging the extractor."""
    print("🔍 Technical Indicators Extractor - Debug Helper")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(
        description='Debug helper for technical indicators extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python debug_extractor.py                    # Quick test with 3 tickers
  python debug_extractor.py --limit 1         # Test with just 1 ticker
  python debug_extractor.py --no-headless     # Run with visible browser
  python debug_extractor.py --check-files     # Just check file structure
        '''
    )
    
    parser.add_argument('--limit', type=int, default=3,
                       help='Number of tickers to process (default: 3)')
    parser.add_argument('--url-file', default='URL.xlsx',
                       help='Input URL file (default: URL.xlsx)')
    parser.add_argument('--output-file', default='tickers.xlsx',
                       help='Output file (default: tickers.xlsx)')
    parser.add_argument('--check-files', action='store_true',
                       help='Just check file structure and exit')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser in visible mode (for debugging)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Check file structure first
    print("📋 Checking Prerequisites...")
    print("-" * 30)
    
    # Check URL.xlsx
    if not os.path.exists(args.url_file):
        print(f"❌ ERROR: {args.url_file} not found!")
        return 1
    
    try:
        url_df = pd.read_excel(args.url_file)
        print(f"✅ {args.url_file} found: {len(url_df)} rows")
        
        # Check required columns
        required_cols = ['Ticker', 'URL']
        missing_cols = [col for col in required_cols if col not in url_df.columns]
        if missing_cols:
            print(f"❌ ERROR: Missing required columns: {missing_cols}")
            print(f"   Available columns: {list(url_df.columns)}")
            return 1
        print(f"✅ Required columns present: {required_cols}")
        
        # Show sample data
        print(f"📊 Sample data from {args.url_file}:")
        print(url_df[['Ticker', 'URL']].head(args.limit))
        
    except Exception as e:
        print(f"❌ ERROR reading {args.url_file}: {e}")
        return 1
    
    # Check output file
    if os.path.exists(args.output_file):
        try:
            output_df = pd.read_excel(args.output_file)
            print(f"✅ {args.output_file} found: {len(output_df)} rows")
        except Exception as e:
            print(f"⚠️  WARNING: {args.output_file} exists but can't read it: {e}")
    else:
        print(f"ℹ️  {args.output_file} doesn't exist (will be created)")
    
    # Check permissions
    try:
        test_file = f"{args.output_file}.test"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ Write permissions OK for {args.output_file}")
    except Exception as e:
        print(f"❌ ERROR: Cannot write to {args.output_file}: {e}")
        return 1
    
    if args.check_files:
        print("\n✅ File structure check completed successfully!")
        return 0
    
    # Run the actual extraction
    print(f"\n🚀 Running extraction with limit={args.limit}...")
    print("-" * 50)
    
    # Set environment for debugging
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Import and run the extractor
    try:
        from technical_indicators_extractor import TechnicalIndicatorsExtractor
        
        # Create limited URL file
        limited_df = url_df.head(args.limit)
        limited_file = f"debug_limited_URL_{args.limit}.xlsx"
        limited_df.to_excel(limited_file, index=False)
        print(f"📁 Created temporary file: {limited_file}")
        
        # Initialize extractor
        extractor = TechnicalIndicatorsExtractor(
            headless=not args.no_headless,
            timeout=args.timeout,
            delay_min=0.5,
            delay_max=1.0  # Shorter delay for debugging
        )
        
        print(f"⚙️  Extractor settings:")
        print(f"   - Headless: {not args.no_headless}")
        print(f"   - Timeout: {args.timeout}s")
        print(f"   - Processing {args.limit} tickers")
        
        # Process the file
        print(f"\n🔄 Processing {args.limit} tickers...")
        start_time = datetime.now()
        
        success = extractor.process_tickers_file(limited_file, args.output_file)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Clean up
        extractor.cleanup()
        if os.path.exists(limited_file):
            os.remove(limited_file)
            print(f"🧹 Cleaned up temporary file: {limited_file}")
        
        # Show results
        print(f"\n📊 Results Summary:")
        print(f"   - Success: {success}")
        print(f"   - Duration: {duration:.2f}s")
        print(f"   - Rate: {args.limit/duration:.2f} tickers/second")
        
        if success:
            # Show updated output file
            try:
                result_df = pd.read_excel(args.output_file)
                print(f"   - Output file now has {len(result_df)} rows")
                
                # Show recent updates
                if 'indicator_last_checked' in result_df.columns:
                    recent = result_df[result_df['indicator_last_checked'].notna()]
                    if len(recent) > 0:
                        latest_time = recent['indicator_last_checked'].max()
                        recent_count = len(recent[recent['indicator_last_checked'] == latest_time])
                        print(f"   - {recent_count} tickers updated in this run")
                        
                        if 'data_quality' in result_df.columns:
                            quality_counts = recent[recent['indicator_last_checked'] == latest_time]['data_quality'].value_counts()
                            print(f"   - Quality breakdown: {dict(quality_counts)}")
                
            except Exception as e:
                print(f"   - ⚠️  Couldn't analyze output file: {e}")
            
            print(f"\n✅ Extraction completed successfully!")
            print(f"💡 Tip: Open {args.output_file} to see the updated data")
            return 0
        else:
            print(f"\n❌ Extraction failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())