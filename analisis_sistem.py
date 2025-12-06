import matplotlib.pyplot as plt
import pandas as pd
from app import KnowledgeBase

def analyze_system_metrics():
    """
    Analyzes the system's components and generates a summary table.
    """
    kb = KnowledgeBase()
    
    # 1. Knowledge Base Stats
    total_majors = len(kb.majors)
    total_questions = len(kb.questions)
    total_rules = len(kb.rules)
    
    # 2. System Capabilities
    capabilities = [
        "Forward Chaining Inference",
        "Rule-Based Logic (IF-THEN)",
        "Cosine Similarity Matching",
        "LLM Integration (DeepSeek)",
        "Dynamic Quiz UI (Wizard)",
        "Session Management"
    ]
    
    # 3. Technical Stack
    tech_stack = [
        "Python (Flask)",
        "Matplotlib (Visualization)",
        "OpenAI API (LLM)",
        "HTML/CSS/JS (Frontend)",
        "CSV (Data Storage)"
    ]
    
    return {
        'stats': {
            'Total Jurusan': total_majors,
            'Total Pertanyaan': total_questions,
            'Total Rules': total_rules
        },
        'capabilities': capabilities,
        'tech_stack': tech_stack
    }

def create_system_analysis_table(metrics):
    fig = plt.figure(figsize=(12, 10))
    
    # Title
    plt.suptitle("Analisis Sistem Pakar Rekomendasi Jurusan (SISCER)", fontsize=16, fontweight='bold', y=0.95)
    
    # 1. System Statistics Table (Top Left)
    ax1 = plt.subplot2grid((3, 2), (0, 0))
    ax1.axis('off')
    ax1.set_title("Statistik Knowledge Base", fontsize=12, pad=10, loc='left')
    
    stats_data = [[k, v] for k, v in metrics['stats'].items()]
    table1 = ax1.table(cellText=stats_data, colLabels=['Komponen', 'Jumlah'], loc='center', cellLoc='left')
    table1.scale(1, 1.5)
    table1.auto_set_font_size(False)
    table1.set_fontsize(10)
    
    # 2. Technical Stack Table (Top Right)
    ax2 = plt.subplot2grid((3, 2), (0, 1))
    ax2.axis('off')
    ax2.set_title("Teknologi yang Digunakan", fontsize=12, pad=10, loc='left')
    
    tech_data = [[t] for t in metrics['tech_stack']]
    table2 = ax2.table(cellText=tech_data, colLabels=['Tech Stack'], loc='center', cellLoc='left')
    table2.scale(1, 1.5)
    
    # 3. System Capabilities (Middle)
    ax3 = plt.subplot2grid((3, 2), (1, 0), colspan=2)
    ax3.axis('off')
    ax3.set_title("Kapabilitas Sistem", fontsize=12, pad=10, loc='center')
    
    cap_data = [[c] for c in metrics['capabilities']]
    # Split into 2 columns for better layout
    mid = len(cap_data) // 2
    col1 = cap_data[:mid]
    col2 = cap_data[mid:]
    
    # Pad if uneven
    if len(col1) > len(col2):
        col2.append([''])
        
    combined_cap_data = [[c1[0], c2[0]] for c1, c2 in zip(col1, col2)]
    
    table3 = ax3.table(cellText=combined_cap_data, colLabels=['Fitur Utama', 'Fitur Tambahan'], loc='center', cellLoc='left')
    table3.scale(1, 1.5)
    
    # 4. Brief Analysis Text (Bottom)
    ax4 = plt.subplot2grid((3, 2), (2, 0), colspan=2)
    ax4.axis('off')
    
    analysis_text = (
        "ANALISIS SINGKAT:\n\n"
        "Sistem ini menggunakan pendekatan Hybrid yang menggabungkan keandalan Rule-Based System (Forward Chaining)\n"
        "dengan kecerdasan generatif AI (LLM). Forward Chaining menjamin hasil yang deterministik dan cepat berdasarkan\n"
        "teori RIASEC yang baku, sementara LLM memberikan analisis kualitatif yang lebih mendalam dan fleksibel.\n\n"
        "Penggunaan Cosine Similarity memungkinkan sistem untuk meranking jurusan berdasarkan tingkat kemiripan profil,\n"
        "bukan hanya sekedar match biner (cocok/tidak), memberikan rekomendasi yang lebih nuansa."
    )
    
    ax4.text(0.5, 0.5, analysis_text, ha='center', va='center', fontsize=11, wrap=True, 
             bbox=dict(boxstyle="round,pad=1", fc="#FAFAF8", ec="#2C241B"))

    # Styling
    for table in [table1, table2, table3]:
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#2C241B')
            else:
                cell.set_facecolor('#FAFAF8')

    plt.tight_layout()
    plt.savefig('analisis_sistem.png')
    print("\nAnalisis sistem telah disimpan sebagai 'analisis_sistem.png'")
    # plt.show()

if __name__ == "__main__":
    metrics = analyze_system_metrics()
    create_system_analysis_table(metrics)
