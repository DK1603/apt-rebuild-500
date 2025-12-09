"""
Download 500 PDFs from ArticlesDataset_underScope2.csv
Downloads from URLs specified in the CSV file
"""

import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time
import os

# Configuration
INPUT_CSV = "ArticlesDataset_500_Valid.csv"
BASE_DIR = Path("Reports/APT_CyberCriminal_Campagin_Collections Reports")
TIMEOUT = 60  # seconds
RETRY_ATTEMPTS = 3
DELAY_BETWEEN_DOWNLOADS = 0.5  # seconds (be nice to servers)

def create_directories(df):
    """Create year directories based on dates in CSV"""
    years = pd.to_datetime(df['Date']).dt.year.unique()
    
    for year in years:
        year_dir = BASE_DIR / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created directories for {len(years)} years")

def get_year_from_date(date_str):
    """Extract year from date string"""
    return pd.to_datetime(date_str).year

def sanitize_filename(filename):
    """Clean filename to be filesystem-safe"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ensure it ends with .pdf
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    return filename

def download_pdf(url, dest_path, retry_attempts=3):
    """
    Download a single PDF with retry logic
    Returns: 'success', 'skipped', or 'failed'
    """
    # Skip if already exists
    if dest_path.exists():
        return 'skipped'
    
    for attempt in range(retry_attempts):
        try:
            # Add headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True)
            
            if response.status_code == 200:
                # Check if it's actually a PDF
                content_type = response.headers.get('content-type', '')
                
                # Write to file
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file size
                if dest_path.stat().st_size < 1000:  # Less than 1KB is suspicious
                    dest_path.unlink()  # Delete suspicious file
                    return 'failed'
                
                return 'success'
            
            elif response.status_code == 404:
                return 'not_found'
            
            else:
                if attempt < retry_attempts - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return 'failed'
        
        except requests.Timeout:
            if attempt < retry_attempts - 1:
                time.sleep(2)
                continue
            return 'timeout'
        
        except Exception as e:
            if attempt < retry_attempts - 1:
                time.sleep(2)
                continue
            return 'failed'
    
    return 'failed'

def download_all_pdfs(df):
    """Download all PDFs from the dataframe"""
    
    print("\n" + "="*70)
    print("Downloading PDFs")
    print("="*70)
    
    total = len(df)
    stats = {
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'not_found': 0,
        'timeout': 0
    }
    
    failed_downloads = []
    
    print(f"\n📥 Starting download of {total} PDFs...")
    print("   This may take 15-45 minutes depending on file sizes and network speed\n")
    
    # Progress bar
    for idx, row in tqdm(df.iterrows(), total=total, desc="Downloading", unit="file"):
        date = row['Date']
        filename = row['Filename']
        url = row['Download Url']
        
        # Get year for directory
        year = get_year_from_date(date)
        year_dir = BASE_DIR / str(year)
        
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        dest_path = year_dir / safe_filename
        
        # Download
        result = download_pdf(url, dest_path, RETRY_ATTEMPTS)
        stats[result] += 1
        
        if result == 'failed' or result == 'not_found' or result == 'timeout':
            failed_downloads.append({
                'Filename': filename,
                'URL': url,
                'Reason': result
            })
        
        # Small delay between downloads
        time.sleep(DELAY_BETWEEN_DOWNLOADS)
    
    # Summary
    print("\n" + "="*70)
    print("Download Summary")
    print("="*70)
    print(f"✅ Successfully downloaded:  {stats['success']:4d}")
    print(f"⚠️  Already existed (skipped): {stats['skipped']:4d}")
    print(f"❌ Failed:                   {stats['failed']:4d}")
    print(f"🔍 Not found (404):          {stats['not_found']:4d}")
    print(f"⏱️  Timeout:                  {stats['timeout']:4d}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📊 Total available:          {stats['success'] + stats['skipped']:4d}")
    
    # Save failed downloads log
    if failed_downloads:
        failed_df = pd.DataFrame(failed_downloads)
        failed_df.to_csv('failed_downloads.csv', index=False)
        print(f"\n⚠️  Failed downloads saved to: failed_downloads.csv")
        print(f"   You can manually download these {len(failed_downloads)} files later")
    
    return stats

def main():
    print("="*70)
    print("Download 500 PDFs from Selected Reports")
    print("="*70)
    
    # Check if CSV exists
    if not os.path.exists(INPUT_CSV):
        print(f"\n❌ Error: {INPUT_CSV} not found!")
        print("   Run: python select_500_reports.py first")
        return
    
    # Load CSV
    print(f"\n📂 Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"✓ Loaded {len(df)} reports")
    
    # Verify required columns
    if 'Download Url' not in df.columns:
        print("❌ Error: 'Download Url' column not found in CSV")
        return
    
    # Show breakdown by year
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    year_counts = df['Year'].value_counts().sort_index()
    
    print("\n📊 Reports by year:")
    for year, count in year_counts.items():
        print(f"  {year}: {count} reports")
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories(df)
    
    # Confirm before downloading
    print("\n⚠️  This will download ~500 PDFs (~2-3 GB total)")
    print(f"   Destination: {BASE_DIR}/")
    response = input("\n📥 Proceed with download? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Download all PDFs
    stats = download_all_pdfs(df)
    
    # Final message
    total_available = stats['success'] + stats['skipped']
    
    if total_available >= 450:  # At least 90% success
        print("\n" + "="*70)
        print("🎉 Download Complete!")
        print("="*70)
        print(f"\n✅ You now have {total_available} PDFs ready for processing")
        
        print("\n📝 Next steps:")
        print("1. Set your API keys:")
        print("   $env:OPENAI_API_KEY=\"sk-your-key\"")
        print("   $env:GOOGLE_API_KEY=\"your-key\"")
        print("\n2. Install dependencies:")
        print("   pip install -r code/requirements.txt")
        print("\n3. Run preprocessing:")
        print("   python code/preprocessPdf_Submission.py")
    else:
        print("\n⚠️  Warning: Only {total_available} PDFs downloaded successfully")
        print("   You may need to manually download the failed ones")
        print("   Check failed_downloads.csv for details")

if __name__ == "__main__":
    main()

