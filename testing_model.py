import time
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
from app import ForwardChainingEngine, KnowledgeBase, get_llm_recommendation

load_dotenv()

def generate_synthetic_test_cases():
    """
    Generates 6 test cases, one for each RIASEC dominant type.
    Returns a list of dictionaries: {'type': 'R', 'answers': [...], 'scores': {...}}
    """
    test_cases = []
    types = ['R', 'I', 'A', 'S', 'E', 'C']
    
    # We need to know which Question IDs correspond to which Type to generate correct answers
    # Let's inspect the KB questions
    kb = KnowledgeBase()
    
    for target_type in types:
        # Simulate a user who answers 'Y' to all questions of target_type, and 'N' to others
        facts = set()
        scores = {t: 0 for t in types}
        
        for q in kb.questions:
            # We need to know the category of the question. 
            # In questions.csv, 'kategori' is full name (Realistic, etc.)
            # We need to map it to code (R, I, etc.)
            cat_map = {
                'Realistic': 'R', 'Investigative': 'I', 'Artistic': 'A',
                'Social': 'S', 'Enterprising': 'E', 'Conventional': 'C'
            }
            q_type = cat_map.get(q['kategori'])
            
            if q_type == target_type:
                # Answer Yes
                facts.add(f"{q['id']}Y")
                scores[q_type] += 2 # Based on rules.csv (2 points for Y)
            else:
                # Answer No
                facts.add(f"{q['id']}N")
        
        test_cases.append({
            'target_type': target_type,
            'facts': facts,
            'expected_scores': scores
        })
        
    return test_cases

def test_forward_chaining(test_cases):
    kb = KnowledgeBase()
    engine = ForwardChainingEngine(kb)
    
    latencies = []
    correct_matches = 0
    
    print("\n--- Testing Forward Chaining ---")
    
    for case in test_cases:
        # Reset engine facts
        engine.facts = set()
        for fact in case['facts']:
            engine.add_fact(fact)
            
        start_time = time.time()
        
        # Run Inference
        scores = engine.run()
        recommendations = engine.recommend_majors()
        
        end_time = time.time()
        latencies.append(end_time - start_time)
        
        # Check Accuracy (Top recommendation should match target type)
        if recommendations:
            top_major = recommendations[0]
            # Check if the major's dominant type matches target
            # major['riasec_code'] is like 'RIS'
            if top_major['riasec_code'].startswith(case['target_type']):
                correct_matches += 1
                
    avg_latency = sum(latencies) / len(latencies)
    accuracy = (correct_matches / len(test_cases)) * 100
    
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Accuracy: {accuracy:.2f}%")
    
    return avg_latency, accuracy

def test_llm(test_cases):
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    print(f"\n--- Testing LLM (Groq: {model_name}) ---")
    print("Note: This involves real API calls and may take some time...")
    
    latencies = []
    correct_matches = 0
    
    # Limit to 3 cases to save time/tokens if needed, but user asked for performance test.
    # Let's run all 6 for completeness.
    for i, case in enumerate(test_cases):
        scores = case['expected_scores']
        
        start_time = time.time()
        
        # Call LLM
        result = get_llm_recommendation(scores)
        
        end_time = time.time()
        latencies.append(end_time - start_time)
        
        # Check Accuracy
        # LLM returns JSON with "recommendations": [{"major": "...", ...}]
        if result and 'recommendations' in result and len(result['recommendations']) > 0:
            top_rec = result['recommendations'][0]['major']
            
            # We need to check if this major is valid for the target type
            # We can check against our local KB to see the major's profile
            kb = KnowledgeBase()
            if top_rec in kb.majors:
                major_profile = kb.majors[top_rec]
                # Find dominant type of this major
                # Filter only RIASEC keys
                p_only = {k: v for k, v in major_profile.items() if k in ['R','I','A','S','E','C']}
                dominant = max(p_only, key=p_only.get)
                
                if dominant == case['target_type']:
                    correct_matches += 1
            else:
                # LLM hallucinated a major or format mismatch
                print(f"Warning: LLM recommended unknown major '{top_rec}'")
        
        print(f"Case {i+1}/{len(test_cases)} completed.")

    avg_latency = sum(latencies) / len(latencies)
    accuracy = (correct_matches / len(test_cases)) * 100
    
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Accuracy: {accuracy:.2f}%")
    
    return avg_latency, accuracy

def plot_results(fc_metrics, llm_metrics):
    labels = ['Forward Chaining', 'LLM (AI)']
    latencies = [fc_metrics[0], llm_metrics[0]]
    accuracies = [fc_metrics[1], llm_metrics[1]]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot Latency
    colors = ['#2C241B', '#4285F4']
    ax1.bar(labels, latencies, color=colors)
    ax1.set_title('Perbandingan Waktu Eksekusi (Latency)')
    ax1.set_ylabel('Waktu (detik)')
    for i, v in enumerate(latencies):
        ax1.text(i, v, f"{v:.4f}s", ha='center', va='bottom')
        
    # Plot Accuracy
    ax2.bar(labels, accuracies, color=colors)
    ax2.set_title('Perbandingan Akurasi (Kesesuaian Profil)')
    ax2.set_ylabel('Akurasi (%)')
    ax2.set_ylim(0, 110)
    for i, v in enumerate(accuracies):
        ax2.text(i, v, f"{v:.1f}%", ha='center', va='bottom')
        
    plt.tight_layout()
    plt.savefig('model_performance_comparison.png')
    print("\nGrafik telah disimpan sebagai 'model_performance_comparison.png'")
    plt.show()

if __name__ == "__main__":
    # 1. Generate Data
    test_cases = generate_synthetic_test_cases()
    
    # 2. Test Forward Chaining
    fc_metrics = test_forward_chaining(test_cases)
    
    # 3. Test LLM
    llm_metrics = test_llm(test_cases)
    
    # 4. Visualize
    plot_results(fc_metrics, llm_metrics)
