import random #乱数生成に必要
from sympy import Symbol, expand, latex #数学計算用


def quadoratic_axis():
    """二次関数とx軸の共有点を求める問題"""
    x = Symbol('x') #xは変数であることを伝える
    ans1, ans2 = random.randint(-5, 5), random.randint(-5, 5) #x軸との共有点. random.radintは両端を含む関数.
    a = random.choice([1, -1]) #グラフが上に凸か下に凸か
    expr = expand(a * (x - ans1) * (x - ans2)) # type: ignore 自動で展開してくれる
    
    eq_str = latex(expr) 
    step1 = f"${eq_str}=0$ とおくと"
    step2 = f"${latex(expand((x - ans1) * (x - ans2)))}=0$ \\\\\n        " if a == -1 else "" # type: ignore 上に凸ならstep2にはマイナス倍したものを入れる
        
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
