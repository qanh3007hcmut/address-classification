from utils.decorators import track_time_ns
import json

@track_time_ns
def export_sample(preprocess, src = "test/public.json", dst = "input_test/preprocessed_test.json"):
    with open(src, "r", encoding="utf-8") as f:
        tests = json.load(f)
    
    preprocesses = []
    for test in tests:
        preprocesses.append(
            {
                "text": test["text"],
                "expected": preprocess(test["text"])
            }
        )
    
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(preprocesses, f, ensure_ascii=False, indent=4) 
        
    print("Exported preprocessed test to", dst + "preprocessed_test.json")
    
def export_diff(preprocess, src = "input_test/sample_test.json", dst = "input_test/diff_test.json"):
    with open(src, "r", encoding="utf-8") as f:
        tests = json.load(f)
        
    fails = []
    for test in tests:
        processed = preprocess(test["text"])
        if processed != test["expected"]:
            fails.append(
                {
                    "text": test["text"],
                    "expected": test["expected"],
                    "processed": processed
                }
            )
            
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(fails, f, ensure_ascii=False, indent=4) 
        
    print("Exported preprocessed test to", dst + "preprocessed_test.json")
    