import sys
import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from production_pipeline import load_data, clean_data, match_workers, calculate_expected_pay
from backend.reconcile import prepare_bank_transfers, map_transfers_to_workers

def main():
    print("Initializing Deep Root Cause Analysis...\n")
    
    # -------------------------------------------------------------------------
    # Pre-computation / Loading
    # -------------------------------------------------------------------------
    data_dir = os.path.join(ROOT_DIR, 'data')
    raw = load_data(data_dir)
    cleaned = clean_data(raw)
    
    # Run pipelines
    mapping = match_workers(cleaned['supervisor_logs'], cleaned['workers'])
    logs_final = calculate_expected_pay(cleaned['supervisor_logs'], mapping, cleaned['workers'], cleaned['wage_rates'])
    transfers = prepare_bank_transfers(cleaned['bank_transfers'])
    bank_mapped = map_transfers_to_workers(transfers, cleaned['workers'])
    
    # Filter valid data
    trusted_logs = logs_final[~logs_final['needs_manual_review']].copy()
    valid_bank = bank_mapped[bank_mapped['worker_id'].notna()].copy()
    
    # Need timestamps for time-window checks, so merge back the work_date from cleaned supervisor logs
    trusted_logs = trusted_logs.merge(cleaned['supervisor_logs'][['log_id', 'work_date']], on='log_id', how='left')
    
    # -------------------------------------------------------------------------
    # 1. Payment vs Shift Count Analysis
    # -------------------------------------------------------------------------
    print("=" * 60)
    print("1. Payment vs Shift Count Analysis")
    print("=" * 60)
    total_shifts = len(trusted_logs)
    total_payments = len(valid_bank)
    ratio = total_payments / total_shifts if total_shifts > 0 else 0
    
    print(f"Total Shifts Logged: {total_shifts}")
    print(f"Total Bank Payments: {total_payments}")
    print(f"Ratio (Payments / Shifts): {ratio:.2f}")
    
    shifts_per_worker = trusted_logs.groupby('worker_id').size()
    payments_per_worker = valid_bank.groupby('worker_id').size()
    
    print(f"Avg Shifts per Worker: {shifts_per_worker.mean():.2f}")
    print(f"Avg Payments per Worker: {payments_per_worker.mean():.2f}")
    
    # -------------------------------------------------------------------------
    # 2. Time Window Alignment Check
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("2. Time Window Alignment Check")
    print("=" * 60)
    
    log_min_date = trusted_logs['work_date'].min()
    log_max_date = trusted_logs['work_date'].max()
    bank_min_date = valid_bank['transfer_timestamp'].min()
    bank_max_date = valid_bank['transfer_timestamp'].max()
    
    print("Supervisor Logs:")
    print(f"  Min Date: {log_min_date}")
    print(f"  Max Date: {log_max_date}")
    print("Bank Transfers:")
    print(f"  Min Date: {bank_min_date}")
    print(f"  Max Date: {bank_max_date}")
    
    same_range = (log_min_date == bank_min_date) and (log_max_date == bank_max_date)
    print(f"\nDo both datasets cover same date range? {'YES' if same_range else 'NO'}")
    
    print("\nDaily Volume Comparison (Expected vs Actual):")
    log_daily = trusted_logs.groupby(trusted_logs['work_date'].dt.date)['expected_pay'].sum()
    bank_daily = valid_bank.groupby(valid_bank['transfer_timestamp'].dt.date)['amount'].sum()
    
    daily_comp = pd.DataFrame({'Expected': log_daily, 'Actual': bank_daily}).fillna(0)
    print(daily_comp.head(10).to_string())
    print("... (truncated)")
    
    # -------------------------------------------------------------------------
    # 3. Payment Aggregation Pattern
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("3. Payment Aggregation Pattern")
    print("=" * 60)
    
    agg_df = pd.DataFrame({
        'trusted_expected_pay': trusted_logs.groupby('worker_id')['expected_pay'].sum(),
        'num_shifts': shifts_per_worker,
        'total_actual_pay': valid_bank.groupby('worker_id')['amount'].sum(),
        'num_payments': payments_per_worker
    }).fillna(0)
    
    agg_df['avg_expected_per_shift'] = agg_df['trusted_expected_pay'] / agg_df['num_shifts']
    agg_df['avg_payment_amount'] = agg_df['total_actual_pay'] / agg_df['num_payments']
    
    print(agg_df[['avg_expected_per_shift', 'avg_payment_amount']].head(5).to_string())
    
    # -------------------------------------------------------------------------
    # 4. Missing Payment Detection
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("4. Missing Payment Detection")
    print("=" * 60)
    
    agg_df['difference'] = agg_df['total_actual_pay'] - agg_df['trusted_expected_pay']
    
    missing_payments_flag = (agg_df['num_payments'] < agg_df['num_shifts']) & (agg_df['difference'] < -1000)
    print(f"Workers flagged (fewer payments AND large underpayment): {missing_payments_flag.sum()}")
    
    # -------------------------------------------------------------------------
    # 5. Distribution Comparison
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("5. Distribution Comparison")
    print("=" * 60)
    
    exp = trusted_logs['expected_pay']
    act = valid_bank['amount']
    
    print("Expected Pay Per Shift:")
    print(f"  Min: ₹{exp.min():.2f}")
    print(f"  Max: ₹{exp.max():.2f}")
    print(f"  Avg: ₹{exp.mean():.2f}")
    
    print("\nActual Bank Payment Amounts:")
    print(f"  Min: ₹{act.min():.2f}")
    print(f"  Max: ₹{act.max():.2f}")
    print(f"  Avg: ₹{act.mean():.2f}")
    
    # -------------------------------------------------------------------------
    # 6. Top Root Cause Signals
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("6. Top Root Cause Signals")
    print("=" * 60)
    
    fewer_payments = total_payments < total_shifts
    mismatched_time = log_max_date > bank_max_date
    aggregation = act.mean() > exp.mean() * 1.5
    
    print(f"Are payments fewer than shifts? {'YES' if fewer_payments else 'NO'}")
    print(f"Is time range mismatched? {'YES' if mismatched_time else 'NO'}")
    print(f"Is aggregation happening? {'YES' if aggregation else 'NO'}")
    
    lower_amounts = act.mean() < exp.mean()
    if lower_amounts:
        print("Is underpayment due to missing entries or lower amounts? LOWER AMOUNTS")
    else:
        print("Is underpayment due to missing entries or lower amounts? MISSING ENTRIES (Shifts outnumber payments)")
        
    # -------------------------------------------------------------------------
    # 7. Final Verdict
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("7. Final Verdict")
    print("=" * 60)
    
    if mismatched_time and fewer_payments:
        root_cause = "TIME WINDOW CUTOFF: Bank transfers end earlier than the shift logs."
        contributing = "Recent shifts have been logged but simply not paid out yet."
        conf = "HIGH"
    elif lower_amounts:
        root_cause = "RATE DISCREPANCY / DEDUCTIONS: The bank transfers are systematically paying less than the expected hourly rate."
        contributing = "Could be vendor fees, taxes, or outdated wage rate master data."
        conf = "MEDIUM"
    elif aggregation and fewer_payments:
        root_cause = "MISSING ENTRIES WITH AGGREGATION: Payments are grouped, but some groups are entirely missing."
        contributing = "Check if specific regions or vendors failed to submit payment batches."
        conf = "HIGH"
    elif fewer_payments:
         root_cause = "MISSING PAYMENTS: Payments are 1-to-1 but some shifts are simply missing from the bank file."
         contributing = "Payments might have failed or bounced."
         conf = "HIGH"
    else:
        root_cause = "UNKNOWN SYSTEMIC ERROR: Further investigation required."
        contributing = "N/A"
        conf = "LOW"
        
    print(f"Primary Root Cause: {root_cause}")
    print(f"Secondary Contributing Factors: {contributing}")
    print(f"Confidence Level: {conf}")

if __name__ == "__main__":
    main()
