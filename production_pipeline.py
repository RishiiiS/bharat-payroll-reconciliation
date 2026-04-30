import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
from pathlib import Path

# ==============================================================================
# 1. Data Cleaning
# ==============================================================================
def load_data(data_dir: str) -> dict:
    files = {
        'supervisor_logs': 'supervisor_logs.csv',
        'bank_transfers': 'bank_transfers.csv',
        'wage_rates': 'wage_rates 3 (1).csv',
        'workers': 'workers (1).csv'
    }
    
    dataframes = {}
    for name, file_name in files.items():
        path = Path(data_dir) / file_name
        dataframes[name] = pd.read_csv(path)
    return dataframes

def normalize_phones(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    df_clean = df.copy()
    for col in columns:
        if col in df_clean.columns:
            # Keep only digits
            cleaned = df_clean[col].astype(str).str.replace(r'\D', '', regex=True)
            # Take last 10 characters
            cleaned = cleaned.str[-10:]
            # Ensure it is exactly 10 digits
            cleaned = cleaned.apply(lambda x: x if len(str(x)) == 10 else pd.NA)
            df_clean[col] = cleaned
    return df_clean

def standardize_timestamps(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    df_clean = df.copy()
    for col in columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce', utc=True)
    return df_clean

def clean_data(dataframes: dict) -> dict:
    cleaned = {}
    phone_cols = ['worker_phone', 'phone']
    time_cols = ['transfer_timestamp', 'work_date', 'entered_at', 'registered_on', 'effective_from', 'effective_to']
    name_cols = ['worker_name', 'name']
    
    for name, df in dataframes.items():
        df_clean = df.copy()
        
        # Phone
        df_clean = normalize_phones(df_clean, phone_cols)
        
        # Timestamps
        df_clean = standardize_timestamps(df_clean, time_cols)
        
        # Names
        for col in name_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.lower().str.strip()
                df_clean[col] = df_clean[col].replace('nan', pd.NA)
                
        # Wage Rates Specifics
        if name == 'wage_rates':
            # Add row id for traceability
            df_clean['rate_source_row_id'] = df_clean.index.astype(str)
            
            # Fill effective_to
            max_date = pd.to_datetime('2099-12-31').tz_localize('UTC')
            df_clean['effective_to'] = df_clean['effective_to'].fillna(max_date)
            
        cleaned[name] = df_clean
        
    return cleaned

# ==============================================================================
# 2. Worker Matching
# ==============================================================================
def match_workers(logs_df: pd.DataFrame, workers_df: pd.DataFrame) -> pd.DataFrame:
    results = []
    
    phone_map = workers_df.dropna(subset=['phone']).groupby('phone')['worker_id'].apply(list).to_dict()
    name_map = workers_df.dropna(subset=['name']).groupby('name')['worker_id'].apply(list).to_dict()
    worker_names = list(name_map.keys())
    
    for _, log in logs_df.iterrows():
        log_id = log['log_id']
        phone = log['worker_phone']
        name = log['worker_name']
        
        worker_id = None
        confidence = 0.0
        needs_review = False
        reason = []
        
        # Exact phone match
        if pd.notna(phone) and phone in phone_map:
            matches = phone_map[phone]
            if len(matches) == 1:
                worker_id = matches[0]
                confidence = 1.0
            else:
                needs_review = True
                reason.append("multiple matches (shared phone)")
        else:
            # Fuzzy name match
            if pd.isna(name) or not str(name).strip():
                needs_review = True
                reason.append("no match (missing name and phone)")
            else:
                fuzzy_matches = process.extract(str(name), worker_names, scorer=fuzz.token_sort_ratio, limit=1)
                if not fuzzy_matches:
                    needs_review = True
                    reason.append("no match")
                else:
                    best_match, best_score, _ = fuzzy_matches[0]
                    confidence = best_score / 100.0
                    
                    if confidence < 0.60:
                        needs_review = True
                        reason.append(f"no match (low confidence: {confidence:.2f})")
                        confidence = 0.0
                    else:
                        matches = name_map[best_match]
                        if len(matches) > 1:
                            needs_review = True
                            reason.append(f"multiple matches (fuzzy name shared)")
                        else:
                            worker_id = matches[0]
                            if confidence < 0.85:
                                needs_review = True
                                reason.append(f"low confidence match ({confidence:.2f})")
                                
        results.append({
            'log_id': log_id,
            'worker_id': worker_id,
            'confidence_score': confidence,
            'needs_manual_review': needs_review,
            'review_reason_match': " | ".join(reason) if reason else ""
        })
        
    return pd.DataFrame(results)

# ==============================================================================
# 3. & 4. Expected Pay Calculation & Wage Rate Robustness
# ==============================================================================
def calculate_expected_pay(logs_df: pd.DataFrame, mapping_df: pd.DataFrame, workers_df: pd.DataFrame, wage_rates_df: pd.DataFrame) -> pd.DataFrame:
    df = logs_df.merge(mapping_df, on='log_id', how='left')
    df = df.merge(workers_df[['worker_id', 'role', 'state', 'seniority']], on='worker_id', how='left')
    
    # User requested hours_worked = (end_time - start_time) / 3600, but data only has 'hours'.
    # We rename 'hours' to 'hours_worked'
    if 'hours' in df.columns:
        df = df.rename(columns={'hours': 'hours_worked'})
    
    df['hourly_rate'] = 0.0
    df['expected_pay'] = 0.0
    df['rate_source_row_id'] = None
    
    new_review_reasons = []
    new_needs_review = []
    
    for idx, row in df.iterrows():
        review_flags = []
        if row['review_reason_match']:
            review_flags.append(row['review_reason_match'])
            
        needs_review = row['needs_manual_review']
        hours = row['hours_worked']
        
        # Shift validations
        if hours > 12:
            needs_review = True
            review_flags.append("unrealistic shift duration (>12 hrs)")
        elif hours <= 0:
            needs_review = True
            review_flags.append("invalid shift duration (<=0)")
            
        rate = 0.0
        source_id = None
        
        if pd.notna(row['worker_id']) and pd.notna(row['role']):
            work_date = row['work_date']
            mask = (
                (wage_rates_df['role'] == row['role']) &
                (wage_rates_df['state'] == row['state']) &
                (wage_rates_df['seniority'] == row['seniority']) &
                (wage_rates_df['effective_from'] <= work_date) &
                (wage_rates_df['effective_to'] >= work_date)
            )
            matches = wage_rates_df[mask]
            
            if len(matches) == 1:
                rate = matches.iloc[0]['hourly_rate_inr']
                source_id = matches.iloc[0]['rate_source_row_id']
            elif len(matches) > 1:
                needs_review = True
                review_flags.append("overlapping wage rates")
            else:
                needs_review = True
                review_flags.append("no wage rate found")
                
        df.at[idx, 'hourly_rate'] = rate
        df.at[idx, 'rate_source_row_id'] = source_id
        
        # Pay calculation
        expected_pay = max(0.0, hours * rate)
        df.at[idx, 'expected_pay'] = expected_pay
        
        new_needs_review.append(needs_review)
        new_review_reasons.append(" | ".join(review_flags))
        
    df['needs_manual_review'] = new_needs_review
    df['review_reason'] = new_review_reasons
    
    # 5. Final Output Format
    final_cols = [
        'log_id', 'worker_id', 'work_date', 'hours_worked', 'hourly_rate', 
        'expected_pay', 'confidence_score', 'needs_manual_review', 
        'review_reason', 'rate_source_row_id'
    ]
    return df[final_cols]

# ==============================================================================
# 6. Validation & Verification
# ==============================================================================
def verify_pipeline():
    print("🚀 Starting Production Pipeline Verification...\n")
    
    # Execute Pipeline
    raw = load_data('data')
    cleaned = clean_data(raw)
    mapping = match_workers(cleaned['supervisor_logs'], cleaned['workers'])
    final_df = calculate_expected_pay(cleaned['supervisor_logs'], mapping, cleaned['workers'], cleaned['wage_rates'])
    
    total = len(final_df)
    high_conf = len(final_df[(final_df['confidence_score'] >= 0.95) & (~final_df['needs_manual_review'])])
    flagged = final_df['needs_manual_review'].sum()
    
    print("-" * 50)
    print("A. Pipeline Summary")
    print("-" * 50)
    print(f"Total logs processed: {total}")
    print(f"High confidence matches (>= 0.95): {(high_conf/total*100):.2f}%")
    print(f"Logs flagged for review: {(flagged/total*100):.2f}%")
    
    print("\n" + "-" * 50)
    print("B. Data Integrity Checks")
    print("-" * 50)
    print(f"Negative hours: {(final_df['hours_worked'] < 0).sum()}")
    print(f"Hours > 12: {(final_df['hours_worked'] > 12).sum()}")
    print(f"Expected Pay > 5000: {(final_df['expected_pay'] > 5000).sum()}")
    print(f"Missing worker_id: {final_df['worker_id'].isna().sum()}")
    
    # Timezone check
    ts_check = cleaned['supervisor_logs']['work_date'].dt.tz is not None
    print(f"All timestamps are UTC: {'YES' if ts_check else 'NO'}")
    
    print("\n" + "-" * 50)
    print("C. Wage Rate Checks")
    print("-" * 50)
    print(f"Logs with 'no wage rate found': {final_df['review_reason'].str.contains('no wage rate found').sum()}")
    print(f"Logs with 'overlapping wage rates': {final_df['review_reason'].str.contains('overlapping wage rates').sum()}")
    
    print("\n" + "-" * 50)
    print("D. Distribution Check (Expected Pay)")
    print("-" * 50)
    valid_pay = final_df[final_df['expected_pay'] > 0]['expected_pay']
    if not valid_pay.empty:
        print(f"Min: ₹{valid_pay.min():.2f}")
        print(f"Max: ₹{valid_pay.max():.2f}")
        print(f"Average: ₹{valid_pay.mean():.2f}")
    
    print("\n" + "-" * 50)
    print("E. Debug Samples")
    print("-" * 50)
    display_cols = ['log_id', 'hours_worked', 'hourly_rate', 'expected_pay', 'review_reason']
    print("\n📈 Top 5 Logs (Highest Pay):")
    print(final_df.nlargest(5, 'expected_pay')[display_cols].to_string(index=False))
    
    print("\n📉 Bottom 5 Logs (Lowest Pay, >0):")
    print(final_df[final_df['expected_pay'] > 0].nsmallest(5, 'expected_pay')[display_cols].to_string(index=False))
    
    print("\n" + "=" * 60)
    print("7. Final Verification Output")
    print("=" * 60)
    
    is_safe = (flagged / total) < 0.10 and (final_df['hours_worked'] < 0).sum() == 0 # Arbitrary safety threshold
    
    print(f"SAFE TO PROCEED TO RECONCILIATION: {'YES' if is_safe else 'NO (Requires review of flagged anomalies)'}")
    print("\nAnomalies / Risks:")
    if (final_df['hours_worked'] > 12).sum() > 0:
        print("- Found logs with unrealistic shift durations (>12 hours). This massive outlier breaks budget logic.")
    if final_df['review_reason'].str.contains('overlapping wage rates').sum() > 0:
        print("- Found overlapping wage rates in the master data. Some roles/states have multiple active rates.")
        
    print("\nNote: 'start_time' and 'end_time' were not present in the source logs, so 'hours' was mapped directly to 'hours_worked'.")

if __name__ == "__main__":
    verify_pipeline()
