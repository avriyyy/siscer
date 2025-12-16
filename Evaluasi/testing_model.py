import time
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from riasec_engine import ForwardChainingEngine, KnowledgeBase
from riasec_engine import get_llm_recommendation

load_dotenv()

def generate_synthetic_test_cases():
    test_cases = []
    types = ['R', 'I', 'A', 'S', 'E', 'C']
    
    kb = KnowledgeBase()
    
    for target_type in types:
        facts = set()
        scores = {t: 0 for t in types}
        
        for q in kb.questions:
            cat_map = {
                'Realistic': 'R', 'Investigative': 'I', 'Artistic': 'A',
                'Social': 'S', 'Enterprising': 'E', 'Conventional': 'C'
            }
            q_type = cat_map.get(q['kategori'])
            
            if q_type == target_type:
                facts.add(f"{q['id']}Y")
                scores[q_type] += 2 
            else:
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
        engine.facts = set()
        for fact in case['facts']:
            engine.add_fact(fact)
            
        start_time = time.time()
        
        scores = engine.run()
        recommendations = engine.recommend_majors()
        
        end_time = time.time()
        latencies.append(end_time - start_time)
        
        if recommendations:
            top_major = recommendations[0]
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
    
    for i, case in enumerate(test_cases):
        scores = case['expected_scores']
        
        start_time = time.time()
        
        result = get_llm_recommendation(scores)
        
        end_time = time.time()
        latencies.append(end_time - start_time)
        
        if result and 'recommendations' in result and len(result['recommendations']) > 0:
            top_rec = result['recommendations'][0]['major']
            
            kb = KnowledgeBase()
            if top_rec in kb.majors:
                major_profile = kb.majors[top_rec]
                p_only = {k: v for k, v in major_profile.items() if k in ['R','I','A','S','E','C']}
                dominant = max(p_only, key=p_only.get)
                
                if dominant == case['target_type']:
                    correct_matches += 1
            else:
                print(f"Warning: LLM recommended unknown major '{top_rec}'")
        
        print(f"Case {i+1}/{len(test_cases)} completed.")

    avg_latency = sum(latencies) / len(latencies)
    accuracy = (correct_matches / len(test_cases)) * 100
    
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Accuracy: {accuracy:.2f}%")
    
    return avg_latency, accuracy

def plot_results(fc_metrics, llm_metrics):
    labels = ['Forward Chaining', 'LLM (Llama‑3.3‑70B)']
    latencies = [fc_metrics[0], llm_metrics[0]]
    accuracies = [fc_metrics[1], llm_metrics[1]]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    colors = ['#2C241B', '#4285F4']
    ax1.bar(labels, latencies, color=colors)
    ax1.set_title('Perbandingan Waktu Eksekusi (Latency)')
    ax1.set_ylabel('Waktu (detik)')
    for i, v in enumerate(latencies):
        ax1.text(i, v, f"{v:.4f}s", ha='center', va='bottom')
        
    ax2.bar(labels, accuracies, color=colors)
    ax2.set_title('Perbandingan Akurasi (Kesesuaian Profil)')
    ax2.set_ylabel('Akurasi (%)')
    ax2.set_ylim(0, 110)
    for i, v in enumerate(accuracies):
        ax2.text(i, v, f"{v:.1f}%", ha='center', va='bottom')
        
    plt.tight_layout()
    plt.tight_layout()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'perbandingan_model.png')
    plt.savefig(output_path)
    print(f"\nGrafik telah disimpan sebagai '{output_path}'")
    print("\nGrafik telah disimpan sebagai 'perbandingan_model.png'")
    plt.show()

if __name__ == "__main__":
    test_cases = generate_synthetic_test_cases()
    
    fc_metrics = test_forward_chaining(test_cases)
    
    llm_metrics = test_llm(test_cases)
    
    plot_results(fc_metrics, llm_metrics)
