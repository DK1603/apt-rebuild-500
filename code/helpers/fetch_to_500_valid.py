"""
Fetch Additional Valid PDFs to Reach 500 Total
Downloads and validates PDFs in real-time, continues until 500 valid PDFs
"""

import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time
from PyPDF2 import PdfReader
import random

# Configuration
FULL_CSV = "code/Technical_Report_Collection.csv"
CURRENT_VALID_CSV = "ArticlesDataset_Valid.csv"
OUTPUT_CSV = "ArticlesDataset_500_Valid.csv"
BASE_DIR = Path("Reports/APT_CyberCriminal_Campagin_Collections Reports")
TARGET_COUNT = 500
MIN_SIZE_KB = 50
TIMEOUT = 60
RANDOM_SEED = 42

def check_pdf_valid(pdf_path):
    """Validate PDF file"""
    try:
        if not pdf_path.exists():
            return False, "Not found"
        
        file_size_kb = pdf_path.stat().st_size / 1024
        
        if file_size_kb < MIN_SIZE_KB:
            return False, f"Too small ({file_size_kb:.1f} KB)"
        
        reader = PdfReader(str(pdf_path))
        if len(reader.pages) == 0:
            return False, "Zero pages"
        
        # Try to read first page
        reader.pages[0].extract_text()
        
        return True, "Valid"
    
    except Exception as e:
        return False, f"Error: {str(e)[:30]}"

def sanitize_filename(filename):
    """Clean filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    return filename

def download_and_validate(url, dest_path):
    """
    Download PDF and immediately validate
    Returns: (success, is_valid, message)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True)
        
        if response.status_code == 404:
            return False, False, "404 Not Found"
        
        if response.status_code != 200:
            return False, False, f"HTTP {response.status_code}"
        
        # Download file
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Immediately validate
        is_valid, msg = check_pdf_valid(dest_path)
        
        if not is_valid:
            # Delete invalid file
            if dest_path.exists():
                dest_path.unlink()
            return True, False, msg
        
        return True, True, "Valid"
    
    except requests.Timeout:
        return False, False, "Timeout"
    except Exception as e:
        return False, False, f"Error: {str(e)[:30]}"

def main():
    print("="*70)
    print("Fetch Additional Valid PDFs to Reach 500 Total")
    print("="*70)
    
    # Load current valid PDFs
    print(f"\n📂 Loading current valid dataset...")
    df_current = pd.read_csv(CURRENT_VALID_CSV)
    current_count = len(df_current)
    print(f"   ✓ Currently have: {current_count} valid PDFs")
    
    needed = TARGET_COUNT - current_count
    print(f"   ⚠️  Need: {needed} more valid PDFs")
    
    if needed <= 0:
        print(f"\n✅ Already have {current_count} valid PDFs!")
        return
    
    # Load full dataset
    print(f"\n📂 Loading full dataset...")
    df_full = pd.read_csv(FULL_CSV)
    print(f"   ✓ Full dataset: {len(df_full)} reports")
    
    # Exclude already selected files
    print(f"\n🔍 Filtering out already selected reports...")
    current_filenames = set(df_current['Filename'].values)
    df_available = df_full[~df_full['Filename'].isin(current_filenames)].copy()
    print(f"   ✓ Available: {len(df_available)} reports")
    
    # Calculate how many we need per year (proportional)
    df_available['Date'] = pd.to_datetime(df_available['Date'])
    df_available['Year'] = df_available['Date'].dt.year
    
    df_current['Date'] = pd.to_datetime(df_current['Date'])
    df_current['Year'] = df_current['Date'].dt.year
    
    print(f"\n📊 Current distribution:")
    current_year_counts = df_current['Year'].value_counts().sort_index()
    for year, count in current_year_counts.items():
        print(f"   {year}: {count}")
    
    # We'll select MORE than needed (2x) to account for failures
    # Then download and validate until we reach target
    select_count = needed * 3  # Select 3x to account for ~67% failure rate
    
    print(f"\n🎲 Selecting {select_count} candidate reports (stratified)...")
    
    # Stratified sampling from available
    random.seed(RANDOM_SEED)
    
    # Calculate proportions from available data
    year_counts = df_available['Year'].value_counts().sort_index()
    samples_per_year = {}
    
    for year, count in year_counts.items():
        proportion = count / len(df_available)
        samples = min(int(proportion * select_count), count)
        samples_per_year[year] = samples
    
    # Sample from each year
    selected_samples = []
    for year, n_samples in samples_per_year.items():
        year_data = df_available[df_available['Year'] == year]
        sampled = year_data.sample(n=n_samples, random_state=RANDOM_SEED + year)
        selected_samples.append(sampled)
    
    df_candidates = pd.concat(selected_samples, ignore_index=True)
    df_candidates = df_candidates.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)  # Shuffle
    
    print(f"   ✓ Selected {len(df_candidates)} candidates")
    
    # Download and validate candidates
    print(f"\n📥 Downloading and validating candidates...")
    print(f"   Target: {needed} more valid PDFs")
    print(f"   This will stop automatically when target is reached\n")
    
    valid_reports = []
    stats = {'downloaded': 0, 'valid': 0, 'invalid': 0, 'failed': 0}
    
    with tqdm(total=needed, desc="Valid PDFs collected", unit="valid") as pbar:
        for idx, row in df_candidates.iterrows():
            if len(valid_reports) >= needed:
                break
            
            filename = row['Filename']
            url = row['Download Url']
            date = row['Date']
            year = pd.to_datetime(date).year
            
            # Prepare destination
            year_dir = BASE_DIR / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            safe_filename = sanitize_filename(filename)
            dest_path = year_dir / safe_filename
            
            # Skip if already exists and valid
            if dest_path.exists():
                is_valid, msg = check_pdf_valid(dest_path)
                if is_valid:
                    valid_reports.append(row)
                    stats['valid'] += 1
                    pbar.update(1)
                    continue
            
            # Download and validate
            downloaded, is_valid, msg = download_and_validate(url, dest_path)
            
            if downloaded:
                stats['downloaded'] += 1
                if is_valid:
                    valid_reports.append(row)
                    stats['valid'] += 1
                    pbar.update(1)
                else:
                    stats['invalid'] += 1
            else:
                stats['failed'] += 1
            
            time.sleep(0.3)  # Be nice to servers
    
    print(f"\n📊 Download Statistics:")
    print(f"   Downloaded: {stats['downloaded']}")
    print(f"   Valid: {stats['valid']}")
    print(f"   Invalid: {stats['invalid']}")
    print(f"   Failed: {stats['failed']}")
    
    # Combine with current valid PDFs
    if len(valid_reports) > 0:
        df_new_valid = pd.DataFrame(valid_reports)
        df_new_valid = df_new_valid.drop('Year', axis=1, errors='ignore')
        
        # Combine with existing
        df_final = pd.concat([df_current, df_new_valid], ignore_index=True)
        df_final = df_final.sort_values('Date').reset_index(drop=True)
        
        # Save final dataset
        df_final.to_csv(OUTPUT_CSV, index=False)
        
        print(f"\n💾 Saved: {OUTPUT_CSV}")
        print(f"   Total valid PDFs: {len(df_final)}")
        
        # Show final distribution
        print(f"\n📊 Final distribution by year:")
        df_final['Year'] = pd.to_datetime(df_final['Date']).dt.year
        final_counts = df_final['Year'].value_counts().sort_index()
        
        for year, count in final_counts.items():
            added = count - current_year_counts.get(year, 0)
            print(f"   {year}: {count} (+{added})")
        
        print(f"\n" + "="*70)
        if len(df_final) >= TARGET_COUNT:
            print(f"✅ SUCCESS! You now have {len(df_final)} valid PDFs")
        else:
            print(f"⚠️  Reached {len(df_final)} valid PDFs (target: {TARGET_COUNT})")
            print(f"   Remaining candidates exhausted.")
            print(f"   You can:")
            print(f"   1. Use {len(df_final)} PDFs (still a good sample size)")
            print(f"   2. Re-run this script (it will try more candidates)")
        
        print(f"\n📝 Next step:")
        print(f"   Update preprocessPdf_Submission.py:")
        print(f"   CSV_FILE = '{OUTPUT_CSV}'")
        print("="*70)
    
    else:
        print("\n❌ No valid PDFs could be downloaded from candidates")
        print("   Current dataset remains at {current_count} PDFs")

if __name__ == "__main__":
    main()

