import matplotlib.pyplot as plt
import numpy as np
import json
import os
from openai import OpenAI
from app import KnowledgeBase, ForwardChainingEngine

def get_llm_probabilities(student_scores, majors_list):
    """
    Asks LLM to rate the probability/suitability of EACH major for the student.
    Returns a dictionary: {major_name: score_0_to_10}
    """
    api_key = "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"
    
    scores_text = ", ".join([f"{k}: {v}" for k, v in student_scores.items()])
    majors_text = ", ".join(majors_list)
    
    prompt = f"""
    You are an academic counselor.
    
    STUDENT PROFILE (RIASEC):
    {scores_text}
    
    LIST OF MAJORS:
    {majors_text}
    
    TASK:
    Analyze the compatibility of the student with EACH major in the list.
    Assign a "Match Score" from 0.0 to 10.0 for EVERY major.
    
    RESPONSE FORMAT (JSON ONLY):
    {{
        "scores": {{
            "Major Name 1": 8.5,
            "Major Name 2": 3.2,
            ...
        }}
    }}
    """
    
    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=api_key,
    )

    try:
        print("Requesting analysis from LLM (this may take a moment)...")
        completion = client.chat.completions.create(
          extra_headers={
            "HTTP-Referer": "http://localhost:5000", 
            "X-Title": "SISCER_TEST", 
          },
          model="x-ai/grok-4.1-fast:free",
          messages=[
            {"role": "user", "content": prompt}
          ]
        )
        
        content = completion.choices[0].message.content
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        data = json.loads(content)
        return data.get("scores", {})
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return {}

def main():
    # 1. Setup Data
    kb = KnowledgeBase()
    engine = ForwardChainingEngine(kb)
    
    # Define a Test Student Profile (e.g., High Realistic & Investigative)
    test_student_scores = {'R': 9, 'I': 8, 'A': 3, 'S': 2, 'E': 4, 'C': 5}
    print(f"Test Student Profile: {test_student_scores}")
    
    majors_names = list(kb.majors.keys())
    
    # 2. Calculate Forward Chaining Scores
    fc_scores = {}
    print("Calculating Forward Chaining scores...")
    for major in majors_names:
        profile = kb.majors[major]
        # Use the internal similarity method
        score = engine._calculate_similarity(test_student_scores, profile)
        fc_scores[major] = score

    # 3. Calculate LLM Scores
    llm_scores_map = get_llm_probabilities(test_student_scores, majors_names)
    
    # Align LLM scores with the majors list (handle missing keys if any)
    llm_scores = []
    fc_scores_list = []
    
    for major in majors_names:
        fc_scores_list.append(fc_scores.get(major, 0))
        llm_scores.append(llm_scores_map.get(major, 0))

    # 4. Visualization
    x = np.arange(len(majors_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(15, 8))
    rects1 = ax.bar(x - width/2, fc_scores_list, width, label='Forward Chaining', color='#2C241B')
    rects2 = ax.bar(x + width/2, llm_scores, width, label='LLM (AI)', color='#4285F4')
    
    ax.set_ylabel('Match Score (0-10)')
    ax.set_title('Perbandingan Probabilitas Kecocokan Jurusan (FC vs LLM)')
    ax.set_xticks(x)
    ax.set_xticklabels(majors_names, rotation=45, ha='right')
    ax.legend()
    
    ax.set_ylim(0, 11)
    
    plt.tight_layout()
    plt.savefig('probability_comparison.png')
    print("\nGrafik telah disimpan sebagai 'probability_comparison.png'")
    # plt.show()

if __name__ == "__main__":
    main()
