# Code to reproduce the overtime changes of APT attack vectors
# This figure corresponds to Figure 5(b) in the paper 
# Section 4.1: Initial Attack Vectors

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

INPUT_CSV = '../../ArticlesDataset_LLMAnswered.csv'
OUTPUT_PDF = 'Figure5b_AttackVectorChanges.pdf'

'''
Function to process the original data and filter to the attack vectors
Counts the number of attacks per year for each attack vector
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
    # Filter out "Not mentioned" values
    df_filtered = df_filtered[df_filtered[col].astype(str).str.lower() != 'not mentioned']
    
    # Handle comma-separated values, remove trailing periods
    df_filtered[col] = df_filtered[col].astype(str).str.replace('.', '', regex=False)
    df_filtered[col] = df_filtered[col].str.split(',')
    df_filtered[col] = df_filtered[col].apply(lambda items: [item.strip() for item in items if item.strip() and item.strip().lower() != 'not mentioned'])
    df_exploded = df_filtered.explode(col)
    
    # Filter out any remaining "Not mentioned" values after explode
    df_exploded = df_exploded[df_exploded[col].astype(str).str.lower() != 'not mentioned']
    
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
    # Filter for the "Attack Vector"
    # ------------------------------
    vector_df = df[df['Column'] == 'AttackVector'].reset_index(drop=True)
    
    # Filter out "Not mentioned" values
    vector_df = vector_df[vector_df['Subcategory'].astype(str).str.lower() != 'not mentioned']
    
    vector_df['Subcategory'] = vector_df['Subcategory'].str.strip().str.title()

    # Comprehensive mapping for attack vector variations
    attack_vectors_mapping = {
        'Exploit Vulnerability': 'Vulnerability Exploitation',
        'Spearphishing': 'Spear Phishing',  # Handle case variations
        'Spear-Phishing': 'Spear Phishing',
        'Spear Phishing': 'Spear Phishing',
        'Drive-By Download': 'Drive-By Download',
        'Drive By Download': 'Drive-By Download',
        'Driveby Download': 'Drive-By Download',
        'Watering Hole': 'Watering Hole',
        'Wateringhole': 'Watering Hole',
        'Social Engineering': 'Social Engineering',
        'Malicious Documents': 'Malicious Documents',
        'Phishing': 'Phishing',
        'Credential Reuse': 'Credential Reuse',
        'Removable Media': 'Removable Media',
        'Website Equipping': 'Website Equipping',
        'Covert Channels': 'Covert Channels',
        'Meta Data Monitoring': 'Meta Data Monitoring',
        'Metadata Monitoring': 'Meta Data Monitoring',
    }
    vector_df['Subcategory'] = vector_df['Subcategory'].replace(attack_vectors_mapping)
    
    # Handle case-insensitive matching for remaining variations
    # This function extracts the main attack vector category from descriptions
    def normalize_vector_name(name):
        if pd.isna(name):
            return name
        name_str = str(name).strip()
        name_lower = name_str.lower()
        
        # Remove markdown formatting if present
        if '**' in name_str:
            # Extract text between ** markers
            parts = name_str.split('**')
            if len(parts) >= 2:
                name_str = parts[1].strip().rstrip(':')
                name_lower = name_str.lower()
        
        # Extract main category before colon or parenthesis (e.g., "Exploit Vulnerability: SQL injection" -> "Exploit Vulnerability")
        if ':' in name_str:
            name_str = name_str.split(':')[0].strip()
            name_lower = name_str.lower()
        if '(' in name_str:
            name_str = name_str.split('(')[0].strip()
            name_lower = name_str.lower()
        
        # Remove trailing periods and clean up
        name_str = name_str.rstrip('.').strip()
        name_lower = name_str.lower()
        
        # Check for common patterns (order matters - check more specific first)
        if 'spear' in name_lower and 'phish' in name_lower:
            return 'Spear Phishing'
        elif 'drive' in name_lower and ('by' in name_lower or 'by' in name_str) and 'download' in name_lower:
            return 'Drive-By Download'
        elif 'watering' in name_lower and 'hole' in name_lower:
            return 'Watering Hole'
        elif 'exploit' in name_lower and 'vulnerability' in name_lower:
            return 'Vulnerability Exploitation'
        elif 'exploit' in name_lower and ('cve' in name_lower or 'sql' in name_lower or 'injection' in name_lower or 'brute' in name_lower):
            # Specific exploit types should map to Vulnerability Exploitation
            return 'Vulnerability Exploitation'
        elif 'social' in name_lower and 'engineering' in name_lower:
            return 'Social Engineering'
        elif 'malicious' in name_lower and 'document' in name_lower:
            return 'Malicious Documents'
        elif 'phishing' in name_lower:
            return 'Phishing'
        elif 'credential' in name_lower and 'reuse' in name_lower:
            return 'Credential Reuse'
        elif 'removable' in name_lower and 'media' in name_lower:
            return 'Removable Media'
        elif 'website' in name_lower and 'equipping' in name_lower:
            return 'Website Equipping'
        elif 'covert' in name_lower and 'channel' in name_lower:
            return 'Covert Channels'
        elif 'metadata' in name_lower or ('meta' in name_lower and 'data' in name_lower and 'monitoring' in name_lower):
            return 'Meta Data Monitoring'
        
        # If it's a single word or very short, might be a category name itself
        # Check if it matches any of our standard categories (case-insensitive)
        standard_categories_map = {
            'spear phishing': 'Spear Phishing',
            'drive-by download': 'Drive-By Download',
            'drive by download': 'Drive-By Download',
            'watering hole': 'Watering Hole',
            'vulnerability exploitation': 'Vulnerability Exploitation',
            'exploit vulnerability': 'Vulnerability Exploitation',
            'social engineering': 'Social Engineering',
            'malicious documents': 'Malicious Documents',
            'phishing': 'Phishing',
            'credential reuse': 'Credential Reuse',
            'removable media': 'Removable Media',
            'website equipping': 'Website Equipping',
            'covert channels': 'Covert Channels',
            'meta data monitoring': 'Meta Data Monitoring',
            'metadata monitoring': 'Meta Data Monitoring'
        }
        
        # Normalize the name for comparison (remove hyphens, underscores, extra spaces)
        name_normalized = ' '.join(name_lower.replace('-', ' ').replace('_', ' ').split())
        
        for cat_key, cat_value in standard_categories_map.items():
            cat_normalized = ' '.join(cat_key.replace('-', ' ').replace('_', ' ').split())
            # Exact match or name starts with category (e.g., "Phishing (via spam)" starts with "Phishing")
            if name_normalized == cat_normalized or name_normalized.startswith(cat_normalized + ' '):
                return cat_value
        
        # If no match found, return None to filter it out (it's likely noise)
        return None
    
    # Apply normalization to any remaining unmapped vectors
    unmapped = vector_df[~vector_df['Subcategory'].isin(attack_vectors_mapping.values())]['Subcategory'].unique()
    if len(unmapped) > 0:
        print(f"[INFO] Normalizing {len(unmapped)} unmapped attack vectors")
        vector_df['Subcategory'] = vector_df['Subcategory'].apply(normalize_vector_name)
        # Filter out None values (unmappable vectors)
        vector_df = vector_df[vector_df['Subcategory'].notna()].copy()
    
    # Aggregate duplicates: after mapping, we might have multiple rows with same Year-Subcategory
    # Sum up the attacks for each Year-Subcategory combination
    vector_df = vector_df.groupby(['Year', 'Subcategory'])['Attacks'].sum().reset_index()

    pivot_df = vector_df.pivot(index='Year', columns='Subcategory', values='Attacks').fillna(0)

    # ------------------------------
    # Reorder the columns to place 
    # the top 3 at the bottom
    # ------------------------------
    total_attacks = pivot_df.sum(axis=0).sort_values(ascending=False)
    top_three_vectors = total_attacks.head(3).index
    remaining_vectors = total_attacks.index.difference(top_three_vectors)
    ordered_columns = top_three_vectors.tolist() + remaining_vectors.tolist()
    pivot_df = pivot_df[ordered_columns]

    # ------------------------------
    # Set the color palette for each attack vector
    # ------------------------------
    full_tab20 = sns.color_palette("tab20", 20)

    color_map = {
        'Malicious Documents': full_tab20[0],
        'Spear Phishing': full_tab20[2],
        'Vulnerability Exploitation': full_tab20[4],
        'Covert Channels': full_tab20[5],
        'Credential Reuse': full_tab20[9],
        'Drive-By Download': full_tab20[8],
        'Meta Data Monitoring': full_tab20[6],     
        'Phishing': full_tab20[7],
        'Removable Media': full_tab20[10],
        'Social Engineering': full_tab20[11],
        'Watering Hole': full_tab20[14],
        'Website Equipping': full_tab20[15] 
    }

    # Handle missing vectors gracefully - use a default color if not in map
    default_color = (0.5, 0.5, 0.5)  # Gray for unmapped vectors
    colors = [color_map.get(vector, default_color) for vector in pivot_df.columns]
    
    # Warn about any missing vectors
    missing_vectors = [vector for vector in pivot_df.columns if vector not in color_map]
    if missing_vectors:
        print(f"[WARNING] Attack vectors not in color_map (using gray): {missing_vectors}")

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
    plt.ylabel('Number of Attack Vectors', fontsize=56, fontweight='bold')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial']
    plt.xticks(rotation=0, fontweight='bold')
    plt.yticks(ticks=range(0, 126, 25), fontweight='bold')

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
        
        # Determine top 3 vectors for this year
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
                    fontsize=42,
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
    print(f"[✓] Figure 5(b) saved to {OUTPUT_PDF}")

if __name__ == "__main__":
    final_df = process_filter_data(INPUT_CSV, 'Attack Vector')
    draw_figure(final_df)