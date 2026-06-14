import random
from sympy import Symbol, expand, latex

def generate_quadratic_problem():
    x = Symbol('x')
    ans1, ans2 = random.randint(-5, 5), random.randint(-5, 5)
    a = random.choice([1, -1])
    expr = expand(a * (x - ans1) * (x - ans2))
    
    eq_str = latex(expr)
    
    # --- 解説・解答の組み立て ---
    step1 = f"${latex(expr)}=0$ とおくと"
    step2 = ""
    if a == -1:
        step2 = f"${latex(expand((x - ans1) * (x - ans2)))}=0$ \\\\\n        "
        
    ans_list = sorted([ans1, ans2])
    
    if ans_list[0] == ans_list[1]:
        if ans_list[0] == 0:
            factor = "x^{2}"
        else:
            sign = "-" if ans_list[0] > 0 else "+"
            factor = f"(x {sign} {abs(ans_list[0])})^{{2}}"
    else:
        def fmt(val):
            if val == 0: return "x"
            return f"(x - {val})" if val > 0 else f"(x + {abs(val)})"
        factor = f"{fmt(ans_list[0])}{fmt(ans_list[1])}"
        
    step3 = f"${factor}=0$"
    step4 = f"$x={ans_list[0]}, {ans_list[1]}$" if ans1 != ans2 else f"$x={ans_list[0]}$"
    ans_val = f"({ans_list[0]}, 0), ({ans_list[1]}, 0)" if ans1 != ans2 else f"({ans_list[0]}, 0)"
    
    return {
        "eq": eq_str, 
        "step1": step1, 
        "step2": step2, 
        "step3": step3, 
        "step4": step4, 
        "ans": ans_val
    }

def create_output_tex(quiz_set):
    # 1ページ目：問題リストの生成
    prob_items = ""
    for p in quiz_set:
        prob_items += f"    \\item $y={p['eq']}$\n    \\vspace{{4cm}}\n"

    # 2ページ目：解答リストの生成
    ans_items = ""
    for p in quiz_set:
        ans_items += f"    \\item $y={p['eq']}$ \\\\\n"
        ans_items += f"    {{\\color{{red}}\n"
        ans_items += f"    {p['step1']} \\\\\n"
        if p['step2']:
            ans_items += f"    {p['step2']}"
        ans_items += f"    {p['step3']} \\\\\n"
        ans_items += f"    {p['step4']} \\\\\n"
        # 【修正】答の座標を $ $ で囲み、数式モードの美しいマイナスにする
        ans_items += f"    答. ${p['ans']}$\n"
        ans_items += f"    }}\n    \\vspace{{1.5cm}}\n"

    # 1つのLaTeXファイルとして全体を構築
    full_tex = r"""\documentclass[a4paper,11pt]{jsarticle}
\usepackage[dvipdfmx]{graphicx}
\usepackage{amsmath,amssymb,xcolor}
\usepackage{multicol}
\usepackage[margin=1.5cm]{geometry}

\setlength{\columnseprule}{0.4pt}
\setlength{\columnsep}{1cm}

\begin{document}

% ==============================
% 1ページ目：問題編
% ==============================
\begin{center}
    {\Large \textbf{二次関数 グラフと軸の共有点を求める問題}}
\end{center}
\begin{flushright}
    年\hspace{1em}組\hspace{1em}番\hspace{1em}氏名\underline{\hspace{5cm}}
\end{flushright}
\vspace{0.5em}
問題: 次の二次関数のグラフと軸の共有点の座標を求めよ。
\vspace{1em}

\begin{multicols}{2}
\begin{enumerate}
""" + prob_items + r"""\end{enumerate}
\end{multicols}

\newpage
% ==============================
% 2ページ目：解答編
% ==============================
\begin{center}
    {\Large \textbf{二次関数 グラフと軸の共有点を求める問題 【解答】}}
\end{center}
\begin{flushright}
    年\hspace{1em}組\hspace{1em}番\hspace{1em}氏名\underline{\hspace{5cm}}
\end{flushright}
\vspace{0.5em}
問題: 次の二次関数のグラフと軸の共有点の座標を求めよ。
\vspace{1em}

\begin{multicols}{2}
\begin{enumerate}
""" + ans_items + r"""\end{enumerate}
\end{multicols}

\end{document}
"""

    with open("src/output.tex", "w", encoding="utf-8") as f:
        f.write(full_tex)
    print("✅ src/output.tex を作成しました。")

if __name__ == "__main__":
    quiz = []
    seen = set()
    
    while len(quiz) < 10:
        p = generate_quadratic_problem()
        if p['eq'] not in seen:
            seen.add(p['eq'])
            quiz.append(p)
            
    create_output_tex(quiz)