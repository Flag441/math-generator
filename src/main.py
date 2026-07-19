import os
import subprocess
import random #乱数生成に必要
from fastapi import FastAPI #フレームワーク
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sympy import Symbol, expand, latex #数学計算用

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
    """1問分のデータを生成する関数"""
    x = Symbol('x') #xは変数であることを伝える
    ans1, ans2 = random.randint(-5, 5), random.randint(-5, 5) #x軸との共有点
    a = random.choice([1, -1]) #グラフが上に凸か下に凸か
    expr = expand(a * (x - ans1) * (x - ans2)) #自動で展開してくれる
    
    eq_str = latex(expr) 
    step1 = f"${latex(expr)}=0$ とおくと"
    step2 = f"${latex(expand((x - ans1) * (x - ans2)))}=0$ \\\\\n        " if a == -1 else "" #上に凸ならstep2にはマイナス倍したものを入れる
        
    ans_list = sorted([ans1, ans2]) #答えを入れたもの
    
    #因数分解をした形を生成
    if ans_list[0] == ans_list[1]: #重解のとき
        #解が0なのかそうでないかで形が変わる
        factor = "x^{2}" if ans_list[0] == 0 else f"(x {'-' if ans_list[0] > 0 else '+'} {abs(ans_list[0])})^{{2}}"
    else:
        # 重解でないとき

        #ラムダ式 valが0ならx, そうでないなら(x-val) を返す関数
        fmt = lambda val: "x" if val == 0 else (f"(x - {val})" if val > 0 else f"(x + {abs(val)})")

        #因数分解した形
        factor = f"{fmt(ans_list[0])}{fmt(ans_list[1])}"
        
    step3 = f"${factor}=0$"
    step4 = f"$x={ans_list[0]}, {ans_list[1]}$" if ans1 != ans2 else f"$x={ans_list[0]}$"
    ans_val = f"$({ans_list[0]}, 0), ({ans_list[1]}, 0)$" if ans1 != ans2 else f"$({ans_list[0]}, 0)$"
    
    #C++でいうところの map<string,string> というデータ型を返している
    return {
        "eq": eq_str, "step1": step1, "step2": step2, 
        "step3": step3, "step4": step4, "ans": ans_val
    }

# --- ここからがAPIの窓口（エンドポイント） ---

@app.get("/api/generate")
def generate_pdf(num_problems: int = 10, num_prints: int = 1):
    """
    指定された問題数と枚数でLaTeXファイルを作成し、
    PDFに変換してフロントエンドに返すAPI
    """
    # """を付けると \ を普通の文字列として処理できるようになる
    tex_content = r"""
\documentclass[a4paper,11pt]{jsarticle}
\usepackage{amsmath,amssymb}
\usepackage{multicol}
\usepackage{xcolor}
% 下の余白をピッタリ30mm（3cm）に指定
\usepackage[top=20mm, left=20mm, right=20mm, bottom=30mm]{geometry} 

\pagestyle{empty}
\renewcommand{\labelenumi}{(\arabic{enumi})}
\setlength{\columnseprule}{0.4pt}

\begin{document}
"""

    # 2段組みにしたいため問題数を2分割
    midpoint = (num_problems + 1) // 2 - 1

    # 指定されたプリント枚数（num_prints）分だけループ処理
    for print_idx in range(num_prints):
        # 1. このプリント用の問題データを作成
        quiz = []
        seen = set() # 過去に出現した問題
        while len(quiz) < num_problems:
            p = generate_quadratic_problem()
            if p['eq'] not in seen: # まだ出現していない問題なら追加をする
                seen.add(p['eq'])
                quiz.append(p)

        # 2. 問題ページを追記
        tex_content += r"""
% ------ 問題ページ ------
\noindent
{\large \textbf{二次関数 グラフと$x$軸の共有点を求める問題}} \hfill 年\hspace{5mm}組\hspace{5mm}番\hspace{2mm}氏名\rule{40mm}{0.4pt}
\vspace{3mm}

\noindent
問題: 次の二次関数のグラフと$x$軸の共有点の座標を求めよ。
\vspace{3mm}

\begin{multicols*}{2}
\begin{enumerate}
"""

        for i, p in enumerate(quiz):
            tex_content += f"  \\item $y = {p['eq']}$\n"
            if i == midpoint:
                tex_content += "  \\vspace*{\\fill}\n  \\columnbreak\n"
            elif i == num_problems - 1:
                tex_content += "  \\vspace*{\\fill}\n"
            else:
                tex_content += "  \\vspace{35mm}\n"

        tex_content += r"""
\end{enumerate}
\end{multicols*}

\newpage

% ------ 解答ページ ------
\noindent
{\large \textbf{二次関数 グラフと$x$軸の共有点を求める問題 【解答】}} \hfill 年\hspace{5mm}組\hspace{5mm}番\hspace{2mm}氏名\rule{40mm}{0.4pt}
\vspace{3mm}

\noindent
問題: 次の二次関数のグラフと$x$軸の共有点の座標を求めよ。
\vspace{3mm}

\begin{multicols*}{2}
\begin{enumerate}
"""

        for i, p in enumerate(quiz):
            step2_str = f"  {p['step2']}" if p['step2'] else ""
            
            # 🌟 修正ポイント：「答.\」の不要なバックスラッシュを削除して「答.」にしました
            ans_block = (
                f"  \\item $y = {p['eq']}$ \\\\\n"
                f"  {{\\color{{red}}\n"
                f"  {p['step1']} \\\\\n"
                f"{step2_str}"
                f"  {p['step3']} \\\\\n"
                f"  {p['step4']} \\\\\n"
                f"  答. {p['ans']}\n"
                f"  }}\n"
            )
            tex_content += ans_block
            if i == midpoint:
                tex_content += "  \\vspace*{\\fill}\n  \\columnbreak\n"
            elif i == num_problems - 1:
                tex_content += "  \\vspace*{\\fill}\n"
            else:
                tex_content += "  \\vspace{12mm}\n"

        tex_content += r"""
        \end{enumerate}
        \end{multicols*}
        """
        # 最後のプリント以外は、次のプリントのために改ページを入れる
        if print_idx < num_prints - 1:
            tex_content += "\n\\newpage\n"

    # LaTeXの終了タグ
    tex_content += "\n\\end{document}\n"

    # 🌟 修正ポイント：ファイル名を「output」に変更してロックエラーを回避
    tex_filename = "output.tex"
    pdf_filename = "output.pdf"
    
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # 4. LaTeXコマンドを実行してPDF化する
    import subprocess
    try:
        subprocess.run(["platex", "-interaction=nonstopmode", tex_filename], check=True)
        # 🌟 ここも「output.dvi」に変更
        subprocess.run(["dvipdfmx", "output.dvi"], check=True)
    except Exception as e:
        return {"error": f"PDFの作成に失敗しました: {str(e)}"}

    # 5. 完成したPDFファイルをフロントエンドに返却
    from fastapi.responses import FileResponse
    return FileResponse(
        pdf_filename, 
        media_type="application/pdf", 
        filename=f"math_print_{num_problems}problems_{num_prints}prints.pdf"
    )