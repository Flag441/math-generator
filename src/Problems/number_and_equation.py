import random #乱数生成に必要
from .problem import Problem,register
from sympy import Symbol, expand, latex, collect #数学計算用
from sympy import Poly

# 数学I 数と式

def like_term_value(rng : random.Random):
    """同類項の整理と次数・定数項"""
    # 例 : 3x^2+2x-6-4x^2+3x+2 [x] の同類項をまとめよ.また,[]内の文字に着目したとき,その次数と定数項を言え.
    # パターン1 1文字のみを用いる. 2次式で各項が2つずつ出てくるようにしたい.
    # パターン2 2文字を用いる. 二次までを許容すると x^2,xy,y^2,x,y 及び定数項がでてくるので6項文を考える必要がある.
    # パターン3 3文字を用いる. [x],[xとy]など2文字に着目するパターンも考える.
    # 4次式を許容すると 4次の項が15個, 3次の項が10個, 2次の項が6個, 1次の項が3個, 及び定数項 の35項出てくる. これは多すぎるので 6~10項で考えようと思う.
    pattern = rng.choice([1,2,3])
    pattern = 1 # デバック用
    chars = ['x','y','z','s','t','a','b','c']
    if pattern==1:
        # 1文字だけを使う.
        names = rng.sample(chars,1)
        X = Symbol(names[0])
        monomials = [X**2,X,1]

        non_zero_coefficient = [n for n in range(-10,11) if n!=0]

        left_coeffs,right_coeffs = [],[]

        for _ in monomials:
            a = rng.choice(non_zero_coefficient)
            b = rng.choice([n for n in non_zero_coefficient if n!=-a])

            left_coeffs.append(a)
            right_coeffs.append(b)

        left = sum(c*m for c,m in zip(left_coeffs,monomials))
        right = sum(c*m for c,m in zip(right_coeffs,monomials))
        total = left+right

        focus = X
        p = Poly(total,focus)
        return{
            "left": left,
            "right": right,
            "monomials": monomials,
            "left_coeffs": left_coeffs,
            "right_coeffs": right_coeffs,
            "total": total,
            "focus": focus,
            "degree": p.degree(),
            "constant": p.coeff_monomial(1),
        }
    elif pattern==2:
        # 2文字を使う.
        raise NotImplementedError("パターン2は未実装です")
    else:
        # 3文字を使う
        raise NotImplementedError("パターン3は未実装です")

@register(
        key="like_term",
        subject="数学I",
        unit="数と式",
        sub_unit="同類項の整理と次数・定数項",
        label="同類項を整理する",
        title="数と式 同類項の整理と次数・定数項",
        instruction="次の多項式の同類項を整理せよ. また, [ ]内の文字に関して着目したとき,その次数と定数項をいえ.",
        per_page=12,
)
def like_term_problem(rng: random.Random):
    v = like_term_value(rng)

    # 辞書から一度取り出しておく（f-string の中に " をネストしないため）
    left, right   = v["left"], v["right"]
    total, focus  = v["total"], v["focus"]
    degree        = v["degree"]
    constant      = v["constant"]
    monomials     = v["monomials"]
    left_coeffs   = v["left_coeffs"]
    right_coeffs  = v["right_coeffs"]

    # 問題文: left と right を足さずに並べる（right が負で始まるかで繋ぎ方を変える）
    r_tex = latex(right)
    body = latex(left) + (" " + r_tex if r_tex.lstrip().startswith("-") else " + " + r_tex)
    question = f"{body} \\quad [{latex(focus)}]"

    # 途中式: (a + b)m の形。SymPy は足すと計算してしまうので文字列で組み立てる
    parts = []
    for a, b, m in zip(left_coeffs, right_coeffs, monomials):
        sign = "+" if b >= 0 else "-"
        coeff = f"({a} {sign} {abs(b)})"
        parts.append(coeff if m == 1 else coeff + latex(m))
    mid_equation = " + ".join(parts)

    # 整理後の式は太字にする（青チャートの体裁）
    step = [
        f"${body}$",
        f"$={mid_equation}$",
        f"$= \\boldsymbol{{{latex(total)}}}$",
    ]

    # 着目する文字について降順に整理した形。1文字のときは total と同じなので省く
    collected = collect(total, focus)
    if collected != total:
        step.append(f"${latex(focus)}$ に着目すると ${latex(collected)}$")

    answer = f"次数 ${degree}$, 定数項 ${latex(constant)}$"

    return Problem(question, step, answer)
