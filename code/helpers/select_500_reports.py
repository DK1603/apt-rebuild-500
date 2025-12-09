"""
Select 500 Reports from 1509 Total Reports
Strategy: Evenly distributed across years to avoid cherry-picking
"""

import pandas as pd
from collections import Counter
import random

# Configuration
INPUT_CSV = "code/Technical_Report_Collection.csv"
OUTPUT_CSV = "ArticlesDataset_underScope2.csv"
TARGET_COUNT = 500
RANDOM_SEED = 42  # For reproducibility

def select_stratified_sample(df, target_count, random_seed=42):
    """
    Select samples evenly distributed across years
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Extract year from date
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    
    # Count reports per year
    year_counts = df['Year'].value_counts().sort_index()
    
    print("\n📊 Original Distribution:")
    print("="*50)
    for year, count in year_counts.items():
        print(f"  {year}: {count:4d} reports")
    print(f"  {'Total'}: {len(df):4d} reports")
    
    # Calculate how many to sample from each year (proportional)
    samples_per_year = {}
    total_reports = len(df)
    
    for year, count in year_counts.items():
        # Proportional sampling
        proportion = count / total_reports
        samples = round(proportion * target_count)
        samples_per_year[year] = min(samples, count)  # Can't sample more than available
    
    # Adjust if total doesn't equal target (due to rounding)
    total_samples = sum(samples_per_year.values())
    if total_samples < target_count:
        # Add missing samples to years with most reports
        diff = target_count - total_samples
        sorted_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)
        for year, count in sorted_years:
            if diff == 0:
                break
            if samples_per_year[year] < count:
                samples_per_year[year] += 1
                diff -= 1
    
    elif total_samples > target_count:
        # Remove extra samples from years with most samples
        diff = total_samples - target_count
        sorted_years = sorted(samples_per_year.items(), key=lambda x: x[1], reverse=True)
        for year, _ in sorted_years:
            if diff == 0:
                break
            if samples_per_year[year] > 1:
                samples_per_year[year] -= 1
                diff -= 1
    
    print("\n🎯 Target Distribution (Proportional Sampling):")
    print("="*50)
    for year in sorted(samples_per_year.keys()):
        print(f"  {year}: {samples_per_year[year]:4d} reports")
    print(f"  {'Total'}: {sum(samples_per_year.values()):4d} reports")
    
    # Sample from each year
    selected_samples = []
    
    for year, n_samples in samples_per_year.items():
        year_data = df[df['Year'] == year]
        
        # Random sample without replacement
        sampled = year_data.sample(n=n_samples, random_state=random_seed + year)
        selected_samples.append(sampled)
    
    # Combine all samples
    result_df = pd.concat(selected_samples, ignore_index=True)
    
    # Sort by date
    result_df = result_df.sort_values('Date').reset_index(drop=True)
    
    # Drop the temporary Year column
    result_df = result_df.drop('Year', axis=1)
    
    return result_df

def main():
    print("="*70)
    print("Select 500 Reports from 1509 (Stratified Sampling)")
    print("="*70)
    
    # Load the full dataset
    print(f"\n📂 Loading: {INPUT_CSV}")
    
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"❌ Error: {INPUT_CSV} not found!")
        return
    
    print(f"✓ Loaded {len(df)} reports")
    
    # Verify columns
    required_cols = ['Date', 'Filename', 'Download Url']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"❌ Missing required columns: {missing_cols}")
        print(f"   Available columns: {list(df.columns)}")
        return
    
    # Select 500 reports (stratified by year)
    print(f"\n🎲 Selecting {TARGET_COUNT} reports (stratified sampling)...")
    selected_df = select_stratified_sample(df, TARGET_COUNT, RANDOM_SEED)
    
    # Verify selection
    print(f"\n✓ Selected {len(selected_df)} reports")
    
    # Save to output CSV
    print(f"\n💾 Saving to: {OUTPUT_CSV}")
    selected_df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "="*70)
    print("✅ Success!")
    print("="*70)
    print(f"\n📄 Output file: {OUTPUT_CSV}")
    print(f"   Contains {len(selected_df)} reports evenly distributed across years")
    
    # Show sample
    print("\n📋 Sample of selected reports:")
    print(selected_df[['Date', 'Filename']].head(5).to_string(index=False))
    print("   ...")
    
    print("\n📝 Next step:")
    print(f"   Run: python download_500_pdfs.py")
    print(f"   This will download all {TARGET_COUNT} PDFs from the URLs")

if __name__ == "__main__":
    main()

