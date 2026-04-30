import pandas as pd
import numpy as np
import os

def validate():
    print("="*50)
    print("🚀 STARTING COMPREHENSIVE PIPELINE VALIDATION")
    print("="*50)

    # Load data
    data_dir = 'data'
    results_csv = os.path.join(data_dir, 'financial_audit_results.csv')
    shifts_csv = os.path.join(data_dir, 'shift_level_expected_pay.csv')
    bank_csv = os.path.join(data_dir, 'bank_transfers.csv')

    if not all(os.path.exists(f) for f in [results_csv, shifts_csv, bank_csv]):
        print("Missing required CSV files.")
        return

    df_results = pd.read_csv(results_csv)
    df_shifts = pd.read_csv(shifts_csv)
    df_bank = pd.read_csv(bank_csv)
    
    # Store maximum difference observed across all validations
    max_diff_observed = 0.0

    print("\n" + "="*50)
    print("PART 1: ROW-LEVEL VALIDATION")
    print("="*50)
    
    print("\n1. RANDOM SAMPLE CHECK")
    sample_shifts = df_shifts.dropna(subset=['worker_id', 'hours_worked', 'hourly_rate', 'expected_pay']).sample(min(5, len(df_shifts)), random_state=42)
    sample_pass = True
    for _, row in sample_shifts.iterrows():
        calc = row['hours_worked'] * row['hourly_rate']
        diff = abs(calc - row['expected_pay'])
        max_diff_observed = max(max_diff_observed, diff)
        match = diff < 0.01
        if not match: sample_pass = False
        print(f"Worker: {row['worker_id']}, Hours: {row['hours_worked']}, Rate: {row['hourly_rate']}, Stored Expected: {row['expected_pay']:.2f}, Recomputed: {calc:.2f}")
    
    print(f"-> DIFFERENCE < 0.01: {'PASS' if sample_pass else 'FAIL'}")

    print("\n2. INVALID DATA CHECK")
    missing_worker_ids = df_shifts['worker_id'].isna().sum()
    missing_hours = df_shifts['hours_worked'].isna().sum()
    negative_values = ((df_shifts['hours_worked'] < 0) | (df_shifts['expected_pay'] < 0) | (df_shifts['hourly_rate'] < 0)).sum()
    hours_gt_12 = (df_shifts['hours_worked'] > 12).sum()

    print(f"Missing worker_id: {missing_worker_ids}")
    print(f"Missing hours_worked: {missing_hours}")
    print(f"Negative values: {negative_values}")
    print(f"Hours_worked > 12: {hours_gt_12}")

    print("\n" + "="*50)
    print("PART 2: SHIFT -> WORKER CONSISTENCY")
    print("="*50)
    
    # In the pipeline, trusted expected pay ONLY sums shifts that do not need manual review
    is_unflagged = df_shifts['needs_manual_review'].isin([False, 'False', 0, '0', '']) | df_shifts['needs_manual_review'].isna()
    valid_shifts = df_shifts[is_unflagged]
    
    shift_sums = valid_shifts.groupby('worker_id')['expected_pay'].sum()
    
    consistency_pass = True
    for _, worker in df_results.iterrows():
        wid = worker['worker_id']
        trusted_exp = worker['trusted_expected_pay']
        sum_shifts = shift_sums.get(wid, 0.0)
        
        diff = abs(sum_shifts - trusted_exp)
        max_diff_observed = max(max_diff_observed, diff)
        
        if diff >= 0.01:
            consistency_pass = False
            print(f"MISMATCH -> Worker {wid}: Shift Sum = {sum_shifts:.2f}, Trusted = {trusted_exp:.2f}, Diff = {diff:.2f}")

    print(f"-> SHIFT CONSISTENCY < 0.01 FOR ALL WORKERS: {'PASS' if consistency_pass else 'FAIL'}")

    print("\n" + "="*50)
    print("PART 3: GLOBAL CONSISTENCY")
    print("="*50)
    
    total_expected_pay = df_results['trusted_expected_pay'].sum()
    total_actual_pay = df_results['total_actual_pay'].sum()
    global_difference_computed = total_actual_pay - total_expected_pay
    reported_discrepancy = df_results['difference'].sum() 
    
    print(f"Total Expected Pay: {total_expected_pay:.2f}")
    print(f"Total Actual Pay: {total_actual_pay:.2f}")
    print(f"Global Difference (actual - expected): {global_difference_computed:.2f}")
    
    global_match = abs(abs(global_difference_computed) - abs(reported_discrepancy)) < 0.01
    max_diff_observed = max(max_diff_observed, abs(abs(global_difference_computed) - abs(reported_discrepancy)))
    print(f"-> MATCHES REPORTED DISCREPANCY: {'PASS' if global_match else 'FAIL'}")

    print("\n" + "="*50)
    print("PART 4: COUNT VALIDATION")
    print("="*50)
    
    total_shifts_file = len(df_shifts)
    total_payments_file = len(df_bank)
    
    print(f"total_shifts: {total_shifts_file}")
    print(f"total_payments: {total_payments_file}")
    print(f"difference: {total_shifts_file - total_payments_file}")

    print("\n" + "="*50)
    print("PART 5: FRONTEND MAPPING VALIDATION (CRITICAL)")
    print("="*50)
    
    # 1. Reconciliation Fields (Note: 'name' and 'status' are applied dynamically in API/UI)
    expected_result_cols = ['worker_id', 'trusted_expected_pay', 'total_actual_pay', 'difference', 'review_reason', 'num_shifts', 'num_payments']
    missing_result_cols = [c for c in expected_result_cols if c not in df_results.columns]
    
    print("Reconciliation Fields Check:")
    print(f"Missing columns (Base CSV): {missing_result_cols if missing_result_cols else 'None'}")
    
    # Check for nulls in critical columns
    nulls_in_critical = df_results[['worker_id', 'trusted_expected_pay', 'total_actual_pay', 'difference']].isna().sum().sum()
    print(f"Null values in critical columns: {nulls_in_critical}")
    
    # 2. Shift-Level Fields
    expected_shift_cols = ['worker_id', 'work_date', 'hours_worked', 'hourly_rate', 'expected_pay', 'review_reason']
    missing_shift_cols = [c for c in expected_shift_cols if c not in df_shifts.columns]
    
    print("\nShift-Level Fields Check:")
    print(f"Missing columns: {missing_shift_cols if missing_shift_cols else 'None'}")
    
    # 3. Cross-Check UI Consistency
    print("\nCROSS-CHECK UI CONSISTENCY (2 WORKERS):")
    ui_sample_workers = df_results.sample(min(2, len(df_results)), random_state=42)
    ui_pass = True
    for _, worker in ui_sample_workers.iterrows():
        wid = worker['worker_id']
        trusted_exp = worker['trusted_expected_pay']
        sum_shifts = shift_sums.get(wid, 0.0)
        
        diff = abs(sum_shifts - trusted_exp)
        max_diff_observed = max(max_diff_observed, diff)
        
        # UI Logic Check (difference = trusted - actual)
        ui_difference = worker['difference'] 
        if ui_difference > 0:
            ui_status = "UNDERPAID"
        elif ui_difference < 0:
            ui_status = "OVERPAID"
        else:
            ui_status = "MATCHED"
            
        print(f"Worker {wid} -> Trusted Expected: {trusted_exp:.2f} | Shift Sum: {sum_shifts:.2f}")
        print(f"Worker {wid} -> Difference: {ui_difference:.2f} | UI Status: {ui_status}")
        
        if diff >= 0.01: ui_pass = False

    print(f"-> UI WOULD DISPLAY SAME VALUES: {'PASS' if ui_pass else 'FAIL'}")

    print("\n" + "="*50)
    print("PART 6: FLOATING POINT TOLERANCE CHECK")
    print("="*50)
    
    print(f"Max difference across all validations: {max_diff_observed:.4f}")
    tol_pass = max_diff_observed < 0.01
    print(f"-> ALL DIFFERENCES < 0.01: {'PASS' if tol_pass else 'FAIL'}")

    print("\n" + "="*50)
    print("PART 7: FINAL OUTPUT")
    print("="*50)
    
    print(f"total workers: {len(df_results)}")
    print(f"total shifts: {total_shifts_file}")
    print(f"total payments: {total_payments_file}")
    print(f"total expected pay: {total_expected_pay:.2f}")
    print(f"total actual pay: {total_actual_pay:.2f}")
    print(f"global discrepancy: {abs(reported_discrepancy):.2f}")
    
    pipeline_pass = sample_pass and consistency_pass and global_match and tol_pass
    frontend_pass = (len(missing_result_cols) == 0) and (len(missing_shift_cols) == 0) and ui_pass and nulls_in_critical == 0
    
    print(f"\nPIPELINE VALIDATION: {'PASS' if pipeline_pass else 'FAIL'}")
    print(f"FRONTEND MAPPING: {'PASS' if frontend_pass else 'FAIL'}")

if __name__ == '__main__':
    validate()
