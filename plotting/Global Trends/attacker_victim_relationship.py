# Code to reproduce the heatmap of top 20 countries
# This figure corresponds to Figure 8 in the paper 
# Section 4.3: Two-sided Nature as Both Attacker and Victim and Self-directed APT Attacks
#
# This script maps Threat Actor names to their countries of origin
# to create the attacker-victim country heatmap.

import pandas as pd
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import re

INPUT_CSV = '../../ArticlesDataset_LLMAnswered.csv'
OUTPUT_PDF = 'Figure8_Heatmap.pdf'

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
    'France': 'FR',
    'Germany': 'DE',
    'Japan': 'JP',
    'Taiwan': 'TW',
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
    'Chile': 'CL',
    'Colombia': 'CO',
    'Peru': 'PE',
    'Venezuela': 'VE',
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
    'Kazakhstan': 'KZ',
    'Uzbekistan': 'UZ',
    'Tajikistan': 'TJ',
    'Kyrgyzstan': 'KG',
    'Turkmenistan': 'TM',
    'Belarus': 'BY',
    'Ukraine': 'UA',
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
    'Lithuania': 'LT',
    'Latvia': 'LV',
    'Estonia': 'EE',
    'Georgia': 'GE',
    'Moldova': 'MD',
    'Macedonia': 'MK',
    'Slovenia': 'SI',
    'Croatia': 'HR',
    'Serbia': 'RS',
    'Bosnia and Herzegovina': 'BA',
    'Albania': 'AL',
    'Cyprus': 'CY',
    'Malta': 'MT',
    'Iceland': 'IS',
    'Luxembourg': 'LU',
    'Monaco': 'MC',
    'Gibraltar': 'GI',
    'Great Britain': 'GB',
    'Britain': 'GB',
    'New Zealand': 'NZ',
    'South Africa': 'ZA',
    'Nigeria': 'NG',
    'Kenya': 'KE',
    'Ethiopia': 'ET',
    'Morocco': 'MA',
    'Algeria': 'DZ',
    'Tunisia': 'TN',
    'Libya': 'LY',
    'Sudan': 'SD',
    'Somalia': 'SO',
    'Eritrea': 'ER',
    'Djibouti': 'DJ',
    'Mauritius': 'MU',
    'Madagascar': 'MG',
    'Mozambique': 'MZ',
    'Angola': 'AO',
    'Zimbabwe': 'ZW',
    'Zambia': 'ZM',
    'Botswana': 'BW',
    'Namibia': 'NA',
    'Ghana': 'GH',
    'Senegal': 'SN',
    'Ivory Coast': 'CI',
    'Cameroon': 'CM',
    'Gabon': 'GA',
    'Congo': 'CG',
    'DRC': 'CD',
    'Democratic Republic of the Congo': 'CD',
    'Uganda': 'UG',
    'Tanzania': 'TZ',
    'Rwanda': 'RW',
    'Burundi': 'BI',
    'Malawi': 'MW',
    'Lesotho': 'LS',
    'Swaziland': 'SZ',
    'Eswatini': 'SZ',
    'Guinea': 'GN',
    'Sierra Leone': 'SL',
    'Liberia': 'LR',
    'Togo': 'TG',
    'Benin': 'BJ',
    'Burkina Faso': 'BF',
    'Mali': 'ML',
    'Niger': 'NE',
    'Chad': 'TD',
    'Central African Republic': 'CF',
    'Equatorial Guinea': 'GQ',
    'Sao Tome and Principe': 'ST',
    'Cape Verde': 'CV',
    'Gambia': 'GM',
    'Guinea-Bissau': 'GW',
    'Mauritania': 'MR',
    'Western Sahara': 'EH',
    'Sahrawi Arab Democratic Republic': 'EH',
    'SADR': 'EH',
    # Additional countries from the dataset
    'Hong Kong': 'HK',
    'Armenia': 'AM',
    'Azerbaijan': 'AZ',
    'Bolivia': 'BO',
    'Costa Rica': 'CR',
    'Ecuador': 'EC',
    'Fiji': 'FJ',
    'Guatemala': 'GT',
    'Guyana': 'GY',
    'Maldives': 'MV',
    'Uruguay': 'UY',
    'South Sudan': 'SS',
    'Brunei': 'BN',
    'East Timor': 'TL',
    'Timor-Leste': 'TL',
    'Bhutan': 'BT',
    'Mauritius': 'MU',
    'Seychelles': 'SC',
    'Comoros': 'KM',
    'Brunei': 'BN',
    'East Timor': 'TL',
    'Timor-Leste': 'TL',
    'Bhutan': 'BT',
    'Seychelles': 'SC',
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
    
    # Handle common variations and partial matches
    country_lower = country_clean.lower()
    
    # Common abbreviations and variations
    variations = {
        'u.s.': 'US', 'u.s': 'US', 'us': 'US', 'usa': 'US', 'the united states': 'US',
        'u.k.': 'GB', 'u.k': 'GB', 'uk': 'GB', 'great britain': 'GB', 'britain': 'GB', 'the uk': 'GB',
        'uae': 'AE', 'united arab emirates': 'AE',
        'north korea': 'KP', 'dprk': 'KP',
        'south korea': 'KR', 'korea': 'KR', 'republic of korea': 'KR',
        'kingdom of saudi arabia': 'SA', 'saudi': 'SA', 'saudi arabia': 'SA',
        'russian federation': 'RU', 'russia': 'RU',
        "people's republic of china": 'CN', 'prc': 'CN', 'mainland china': 'CN',
        'türkiye': 'TR', 'turkey': 'TR',
        'syrian arab republic': 'SY', 'syria': 'SY',
        'palestinian territories': 'PS', 'palestine': 'PS',
        'israel': 'IL',
        'india': 'IN',
        'iran': 'IR', 'islamic republic of iran': 'IR',
        'vietnam': 'VN', 'viet nam': 'VN',
        'philippines': 'PH',
        'myanmar': 'MM', 'burma': 'MM',
        'czech republic': 'CZ', 'czechia': 'CZ',
        'bosnia and herzegovina': 'BA', 'bosnia': 'BA',
        'macedonia': 'MK', 'north macedonia': 'MK',
        'hong kong': 'HK',
        'kenya': 'KE', 'kenia': 'KE',  # Common misspelling
        'sri lanka': 'LK', 'sri-lanka': 'LK',
        'ivory coast': 'CI', "côte d'ivoire": 'CI',
        'dubai': 'AE',  # Dubai is in UAE
        'the philippines': 'PH',
        'the palestinian authority': 'PS',
    }
    
    if country_lower in variations:
        return variations[country_lower]
    
    # Handle country codes that are already in the data (like "CN", "US", "KR", "GB", etc.)
    if len(country_clean) == 2 and country_clean.isupper():
        # Check if it's a valid ISO code by seeing if any country maps to it
        for name, code in COUNTRY_TO_CODE.items():
            if code == country_clean:
                return code
    
    # Partial matching for common patterns (e.g., "United States" in "United States and Canada")
    # But be careful - only match if the country name is a significant part
    for full_name, code in COUNTRY_TO_CODE.items():
        full_lower = full_name.lower()
        # Check if full country name appears in the string
        if full_lower in country_lower:
            # Make sure it's not just a partial word match
            # Check if it's at word boundaries or the whole string
            if (country_lower == full_lower or 
                country_lower.startswith(full_lower + ' ') or
                country_lower.endswith(' ' + full_lower) or
                country_lower.endswith(',' + full_lower) or
                ' ' + full_lower + ' ' in country_lower or
                ' ' + full_lower + ',' in country_lower or
                ',' + full_lower + ' ' in country_lower or
                ',' + full_lower + ',' in country_lower):
                return code
    
    # Try matching common country name patterns at the start of the string
    # (e.g., "United States" at the start of "United States and Canada")
    for full_name, code in COUNTRY_TO_CODE.items():
        full_lower = full_name.lower()
        if country_lower.startswith(full_lower):
            # Check if it's followed by a separator or end of string
            remaining = country_lower[len(full_lower):].strip()
            if not remaining or remaining.startswith((' and ', ' or ', ',', ';', ' ')):
                return code
    
    return None

# Comprehensive mapping of threat actors to their countries of origin
# Based on well-established cybersecurity attribution
THREAT_ACTOR_TO_COUNTRY = {
    # North Korea
    'lazarus': 'North Korea',
    'lazarus group': 'North Korea',
    'hidden cobra': 'North Korea',
    'apt37': 'North Korea',
    'scarcruft': 'North Korea',
    'reaper': 'North Korea',
    'group123': 'North Korea',
    'rokr': 'North Korea',
    'inkysquid': 'North Korea',
    'kimsuky': 'North Korea',
    'konni': 'North Korea',
    'andariel': 'North Korea',
    
    # Russia
    'apt28': 'Russia',
    'fancy bear': 'Russia',
    'sofacy': 'Russia',
    'sednit': 'Russia',
    'apt29': 'Russia',
    'cozy bear': 'Russia',
    'cozyduke': 'Russia',
    'cozycar': 'Russia',
    'the dukes': 'Russia',
    'turla': 'Russia',
    'uroburos': 'Russia',
    'snake': 'Russia',
    'sandworm': 'Russia',
    'voodoo bear': 'Russia',
    'electrum': 'Russia',
    'telebots': 'Russia',
    'shuckworm': 'Russia',
    'gamaredon': 'Russia',
    'armageddon': 'Russia',
    'nobelium': 'Russia',
    'seaborgium': 'Russia',
    'strontium': 'Russia',
    'inception attackers': 'Russia',
    'quedagh': 'Russia',
    'void rabisu': 'Russia',
    'blackenergy gang': 'Russia',
    'carberp': 'Russia',
    'carbanak': 'Russia',
    'carbanak group': 'Russia',
    'fin1': 'Russia',
    'fin7': 'Russia',
    'evil corp': 'Russia',
    'buhtrap group': 'Russia',
    'tele bots': 'Russia',
    
    # China
    'apt1': 'China',
    'comment crew': 'China',
    'apt10': 'China',
    'menupass': 'China',
    'stone panda': 'China',
    'apt12': 'China',
    'apt12 by mandiant': 'China',
    'number panda': 'China',
    'numbered panda': 'China',
    'ixeshe': 'China',
    'apt17': 'China',
    'deputy dog': 'China',
    'apt18': 'China',
    'threat group-3390': 'China',
    'tg-3390': 'China',
    'iron tiger': 'China',
    'emissary panda': 'China',
    'emissary panda 1': 'China',
    'apt41': 'China',
    'barium': 'China',
    'winnti': 'China',
    'winnti group': 'China',
    'winnti apt group': 'China',
    'apt3': 'China',
    'ups or apt3': 'China',
    'gothic panda': 'China',
    'deep panda': 'China',
    'shell crew': 'China',
    'shell_crew': 'China',
    'putter panda': 'China',
    'cpyy': 'China',
    'apt16': 'China',
    'admin@338': 'China',
    'machete': 'China',
    'apt-c-43 or machete': 'China',
    'mustang panda': 'China',
    'mustangpanada': 'China',
    'reddelta': 'China',
    'pkplug': 'China',
    'ta416': 'China',
    'blacktech': 'China',
    'palmerworm': 'China',
    'bronze butler': 'China',
    'tick': 'China',
    'redbaldknight': 'China',
    'apt27': 'China',
    'bronze union': 'China',
    'luckymouse': 'China',
    'lucky mouse': 'China',
    'earth berberoka': 'China',
    'apt15': 'China',
    'mirage': 'China',
    'miragefox': 'China',
    'clouddragon': 'China',
    'apt32': 'China',
    'oceanlotus': 'China',
    'ocean lotus': 'China',
    'oceanlotus group': 'China',
    'bitter': 'China',
    'bitter apt': 'China',
    'patchwork': 'China',
    'patchwork apt': 'China',
    'patchwork apt group': 'China',
    'dropping elephant': 'China',
    'confucius': 'China',
    'confucius apt': 'China',
    'transparent tribe': 'China',
    'apt-36': 'China',
    'apt36': 'China',
    'mythic leopard': 'China',
    'gorgon': 'China',
    'subaat': 'China',
    'ta413': 'China',
    'ta406': 'North Korea',  # TA406 is North Korean
    'ta456': 'China',
    'tortoiseshell': 'China',
    'apt-c-43': 'China',
    'apt-c-01': 'China',
    'apt-c-17': 'China',
    'apt-c-09': 'China',
    'apt-c-36': 'China',
    'apt-c-12': 'China',
    'apt-c-37': 'China',
    'apt-c-35': 'China',
    'apt-c-40': 'China',
    'apt-c-39': 'China',
    'aurora panda': 'China',
    'group 72': 'China',
    'group72': 'China',
    'th3bug 7': 'China',
    'china\'s unit 78020': 'China',
    'chinese government cyber actors': 'China',
    'chineses actor apt': 'China',
    'dragonok': 'China',
    'moafee': 'China',
    'zombie zero': 'China',
    'blue termite': 'China',
    'grand theft auto panda': 'China',
    'sectorj04 group': 'China',
    'suckfly': 'China',
    'black vine': 'China',
    'blackfly': 'China',
    'hidden lynx': 'China',
    'cactuspete': 'China',
    'karma panda': 'China',
    'tonto team': 'China',
    'unc1945': 'China',
    'unc3524': 'China',
    'luoyu': 'China',
    'luoyu attack group': 'China',
    'famoussparrow': 'China',
    'shrouded snooper': 'China',
    'volt typhoon': 'China',
    'earth aughisky': 'China',
    'water pamola': 'China',
    'amoeba': 'China',
    'bronze atlas': 'China',
    'bronze president': 'China',
    'a 공격 그룹': 'China',
    'a41apt': 'China',
    '双尾蝎组织': 'China',
    '毒云藤': 'China',
    '绿斑': 'China',
    'greenspot': 'China',
    '蔓灵花': 'China',
    
    # Iran
    'apt33': 'Iran',
    'elfin': 'Iran',
    'apt34': 'Iran',
    'oilrig': 'Iran',
    'oilrig group': 'Iran',
    'helix kitten': 'Iran',
    'apt39': 'Iran',
    'chafer': 'Iran',
    'crambus': 'Iran',
    'crambus (aka oilrig)': 'Iran',
    'muddywater': 'Iran',
    'muddywater apt': 'Iran',
    'static kitten': 'Iran',
    'apt35': 'Iran',
    'charming kitten': 'Iran',
    'newscaster': 'Iran',
    'ajax security team': 'Iran',
    'flying kitten': 'Iran',
    'newsbeef': 'Iran',
    'magic hound': 'Iran',
    'promethium': 'Iran',
    'strongpity': 'Iran',
    'yellow garuda': 'Iran',
    'darkhydrus': 'Iran',
    'darkhydrus group': 'Iran',
    'tortoiseshell': 'Iran',
    'tortoiseshell apt': 'Iran',
    
    # United States
    'equation group': 'United States',
    'the equation group': 'United States',
    'longhorn': 'United States',
    'lamberts': 'United States',
    'lamberts (aka longhorn)': 'United States',
    'shadow brokers group': 'United States',
    'the shadow brokers': 'United States',
    
    # Israel/Palestine
    'apt-c-23': 'Israel',  # Double Tail Scorpion
    'double tail scorpion': 'Israel',
    'nso group': 'Israel',
    'molerats': 'Palestine',  # Gaza Cybergang
    'gaza cybergang': 'Palestine',
    'gaza hackers': 'Palestine',
    'gaza cybergang group1': 'Palestine',
    'gaza cybergang (aka gaza hacker team aka molerats)': 'Palestine',
    'the gaza cybergang': 'Palestine',
    'hamas-affiliated apt': 'Palestine',
    
    # Other
    'syrian malware team': 'Syria',
    'the resistant syrian electronic army': 'Syria',
    'group5': 'Syria',
    'darkhotel': 'South Korea',  # Actually attributed to South Korea in some reports
    'dark hotel apt group': 'South Korea',
    
    # France
    'french intelligence': 'France',
    'animal farm': 'France',
    'bismuth': 'France',
}

def normalize_threat_actor_name(name):
    """Normalize threat actor name for matching (case-insensitive)"""
    if pd.isna(name) or name == '':
        return None
    # Convert to lowercase for case-insensitive matching
    name = str(name).strip().lower()
    # Remove common suffixes and prefixes
    name = re.sub(r'\s*\(.*?\)', '', name)  # Remove parentheses content
    name = re.sub(r'\s*also known as.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*aka.*', '', name, flags=re.IGNORECASE)
    # Normalize multiple spaces to single space
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def map_threat_actor_to_country(threat_actor):
    """Map threat actor name to country of origin"""
    if pd.isna(threat_actor) or threat_actor == '' or str(threat_actor).strip().lower() == 'not mentioned':
        return None
    
    normalized = normalize_threat_actor_name(threat_actor)
    if not normalized:
        return None
    
    # Skip anonymous or unknown actors
    if normalized in ['anonymous', 'unknown', 'unnamed', 'unidentified']:
        return None
    
    # Direct match
    if normalized in THREAT_ACTOR_TO_COUNTRY:
        return THREAT_ACTOR_TO_COUNTRY[normalized]
    
    # Partial match (check if any key is contained in the name or vice versa)
    # This handles variations like "Syrian Malware Team" matching "syrian malware team"
    for key, country in THREAT_ACTOR_TO_COUNTRY.items():
        # Exact match (already handled above, but double-check)
        if normalized == key:
            return country
        # Check if key is a substring of normalized name
        if key in normalized:
            return country
        # Check if normalized name is a substring of key (for partial matches)
        if normalized in key and len(normalized) > 3:  # Avoid very short matches
            return country
    
    # Check for common patterns (fallback matching)
    if 'lazarus' in normalized or 'hidden cobra' in normalized:
        return 'North Korea'
    if any(x in normalized for x in ['apt28', 'fancy bear', 'sofacy', 'sednit']):
        return 'Russia'
    if any(x in normalized for x in ['apt29', 'cozy bear', 'the dukes', 'nobelium']):
        return 'Russia'
    if any(x in normalized for x in ['turla', 'uroburos', 'snake']):
        return 'Russia'
    if any(x in normalized for x in ['sandworm', 'electrum', 'gamaredon']):
        return 'Russia'
    if any(x in normalized for x in ['apt1', 'comment crew']):
        return 'China'
    if any(x in normalized for x in ['apt10', 'menupass', 'stone panda']):
        return 'China'
    if any(x in normalized for x in ['apt41', 'winnti', 'barium']):
        return 'China'
    if any(x in normalized for x in ['apt33', 'oilrig', 'elfin']):
        return 'Iran'
    if any(x in normalized for x in ['apt34', 'helix kitten', 'chafer', 'crambus']):
        return 'Iran'
    if any(x in normalized for x in ['muddywater', 'static kitten', 'charming kitten']):
        return 'Iran'
    if any(x in normalized for x in ['equation', 'longhorn']):
        return 'United States'
    if 'gaza' in normalized or 'molerats' in normalized:
        return 'Palestine'
    if 'syrian' in normalized:
        return 'Syria'
    
    # If still no match, return None (will be filtered out)
    return None 

'''
Function to process the original data and filter to the top 20 attacker countries
Counts the number of cases where a country is both an attacker and a victim
Maps Threat Actor names to their countries of origin
'''
def process_filter_data(input_csv):
    # ------------------------------
    # Load and Prepare Data
    # ------------------------------
    df = pd.read_csv(input_csv)
    
    # Filter out rows with missing Threat Actor or Victim Country
    df = df.dropna(subset=['Threat Actor', 'Victim Country'])
    df = df[df['Threat Actor'].astype(str).str.lower() != 'not mentioned']
    df = df[df['Victim Country'].astype(str).str.lower() != 'not mentioned']
    
    # ------------------------------
    # Map Threat Actors to Countries
    # ------------------------------
    # Split Threat Actor column (may contain multiple actors separated by commas)
    df['Threat Actor'] = df['Threat Actor'].apply(
        lambda x: [item.strip() for item in str(x).split(',') if item.strip().lower() != 'not mentioned'] 
        if isinstance(x, str) else []
    )
    
    # Explode to have one row per threat actor
    df_exploded = df.explode('Threat Actor')
    df_exploded = df_exploded[df_exploded['Threat Actor'].notna()]
    
    # Map each threat actor to country
    df_exploded['Threat_country'] = df_exploded['Threat Actor'].apply(map_threat_actor_to_country)
    
    # Filter out rows where we couldn't map to a country
    df_exploded = df_exploded[df_exploded['Threat_country'].notna()]
    
    # ------------------------------
    # Process Victim Countries
    # ------------------------------
    # Split Victim Country column (may contain multiple countries separated by commas, "and", "or")
    def split_countries(country_str):
        """Split country string into individual countries"""
        if pd.isna(country_str) or not isinstance(country_str, str):
            return []
        
        # List of non-country entries to filter out
        non_countries = {
            'asia', 'europe', 'africa', 'middle east', 'north america', 'south america',
            'latin america', 'oceania', 'worldwide', 'globally', 'nato countries',
            'nato members', 'nato member states', 'nato nations', 'european union',
            'asean region', 'apac', 'southeast asia', 'east asia', 'south asia',
            'central asia', 'western europe', 'eastern europe', 'central europe',
            'defense contractors', 'aerospace firms', 'companies and organizations around the world',
            'many different countries', 'more than a dozen countries', 'various middle eastern countries',
            'neighboring countries', 'countries around the world', 'countries in europe',
            'countries supporting ukraine', 'countries cooperating with nato exercises',
            'web threats', 'email threats', 'spam', 'cyber espionage', 'an espionage operation',
            'what was the objective of the attack', 'who was targeted in the attack',
            'what was the timeline of the activity', 'incident', 'domains shared',
            'identified in', 'fbi flash report', 'pwc blog post', 'roughly a year',
            'a country of the european union', 'for web threats', 'for email threats',
            'targeted countries are not mentioned', 'or something different',
            'or technical targeting operations', 'asset recruitment', 'blackmail',
            'military', 'government agencies', 'critical infrastructure sectors',
            'government entity', 'airline', 'banks', 'shoppers', 'users', 'customers',
            'organizations', 'companies', 'citizens', 'activists', 'community',
            'minorities', 'experts', 'institutions', 'entities', 'sectors',
        }
        
        country_lower = country_str.lower().strip()
        
        # Filter out obvious non-country entries
        if country_lower in non_countries:
            return []
        
        # Check if it's a non-country entry (contains key phrases)
        if any(nc in country_lower for nc in non_countries if len(nc) > 15):
            return []
        
        # Split on common separators: comma, "and", "or", semicolon
        # First try splitting on commas
        parts = re.split(r'[,;]', country_str)
        countries = []
        
        for part in parts:
            part = part.strip().rstrip('.')
            if not part or part.lower() in non_countries:
                continue
            
            # Check if part contains "and" or "or" - split further
            if ' and ' in part.lower() or ' or ' in part.lower():
                subparts = re.split(r'\s+(?:and|or)\s+', part, flags=re.IGNORECASE)
                for subpart in subparts:
                    subpart = subpart.strip().rstrip('.')
                    if subpart and subpart.lower() not in non_countries:
                        countries.append(subpart)
            else:
                countries.append(part)
        
        # Filter out "not mentioned" and empty strings
        return [c for c in countries if c and c.lower() not in ['not mentioned', '']]
    
    df_exploded['Victim Country'] = df_exploded['Victim Country'].apply(split_countries)
    
    # Explode to have one row per victim country
    df_exploded = df_exploded.explode('Victim Country')
    df_exploded = df_exploded[df_exploded['Victim Country'].notna()]
    
    # Normalize victim country names and convert to codes
    df_exploded['Victim_country'] = df_exploded['Victim Country'].apply(country_to_code)
    
    # Convert Threat_country (which is already a full country name) to code
    df_exploded['Threat_country'] = df_exploded['Threat_country'].apply(country_to_code)
    
    # Filter out rows where we couldn't convert to codes
    df_exploded = df_exploded[df_exploded['Threat_country'].notna()]
    df_exploded = df_exploded[df_exploded['Victim_country'].notna()]
    
    # ------------------------------
    # Generate Threat–Victim pairs
    # ------------------------------
    processed_data = []
    for _, row in df_exploded.iterrows():
        threat_country = row['Threat_country']  # Now a code like 'CN', 'RU', etc.
        victim_country = row['Victim_country']  # Now a code like 'US', 'IN', etc.
        
        if threat_country and victim_country:
            processed_data.append([threat_country, victim_country])
    
    new_df = pd.DataFrame(processed_data, columns=['Threat_country', 'Victim_country'])
    
    # Count occurrences
    new_df['Value'] = new_df.groupby(['Threat_country', 'Victim_country'])['Victim_country'].transform('count')
    new_df = new_df.drop_duplicates()
    
    # ------------------------------
    # Filter to top 20 countries
    # ------------------------------
    country_value_sum = new_df.groupby('Threat_country')['Value'].sum()
    
    top_20_countries = country_value_sum.nlargest(20).index.tolist()
    
    final_df = new_df[new_df['Threat_country'].isin(top_20_countries)]
    
    print(f"[✓] Mapped {len(df_exploded)} threat actor-victim pairs")
    print(f"[✓] Found {len(new_df['Threat_country'].unique())} unique attacker countries")
    print(f"[✓] Top 5 attacker countries: {', '.join(country_value_sum.nlargest(5).index.tolist())}")
    
    return final_df

# Function to draw the figure
def draw_figure(input_df):
    mpl.rcParams['font.family'] = 'Liberation Sans'

    # Rename columns
    df = input_df.rename(columns={
        "Threat_country": "AttackerCol",
        "Victim_country": "VictimCol",
        "Value": "FlowValue"
    })
    df['AttackerCol'] = df['AttackerCol'].astype(str)
    df['VictimCol'] = df['VictimCol'].astype(str)

    # Sort attacker list alphabetically
    all_attackers = sorted(df['AttackerCol'].dropna().unique(), key=str)

    # ------------------------------
    # Create a pivot table for the heatmap
    # ------------------------------
    data_pivot = df.pivot_table(
        index='AttackerCol',
        columns='VictimCol',
        values='FlowValue',
        aggfunc='sum',
        fill_value=0
    )
    data_pivot = data_pivot.reindex(index=all_attackers, columns=all_attackers, fill_value=0)

    # Define custom colormap: white (low) to red (high)
    cmap = LinearSegmentedColormap.from_list("white_red", ["white", "red"])

    # ------------------------------
    # Create the heatmap
    # ------------------------------
    plt.figure(figsize=(13, 13))
    ax = sns.heatmap(
        data_pivot,
        cmap=cmap,
        annot=True,
        fmt="d",
        linewidths=0,
        linecolor='black',
        vmin=0,
        annot_kws={"size": 16, "ha": "center", "va": "center", "fontweight": "bold"},
        cbar_kws={"label": "", "pad": 0.08}
    )

    # Set outer border visible and bold
    for _, spine in ax.spines.items():
        spine.set_visible(True)
        spine.set_linewidth(2)

    # ------------------------------
    # Set axis properties
    # ------------------------------
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=16, fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=16, fontweight='bold')
    ax.set_xlabel('Victim Country', fontsize=22, fontweight='bold')
    ax.set_ylabel('Attacker Country', fontsize=22, fontweight='bold')

    ax.set_aspect('equal')

    # ------------------------------
    # Customize colorbar
    # ------------------------------
    cbar = ax.collections[0].colorbar
    cbar.ax.set_title('# of Cases', fontsize=18, weight='bold', loc='left')
    cbar.ax.set_ylabel(' ', fontsize=15, weight='bold')
    cbar.ax.set_position([0.75, 0.194, 0.03, 0.58])
    cbar.ax.tick_params(labelsize=19)

    # Save to PDF
    plt.savefig(OUTPUT_PDF, format='pdf')
    print(f"[✓] Figure 8 saved to {OUTPUT_PDF}")

if __name__ == "__main__":
    final_df = process_filter_data(INPUT_CSV)
    draw_figure(final_df)