import matplotlib.pyplot as plt
import numpy as np
import json
import os
from dotenv import load_dotenv
from groq import Groq
from app import KnowledgeBase, ForwardChainingEngine

load_dotenv()

def get_llm_probabilities(student_scores, majors_list):
    """
    Asks LLM to rate the probability/suitability of EACH major for the student.
    Returns a dictionary: {major_name: score_0_to_10}
    """
    api_key = os.getenv("GROQ_API_KEY")
    
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
    
    client = Groq(api_key=api_key)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        print("Requesting analysis from LLM (this may take a moment)...")
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_completion_tokens=4096,
            top_p=0.95,
            stop=None,
            stream=False
        )
        
        content = completion.choices[0].message.content
        print(f"DEBUG: Raw LLM Content:\n{content[:500]}...") # Print first 500 chars

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
    print(f"DEBUG: LLM Response Keys: {list(llm_scores_map.keys())}")
    print(f"DEBUG: Expected Majors: {majors_names}")
    
    # Align LLM scores with the majors list (handle missing keys if any)
    llm_scores = []
    fc_scores_list = []
    
    for major in majors_names:
        fc_scores_list.append(fc_scores.get(major, 0))
        val = llm_scores_map.get(major, 0)
        if val == 0:
             # Try to find a partial match or case-insensitive match
             for k, v in llm_scores_map.items():
                 if major.lower() in k.lower() or k.lower() in major.lower():
                     val = v
                     break
        llm_scores.append(val)

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
