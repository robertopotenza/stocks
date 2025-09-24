#!/usr/bin/env python3
"""
CLI script to run technical indicators extraction.

This script provides a simple command-line interface to extract technical indicators
from web pages and update the Excel file with the results.
"""

import sys
import argparse
from technical_indicators_extractor import main as run_extractor


def main():
    """Main CLI entry point."""
    print("🔍 Technical Indicators Extractor")
    print("=" * 50)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Extract technical indicators from web pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_technical_indicators.py                    # Run with defaults
  python run_technical_indicators.py --no-headless     # Run with visible browser
  python run_technical_indicators.py --timeout 60      # Increase timeout
  python run_technical_indicators.py --url-file test_URL.xlsx --output-file test_output.xlsx
        '''
    )
    
    parser.add_argument('--url-file', default='URL.xlsx',
                       help='Excel file with Ticker and URL columns (default: URL.xlsx)')
    parser.add_argument('--output-file', default='tickers.xlsx',
                       help='Excel file to update with indicators (default: tickers.xlsx)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser with visible interface')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Page load timeout in seconds (default: 30)')
    parser.add_argument('--delay-min', type=float, default=0.5,
                       help='Minimum delay between requests in seconds (default: 0.5)')
    parser.add_argument('--delay-max', type=float, default=2.0,
                       help='Maximum delay between requests in seconds (default: 2.0)')
    parser.add_argument('--limit', type=int,
                       help='Limit number of tickers to process (for testing)')
    
    args = parser.parse_args()
    
    print(f"📁 URL file: {args.url_file}")
    print(f"📄 Output file: {args.output_file}")
    print(f"🖥️  Headless mode: {args.headless}")
    print(f"⏱️  Timeout: {args.timeout}s")
    print(f"⏰ Delay range: {args.delay_min}-{args.delay_max}s")
    if args.limit:
        print(f"🔢 Processing limit: {args.limit} tickers")
    print()
    
    # If limit is specified, create a limited URL file
    if args.limit:
        import pandas as pd
        import os
        
        print(f"🔄 Creating limited URL file with {args.limit} tickers...")
        try:
            full_df = pd.read_excel(args.url_file)
            limited_df = full_df.head(args.limit)
            
            limited_file = f"limited_{args.url_file}"
            limited_df.to_excel(limited_file, index=False)
            
            # Update args to use limited file
            original_url_file = args.url_file
            args.url_file = limited_file
            
            print(f"✅ Created {limited_file} with {len(limited_df)} tickers")
            
        except Exception as e:
            print(f"❌ Error creating limited URL file: {e}")
            return 1
    
    # Update sys.argv to pass arguments to the main function
    sys.argv = ['technical_indicators_extractor.py']
    if args.url_file != 'URL.xlsx':
        sys.argv.extend(['--url-file', args.url_file])
    if args.output_file != 'tickers.xlsx':
        sys.argv.extend(['--output-file', args.output_file])
    if not args.headless:
        sys.argv.append('--no-headless')
    if args.timeout != 30:
        sys.argv.extend(['--timeout', str(args.timeout)])
    if args.delay_min != 0.5:
        sys.argv.extend(['--delay-min', str(args.delay_min)])
    if args.delay_max != 2.0:
        sys.argv.extend(['--delay-max', str(args.delay_max)])
    
    # Run the extractor
    try:
        result = run_extractor()
        
        # Cleanup limited file if created
        if args.limit and 'limited_file' in locals():
            try:
                os.remove(limited_file)
                print(f"🧹 Cleaned up {limited_file}")
            except:
                pass
        
        return result
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Extraction cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())