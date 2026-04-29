import pandas as pd
from rapidfuzz import process, fuzz
from clean_data import clean_pipeline
from analyze_data import load_data

def match_logs_to_workers(logs_df: pd.DataFrame, workers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Matches supervisor logs to workers based on:
    1. Exact phone match (primary)
    2. Fuzzy name match (fallback)
    
    Returns a DataFrame with [log_id, worker_id, confidence_score, needs_manual_review, review_reason]
    """
    
    results = []
    
    # Precompute dictionary maps for O(1) lookups
    # phone_to_workers: mapping of phone -> list of worker_ids (handles duplicate phones)
    phone_to_workers = workers_df.groupby('phone')['worker_id'].apply(list).to_dict()
    
    # name_to_workers: mapping of name -> list of worker_ids (handles duplicate names)
    name_to_workers = workers_df.dropna(subset=['name']).groupby('name')['worker_id'].apply(list).to_dict()
    worker_names = list(name_to_workers.keys())
    
    for _, log in logs_df.iterrows():
        log_id = log['log_id']
        log_phone = log['worker_phone']
        log_name = log['worker_name']
        
        worker_id = None
        confidence = 0.0
        needs_review = False
        reason = ""
        
        # ---------------------------------------------------------
        # 1. Primary Strategy: Exact Phone Match
        # ---------------------------------------------------------
        matched_workers_by_phone = phone_to_workers.get(log_phone, [])
        
        if len(matched_workers_by_phone) == 1:
            worker_id = matched_workers_by_phone[0]
            confidence = 1.0
            
        elif len(matched_workers_by_phone) > 1:
            needs_review = True
            reason = "multiple matches (phone number shared by multiple workers)"
            
        # ---------------------------------------------------------
        # 2. Fallback Strategy: Fuzzy Name Match
        # ---------------------------------------------------------
        else:
            if pd.isna(log_name) or not str(log_name).strip():
                needs_review = True
                reason = "no match (missing name and phone)"
            else:
                # fuzz.token_sort_ratio helps match "Pooja D." to "D. Pooja" regardless of word order
                matches = process.extract(str(log_name), worker_names, scorer=fuzz.token_sort_ratio, limit=1)
                
                if not matches:
                    needs_review = True
                    reason = "no match"
                else:
                    best_match_str, best_score, _ = matches[0]
                    confidence = best_score / 100.0
                    
                    if confidence < 0.60:
                        # Very low score -> hard reject
                        needs_review = True
                        reason = f"no match (best fuzzy score {confidence:.2f} is too low)"
                        confidence = 0.0
                    else:
                        matched_workers_by_name = name_to_workers.get(best_match_str, [])
                        
                        if len(matched_workers_by_name) > 1:
                            needs_review = True
                            reason = f"multiple matches (fuzzy name '{best_match_str}' shared by multiple workers)"
                        else:
                            worker_id = matched_workers_by_name[0]
                            # If between 0.60 and 0.85, assign the ID but flag for manual review
                            if confidence < 0.85:
                                needs_review = True
                                reason = f"low confidence match (fuzzy matched to '{best_match_str}')"
                                
        # ---------------------------------------------------------
        # Append Result
        # ---------------------------------------------------------
        results.append({
            'log_id': log_id,
            'worker_id': worker_id,
            'confidence_score': round(confidence, 2),
            'needs_manual_review': needs_review,
            'review_reason': reason
        })
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    print("🚀 Running Worker Matching Module...\n")
    
    # 1. Load Raw Data
    raw_data = load_data('data')
    
    # 2. Clean Data (Normalization is critical for matching!)
    # (Phone numbers will be strictly 10 digits, names will be stripped/lowercased)
    cleaned_data = clean_pipeline(raw_data)
    logs = cleaned_data['supervisor_logs']
    workers = cleaned_data['workers']
    
    # 3. Perform Matching
    print("\n🔗 Matching logs to workers...")
    mapping_df = match_logs_to_workers(logs, workers)
    
    # 4. Display Results
    print("\n📊 Matching Summary:")
    print(f"Total Logs Processed: {len(mapping_df)}")
    print(f"Exact/High Confidence Matches: {len(mapping_df[(mapping_df['confidence_score'] >= 0.85) & (~mapping_df['needs_manual_review'])])}")
    print(f"Total Needing Manual Review: {mapping_df['needs_manual_review'].sum()}")
    
    print("\n⚠️ Breakdown of Review Reasons:")
    print(mapping_df[mapping_df['needs_manual_review']]['review_reason'].value_counts().to_string())
    
    print("\n🔍 Snippet of Mapping Results:")
    print(mapping_df.head(15).to_string())
