import pandas as pd
import re
from pathlib import Path

def load_data(data_dir: str) -> dict:
    """Loads CSV files into Pandas DataFrames."""
    # Mapping friendly names to the actual filenames in the directory
    files = {
        'supervisor_logs': 'supervisor_logs.csv',
        'bank_transfers': 'bank_transfers.csv',
        'wage_rates': 'wage_rates 3 (1).csv',
        'workers': 'workers (1).csv'
    }
    
    dataframes = {}
    for name, file_name in files.items():
        path = Path(data_dir) / file_name
        if path.exists():
            dataframes[name] = pd.read_csv(path)
            print(f"✅ Loaded {name} ({len(dataframes[name])} rows)")
        else:
            print(f"❌ File not found: {path}")
            
    return dataframes

def show_basic_info(df_name: str, df: pd.DataFrame):
    """Prints column names, data types, first 5 rows, and missing value counts."""
    print(f"\n" + "="*60)
    print(f"📊 Basic Info for: {df_name}")
    print("="*60)
    
    # Identify missing values and data types
    print("\n--- Column Types & Missing Values ---")
    info_df = pd.DataFrame({
        'Data Type': df.dtypes,
        'Missing Values': df.isna().sum(),
        '% Missing': (df.isna().sum() / len(df) * 100).round(2)
    })
    print(info_df.to_string())
    
    # Show first 5 rows
    print("\n--- First 5 Rows ---")
    print(df.head().to_string())

def analyze_formats(df_name: str, df: pd.DataFrame, columns: list, col_type: str):
    """Identifies unique string formats by masking digits (e.g., +91 98... -> +dd ddd...)."""
    for col in columns:
        if col in df.columns:
            print(f"\n🔍 Unique {col_type} Formats in '{col}':")
            # Drop NaN, convert to string, replace all digits with 'd'
            formats = df[col].dropna().astype(str).apply(
                lambda x: re.sub(r'\d', 'd', x)
            )
            format_counts = formats.value_counts()
            for fmt, count in format_counts.items():
                print(f"  - Format: '{fmt}' (Count: {count})")

def highlight_data_quality_issues(df_name: str, df: pd.DataFrame):
    """Highlights potential data quality issues like duplicates, missing values, or negatives."""
    print(f"\n⚠️ Potential Data Quality Issues in {df_name}:")
    issues_found = False
    
    # 1. Missing Values
    missing_cols = df.columns[df.isna().any()].tolist()
    if missing_cols:
        print(f"  - Missing values present in columns: {', '.join(missing_cols)}")
        issues_found = True
        
    # 2. Check for negative numbers in numeric columns (amounts, hours, etc.)
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        if (df[col] < 0).any():
            print(f"  - Negative values found in numeric column '{col}'")
            issues_found = True
            
    # 3. Check for exact duplicate records
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        print(f"  - Found {dup_count} exact duplicate rows")
        issues_found = True

    # 4. Inconsistent column names (e.g., leading/trailing spaces)
    bad_cols = [col for col in df.columns if col != col.strip()]
    if bad_cols:
        print(f"  - Columns with leading/trailing whitespaces: {', '.join(bad_cols)}")
        issues_found = True

    if not issues_found:
        print("  - No obvious structural issues found! 🎉")

def main():
    data_dir = "data"
    
    print("🚀 Starting Data Analysis Pipeline...\n")
    dataframes = load_data(data_dir)
    
    # Columns we suspect might contain phones or timestamps based on typical schemas
    phone_columns = ['worker_phone', 'phone']
    timestamp_columns = [
        'transfer_timestamp', 'work_date', 'entered_at', 
        'effective_from', 'effective_to', 'registered_on'
    ]
    
    for name, df in dataframes.items():
        # 2. Print column names, data types, and first 5 rows
        # 3. Identify missing values
        show_basic_info(name, df)
        
        # 4. Show unique formats for phone numbers and timestamps
        analyze_formats(name, df, phone_columns, "Phone")
        analyze_formats(name, df, timestamp_columns, "Timestamp")
        
        # 5. Highlight potential data quality issues
        highlight_data_quality_issues(name, df)

if __name__ == "__main__":
    main()
