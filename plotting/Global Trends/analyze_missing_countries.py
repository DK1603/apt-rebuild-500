import pandas as pd
import re

# Load the CSV
df = pd.read_csv('../../ArticlesDataset_LLMAnswered.csv')

print("="*70)
print("ANALYZING MISSING THREAT ACTORS AND COUNTRIES")
print("="*70)

# Get all unique threat actors
print("\n[1] Unique Threat Actors (excluding 'Not mentioned' and 'Anonymous'):")
threat_actors = df[df['Threat Actor'].notna()]['Threat Actor']
threat_actors = threat_actors[~threat_actors.astype(str).str.lower().isin(['not mentioned', 'anonymous'])]
unique_actors = set()
for actor in threat_actors:
    if pd.notna(actor):
        # Split by comma and add each
        for a in str(actor).split(','):
            a_clean = a.strip()
            if a_clean and a_clean.lower() not in ['not mentioned', 'anonymous']:
                unique_actors.add(a_clean)

print(f"Found {len(unique_actors)} unique threat actor names")
for i, actor in enumerate(sorted(unique_actors), 1):
    print(f"  {i}. {actor}")

# Get all unique victim countries
print("\n[2] Unique Victim Countries (excluding 'Not mentioned'):")
victim_countries = df[df['Victim Country'].notna()]['Victim Country']
victim_countries = victim_countries[~victim_countries.astype(str).str.lower().isin(['not mentioned'])]
unique_countries = set()
for country in victim_countries:
    if pd.notna(country):
        # Split by comma and clean
        for c in str(country).split(','):
            c_clean = c.strip().rstrip('.')
            if c_clean and c_clean.lower() != 'not mentioned':
                unique_countries.add(c_clean)

print(f"Found {len(unique_countries)} unique victim country names")
for i, country in enumerate(sorted(unique_countries), 1):
    print(f"  {i}. {country}")

print("\n" + "="*70)

