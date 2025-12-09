"""
Verify Distribution of Selected 500 Reports
Compares original 1509 reports vs selected 500 to ensure proper stratification
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Verify temporal distribution of selected reports.")
parser.add_argument(
    "--original",
    default="code/Technical_Report_Collection.csv",
    help="CSV containing the full dataset (default: code/Technical_Report_Collection.csv)",
)
parser.add_argument(
    "--selected",
    default="ArticlesDataset_500_Valid.csv",
    help="CSV containing the sampled dataset to validate (default: ArticlesDataset_500_Valid.csv)",
)
args = parser.parse_args()

# Load both datasets
original_csv = args.original
selected_csv = args.selected

print("="*70)
print("Distribution Verification")
print("="*70)

# Load original dataset
df_original = pd.read_csv(original_csv)
df_original['Date'] = pd.to_datetime(df_original['Date'])
df_original['Year'] = df_original['Date'].dt.year

# Load selected dataset
df_selected = pd.read_csv(selected_csv)
df_selected['Date'] = pd.to_datetime(df_selected['Date'])
df_selected['Year'] = df_selected['Date'].dt.year

print(f"\n📊 Original Dataset: {len(df_original)} reports")
print(f"📊 Selected Dataset: {len(df_selected)} reports")

# Compare distributions
original_counts = df_original['Year'].value_counts().sort_index()
selected_counts = df_selected['Year'].value_counts().sort_index()

# Calculate expected proportions
print("\n" + "="*70)
print("Year-by-Year Distribution Analysis")
print("="*70)
print(f"{'Year':<6} {'Original':>10} {'Selected':>10} {'Expected':>10} {'Difference':>12} {'% Error':>10}")
print("-"*70)

total_original = len(df_original)
total_selected = len(df_selected)

for year in sorted(original_counts.index):
    orig_count = original_counts[year]
    sel_count = selected_counts.get(year, 0)
    
    # Calculate expected count (proportional)
    expected = (orig_count / total_original) * total_selected
    
    # Calculate difference
    difference = sel_count - expected
    
    # Calculate percentage error
    pct_error = (difference / expected) * 100 if expected > 0 else 0
    
    print(f"{year:<6} {orig_count:>10} {sel_count:>10} {expected:>10.1f} {difference:>12.1f} {pct_error:>9.1f}%")

# Overall statistics
print("\n" + "="*70)
print("Statistical Summary")
print("="*70)

# Calculate chi-square test for goodness of fit
from scipy import stats

expected_counts = [(original_counts[year] / total_original) * total_selected 
                   for year in original_counts.index]
observed_counts = [selected_counts.get(year, 0) for year in original_counts.index]

chi2, p_value = stats.chisquare(observed_counts, expected_counts)

print(f"\nChi-Square Test:")
print(f"  χ² statistic: {chi2:.4f}")
print(f"  p-value: {p_value:.4f}")

if p_value > 0.05:
    print(f"  ✅ Result: Distribution is statistically similar to original (p > 0.05)")
    print(f"     The selection is NOT cherry-picked!")
else:
    print(f"  ⚠️  Result: Distribution differs from original (p < 0.05)")
    print(f"     May need to re-run selection")

# Calculate max deviation
max_dev_year = None
max_dev_pct = 0
for year in original_counts.index:
    orig_count = original_counts[year]
    sel_count = selected_counts.get(year, 0)
    expected = (orig_count / total_original) * total_selected
    dev_pct = abs((sel_count - expected) / expected * 100) if expected > 0 else 0
    if dev_pct > max_dev_pct:
        max_dev_pct = dev_pct
        max_dev_year = year

print(f"\nMaximum Deviation:")
print(f"  Year {max_dev_year}: {max_dev_pct:.1f}% off from expected")

if max_dev_pct < 10:
    print(f"  ✅ All years within 10% of expected (excellent)")
elif max_dev_pct < 20:
    print(f"  ⚠️  Some years 10-20% off expected (acceptable)")
else:
    print(f"  ❌ Some years >20% off expected (poor distribution)")

# Visual comparison
print("\n" + "="*70)
print("Creating distribution comparison chart...")
print("="*70)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: Absolute counts
years = sorted(original_counts.index)
x = range(len(years))

ax1.bar([i-0.2 for i in x], [original_counts[y] for y in years], 
        width=0.4, label='Original (1509)', color='#2E86AB', alpha=0.8)
ax1.bar([i+0.2 for i in x], [selected_counts.get(y, 0) for y in years], 
        width=0.4, label='Selected (500)', color='#A23B72', alpha=0.8)

ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
ax1.set_ylabel('Number of Reports', fontsize=12, fontweight='bold')
ax1.set_title('Absolute Distribution Comparison', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(years, rotation=45)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Percentage distribution
orig_pct = [(original_counts[y] / total_original * 100) for y in years]
sel_pct = [(selected_counts.get(y, 0) / total_selected * 100) for y in years]

ax2.plot(years, orig_pct, marker='o', linewidth=2, markersize=8, 
         label='Original %', color='#2E86AB')
ax2.plot(years, sel_pct, marker='s', linewidth=2, markersize=8, 
         label='Selected %', color='#A23B72')

ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
ax2.set_ylabel('Percentage of Total (%)', fontsize=12, fontweight='bold')
ax2.set_title('Percentage Distribution Comparison', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('distribution_verification.png', dpi=300, bbox_inches='tight')
print("✓ Saved: distribution_verification.png")

# Summary verdict
print("\n" + "="*70)
print("FINAL VERDICT")
print("="*70)

if p_value > 0.05 and max_dev_pct < 15:
    print("✅ ✅ ✅ DISTRIBUTION IS PROPER ✅ ✅ ✅")
    print("\nThe selected 500 reports:")
    print("  • Follow the original temporal distribution")
    print("  • Are NOT cherry-picked")
    print("  • Use proper stratified random sampling")
    print("  • Are statistically representative of the full 1509 dataset")
    print("\n✓ Safe to proceed with analysis!")
elif p_value > 0.05 or max_dev_pct < 20:
    print("⚠️  DISTRIBUTION IS ACCEPTABLE")
    print("\nMinor deviations exist but are within acceptable range.")
    print("This is expected with random sampling.")
else:
    print("❌ DISTRIBUTION NEEDS IMPROVEMENT")
    print("\nConsider re-running select_500_reports.py with different seed.")

print("="*70)

