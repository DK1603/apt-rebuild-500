# Code to reproduce the overtime changes of APT target sectors
# This figure corresponds to Figure 5(a) in the paper 
# Section 4.1: Target Sectors

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

INPUT_CSV = '../../ArticlesDataset_LLMAnswered.csv'
OUTPUT_PDF = 'Figure5a_TargetSectorChanges.pdf' 

'''
Function to process the original data and filter to the target sectors
Count the number of attacks per year for each target sector
'''
def process_filter_data(input_csv, col):
    # ------------------------------
    # Load and Prepare Data
    # ------------------------------
    df = pd.read_csv(input_csv)

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year

    # ------------------------------
    # Process the column
    # ------------------------------
    results = []
    df_filtered = df.dropna(subset=[col]).copy()
    # Handle multi-line format with markdown-style formatting
    # Extract sector names from lines like "*   **Sector Name:** ..."
    # Also handles simple comma-separated format
    def extract_sectors(text):
        if pd.isna(text) or text == '' or str(text).strip() == '':
            return []
        text_str = str(text).strip()
        sectors = []
        
        # First, try to extract from markdown format (lines with **)
        if '**' in text_str:
            for line in text_str.split('\n'):
                line = line.strip()
                if '**' in line:
                    # Extract text between ** markers
                    parts = line.split('**')
                    if len(parts) >= 2:
                        sector = parts[1].strip().rstrip(':')
                        if sector and sector not in sectors:
                            sectors.append(sector)
        
        # If no markdown format found or found some, also try comma-separated
        if not sectors or (len(sectors) == 0):
            # Try comma-separated format
            for sector in text_str.split(','):
                sector = sector.strip().rstrip('.')
                if sector and sector not in sectors:
                    sectors.append(sector)
        
        return sectors
    
    df_filtered[col] = df_filtered[col].apply(extract_sectors)
    df_exploded = df_filtered.explode(col)
    
    grouped = df_exploded.groupby(['Year', col]).size().reset_index(name='Attacks')
    grouped['Column'] = col.replace(' ', '')
    grouped = grouped.rename(columns={col: 'Subcategory'})
    results.append(grouped)

    # Combine all results into a single DataFrame
    final_df = pd.concat(results, ignore_index=True)

    return final_df

# Function to draw the figure
def draw_figure(input_df):
    df = input_df

    # ------------------------------
    # Filter for the "Target Sector"
    # ------------------------------
    sector_df = df[df['Column'] == 'TargetSector'].reset_index(drop=True)
    sector_df['Subcategory'] = sector_df['Subcategory'].str.strip().str.title()

    target_sector_mapping = {
        'Government And Defense Agencies': 'Government/Defense',
        'Corporations And Businesses': 'Corporation/Business',
        'Financial Institutions': 'Financial',
        'Healthcare': 'Healthcare',
        'Energy And Utilities': 'Energy/Utility',
        'Cloud/Iot Services': 'Cloud/IoT',
        'Manufacturing': 'Manufacturing',
        'Education And Research Institutions': 'Education/Research',
        'Media And Entertainment Companies': 'Media/Entertainment',
        'Critical Infrastructure': 'Critical',
        'Non-Governmental Organizations (Ngos) And Nonprofits': 'NGO/Nonprofit',
        'Individuals': 'Individual',
        # Map sub-sectors to main categories
        'Aerospace': 'Government/Defense',  # Aerospace is typically defense-related
        'Defense': 'Government/Defense',
        'Aviation': 'Manufacturing',  # Aviation manufacturing
        'Aircraft Services': 'Corporation/Business',
    }
    sector_df['Subcategory'] = sector_df['Subcategory'].replace(target_sector_mapping)
    
    # If there are still unmapped sectors, map them to the closest category or drop them
    # First, let's see what's left unmapped
    unmapped = sector_df[~sector_df['Subcategory'].isin(target_sector_mapping.values())]['Subcategory'].unique()
    if len(unmapped) > 0:
        print(f"[WARNING] Found unmapped sectors: {unmapped}")
        # For now, we'll map common patterns
        additional_mappings = {}
        for sector in unmapped:
            sector_lower = sector.lower()
            if 'government' in sector_lower or 'defense' in sector_lower or 'military' in sector_lower:
                additional_mappings[sector] = 'Government/Defense'
            elif 'financial' in sector_lower or 'bank' in sector_lower:
                additional_mappings[sector] = 'Financial'
            elif 'health' in sector_lower or 'medical' in sector_lower:
                additional_mappings[sector] = 'Healthcare'
            elif 'energy' in sector_lower or 'utility' in sector_lower:
                additional_mappings[sector] = 'Energy/Utility'
            elif 'education' in sector_lower or 'research' in sector_lower or 'university' in sector_lower:
                additional_mappings[sector] = 'Education/Research'
            elif 'manufacturing' in sector_lower or 'industrial' in sector_lower:
                additional_mappings[sector] = 'Manufacturing'
            elif 'media' in sector_lower or 'entertainment' in sector_lower:
                additional_mappings[sector] = 'Media/Entertainment'
            elif 'individual' in sector_lower or 'person' in sector_lower:
                additional_mappings[sector] = 'Individual'
            elif 'ngo' in sector_lower or 'nonprofit' in sector_lower or 'non-profit' in sector_lower:
                additional_mappings[sector] = 'NGO/Nonprofit'
            elif 'critical' in sector_lower or 'infrastructure' in sector_lower:
                additional_mappings[sector] = 'Critical'
            elif 'cloud' in sector_lower or 'iot' in sector_lower:
                additional_mappings[sector] = 'Cloud/IoT'
            elif 'corporation' in sector_lower or 'business' in sector_lower or 'company' in sector_lower:
                additional_mappings[sector] = 'Corporation/Business'
        
        if additional_mappings:
            print(f"[INFO] Auto-mapping {len(additional_mappings)} sectors: {additional_mappings}")
            sector_df['Subcategory'] = sector_df['Subcategory'].replace(additional_mappings)
        
        # Drop any remaining unmapped sectors (they're likely noise or sub-categories)
        # Valid categories are the values in target_sector_mapping
        valid_categories = set(target_sector_mapping.values())
        remaining_unmapped = sector_df[~sector_df['Subcategory'].isin(valid_categories)]['Subcategory'].unique()
        if len(remaining_unmapped) > 0:
            print(f"[INFO] Dropping {len(remaining_unmapped)} unmapped sectors: {remaining_unmapped}")
            sector_df = sector_df[sector_df['Subcategory'].isin(valid_categories)]
    
    # Aggregate duplicates: after mapping, we might have multiple rows with same Year-Subcategory
    # Sum up the attacks for each Year-Subcategory combination
    sector_df = sector_df.groupby(['Year', 'Subcategory'])['Attacks'].sum().reset_index()
    
    pivot_df = sector_df.pivot(index='Year', columns='Subcategory', values='Attacks').fillna(0)

    # ------------------------------
    # Reorder the columns to place 
    # the top 3 at the bottom
    # ------------------------------
    total_attacks = pivot_df.sum(axis=0).sort_values(ascending=False)
    top_three_sectors = total_attacks.head(3).index
    remaining_sectors = total_attacks.index.difference(top_three_sectors)
    ordered_columns = top_three_sectors.tolist() + remaining_sectors.tolist()
    pivot_df = pivot_df[ordered_columns]

    # ------------------------------
    # Set the color palette for each target sector
    # ------------------------------
    full_tab20 = sns.color_palette("tab20", 20)

    color_map = {
        'Government/Defense': full_tab20[0],
        'Corporation/Business': full_tab20[2],
        'Education/Research': full_tab20[4],
        'Cloud/IoT': full_tab20[5],
        'Critical': full_tab20[9],
        'Energy/Utility': full_tab20[8],
        'Financial': full_tab20[6],     
        'Healthcare': full_tab20[7],
        'Individual': full_tab20[10],
        'Manufacturing': full_tab20[11],
        'Media/Entertainment': full_tab20[14],
        'NGO/Nonprofit': full_tab20[15] 
    }

    # Handle missing sectors gracefully - use a default color if not in map
    default_color = (0.5, 0.5, 0.5)  # Gray for unmapped sectors
    colors = [color_map.get(sector, default_color) for sector in pivot_df.columns]
    
    # Warn about any missing sectors
    missing_sectors = [sector for sector in pivot_df.columns if sector not in color_map]
    if missing_sectors:
        print(f"[WARNING] Sectors not in color_map (using gray): {missing_sectors}")

    # ------------------------------
    # Create the stacked bar plot
    # ------------------------------
    pivot_df.plot(
        kind='bar',
        stacked=True,
        figsize=(30, 17),
        color=colors
    )

    plt.xlabel('Year', fontsize=56, fontweight='bold')
    plt.ylabel('Number of Target Sectors', fontsize=56, fontweight='bold')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.xticks(rotation=0, fontweight='bold')
    plt.yticks(ticks=range(0, 151, 30), fontweight='bold')

    # Add a legend below the plot
    legend = plt.legend(
        bbox_to_anchor=(0.5, -0.4),
        loc='center',
        fontsize=45,
        frameon=False, 
        ncol=3
    )
    for text in legend.get_texts():
        text.set_fontweight('bold')

    # Make axis lines more bold
    ax = plt.gca()

    attacks_per_year = pivot_df.sum(axis=1).tolist()

    # Loop through each bar (year)
    for i, (index, row) in enumerate(pivot_df.iterrows()):
        cumulative_bottom = 0  # Start at the bottom of the bar
        
        # Determine top 3 sectors for this year
        top3_this_year = row.sort_values(ascending=False).head(3).index

        for category in pivot_df.columns:
            height = row[category]
            if category in top3_this_year and height > 0:
                x_pos = i
                y_pos = cumulative_bottom + height / 2

                ax.text(
                    x_pos,
                    y_pos,
                    f"{(height / attacks_per_year[i]) * 100:.0f}%",
                    ha='center',
                    va='center',
                    fontsize=40,
                    fontweight='bold',
                    color='white'
                )
            cumulative_bottom += height

    for spine in ax.spines.values():
        spine.set_linewidth(3) 
        spine.set_color('black')  

    ax.tick_params(
        axis='both',
        length=10,
        width=2,
        pad=10,
        labelsize=52,
        direction='out'
    )

    # Grid and spines
    ax.set_axisbelow(True)
    ax.grid(True, linestyle='--', axis='y', linewidth=3)
    ax.xaxis.grid(False)

    # Add bold black border to entire plot
    ax.patch.set_edgecolor('black')
    ax.set_axisbelow(True)
    
    # Save the plot as a PDF
    plt.tight_layout()
    plt.savefig(OUTPUT_PDF, format='pdf')
    print(f"[✓] Figure 5(a) saved to {OUTPUT_PDF}")

if __name__ == "__main__":
    final_df = process_filter_data(INPUT_CSV, 'Target Sector')
    draw_figure(final_df)