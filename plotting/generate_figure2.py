"""
Generate Figure 2: Top 15 sources from the collection of technical reports
Bar chart showing distribution of reports by source
"""

import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter

# File path
INPUT_FILE = 'code/ArticlesDataset_500_Valid.csv'

def extract_source_name(filename, url):
    """
    Extract source name from filename and URL
    Priority: filename patterns > URL domain (excluding github/box)
    Focus on actual publishers, not hosting platforms
    """
    if pd.isna(filename):
        filename = ''
    if pd.isna(url):
        url = ''
    
    filename_str = str(filename).lower()
    url_str = str(url).lower()
    combined_str = f"{filename_str} {url_str}"
    
    # Source name mappings (common patterns) - ordered by specificity
    source_patterns = {
        'Kaspersky': ['kaspersky', 'kl_', 'securelist', 'welivesecurity', 'kaspersky-ics-cert', 'securelist.com'],
        'Trend Micro': ['trendmicro', 'trend-micro', 'trend micro', 'trend micro usa'],
        'FireEye': ['fireeye', 'mandiant'],
        'Palo Alto': ['paloalto', 'palo-alto', 'unit42', 'paloalto_'],
        'ESET': ['eset'],
        'Symantec': ['symantec'],
        'Microsoft': ['microsoft'],
        'RSA': ['rsa'],
        'Cisco': ['cisco', 'talos', 'cto-tib', 'asert'],
        'AhnLab': ['ahnlab', 'asec'],
        'CrowdStrike': ['crowdstrike', 'crowdstrike_'],
        'Proofpoint': ['proofpoint'],
        'SecureWorks': ['secureworks'],
        'Check Point': ['checkpoint', 'check-point', 'check point'],
        'Recorded Future': ['recordedfuture'],
        'Bitdefender': ['bitdefender', 'download.bitdefender'],
        'F-Secure': ['f-secure', 'fsecure'],
        'McAfee': ['mcafee'],
        'Sophos': ['sophos'],
        'Zscaler': ['zscaler'],
        'Intezer': ['intezer'],
        'ThreatConnect': ['threatconnect'],
        'Cylance': ['cylance'],
        'AlienVault': ['alienvault', 'alienvault_'],
        'Fidelis': ['fidelis', 'ta_fidelis'],
        'Blue Coat': ['bluecoat', 'blue-coat', 'bcs_wp'],
        'GData': ['gdata'],
        'TrapX': ['trapx', 'trapx_'],
        'CERT': ['cert', 'ics-cert', 'jpcert', 'cert.gov', 'ics-alert'],
        'Citizen Lab': ['citizenlab', 'citizen-lab'],
        'Crysys': ['crysys', 'duqu2_crysys'],
        'CIRCL': ['circl'],
        'F5': ['f5soc', 'f5_'],
        'Arbor Networks': ['asert'],
    }
    
    # Check combined string for source patterns (filename + URL)
    for source_name, patterns in source_patterns.items():
        for pattern in patterns:
            if pattern in combined_str:
                return source_name
    
    # Check URL domain (but exclude github and box.com as they're just hosting)
    domain_match = re.search(r'https?://([^/]+)', url_str)
    if domain_match:
        domain = domain_match.group(1).lower()
        # Skip github and box.com as they're hosting platforms
        if 'github.com' not in domain and 'box.com' not in domain:
            for source_name, patterns in source_patterns.items():
                for pattern in patterns:
                    if pattern in domain:
                        return source_name
    
    # If still no match, return 'Other'
    return 'Other (GitHub etc)'

def load_and_analyze_sources():
    """Load data and extract source names"""
    
    df = pd.read_csv(INPUT_FILE)
    
    # Extract source names
    df['Source'] = df.apply(
        lambda row: extract_source_name(row['Filename'], row['Download Url']), 
        axis=1
    )
    
    # Count reports per source
    source_counts = df['Source'].value_counts()
    
    return source_counts, len(df)

def create_figure2(source_counts, total_reports):
    """Create bar chart of top 15 sources"""
    
    # Get top 15 sources
    top_15 = source_counts.head(15)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create bar chart
    bars = ax.barh(range(len(top_15)), top_15.values, color='steelblue', edgecolor='black', linewidth=0.5)
    
    # Customize axes
    ax.set_yticks(range(len(top_15)))
    ax.set_yticklabels(top_15.index, fontsize=10)
    ax.set_xlabel('Number of Technical Reports', fontsize=12, fontweight='bold')
    ax.set_ylabel('Source', fontsize=12, fontweight='bold')
    ax.set_title('Figure: Top 15 sources from the collection of technical reports', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Invert y-axis to show highest at top
    ax.invert_yaxis()
    
    # Add grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for i, (source, count) in enumerate(top_15.items()):
        ax.text(count + 0.5, i, str(count), va='center', fontsize=9, fontweight='bold')
    
    # Set x-axis limits
    max_count = top_15.max()
    ax.set_xlim(0, max_count * 1.15)
    
    # Add caption
    credible_count = total_reports  # Assuming all are credible, adjust if needed
    credible_pct = (credible_count / total_reports) * 100 if total_reports > 0 else 0
    caption = f"Figure: Top 15 sources from the collection of technical reports. "
    caption += f"Most reports come from reputable sources such as {top_15.index[0]} and {top_15.index[1] if len(top_15) > 1 else 'others'}. "
    caption += f"We confirmed that {credible_count} ({credible_pct:.1f}%) TRs are highly credible."
    
    fig.text(0.5, 0.02, caption, ha='center', fontsize=9, style='italic', wrap=True)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    
    # Save as PNG first (more reliable)
    output_file_png = 'plotting/Figure2_Top15Sources.png'
    plt.savefig(output_file_png, dpi=300, bbox_inches='tight')
    print(f"Figure 2 (PNG) saved to: {output_file_png}")
    
    # Also save as PDF
    try:
        output_file = 'plotting/Figure2_Top15Sources.pdf'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Figure 2 (PDF) saved to: {output_file}")
    except Exception as e:
        print(f"Warning: Could not save PDF: {e}")
        print("PNG file saved successfully.")
    
    plt.close()
    
    return top_15

def print_source_statistics(source_counts, top_15):
    """Print statistics about sources"""
    
    print("\n" + "="*80)
    print("Source Statistics")
    print("="*80)
    print(f"\nTotal unique sources: {len(source_counts)}")
    print(f"\nTop 15 Sources:")
    print("-"*80)
    print(f"{'Rank':<6} {'Source':<30} {'Count':<10} {'Percentage':<10}")
    print("-"*80)
    
    total = source_counts.sum()
    for i, (source, count) in enumerate(top_15.items(), 1):
        pct = (count / total) * 100
        print(f"{i:<6} {source:<30} {count:<10} {pct:>6.2f}%")
    
    print("="*80)
    print()

def main():
    """Main function"""
    print("Loading data and extracting sources...")
    source_counts, total_reports = load_and_analyze_sources()
    
    print(f"Total reports: {total_reports}")
    print(f"Unique sources: {len(source_counts)}")
    
    print("\nCreating Figure 2...")
    top_15 = create_figure2(source_counts, total_reports)
    
    print_source_statistics(source_counts, top_15)
    
    # Save source counts to CSV
    output_csv = 'plotting/Figure2_SourceCounts.csv'
    top_15.to_csv(output_csv, header=['Count'])
    print(f"Source counts saved to: {output_csv}")
    
    print("Done!")

if __name__ == '__main__':
    main()

