import csv
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import ask, get_api_call_count

INPUT_CSV  = "eval/questions.csv"
OUTPUT_CSV = "eval/baseline_results.csv"

def read_questions(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    questions = read_questions(INPUT_CSV)
    print(f"Running LLM-alone baseline on {len(questions)} questions...\n")

    rows = []
    for i, q in enumerate(questions, start=1):
        qid      = q["question_id"].strip()
        text     = q["question"].strip()
        category = q["category"].strip()
        refs     = q.get("reference_articles", "").strip()

        print(f"[{i:02d}/{len(questions)}] {qid} ({category}) — {text[:60]}...")

        answer = ask(text) 
        
        # 5-second delay to avoid hitting the 8k TPM limit
        time.sleep(5) 

        rows.append({
            "question_id": qid,
            "category":    category,
            "question":    text,
            "reference_articles": refs,
            "llm_alone_answer": answer,
            "is_correct":   "", 
            "error_type":   "",   
            "cited_article": "",  
            "notes":        "",   
        })

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print(f"\n✅ Done. {len(rows)} answers saved to {OUTPUT_CSV}")
    print(f"   Real API calls (excluding cache): {get_api_call_count()}")

if __name__ == "__main__":
    main()