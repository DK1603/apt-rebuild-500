# Code to reproduce the overtime changes of APT victims
# This figure corresponds to Figure 4(a) in the paper 
# Section 4.1: Victim Countries

import pandas as pd
import numpy as np
import altair as alt

INPUT_CSV = '../../ArticlesDataset_LLMAnswered.csv'
OUTPUT_PDF = 'Figure4a_VictimChanges.pdf'

# Mapping of full country names to ISO 2-letter country codes (acronyms)
COUNTRY_TO_CODE = {
    'China': 'CN',
    'Russia': 'RU',
    'North Korea': 'KP',
    'Iran': 'IR',
    'United States': 'US',
    'United States of America': 'US',
    'USA': 'US',
    'Israel': 'IL',
    'Palestine': 'PS',
    'Syria': 'SY',
    'Turkey': 'TR',
    'India': 'IN',
    'South Korea': 'KR',
    'Korea': 'KR',
    'United Kingdom': 'GB',
    'UK': 'GB',
    'Great Britain': 'GB',
    'Britain': 'GB',
    'France': 'FR',
    'Germany': 'DE',
    'Japan': 'JP',
    'Taiwan': 'TW',
    'Ukraine': 'UA',
    'Pakistan': 'PK',
    'Vietnam': 'VN',
    'Thailand': 'TH',
    'Philippines': 'PH',
    'Indonesia': 'ID',
    'Malaysia': 'MY',
    'Singapore': 'SG',
    'Australia': 'AU',
    'Canada': 'CA',
    'Brazil': 'BR',
    'Mexico': 'MX',
    'Argentina': 'AR',
    'Saudi Arabia': 'SA',
    'United Arab Emirates': 'AE',
    'UAE': 'AE',
    'Egypt': 'EG',
    'Iraq': 'IQ',
    'Jordan': 'JO',
    'Lebanon': 'LB',
    'Kuwait': 'KW',
    'Qatar': 'QA',
    'Oman': 'OM',
    'Bahrain': 'BH',
    'Yemen': 'YE',
    'Afghanistan': 'AF',
    'Bangladesh': 'BD',
    'Sri Lanka': 'LK',
    'Nepal': 'NP',
    'Myanmar': 'MM',
    'Cambodia': 'KH',
    'Laos': 'LA',
    'Mongolia': 'MN',
    'Belarus': 'BY',
    'Poland': 'PL',
    'Romania': 'RO',
    'Bulgaria': 'BG',
    'Hungary': 'HU',
    'Czech Republic': 'CZ',
    'Czechia': 'CZ',
    'Slovakia': 'SK',
    'Greece': 'GR',
    'Italy': 'IT',
    'Spain': 'ES',
    'Portugal': 'PT',
    'Netherlands': 'NL',
    'Belgium': 'BE',
    'Switzerland': 'CH',
    'Austria': 'AT',
    'Sweden': 'SE',
    'Norway': 'NO',
    'Denmark': 'DK',
    'Finland': 'FI',
    'Ireland': 'IE',
    'Hong Kong': 'HK',
}

def country_to_code(country_name):
    """Convert country name to ISO 2-letter code"""
    if pd.isna(country_name) or not isinstance(country_name, str):
        return None
    
    country_clean = country_name.strip().rstrip('.')
    
    # Direct lookup
    if country_clean in COUNTRY_TO_CODE:
        return COUNTRY_TO_CODE[country_clean]
    
    # Case-insensitive lookup
    for full_name, code in COUNTRY_TO_CODE.items():
        if full_name.lower() == country_clean.lower():
            return code
    
    # Handle common variations
    country_lower = country_clean.lower()
    variations = {
        'u.s.': 'US', 'u.s': 'US', 'us': 'US', 'usa': 'US', 'the united states': 'US',
        'u.k.': 'GB', 'u.k': 'GB', 'uk': 'GB', 'great britain': 'GB', 'britain': 'GB', 'the uk': 'GB',
        'uae': 'AE', 'united arab emirates': 'AE',
        'north korea': 'KP', 'dprk': 'KP',
        'south korea': 'KR', 'korea': 'KR', 'republic of korea': 'KR',
        'russian federation': 'RU', 'russia': 'RU',
        "people's republic of china": 'CN', 'prc': 'CN', 'mainland china': 'CN',
        'türkiye': 'TR', 'turkey': 'TR',
        'syrian arab republic': 'SY', 'syria': 'SY',
        'israel': 'IL',
        'india': 'IN',
        'iran': 'IR',
        'vietnam': 'VN',
        'philippines': 'PH',
        'japan': 'JP',
        'germany': 'DE',
        'ukraine': 'UA',
    }
    
    if country_lower in variations:
        return variations[country_lower]
    
    # Handle country codes that are already in the data
    if len(country_clean) == 2 and country_clean.isupper():
        for name, code in COUNTRY_TO_CODE.items():
            if code == country_clean:
                return code
    
    # Partial matching
    for full_name, code in COUNTRY_TO_CODE.items():
        full_lower = full_name.lower()
        if full_lower in country_lower:
            if (country_lower == full_lower or 
                country_lower.startswith(full_lower + ' ') or
                country_lower.endswith(' ' + full_lower) or
                country_lower.endswith(',' + full_lower) or
                ' ' + full_lower + ' ' in country_lower):
                return code
    
    return None

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
Function to process the original data and filter to the victim countries
Enables to count the number of attacks per year for each victim country including zero-day attacks
'''
def process_filter_data(input_csv, col):
    # ------------------------------
    # Load and Prepare Data
    # ------------------------------
    df = pd.read_csv(input_csv)

    # Drop rows with missing 'Date' or the specified column
    df = df.dropna(subset=['Date', col])
    # Also filter out "Not mentioned" values
    df = df[df[col].astype(str).str.lower() != 'not mentioned']

    # Convert 'Date' to datetime format and extract the year
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year

    # Split 'Victim Country' on ','
    df[col] = df[col].apply(
        lambda x: [item.strip() for item in x.split(',') if item.strip().lower() != 'not mentioned'] if isinstance(x, str) else x
    )

    # Explode the Victim Country column
    df_exploded = df.explode(col)
    
    # Filter out any remaining "Not mentioned" values
    df_exploded = df_exploded[df_exploded[col].astype(str).str.lower() != 'not mentioned']
    
    # Convert country names to codes first
    df_exploded['CountryCode'] = df_exploded[col].apply(country_to_code)
    df_exploded = df_exploded[df_exploded['CountryCode'].notna()].copy()
    
    # Get top 10 by country code (aggregating counts for same code)
    top10_codes = (
        df_exploded.groupby('CountryCode')
        .size()
        .sort_values(ascending=False)
        .head(10)
        .index
        .tolist()
    )
    
    # Get the original country names that map to these codes (for filtering)
    code_to_names = {}
    for code in top10_codes:
        code_to_names[code] = []
        for name in df_exploded[col].unique():
            if country_to_code(name) == code:
                code_to_names[code].append(name)
    
    # Get all country names that map to top 10 codes
    top10_victim_countries = []
    for names_list in code_to_names.values():
        top10_victim_countries.extend(names_list)
    
    # Explicit copy - filter by country names that map to top 10 codes
    df_filtered = df_exploded[df_exploded[col].isin(top10_victim_countries)].copy()

    # ------------------------------
    # Handle the 'Zero-Day' Column (with hyphen)
    # ------------------------------
    df_filtered['Zero-Day'] = df_filtered['Zero-Day'].astype(str).str.lower()

    # Set 'Zero-Day' to 1 if 'true', else 0
    df_filtered['Zero-Day'] = np.where(df_filtered['Zero-Day'] == 'true', 1, 0)

    # ------------------------------
    # Count Total Attacks and Zero-Day 
    # Attacks per Country per Year
    # ------------------------------
    final_df = (
        df_filtered.groupby(['Year', 'CountryCode'])
        .agg(
            Attacks=(col, 'count'),
            ZeroDayAttacks=('Zero-Day', 'sum')  
        )
        .reset_index()
        .rename(columns={'CountryCode': 'Country'})
    )
    
    # ------------------------------
    # Ensure all top 10 countries are included for all years (2014-2023)
    # Fill missing combinations with 0 attacks
    # ------------------------------
    # top10_codes is already computed above
    
    # Get all years from the data (or use 2014-2023 if specified)
    all_years = sorted(df['Year'].dropna().unique().astype(int).tolist())
    # Ensure we have years 2014-2023
    all_years = list(range(2014, 2024)) if len(all_years) > 0 else list(range(2014, 2024))
    
    # Create a complete index with all country-year combinations
    complete_index = pd.MultiIndex.from_product(
        [top10_codes, all_years],
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

    # Calculate total number of attacks per country and sort by total attacks (descending)
    country_totals = df.groupby("Country")["Attacks"].sum().sort_values(ascending=False)
    actor_order = country_totals.index.tolist()

    # Define custom size scale to include small values
    size_scale = alt.Scale(domain=[1, 10, 20, 30], range=[300, 800, 1300, 1800])

    # ------------------------------
    # Create the chart
    # ------------------------------
    chart = alt.Chart(df).mark_circle(opacity=0.8, stroke=None).encode(
        x=alt.X(
            "Country:N",
            sort=actor_order,
            axis=alt.Axis(
                title="Victim Country",
                labelAngle=0,
                labelFontSize=28,
                titleFontSize=30,
                labelFontWeight="bold",
                titlePadding=110
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
                values=[1, 10, 20, 30],
                orient="none",
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
    print(f"[✓] Figure 4(a) saved to {OUTPUT_PDF}")
    
if __name__ == "__main__":
    final_df = process_filter_data(INPUT_CSV, 'Victim Country')
    draw_figure(final_df)