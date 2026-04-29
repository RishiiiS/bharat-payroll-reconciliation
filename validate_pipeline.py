import pandas as pd
import numpy as np

from analyze_data import load_data
from clean_data import clean_pipeline
from match_workers import match_logs_to_workers

def calculate_expected_pay(logs_df: pd.DataFrame, mapping_df: pd.DataFrame, workers_df: pd.DataFrame, wage_rates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates expected pay for each log entry.
    Merges logs with matched workers and applies the correct wage rate.
    """
    # 1. Merge logs with their mapped worker info
    df = logs_df.merge(mapping_df, on='log_id', how='left')
    
    # 2. Merge with workers to get role, state, seniority
    df = df.merge(workers_df[['worker_id', 'role', 'state', 'seniority']], on='worker_id', how='left')
    
    # Initialize calculation columns
    df['hourly_rate'] = 0.0
    df['expected_pay'] = 0.0
    df['wage_rate_matches'] = 0
    
    # 3. Match wage rates
    def get_wage_rate(row):
        # If no worker matched, we can't calculate pay
        if pd.isna(row['worker_id']) or pd.isna(row['role']):
            return 0.0, 0
            
        work_date = row['work_date']
        
        # Filter wage rates for matching role, state, seniority, and active date range
        mask = (
            (wage_rates_df['role'] == row['role']) &
            (wage_rates_df['state'] == row['state']) &
            (wage_rates_df['seniority'] == row['seniority']) &
            (wage_rates_df['effective_from'] <= work_date) &
            (wage_rates_df['effective_to'] >= work_date)
        )
        matches = wage_rates_df[mask]
        
        if len(matches) == 1:
            return matches.iloc[0]['hourly_rate_inr'], 1
        elif len(matches) > 1:
            return 0.0, len(matches) # Multiple overlapping rates
        else:
            return 0.0, 0 # No rates found
            
    # Apply logic
    res = df.apply(get_wage_rate, axis=1)
    df['hourly_rate'] = [r[0] for r in res]
    df['wage_rate_matches'] = [r[1] for r in res]
    
    # 4. Calculate final expected pay
    df['expected_pay'] = df['hours'] * df['hourly_rate']
    
    # 5. Update manual review flags based on wage rate anomalies
    multiple_mask = df['wage_rate_matches'] > 1
    df.loc[multiple_mask, 'needs_manual_review'] = True
    df.loc[multiple_mask, 'review_reason'] = df.loc[multiple_mask, 'review_reason'].apply(
        lambda x: f"{x} | multiple matching wage rates" if pd.notna(x) and str(x).strip() else "multiple matching wage rates"
    )
    
    no_match_mask = (df['wage_rate_matches'] == 0) & (df['worker_id'].notna())
    df.loc[no_match_mask, 'needs_manual_review'] = True
    df.loc[no_match_mask, 'review_reason'] = df.loc[no_match_mask, 'review_reason'].apply(
        lambda x: f"{x} | no matching wage rate found" if pd.notna(x) and str(x).strip() else "no matching wage rate found"
    )
    
    return df

def validate_pipeline():
    print("🚀 Starting Full Validation Pipeline...")
    
    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------
    print("\n📦 Loading and Cleaning Data...")
    raw_data = load_data('data')
    cleaned_data = clean_pipeline(raw_data)
    
    logs = cleaned_data['supervisor_logs']
    workers = cleaned_data['workers']
    wage_rates = cleaned_data['wage_rates']
    
    print("\n🔗 Matching logs to workers...")
    mapping_df = match_logs_to_workers(logs, workers)
    
    print("💰 Calculating Expected Pay...")
    calculated_df = calculate_expected_pay(logs, mapping_df, workers, wage_rates)
    
    # ---------------------------------------------------------
    # Validation & Printing (As Requested)
    # ---------------------------------------------------------
    total_logs = len(calculated_df)
    high_conf = len(calculated_df[(calculated_df['confidence_score'] >= 0.95) & (~calculated_df['needs_manual_review'])])
    flagged = calculated_df['needs_manual_review'].sum()
    
    print("\n" + "="*50)
    print("📊 1. Pipeline Summary")
    print("="*50)
    print(f"Total logs processed: {total_logs}")
    print(f"% of logs matched with high confidence (>= 0.95): {(high_conf / total_logs * 100):.2f}%")
    print(f"% of logs flagged for manual review: {(flagged / total_logs * 100):.2f}%")
    
    print("\n" + "="*50)
    print("✅ 2. Data Validations")
    print("="*50)
    
    neg_hours = (calculated_df['hours'] < 0).sum()
    print(f"[{'PASS' if neg_hours == 0 else 'FAIL'}] No negative hours worked (Found: {neg_hours})")
    
    neg_pay = (calculated_df['expected_pay'] < 0).sum()
    print(f"[{'PASS' if neg_pay == 0 else 'FAIL'}] No negative expected_pay (Found: {neg_pay})")
    
    missing_id_but_not_flagged = calculated_df[calculated_df['worker_id'].isna() & (~calculated_df['needs_manual_review'])].shape[0]
    print(f"[{'PASS' if missing_id_but_not_flagged == 0 else 'FAIL'}] All non-flagged logs have a worker_id (Missing: {missing_id_but_not_flagged})")
    
    print("\n" + "="*50)
    print("⚠️ 3. Wage Rate Logic Checks")
    print("="*50)
    no_wage_match = (calculated_df['worker_id'].notna() & (calculated_df['wage_rate_matches'] == 0)).sum()
    multiple_wage_match = (calculated_df['wage_rate_matches'] > 1).sum()
    
    print(f"Logs with NO matching wage rate: {no_wage_match}")
    print(f"Logs with MULTIPLE matching wage rates: {multiple_wage_match}")
    
    print("\n" + "="*50)
    print("💸 4. Expected Pay Distribution Summary")
    print("="*50)
    valid_pay = calculated_df[calculated_df['expected_pay'] > 0]['expected_pay']
    if len(valid_pay) > 0:
        print(f"Minimum Expected Pay: ₹{valid_pay.min():.2f}")
        print(f"Maximum Expected Pay: ₹{valid_pay.max():.2f}")
        print(f"Average Expected Pay: ₹{valid_pay.mean():.2f}")
    else:
        print("No valid expected pay calculated.")
        
    print("\n" + "="*50)
    print("🎲 5. Random Sample Rows (5 rows)")
    print("="*50)
    display_cols = ['worker_id', 'hours', 'hourly_rate', 'expected_pay', 'needs_manual_review', 'review_reason']
    
    # Rename hours to hours_worked for display
    sample_df = calculated_df[display_cols].rename(columns={'hours': 'hours_worked'})
    sample_df = sample_df.sample(min(5, len(calculated_df)), random_state=42)
    
    print(sample_df.to_string(index=False))

if __name__ == "__main__":
    validate_pipeline()
