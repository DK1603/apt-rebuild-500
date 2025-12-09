# Code to reproduce the overtime changes of APT threat actors
# This figure corresponds to Figure 4(b) in the paper 
# Section 4.1: Threat Actors

import pandas as pd
import numpy as np
import altair as alt

INPUT_CSV = '../../ArticlesDataset_LLMAnswered.csv'
OUTPUT_PDF = 'Figure4b_ActorChanges.pdf'

# Helper function to get the top 10 most common items from the specified column
def get_top_10(column, df):
    df = df.dropna(subset=[column]).copy()
    df[column] = df[column].apply(lambda x: [v.strip() for v in str(x).split(',')])
    s = df.explode(column)[column]

    counts = (
        s.value_counts(dropna=False)
         .rename('Attacks')
         .to_frame()
         .reset_index()
         .rename(columns={'index': column})
         .sort_values(['Attacks', column], ascending=[False, True], kind='mergesort')
    )
    
    return counts.head(10)[column].tolist()

'''
Function to process the original data and filter to the  threat actors
Enables to count the number of attacks per year for each threat actor including zero-day attacks
'''
def process_filter_data(input_csv, col):
    # ------------------------------
    # Load and Prepare Data
    # ------------------------------
    df = pd.read_csv(input_csv)

    print(f"[DEBUG] Initial dataset: {len(df)} rows")
    
    # Drop rows with missing 'Date' or the specified column
    df = df.dropna(subset=['Date', col])
    print(f"[DEBUG] After dropping NaN: {len(df)} rows")
    
    # Also filter out "Not mentioned" values
    df = df[df[col].astype(str).str.lower() != 'not mentioned']
    print(f"[DEBUG] After filtering 'Not mentioned': {len(df)} rows")

    # Convert 'Date' to datetime format and extract the year
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year
    
    # Drop rows where Year is NaN (invalid dates)
    df = df[df['Year'].notna()]
    print(f"[DEBUG] After filtering invalid dates: {len(df)} rows")

    # Split 'Threat Actor' on ','
    df[col] = df[col].apply(
        lambda x: [item.strip() for item in x.split(',') if item.strip().lower() != 'not mentioned'] if isinstance(x, str) else x
    )

    # Explode the Threat Actor column
    df_exploded = df.explode(col)
    
    # Filter out any remaining "Not mentioned" values
    df_exploded = df_exploded[df_exploded[col].astype(str).str.lower() != 'not mentioned']
    
    print(f"[DEBUG] After explode: {len(df_exploded)} rows")
    print(f"[DEBUG] Unique threat actors before normalization: {df_exploded[col].nunique()}")
    
    # ------------------------------
    # Dynamically build name mapping from ALL data (not just top 10)
    # Groups similar names and maps to the most common form
    # ------------------------------
    def extract_core_name(name):
        """Extract core name by removing common suffixes and normalizing"""
        if pd.isna(name):
            return None
        name_str = str(name).strip()
        normalized = name_str.lower()
        # Remove common separators
        normalized = normalized.replace('-', ' ').replace('_', ' ')
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Remove common suffixes that don't change the identity (longest first)
        suffixes_to_remove = [
            ' threat actor group', ' threat actor', ' apt group', ' cybergang group',
            ' electronic army', ' hacker team', ' malware team', ' cybergang',
            ' organization', ' hackers', ' group', ' team', ' gang', ' actor',
            ' apt', ' group1'
        ]
        # Sort by length (longest first) to match longer suffixes first
        suffixes_to_remove.sort(key=len, reverse=True)
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break
        
        # Remove common prefixes
        prefixes_to_remove = ['the ', 'apt ', 'apt-', 'aptc-']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break
        
        return normalized
    
    # Count occurrences of each threat actor name from ALL data
    actor_counts = df_exploded[col].value_counts().to_dict()
    
    # Filter out generic/ambiguous terms that shouldn't be grouped
    generic_terms = [
        'not mentioned', 'advanced persistent threats', 'apts', 'unknown',
        'chinese government cyber actors', 'russian', 'iranian', 'north korean',
        'threat actor', 'cyber actors', 'government actors'
    ]
    
    def is_generic_term(name):
        """Check if a name is a generic term that shouldn't be grouped"""
        name_lower = str(name).lower().strip()
        for term in generic_terms:
            if term in name_lower:
                return True
        # Check if it's too generic (very long, contains "also known as", etc.)
        if len(name_lower) > 50 or 'also known as' in name_lower or 'aka' in name_lower:
            # These are often descriptions, not actual names
            if name_lower.count('(') > 1 or name_lower.count('"') > 2:
                return True
        return False
    
    # Group similar names together using core name extraction
    name_groups = {}
    for name, count in actor_counts.items():
        if pd.isna(name):
            continue
        # Skip generic terms - they should remain separate or be filtered
        if is_generic_term(name):
            # Keep generic terms as their own group (don't merge them)
            core_name = str(name).lower().strip()
            if core_name not in name_groups:
                name_groups[core_name] = []
            name_groups[core_name].append((name, count))
            continue
            
        core_name = extract_core_name(name)
        if core_name is None or not core_name:
            continue
        
        if core_name not in name_groups:
            name_groups[core_name] = []
        name_groups[core_name].append((name, count))
    
    # Also handle cases where one name contains another (e.g., "Lazarus" in "Lazarus Group")
    # Merge groups where one core name is a substring/prefix of another
    # BUT only if they're clearly the same actor (not generic terms)
    merged_groups = {}
    core_names_sorted = sorted(name_groups.keys(), key=len, reverse=True)
    for core_name in core_names_sorted:
        merged = False
        # Skip merging if this is a generic term
        if is_generic_term(core_name):
            merged_groups[core_name] = name_groups[core_name]
            continue
            
        for existing_core in list(merged_groups.keys()):
            # Don't merge generic terms with specific names
            if is_generic_term(existing_core):
                continue
                
            # Check if one is a prefix of the other (more precise than substring)
            # e.g., "lazarus" should match "lazarus group"
            shorter = min(core_name, existing_core, key=len)
            longer = max(core_name, existing_core, key=len)
            
            # Only merge if shorter is at least 3 characters (avoid false matches)
            if len(shorter) < 3:
                continue
            
            # Check if shorter is a prefix of longer (with word boundary)
            if shorter and longer.startswith(shorter):
                # Additional check: if longer is just shorter + common word, merge
                remainder = longer[len(shorter):].strip()
                common_words = ['group', 'team', 'gang', 'apt', 'organization', 'hackers', 'cybergang']
                if not remainder or any(remainder.startswith(word) for word in common_words):
                    # Additional safety: ensure the shorter name is substantial (not just 1-2 chars)
                    if len(shorter) >= 3:
                        # Merge into the group with more total occurrences
                        existing_total = sum(count for _, count in merged_groups[existing_core])
                        current_total = sum(count for _, count in name_groups[core_name])
                        if current_total > existing_total:
                            # Replace existing with current
                            merged_groups[core_name] = merged_groups.pop(existing_core) + name_groups[core_name]
                        else:
                            # Add current to existing
                            merged_groups[existing_core].extend(name_groups[core_name])
                        merged = True
                        break
        if not merged:
            merged_groups[core_name] = name_groups[core_name]
    
    # For each group, pick the most common name as canonical
    # and create mapping from all variations to canonical name
    name_mapping = {}
    for core_name, variants in merged_groups.items():
        # Sort by count (descending) to get most common first
        variants_sorted = sorted(variants, key=lambda x: x[1], reverse=True)
        canonical_name = variants_sorted[0][0]  # Most common name
        
        # Map all variations to canonical name
        for variant_name, _ in variants_sorted:
            name_mapping[variant_name] = canonical_name
    
    # Create normalization function using the dynamic mapping
    def normalize_actor_name(name):
        if pd.isna(name):
            return name
        name_str = str(name).strip()
        # Direct lookup (exact match)
        if name_str in name_mapping:
            return name_mapping[name_str]
        # Case-insensitive lookup
        name_lower = name_str.lower()
        for key, value in name_mapping.items():
            if key.lower() == name_lower:
                return value
        # If no match, return original name
        return name_str
    
    # Apply normalization to all data
    df_exploded[col] = df_exploded[col].apply(normalize_actor_name)
    
    print(f"[DEBUG] After normalization: {len(df_exploded)} rows")
    print(f"[DEBUG] Unique threat actors after normalization: {df_exploded[col].nunique()}")
    
    # Filter out generic terms from normalized data before getting top 10
    df_exploded_filtered = df_exploded[~df_exploded[col].apply(is_generic_term)].copy()
    
    # Now get top 10 after normalization (to ensure we get the right ones)
    top10_after_normalization = get_top_10(col, df_exploded_filtered)
    
    # Filter to top 10 threat actors (after normalization)
    df_filtered = df_exploded_filtered[df_exploded_filtered[col].isin(top10_after_normalization)].copy()
    
    # Debug: Print the discovered mapping
    print(f"[DEBUG] Discovered {len(name_mapping)} unique threat actor name mappings")
    print(f"[DEBUG] Number of core name groups: {len(merged_groups)}")
    
    # Show some example mappings
    example_mappings = {}
    for variant, canonical in list(name_mapping.items())[:15]:
        if variant != canonical:
            if canonical not in example_mappings:
                example_mappings[canonical] = []
            example_mappings[canonical].append(variant)
    print(f"[DEBUG] Example mappings (variations -> canonical):")
    for canonical, variants in list(example_mappings.items())[:5]:
        print(f"  {canonical} <- {variants}")
    
    # Count occurrences after normalization to verify grouping worked
    normalized_counts = df_exploded[col].value_counts()
    print(f"[DEBUG] Top 10 actors after normalization (with counts):")
    for actor, count in normalized_counts.head(10).items():
        print(f"  {actor}: {count}")
    
    # Now get top 10 after normalization (to ensure we get the right ones)
    top10_after_normalization = get_top_10(col, df_exploded)
    
    # Filter out any NaN values that might have been created
    df_filtered = df_filtered[df_filtered[col].notna()].copy()
    
    # ------------------------------
    # Handle the 'Zero-Day' Column (with hyphen)
    # ------------------------------
    df_filtered['Zero-Day'] = df_filtered['Zero-Day'].astype(str).str.lower()

    # Set 'Zero-Day' to 1 if 'true', else 0
    df_filtered['Zero-Day'] = np.where(df_filtered['Zero-Day'] == 'true', 1, 0)

    # ------------------------------
    # Count Total Attacks and Zero-Day 
    # Attacks per Threat Actor per Year
    # ------------------------------
    final_df = (
        df_filtered.groupby(['Year', col])
        .agg(
            Attacks=(col, 'count'),   
            ZeroDayAttacks=('Zero-Day', 'sum')
        )
        .reset_index()
        .rename(columns={col: 'Country'})
    )
    
    # ------------------------------
    # Ensure all top 10 threat actors are included for all years (2014-2023)
    # Fill missing combinations with 0 attacks
    # ------------------------------
    # Get unique threat actor names (after normalization)
    top10_actors = df_filtered[col].unique().tolist()
    top10_actors = [a for a in top10_actors if pd.notna(a)]
    
    # Get all years from the data (or use 2014-2023 if specified)
    all_years = sorted(df['Year'].dropna().unique().astype(int).tolist())
    # Ensure we have years 2014-2023
    all_years = list(range(2014, 2024)) if len(all_years) > 0 else list(range(2014, 2024))
    
    # Create a complete index with all actor-year combinations
    complete_index = pd.MultiIndex.from_product(
        [top10_actors, all_years],
        names=['Country', 'Year']
    )
    
    # Reindex to include all combinations, filling missing with 0
    final_df = final_df.set_index(['Country', 'Year'])
    final_df = final_df.reindex(complete_index, fill_value=0).reset_index()
    
    # Ensure Attacks, ZeroDayAttacks, and Year are integers
    final_df['Attacks'] = final_df['Attacks'].astype(int)
    final_df['ZeroDayAttacks'] = final_df['ZeroDayAttacks'].astype(int)
    final_df['Year'] = final_df['Year'].astype(int)

    return final_df

# Function to draw the figure
def draw_figure(input_df):
    # Load your CSV file
    df = input_df.copy()
    
    # Debug: Print info about the dataframe
    print(f"[DEBUG] DataFrame shape: {df.shape}")
    print(f"[DEBUG] Unique actors: {df['Country'].unique()}")
    print(f"[DEBUG] Year range: {df['Year'].min()} - {df['Year'].max()}")
    print(f"[DEBUG] Total attacks: {df['Attacks'].sum()}")

    # Calculate total number of attacks per threat actor
    country_totals = df.groupby("Country")["Attacks"].sum().sort_values(ascending=False)
    actor_order = country_totals.index.tolist()

    # size_scale = alt.Scale(rangeMax=2000)
    size_scale = alt.Scale(domain=[1, 10, 20, 30], range=[300, 800, 1300, 1800])

    # ------------------------------
    # Create the chart
    # ------------------------------
    chart = alt.Chart(df).mark_circle(opacity=0.8, stroke=None).encode(
        x=alt.X(
            "Country:N",
            sort=actor_order,
            axis=alt.Axis(
                title="Threat Actor",
                labelAngle=-45,
                labelFontSize=28,
                titleFontSize=30,
                labelFontWeight="bold"
            )
        ),
        y=alt.Y(
            "Year:O",
            axis=alt.Axis(
                title="Year",
                grid=False,
                labelFontSize=28,
                titleFontSize=30,
                labelFontWeight="bold"
            ),
            scale=alt.Scale(padding=1)
        ),
        size=alt.Size(
            "Attacks:Q",
            title="# of attacks",
            scale=size_scale,
            legend=alt.Legend(
                labelFontSize=24,
                titleFontSize=24,
                values=[1, 10, 20],
                orient='none',
                legendY = 270,
                legendX = 715
            )
        ),
        color=alt.Color(
            "ZeroDayAttacks:Q",
            scale=alt.Scale(scheme="reds", reverse=False),
            title="# of 0-days",
            legend=alt.Legend(
                labelFontSize=24,
                titleFontSize=24
            )
        )
    ).properties(
        width=700,
        height=500
    ).configure_view(
        strokeWidth=2,
        stroke="black"
    )

    # Save the chart as a PDF
    chart.save(OUTPUT_PDF)
    print(f"[✓] Figure 4(b) saved to {OUTPUT_PDF}")

if __name__ == "__main__":
    final_df = process_filter_data(INPUT_CSV, 'Threat Actor')
    draw_figure(final_df)