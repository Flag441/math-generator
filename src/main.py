import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sympy import Symbol, expand, latex

# FastAPIアプリケーションの立ち上げ
app = FastAPI(title="数学プリント自動生成API")

# フロントエンド(Next.js)と通信するための設定（CORS）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 開発中はどこからでもアクセス可能にする
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_quadratic_problem():
    """1問分のデータを生成する関数（先ほどの完成版ロジック）"""
    x = Symbol('x')
    ans1, ans2 = random.randint(-5, 5), random.randint(-5, 5)
    a = random.choice([1, -1])
    expr = expand(a * (x - ans1) * (x - ans2))
    
    eq_str = latex(expr)
    step1 = f"${latex(expr)}=0$ とおくと"
    step2 = f"${latex(expand((x - ans1) * (x - ans2)))}=0$ \\\\\n        " if a == -1 else ""
        
    ans_list = sorted([ans1, ans2])
    
    if ans_list[0] == ans_list[1]:
        factor = "x^{2}" if ans_list[0] == 0 else f"(x {'-' if ans_list[0] > 0 else '+'} {abs(ans_list[0])})^{{2}}"
    else:
        fmt = lambda val: "x" if val == 0 else (f"(x - {val})" if val > 0 else f"(x + {abs(val)})")
        factor = f"{fmt(ans_list[0])}{fmt(ans_list[1])}"
        
    step3 = f"${factor}=0$"
    step4 = f"$x={ans_list[0]}, {ans_list[1]}$" if ans1 != ans2 else f"$x={ans_list[0]}$"
    ans_val = f"({ans_list[0]}, 0), ({ans_list[1]}, 0)" if ans1 != ans2 else f"({ans_list[0]}, 0)"
    
    return {
        "eq": eq_str, "step1": step1, "step2": step2, 
        "step3": step3, "step4": step4, "ans": ans_val
    }

# --- ここからがAPIの窓口（エンドポイント） ---

@app.get("/api/preview")
def get_preview(num_problems: int = 10):
    """
    指定された問題数（デフォルト10問）を生成し、
    フロントエンドのプレビュー用にJSONデータとして返すAPI
    """
    quiz = []
    seen = set()
    
    while len(quiz) < num_problems:
        p = generate_quadratic_problem()
        if p['eq'] not in seen:
            seen.add(p['eq'])
            quiz.append(p)
            
    return {"problems": quiz}