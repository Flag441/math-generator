import random
from sympy import Symbol, expand, latex

def generate_quadratic_problem():
    x = Symbol('x')
    
    # 1. 解となる2つの整数をランダムに生成（例: -5から5の範囲）
    ans1 = random.randint(-5, 5)
    ans2 = random.randint(-5, 5)
    
    # 2. 式を組み立てて展開する: a(x - ans1)(x - ans2)
    # 今回はシンプルに a=1 または a=-1 とする
    a = random.choice([1, -1])
    expr = expand(a * (x - ans1) * (x - ans2))
    
    # 3. LaTeX形式の文字列に変換
    problem_latex = latex(expr)
    
    return {
        "equation": f"y = {problem_latex}",
        "answer": sorted([ans1, ans2])
    }

# テスト実行
if __name__ == "__main__":
    problem = generate_quadratic_problem()
    print("問題: y =", problem["equation"])
    print("解答: x =", problem["answer"])