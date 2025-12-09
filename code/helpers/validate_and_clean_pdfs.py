"""
Validate Downloaded PDFs and Clean Dataset
Identifies corrupted/invalid PDFs and updates CSV with only valid reports
"""

import os
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm import tqdm

# Configuration
INPUT_CSV = "ArticlesDataset_500_Valid.csv"
OUTPUT_CSV = "ArticlesDataset_500_valid_final.csv"
BASE_DIR = Path("Reports/APT_CyberCriminal_Campagin_Collections Reports")
MIN_SIZE_KB = 50  # Flag files smaller than 50KB as suspicious

def check_pdf_valid(pdf_path):
    """
    Check if PDF is valid and readable
    Returns: (is_valid, file_size_kb, error_message)
    """
    try:
        # Check if file exists
        if not pdf_path.exists():
            return False, 0, "File not found"
        
        # Check file size
        file_size = pdf_path.stat().st_size / 1024  # Convert to KB
        
        if file_size < MIN_SIZE_KB:
            return False, file_size, f"Too small ({file_size:.1f} KB)"
        
        # Try to read the PDF
        try:
            reader = PdfReader(str(pdf_path))
            num_pages = len(reader.pages)
            
            if num_pages == 0:
                return False, file_size, "Zero pages"
            
            # Try to extract text from first page (ensure it's readable)
            first_page = reader.pages[0]
            text = first_page.extract_text()
            
            return True, file_size, None
            
        except Exception as e:
            return False, file_size, f"PDF read error: {str(e)[:50]}"
    
    except Exception as e:
        return False, 0, f"System error: {str(e)[:50]}"

def sanitize_filename(filename):
    """Clean filename to be filesystem-safe"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    return filename

def main():
    print("="*70)
    print("PDF Validation and Dataset Cleaning")
    print("="*70)
    
    # Load CSV
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found!")
        return
    
    print(f"\n📂 Loading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"✓ Loaded {len(df)} reports")
    
    # Prepare validation results
    validation_results = []
    
    print("\n🔍 Validating PDFs...")
    print("   This may take a few minutes...\n")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Validating", unit="file"):
        date = row['Date']
        filename = row['Filename']
        
        # Get year for directory
        year = pd.to_datetime(date).year
        year_dir = BASE_DIR / str(year)
        
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        pdf_path = year_dir / safe_filename
        
        # Check if valid
        is_valid, file_size, error_msg = check_pdf_valid(pdf_path)
        
        validation_results.append({
            'index': idx,
            'filename': filename,
            'year': year,
            'is_valid': is_valid,
            'file_size_kb': file_size,
            'error': error_msg,
            'path': str(pdf_path)
        })
    
    # Create results DataFrame
    results_df = pd.DataFrame(validation_results)
    
    # Statistics
    print("\n" + "="*70)
    print("Validation Results")
    print("="*70)
    
    total_files = len(results_df)
    valid_files = results_df['is_valid'].sum()
    invalid_files = total_files - valid_files
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total reports in CSV: {total_files}")
    print(f"   ✅ Valid PDFs: {valid_files}")
    print(f"   ❌ Invalid/Missing: {invalid_files}")
    print(f"   Success rate: {(valid_files/total_files)*100:.1f}%")
    
    # Breakdown by issue
    if invalid_files > 0:
        print(f"\n⚠️  Invalid Files Breakdown:")
        
        # Group by error type
        invalid_df = results_df[~results_df['is_valid']]
        
        # Count by error type
        error_counts = {}
        for error in invalid_df['error']:
            if 'Too small' in str(error):
                error_type = 'Too small (< 50KB)'
            elif 'not found' in str(error):
                error_type = 'File not found'
            elif 'PDF read error' in str(error):
                error_type = 'Corrupted PDF'
            elif 'Zero pages' in str(error):
                error_type = 'Empty PDF'
            else:
                error_type = 'Other error'
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {error_type}: {count}")
    
    # Year-by-year breakdown
    print(f"\n📅 Valid PDFs by Year:")
    year_stats = results_df.groupby('year').agg({
        'is_valid': ['count', 'sum']
    })
    year_stats.columns = ['Total', 'Valid']
    year_stats['Invalid'] = year_stats['Total'] - year_stats['Valid']
    
    for year, row in year_stats.iterrows():
        print(f"   {year}: {int(row['Valid'])}/{int(row['Total'])} valid ({int(row['Valid'])/int(row['Total'])*100:.1f}%)")
    
    # Create cleaned dataset with only valid PDFs
    valid_indices = results_df[results_df['is_valid']]['index'].tolist()
    df_cleaned = df.iloc[valid_indices].reset_index(drop=True)
    
    # Save cleaned CSV
    print(f"\n💾 Saving cleaned dataset...")
    df_cleaned.to_csv(OUTPUT_CSV, index=False)
    print(f"   ✓ Saved: {OUTPUT_CSV}")
    print(f"   Contains {len(df_cleaned)} valid reports")
    
    # Save invalid files list for reference
    if invalid_files > 0:
        invalid_df = results_df[~results_df['is_valid']][['filename', 'year', 'file_size_kb', 'error']]
        invalid_df.to_csv('invalid_pdfs.csv', index=False)
        print(f"   ✓ Saved invalid list: invalid_pdfs.csv")
    
    # Delete corrupted files (optional)
    print("\n🗑️  Delete Invalid PDFs?")
    print("   This will free up disk space by removing corrupted files")
    response = input("   Delete invalid PDFs? (y/n): ").strip().lower()
    
    if response == 'y':
        deleted_count = 0
        for _, row in results_df[~results_df['is_valid']].iterrows():
            pdf_path = Path(row['path'])
            if pdf_path.exists():
                try:
                    pdf_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️  Could not delete {pdf_path.name}: {e}")
        
        print(f"   ✓ Deleted {deleted_count} invalid files")
    else:
        print("   Keeping invalid files (you can delete manually later)")
    
    # Final summary
    print("\n" + "="*70)
    print("✅ Cleaning Complete!")
    print("="*70)
    
    print(f"\n📄 Use {OUTPUT_CSV} for your analysis")
    print(f"   Contains {len(df_cleaned)} validated, working PDFs")
    
    print(f"\n📝 Next steps:")
    print(f"   1. Use {OUTPUT_CSV} as input for preprocessing")
    print(f"   2. Update preprocessPdf_Submission.py:")
    print(f"      Change: CSV_FILE = 'ArticlesDataset_Valid.csv'")
    print(f"   3. Run: python code/preprocessPdf_Submission.py")
    
    # Check if we still have good distribution
    if len(df_cleaned) >= 450:  # At least 90% of target
        print(f"\n✅ You still have {len(df_cleaned)} reports - excellent sample size!")
    elif len(df_cleaned) >= 400:
        print(f"\n⚠️  You have {len(df_cleaned)} reports - acceptable, but slightly below target")
    else:
        print(f"\n⚠️  Only {len(df_cleaned)} reports - may need to find alternative sources")
    
    print("="*70)

if __name__ == "__main__":
    main()

