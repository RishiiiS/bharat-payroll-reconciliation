import pandas as pd
from analyze_data import load_data
from clean_data import clean_pipeline
from match_workers import match_logs_to_workers
from validate_pipeline import calculate_expected_pay

def debug_expected_pay():
    # 1. Load & Process Data
    raw_data = load_data('data')
    cleaned_data = clean_pipeline(raw_data)
    
    logs = cleaned_data['supervisor_logs']
    workers = cleaned_data['workers']
    wage_rates = cleaned_data['wage_rates']
    
    mapping_df = match_logs_to_workers(logs, workers)
    calculated_df = calculate_expected_pay(logs, mapping_df, workers, wage_rates)
    
    # Check if start_time and end_time exist, otherwise use what we have
    cols_to_print = ['log_id', 'worker_id', 'work_date', 'hours', 'hourly_rate', 'expected_pay']
    for col in ['start_time', 'end_time', 'entered_at']:
        if col in calculated_df.columns:
            cols_to_print.append(col)
            
    # 2. Add validations
    calculated_df['flag_high_hours'] = calculated_df['hours'] > 12
    calculated_df['flag_high_pay'] = calculated_df['expected_pay'] > 5000
    cols_to_print.extend(['flag_high_hours', 'flag_high_pay'])
    
    # Ensure columns exist
    cols_to_print = [c for c in cols_to_print if c in calculated_df.columns]
    
    # 3. Print Top 5 highest expected pay
    print("\n" + "="*50)
    print("📈 Top 5 Logs with HIGHEST expected_pay")
    print("="*50)
    top_5 = calculated_df.nlargest(5, 'expected_pay')[cols_to_print]
    print(top_5.to_string(index=False))
    
    # 4. Print Bottom 5 lowest expected pay (excluding zero pay for a fairer look)
    print("\n" + "="*50)
    print("📉 Bottom 5 Logs with LOWEST expected_pay (excluding 0)")
    print("="*50)
    bottom_5 = calculated_df[calculated_df['expected_pay'] > 0].nsmallest(5, 'expected_pay')[cols_to_print]
    print(bottom_5.to_string(index=False))
    
    # 5. Check Anomalies
    print("\n" + "="*50)
    print("🕵️‍♂️ Anomaly Checks")
    print("="*50)
    
    high_hours_count = calculated_df['flag_high_hours'].sum()
    print(f"- Logs with unusually large hours (> 12): {high_hours_count}")
    if high_hours_count > 0:
        print("  Max hours found:", calculated_df['hours'].max())
        
    high_pay_count = calculated_df['flag_high_pay'].sum()
    print(f"- Logs with unusually large pay (> 5000): {high_pay_count}")
    if high_pay_count > 0:
        print("  Max pay found:", calculated_df['expected_pay'].max())
        
    # Check rates
    print(f"- Max hourly rate found: {calculated_df['hourly_rate'].max()}")
    print(f"- Min hourly rate found (excluding 0): {calculated_df[calculated_df['hourly_rate'] > 0]['hourly_rate'].min()}")
    
    # Print max pay rows details
    print("\nDetails of max pay row:")
    max_pay_row = calculated_df.loc[calculated_df['expected_pay'].idxmax()]
    print(max_pay_row[['log_id', 'worker_id', 'hours', 'hourly_rate', 'expected_pay', 'work_date', 'entered_at']].to_string())

if __name__ == "__main__":
    debug_expected_pay()
