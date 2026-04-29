import pandas as pd
from analyze_data import load_data

def normalize_phones(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Normalizes phone numbers to a 10-digit format.
    Removes +91, spaces, dashes, and extracts the last 10 digits.
    """
    df_cleaned = df.copy()
    for col in columns:
        if col in df_cleaned.columns:
            # Strip non-digit characters and keep the last 10 characters
            df_cleaned[col] = (
                df_cleaned[col]
                .astype(str)
                .str.replace(r'\D', '', regex=True)
                .str[-10:]
            )
            # Convert empty strings back to NaN
            df_cleaned[col] = df_cleaned[col].replace('', pd.NA)
    return df_cleaned

def standardize_timestamps_to_utc(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Converts specified columns to timezone-aware UTC datetime objects.
    """
    df_cleaned = df.copy()
    for col in columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce', utc=True)
    return df_cleaned

def standardize_names(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Standardizes names by converting them to lowercase and trimming extra spaces.
    """
    df_cleaned = df.copy()
    for col in columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.lower().str.strip()
            # Replace 'nan' strings that might have been casted back to true NaN
            df_cleaned[col] = df_cleaned[col].replace('nan', pd.NA)
    return df_cleaned

def clean_wage_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the wage_rates table:
    - Converts dates to UTC
    - Fills missing effective_to with a max date (2099-12-31)
    - Detects overlapping date ranges for the same role/state/seniority.
    """
    df_cleaned = df.copy()
    
    # Convert date columns to UTC
    df_cleaned = standardize_timestamps_to_utc(df_cleaned, ['effective_from', 'effective_to'])
    
    # Fill missing effective_to with the max date in UTC
    max_date = pd.to_datetime('2099-12-31').tz_localize('UTC')
    df_cleaned['effective_to'] = df_cleaned['effective_to'].fillna(max_date)
    
    # Sort to prepare for overlap detection
    df_cleaned = df_cleaned.sort_values(by=['role', 'state', 'seniority', 'effective_from'])
    
    # Shift effective_to down by 1 within the same group to compare with the current effective_from
    df_cleaned['prev_effective_to'] = df_cleaned.groupby(['role', 'state', 'seniority'])['effective_to'].shift(1)
    
    # If the current start date is before the previous end date, we have an overlap
    df_cleaned['has_overlap'] = df_cleaned['effective_from'] < df_cleaned['prev_effective_to']
    
    overlaps = df_cleaned[df_cleaned['has_overlap']]
    if not overlaps.empty:
        print(f"⚠️ Warning: Found {len(overlaps)} overlapping wage rate periods!")
        
    # Drop the temporary column used for calculation
    df_cleaned = df_cleaned.drop(columns=['prev_effective_to'])
    
    return df_cleaned

def clean_pipeline(dataframes: dict) -> dict:
    """
    Main orchestration pipeline that applies modular cleaning steps to all datasets.
    """
    cleaned_dataframes = {}
    
    # Define columns to target for specific cleaning operations
    phone_cols = ['worker_phone', 'phone']
    time_cols = ['transfer_timestamp', 'work_date', 'entered_at', 'registered_on']
    name_cols = ['worker_name', 'name']
    
    for name, df in dataframes.items():
        print(f"🧹 Processing {name}...")
        df_clean = df.copy()
        
        # 1. Normalize Phones
        df_clean = normalize_phones(df_clean, phone_cols)
        
        # 2. Standardize Names
        df_clean = standardize_names(df_clean, name_cols)
        
        # 3. Clean Timestamps & Custom Logic
        if name == 'wage_rates':
            df_clean = clean_wage_rates(df_clean)
        else:
            df_clean = standardize_timestamps_to_utc(df_clean, time_cols)
            
        cleaned_dataframes[name] = df_clean
        print(f"✅ Cleaned {name}")
        
    return cleaned_dataframes

if __name__ == "__main__":
    print("🚀 Starting Data Cleaning Pipeline...\n")
    
    # Load raw data using the function from the previous script
    raw_data = load_data('data')
    
    # Run the cleaning pipeline
    cleaned_data = clean_pipeline(raw_data)
    
    print("\n" + "="*50)
    print("🔍 Snippet: Cleaned 'supervisor_logs' (Names & Phones)")
    print("="*50)
    print(cleaned_data['supervisor_logs'][['worker_name', 'worker_phone', 'work_date']].head())
    
    print("\n" + "="*50)
    print("🔍 Snippet: Cleaned 'wage_rates' (Overlaps & Missing Dates filled)")
    print("="*50)
    print(cleaned_data['wage_rates'][['role', 'effective_from', 'effective_to', 'has_overlap']].head())
