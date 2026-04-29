import sys
import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from production_pipeline import load_data, clean_data, match_workers, calculate_expected_pay
from clean_data import normalize_phones

DISCREPANCY_THRESHOLD = 1000.0
SUSPICIOUS_THRESHOLD = 20000.0
MATCH_TOLERANCE = 100.0  # ₹100 tolerance for rounding/data issues

def prepare_bank_transfers(transfers_df: pd.DataFrame) -> pd.DataFrame:
    df = transfers_df.copy()
    df = normalize_phones(df, ['worker_phone'])
    
    if 'amount_paise' in df.columns:
        df['amount'] = pd.to_numeric(df['amount_paise'], errors='coerce') / 100.0
    elif 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    else:
        df['amount'] = 0.0
        
    df['amount'] = df['amount'].fillna(0.0)
    df['amount'] = df['amount'].clip(lower=0.0)
    return df

def map_transfers_to_workers(transfers_df: pd.DataFrame, workers_df: pd.DataFrame) -> pd.DataFrame:
    df = transfers_df.copy()
    phone_map = workers_df.dropna(subset=['phone']).groupby('phone')['worker_id'].apply(list).to_dict()
    
    df['worker_id'] = None
    df['bank_mapping_issue'] = None
    
    for idx, row in df.iterrows():
        phone = row['worker_phone']
        
        if pd.isna(phone) or phone not in phone_map:
            df.at[idx, 'bank_mapping_issue'] = "worker not found in bank data"
        else:
            matches = phone_map[phone]
            if len(matches) == 1:
                df.at[idx, 'worker_id'] = matches[0]
            else:
                df.at[idx, 'bank_mapping_issue'] = "multiple workers for bank record"
                
    return df

def reconcile(logs_final_df: pd.DataFrame, bank_mapped_df: pd.DataFrame, workers_df: pd.DataFrame) -> pd.DataFrame:
    # Aggregations
    trusted = logs_final_df[~logs_final_df['needs_manual_review']]
    untrusted = logs_final_df[logs_final_df['needs_manual_review']]
    
    trusted_agg = trusted.groupby('worker_id')['expected_pay'].sum().rename('trusted_expected_pay')
    untrusted_agg = untrusted.groupby('worker_id')['expected_pay'].sum().rename('untrusted_expected_pay')
    num_shifts = logs_final_df.groupby('worker_id')['log_id'].count().rename('num_shifts')
    
    expected_agg = pd.concat([trusted_agg, untrusted_agg, num_shifts], axis=1).fillna(0)
    
    bank_valid = bank_mapped_df[bank_mapped_df['worker_id'].notna()]
    actual_agg = bank_valid.groupby('worker_id')['amount'].sum().rename('total_actual_pay')
    num_payments = bank_valid.groupby('worker_id')['utr'].count().rename('num_payments')
    
    actual_agg = pd.concat([actual_agg, num_payments], axis=1).fillna(0)
    
    recon_df = pd.DataFrame(index=workers_df['worker_id'].unique())
    recon_df.index.name = 'worker_id'
    
    recon_df = recon_df.join(expected_agg, how='left')
    recon_df = recon_df.join(actual_agg, how='left')
    recon_df = recon_df.fillna(0)
    
    # 1. Tolerance-Based Reconciliation Logic
    recon_df['difference'] = recon_df['total_actual_pay'] - recon_df['trusted_expected_pay']
    
    recon_df['classification'] = "matched"
    recon_df['needs_manual_review'] = False
    recon_df['review_reasons'] = ""
    
    def classify_and_flag(row):
        reasons = []
        needs_review = False
        
        classification = "matched"
        trusted_expected = row['trusted_expected_pay']
        actual = row['total_actual_pay']
        diff = row['difference']
        
        # Missing payment logic takes precedence if no payment made at all but expected is > 0
        if trusted_expected > 0 and actual == 0:
            classification = "missing payment"
            reasons.append("missing payment")
            needs_review = True
        elif abs(diff) <= MATCH_TOLERANCE:
            classification = "matched"
        elif diff < 0: # Actual < Expected
            classification = "underpaid"
            reasons.append("underpayment")
            needs_review = True
        elif diff > 0: # Actual > Expected
            classification = "overpaid"
            reasons.append("overpayment")
            needs_review = True
            
        # Additional Flagging
        if row['untrusted_expected_pay'] > 0:
            needs_review = True
            reasons.append("includes untrusted logs")
            
        if abs(diff) > SUSPICIOUS_THRESHOLD:
            needs_review = True
            reasons.append("highly suspicious discrepancy (>₹20k)")
        elif abs(diff) > DISCREPANCY_THRESHOLD:
            needs_review = True
            reasons.append("large discrepancy (>₹1k)")
            
        return pd.Series([classification, needs_review, " | ".join(reasons)])
        
    res = recon_df.apply(classify_and_flag, axis=1)
    recon_df['classification'] = res[0]
    recon_df['needs_manual_review'] = res[1].astype(bool)
    recon_df['review_reason'] = res[2]
    
    return recon_df.reset_index()

def generate_report(recon_df: pd.DataFrame, bank_mapped_df: pd.DataFrame, logs_final_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("🚀 ADVANCED RECONCILIATION REPORT 🚀")
    print("=" * 60)
    
    # 2. Verify Aggregation Consistency
    total_expected = recon_df['trusted_expected_pay'].sum()
    total_actual = recon_df['total_actual_pay'].sum()
    
    print("\n💰 2. System-Wide Aggregation Checks")
    print("-" * 40)
    print(f"Total Trusted Expected Pay: ₹{total_expected:,.2f}")
    print(f"Total Bank Transfers Mapped: ₹{total_actual:,.2f}")
    diff = total_actual - total_expected
    print(f"Global Net Difference: {'+' if diff > 0 else ''}₹{diff:,.2f}")
    if abs(diff / total_expected) > 0.1:
        print("⚠️ WARNING: Global difference > 10%. Scope mismatch likely (dates, mapped workers, or huge errors).")
    else:
        print("✅ Global difference is within acceptable bulk variance limits.")
        
    # 4. Hidden Mapping Issues
    print("\n🕵️ 4. Hidden Mapping Issues")
    print("-" * 40)
    unmatched_banks = bank_mapped_df['bank_mapping_issue'].notna().sum()
    print(f"Bank Transfers not cleanly mapped: {unmatched_banks}")
    if unmatched_banks > 0:
        print(bank_mapped_df['bank_mapping_issue'].value_counts().to_string())

    # 5. Summary Metrics
    total_workers = len(recon_df)
    underpaid = (recon_df['classification'] == 'underpaid').sum()
    overpaid = (recon_df['classification'] == 'overpaid').sum()
    matched = (recon_df['classification'] == 'matched').sum()
    missing = (recon_df['classification'] == 'missing payment').sum()
    
    total_underpaid_amt = recon_df[recon_df['classification'] == 'underpaid']['difference'].abs().sum()
    total_overpaid_amt = recon_df[recon_df['classification'] == 'overpaid']['difference'].sum()
    
    print("\n📊 5. Summary Metrics (Post-Tolerance)")
    print("-" * 40)
    print(f"Total Workers:       {total_workers}")
    print(f"✅ Matched Workers:   {matched} (Tolerance: ₹{MATCH_TOLERANCE})")
    print(f"❌ Underpaid Workers: {underpaid} (Amount: ₹{total_underpaid_amt:,.2f})")
    print(f"⚠️ Overpaid Workers:  {overpaid} (Amount: ₹{total_overpaid_amt:,.2f})")
    print(f"🚫 Missing Payments:  {missing}")

    # 6. Sanity Checks
    print("\n🛡️ 6. Critical Sanity Checks")
    print("-" * 40)
    pay_no_shifts = recon_df[(recon_df['total_actual_pay'] > 0) & (recon_df['num_shifts'] == 0)]
    shifts_no_pay = recon_df[(recon_df['num_shifts'] > 0) & (recon_df['total_actual_pay'] == 0)]
    suspicious = recon_df[abs(recon_df['difference']) > SUSPICIOUS_THRESHOLD]
    
    print(f"Workers with payments but NO shifts: {len(pay_no_shifts)}")
    print(f"Workers with shifts but NO payments: {len(shifts_no_pay)}")
    print(f"Workers with suspicious diff (>₹20k): {len(suspicious)}")

    # 3. Validation Sample
    print("\n🎲 3. Worker-Level Aggregation Sample (Random 5)")
    print("-" * 40)
    sample_cols = ['worker_id', 'num_shifts', 'num_payments', 'trusted_expected_pay', 'total_actual_pay', 'difference']
    print(recon_df[sample_cols].sample(min(5, len(recon_df)), random_state=42).to_string(index=False))

    # 7. Debug Tables
    print("\n🎯 7. Debug Tables")
    print("-" * 40)
    cols_to_print = ['worker_id', 'trusted_expected_pay', 'total_actual_pay', 'difference', 'classification']
    
    print("\nTop 5 Smallest Differences (Closest to 0):")
    # Smallest absolute difference
    closest = recon_df.reindex(recon_df['difference'].abs().sort_values().index).head(5)
    print(closest[cols_to_print].to_string(index=False))
    
    print("\n📉 Top 5 Largest Underpayments:")
    under_df = recon_df[recon_df['classification'] == 'underpaid']
    if not under_df.empty:
        print(under_df.nsmallest(5, 'difference')[cols_to_print].to_string(index=False))
    else:
        print("None!")
        
    print("\n📈 Top 5 Largest Overpayments:")
    over_df = recon_df[recon_df['classification'] == 'overpaid']
    if not over_df.empty:
        print(over_df.nlargest(5, 'difference')[cols_to_print].to_string(index=False))
    else:
        print("None!")

    # 8. Final Verification
    print("\n" + "=" * 60)
    print("8. Final Verification Output")
    print("=" * 60)
    
    # Simple logic checks for realism
    consistent = len(pay_no_shifts) == 0 and len(shifts_no_pay) == 0
    realistic = len(suspicious) < (total_workers * 0.1) # Less than 10% highly suspicious
    
    print(f"Reconciliation is logically consistent? {'YES' if consistent else 'NO (Found pay/shift orphans)'}")
    print(f"Results are realistic? {'YES' if realistic else 'NO (Massive volume of suspicious discrepancies)'}")
    
    if len(suspicious) > 0:
        print("\n⚠️ Remaining Anomalies/Risks:")
        print(f"- {len(suspicious)} workers have discrepancies exceeding ₹20,000. These MUST be manually investigated.")
        print("- Root cause could be missing logs from specific vendors, or massive data-entry errors in expected pay.")
        
    if unmatched_banks > 0:
        print(f"- {unmatched_banks} bank transfers could not be cleanly mapped to a single worker. Check phone numbers.")

def main():
    print("Initializing Advanced Reconciliation Engine...")
    
    data_dir = os.path.join(ROOT_DIR, 'data')
    raw = load_data(data_dir)
    cleaned = clean_data(raw)
    mapping = match_workers(cleaned['supervisor_logs'], cleaned['workers'])
    logs_final = calculate_expected_pay(cleaned['supervisor_logs'], mapping, cleaned['workers'], cleaned['wage_rates'])
    
    transfers = prepare_bank_transfers(cleaned['bank_transfers'])
    bank_mapped = map_transfers_to_workers(transfers, cleaned['workers'])
    
    recon_df = reconcile(logs_final, bank_mapped, cleaned['workers'])
    
    generate_report(recon_df, bank_mapped, logs_final)
    
    final_cols = [
        'worker_id', 'trusted_expected_pay', 'total_actual_pay', 'difference', 
        'num_shifts', 'num_payments', 'needs_manual_review', 'review_reason', 'classification'
    ]
    final_recon_df = recon_df[final_cols]
    
    out_path = os.path.join(data_dir, 'reconciliation_results.csv')
    final_recon_df.to_csv(out_path, index=False)
    print(f"\n✅ Advanced reconciliation successfully saved to {out_path}")

if __name__ == "__main__":
    main()
