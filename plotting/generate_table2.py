"""
Generate Table 2: Statistics on collection of technical reports (TRs) and news articles on APTs
Shows distribution by year and source categories
"""

import pandas as pd
import numpy as np
import re

# File paths
ORIGINAL_FILE = 'code/Technical_Report_Collection.csv'
SAMPLE_FILE = 'code/ArticlesDataset_500_Valid.csv'

def categorize_source(url, filename):
    """
    Categorize sources into 3 groups based on URL and filename
    TR#1: Major security vendors (FireEye, CrowdStrike, Symantec, Kaspersky, etc.)
    TR#2: Research organizations, CERTs, and government sources
    TR#3: Other sources (blogs, news, GitHub collection, etc.)
    """
    if pd.isna(url) or url == '':
        return 'TR#3'
    
    url_str = str(url).lower()
    filename_str = str(filename).lower() if pd.notna(filename) else ''
    combined_str = f"{url_str} {filename_str}"
    
    # TR#1: Major security vendors
    major_vendors = ['fireeye', 'crowdstrike', 'symantec', 'kaspersky', 'securelist', 
                     'trendmicro', 'proofpoint', 'mandiant', 'paloalto', 'cylance',
                     'bitdefender', 'eset', 'f-secure', 'mcafee', 'sophos', 'zscaler',
                     'intezer', 'secureworks', 'recordedfuture', 'threatconnect']
    
    if any(vendor in combined_str for vendor in major_vendors):
        return 'TR#1'
    
    # TR#2: Research organizations, CERTs, government sources, and Box.com
    if 'app.box.com' in url_str or 'box.com' in url_str:
        return 'TR#2'
    
    # Research organizations and academic sources
    research_orgs = ['citizenlab', 'crysys', 'circl', 'cert', 'ics-cert', 'cisa',
                    'ncsc', 'jpcert', 'ahnlab', 'asec', 'kaspersky-ics-cert',
                    'welivesecurity', 'talos', 'unit42', 'cta-', 'mar-', 'ta-']
    
    if any(org in combined_str for org in research_orgs):
        return 'TR#2'
    
    # TR#3: All other sources (blogs, news, GitHub collection, etc.)
    return 'TR#3'

def load_and_analyze_data():
    """Load both datasets and analyze distribution"""
    
    # Load original dataset (1509 reports)
    df_original = pd.read_csv(ORIGINAL_FILE)
    df_original['Year'] = pd.to_datetime(df_original['Date']).dt.year
    df_original['Source_Category'] = df_original.apply(
        lambda row: categorize_source(row['Download Url'], row['Filename']), axis=1
    )
    
    # Load sample dataset (477 reports)
    df_sample = pd.read_csv(SAMPLE_FILE)
    df_sample['Year'] = pd.to_datetime(df_sample['Date']).dt.year
    df_sample['Source_Category'] = df_sample.apply(
        lambda row: categorize_source(row['Download Url'], row['Filename']), axis=1
    )
    
    return df_original, df_sample

def generate_table2(df_original, df_sample):
    """Generate Table 2 with statistics by year"""
    
    years = range(2014, 2024)
    table_rows = []
    
    # Count unique sources per category (for the [N] notation)
    original_sources_tr1 = df_original[df_original['Source_Category'] == 'TR#1']['Download Url'].nunique()
    original_sources_tr2 = df_original[df_original['Source_Category'] == 'TR#2']['Download Url'].nunique()
    original_sources_tr3 = df_original[df_original['Source_Category'] == 'TR#3']['Download Url'].nunique()
    
    # Process each year
    for year in years:
        # Original dataset counts
        orig_year = df_original[df_original['Year'] == year]
        orig_tr1 = len(orig_year[orig_year['Source_Category'] == 'TR#1'])
        orig_tr2 = len(orig_year[orig_year['Source_Category'] == 'TR#2'])
        orig_tr3 = len(orig_year[orig_year['Source_Category'] == 'TR#3'])
        orig_total = len(orig_year)
        
        # Sample dataset counts
        sample_year = df_sample[df_sample['Year'] == year]
        sample_tr1 = len(sample_year[sample_year['Source_Category'] == 'TR#1'])
        sample_tr2 = len(sample_year[sample_year['Source_Category'] == 'TR#2'])
        sample_tr3 = len(sample_year[sample_year['Source_Category'] == 'TR#3'])
        sample_total = len(sample_year)
        
        # Format: sample_total (original_total)
        all_trs = f"{sample_total} ({orig_total})"
        
        table_rows.append({
            'Year': year,
            'TR#1': sample_tr1,
            'TR#2': sample_tr2,
            'TR#3': sample_tr3,
            'All_TRs': all_trs,
            'News_Articles': 0  # Will be 0 or can be added if you have news articles
        })
    
    # Calculate totals
    total_orig_tr1 = len(df_original[df_original['Source_Category'] == 'TR#1'])
    total_orig_tr2 = len(df_original[df_original['Source_Category'] == 'TR#2'])
    total_orig_tr3 = len(df_original[df_original['Source_Category'] == 'TR#3'])
    total_orig = len(df_original)
    
    total_sample_tr1 = len(df_sample[df_sample['Source_Category'] == 'TR#1'])
    total_sample_tr2 = len(df_sample[df_sample['Source_Category'] == 'TR#2'])
    total_sample_tr3 = len(df_sample[df_sample['Source_Category'] == 'TR#3'])
    total_sample = len(df_sample)
    
    table_rows.append({
        'Year': 'Total',
        'TR#1': total_sample_tr1,
        'TR#2': total_sample_tr2,
        'TR#3': total_sample_tr3,
        'All_TRs': f"{total_sample} ({total_orig})",
        'News_Articles': 0
    })
    
    return table_rows, original_sources_tr1, original_sources_tr2, original_sources_tr3

def print_table2(table_rows, sources_tr1, sources_tr2, sources_tr3):
    """Print Table 2 in formatted text output"""
    
    print("\n" + "="*100)
    print("Table 2: Statistics on our collection of technical reports (TRs) and news articles on APTs")
    print("="*100)
    print()
    print("Out of 1,509 original TRs, we sampled 477 unique TRs for analysis.")
    print("The numbers in parentheses indicate the original count before sampling.")
    print()
    
    # Column widths
    col_widths = [8, 12, 12, 12, 20, 15]
    
    # Print header
    header = ['Year', f'TR#1 [{sources_tr1}]', f'TR#2 [{sources_tr2}]', 
              f'TR#3 [{sources_tr3}]', 'All TRs', 'News Articles']
    
    print(f"{header[0]:<{col_widths[0]}}", end="")
    print(f"{header[1]:<{col_widths[1]}}", end="")
    print(f"{header[2]:<{col_widths[2]}}", end="")
    print(f"{header[3]:<{col_widths[3]}}", end="")
    print(f"{header[4]:<{col_widths[4]}}", end="")
    print(f"{header[5]:<{col_widths[5]}}")
    print("-" * 100)
    
    # Print data rows
    for row in table_rows:
        year_str = str(row['Year'])
        print(f"{year_str:<{col_widths[0]}}", end="")
        print(f"{row['TR#1']:>{col_widths[1]-2}}  ", end="")
        print(f"{row['TR#2']:>{col_widths[2]-2}}  ", end="")
        print(f"{row['TR#3']:>{col_widths[3]-2}}  ", end="")
        print(f"{row['All_TRs']:>{col_widths[4]-2}}  ", end="")
        print(f"{row['News_Articles']:>{col_widths[5]-2}}  ")
    
    print("="*100)
    print()

def save_table2_csv(table_rows, sources_tr1, sources_tr2, sources_tr3, output_file='Table2_Statistics.csv'):
    """Save Table 2 as CSV"""
    
    df = pd.DataFrame(table_rows)
    df.columns = ['Year', f'TR#1 [{sources_tr1}]', f'TR#2 [{sources_tr2}]', 
                  f'TR#3 [{sources_tr3}]', 'All TRs', 'News Articles']
    df.to_csv(output_file, index=False)
    print(f"Table 2 saved to: {output_file}")

def main():
    """Main function"""
    print("Loading data...")
    df_original, df_sample = load_and_analyze_data()
    
    print(f"Original dataset: {len(df_original)} reports")
    print(f"Sample dataset: {len(df_sample)} reports")
    
    print("\nGenerating Table 2...")
    table_rows, sources_tr1, sources_tr2, sources_tr3 = generate_table2(df_original, df_sample)
    
    print_table2(table_rows, sources_tr1, sources_tr2, sources_tr3)
    save_table2_csv(table_rows, sources_tr1, sources_tr2, sources_tr3)
    
    print("Done!")

if __name__ == '__main__':
    main()

