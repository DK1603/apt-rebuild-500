# APT Threat Intelligence Analysis Project

## Overview

This project analyzes **Advanced Persistent Threat (APT) technical reports** from 2014-2023 to extract structured threat intelligence. We use two complementary approaches:

1. **LLM-based extraction** (Gemini 2.5 Flash) - Extracts semantic information like threat actors, victim countries, attack vectors, and target sectors
2. **Rule-based extraction** (IoCParser) - Extracts structured indicators like CVEs, MITRE ATT&CK IDs, and YARA rules

The goal is to transform unstructured PDF reports into structured data for threat intelligence analysis and visualization.

---

## Project Structure

### 📁 `code/` - Main Processing Scripts

This folder contains the core data extraction and processing pipeline:

- **`get_LLMAnswers_500.py`** - Main LLM extraction script
  - Uses RAG (Retrieval-Augmented Generation) with Gemini 2.5 Flash
  - Extracts: Threat Actor, Victim Country, Zero-Day, Attack Vector, Malware, Target Sector
  - Requires: Pre-processed vector stores and Google API key

- **`get_IOCParser_500.py`** - Rule-based IOC extraction
  - Parses PDFs to extract CVE numbers, MITRE ATT&CK IDs, and YARA rules
  - Uses regex patterns for structured indicator extraction

- **`preprocessPdf_embeddings.py`** - PDF preprocessing and vectorization
  - Converts PDFs to text chunks
  - Creates FAISS vector stores using Google Gemini embeddings
  - Required before running LLM extraction

- **`helpers/`** - Utility scripts
  - `select_500_reports.py` - Stratified sampling from 1,509 reports
  - `download_500_pdfs.py` - Downloads PDFs from URLs
  - `validate_and_clean_pdfs.py` - Validates PDF integrity
  - `balance_recent_years.py` - Balances dataset across years
  - `verify_distribution.py` - Verifies year distribution

---

### 📁 `csv_main/` - Datasets

Contains all the processed CSV datasets:

- **`ArticlesDataset_500_Valid.csv`** - 477 validated technical reports (2014-2023)
  - Base dataset with metadata: Date, Filename, Title, Download URL
  - Used as input for both LLM and IOC extraction

- **`ArticlesDataset_LLMAnswered.csv`** - LLM-extracted fields
  - Contains semantic attributes extracted by Gemini
  - Fields: Threat Actor, Victim Country, Zero-Day, Attack Vector, Malware, Target Sector

- **`MergedArticles_IOCParsed_1130.csv`** - Rule-based extracted fields
  - Contains structured indicators extracted by IoCParser
  - Fields: CVE, MITRE, YARA

- **`Technical_Report_Collection_1500.csv`** - Original collection of 1,509 reports
  - Full dataset before sampling

---

### 📁 `plotting/` - Analysis & Visualization

Scripts and outputs for generating figures and tables:

- **`generate_table2.py`** - Generates Table 2 (Statistics on TR collection)
  - Shows distribution by year and source categories
  - Output: `Table2_Statistics.csv`

- **`generate_figure2.py`** - Generates Figure 2 (Top 15 sources)
  - Bar chart of most common report sources
  - Output: `Figure2_Top15Sources.png/pdf`

- **`comparison_tables.py`** - Generates comparison tables
  - Table 5: Precision/Recall/F1 comparison
  - Table 6: Retrieval approach comparison

- **`Global Trends/`** - Trend analysis scripts
  - `overtime_changes_threat_actors.py` - Threat actor trends over time
  - `overtime_changes_victimCountries.py` - Victim country trends
  - `overtime_changes_attack_vectors.py` - Attack vector evolution
  - `overtime_changes_target_sectors.py` - Target sector changes
  - `attacker_victim_relationship.py` - Relationship heatmaps
  - `attack_duration_CDF.py` - Attack duration analysis

- **`Global Trends/graphs/`** - Generated visualizations
  - All figures and tables in PDF/PNG format
  - Includes: Figure 2, 4a, 4b, 5a, 5b, 8, and Tables 2, 5, 6

---

## Quick Start

### 1. Setup Environment
```bash
pip install -r code/requirements.txt
# Set GOOGLE_API_KEY in .env file (see code/env_template.txt)
```

### 2. Data Processing Pipeline
```bash
# Step 1: Select and download reports
python code/helpers/select_500_reports.py
python code/helpers/download_500_pdfs.py

# Step 2: Preprocess PDFs (create embeddings: FAISS )
python code/preprocessPdf_embeddings.py

# Step 3: Extract data
python code/get_LLMAnswers_500.py      # LLM extraction
python code/get_IOCParser_500.py       # Rule-based extraction
```

### 3. Generate Visualizations
```bash
# Generate tables and figures
python plotting/generate_table2.py
python plotting/generate_figure2.py
python plotting/Global Trends/overtime_changes_threat_actors.py
# ... etc
```


## Data Flow

```
1,509 Original Reports
    ↓ (stratified sampling)
477 Valid Reports (ArticlesDataset_500_Valid.csv)
    ↓
    ├─→ LLM Extraction → ArticlesDataset_LLMAnswered.csv
    └─→ IOC Extraction → MergedArticles_IOCParsed_1130.csv
    ↓
Analysis & Visualization → Figures & Tables
```

---

## Notes

- The project uses **477 reports** sampled from **1,509 original reports**
- LLM extraction requires Google Gemini API key
- All PDFs are stored in `Reports/` directory
- Vector stores are saved in `vectorstore_gemini_embeddings/`

---

## Contact & References

Based on the research paper: "A Decade-long Landscape of Advanced Persistent Threats"  
Data source: CyberMonitor/APT_CyberCriminal_Campagin_Collections (GitHub)

