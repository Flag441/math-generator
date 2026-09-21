import random #乱数生成に必要
from .problem import Problem,register
from sympy import Symbol, expand, latex, collect, Mul #数学計算用
from sympy import Poly

# 数学I 数と式

def focus_ordered_latex(total, focus):
    """focus の文字について降順に整理した式を LaTeX 文字列で返す"""
    p = Poly(total, focus)
    parts = []
    for monom, coeff in p.terms():
        c = p.domain.to_sympy(coeff)                      # 係数を通常の式に戻す
        m = Mul(*[g**e for g, e in zip(p.gens, monom)])   # 指数から単項式を組み立てる
        if c.is_Add:                                      # 係数が2項以上なら括弧でくくる
            body = "\\left(" + latex(c) + "\\right)"
            if m != 1:
                body += latex(m)
            sign = "+"
        else:
            term = c * m
            neg = term.could_extract_minus_sign()
            body = latex(-term if neg else term)
            sign = "-" if neg else "+"
        parts.append((sign, body))

    out = parts[0][1] if parts[0][0] == "+" else "-" + parts[0][1]
    for sign, body in parts[1:]:
        out += " " + sign + " " + body
    return out

def terms_to_latex(terms):
    """[(係数,単項式), ...]をLaTeX文字列にする"""
    parts = []
    for c,m in terms:
        a = abs(c)
        if m==1:
            body = str(a) # 定数項のとき
        elif a==1:
            body = latex(m) # 係数が\pm 1のとき
        else:
            body = str(a)+latex(m)
        parts.append(("-" if c<0 else "+",body)) # 符号を考慮してpartsに入れる

    out = parts[0][1] if parts[0][0] == "+" else "-" + parts[0][1] # 先頭の項の+を付けないようにする
    for sign,body in parts[1:]:
        out += " " + sign + " " + body
    return out

def like_term_value(rng : random.Random):
    """同類項の整理と次数・定数項"""
    # 例 : 3x^2+2x-6-4x^2+3x+2 [x] の同類項をまとめよ.また,[]内の文字に着目したとき,その次数と定数項を言え.
    # パターン1 1文字のみを用いる. 2次式で各項が2つずつ出てくるようにしたい.
    # パターン2 2文字を用いる. 二次までを許容すると x^2,xy,y^2,x,y 及び定数項がでてくるので6項文を考える必要がある.
    # パターン3 3文字を用いる. [x],[xとy]など2文字に着目するパターンも考える.
    # 4次式を許容すると 4次の項が15個, 3次の項が10個, 2次の項が6個, 1次の項が3個, 及び定数項 の35項出てくる. これは多すぎるので 6~10項で考えようと思う.
    pattern = rng.choice([1,2,3])
    chars = ['x','y','z','s','t','a','b','c']
    non_zero_coefficient = [n for n in range(-10,11) if n!=0]

    singles = []
    if pattern==1:
        # 1文字だけを使う.
        names = rng.sample(chars,1)
        X = Symbol(names[0])
        monomials = [X**2,X,1]
        focus = [X]

    elif pattern==2:
        # 2文字を使う.
        names = sorted(rng.sample(chars, 2))        # SymPy の並び順に合わせる
        X, Y = Symbol(names[0]), Symbol(names[1])
        all_monomials = [X**2, X*Y, X, Y**2, Y, 1]  # type: ignore
        monomials = sorted(rng.sample(all_monomials, 4), key=all_monomials.index)
        focus = [rng.choice([X, Y])]
    else:
        # 3文字を使う
        names = sorted(rng.sample(chars, 3))
        X, Y, Z = Symbol(names[0]), Symbol(names[1]), Symbol(names[2])
        order = [X**2, X*Y, X*Z, X, Y**2, Y*Z, Y, Z**2, Z, 1] #type: ignore
        # 積の項3つ + どれか1文字の単独項。3個選べば積が必ず2つ入るので3文字が揃う
        v = rng.choice([X, Y, Z])
        pool = [X*Y, X*Z, Y*Z, rng.choice([v, v**2])] #type: ignore
        monomials = sorted(rng.sample(pool, 3), key=order.index)
        focus = sorted(rng.sample([X, Y, Z], rng.choice([1, 2])), key=str)
        singles = [(rng.choice(non_zero_coefficient), 1)]
    
    left_coeffs,right_coeffs = [],[]

    for _ in monomials:
        a = rng.choice(non_zero_coefficient)
        b = rng.choice([n for n in non_zero_coefficient if n!=-a])

        left_coeffs.append(a)
        right_coeffs.append(b)

    terms = list(zip(left_coeffs,monomials)) + list(zip(right_coeffs,monomials)) + singles
    rng.shuffle(terms)
    total = sum(c*m for c,m in terms)

    p = Poly(total,focus)
    return{
        "terms": terms,
        "monomials": monomials,
        "left_coeffs": left_coeffs,
        "right_coeffs": right_coeffs,
        "total": total,
        "focus": focus,
        "degree": p.total_degree(),
        "constant": p.coeff_monomial(1),
        "singles": singles,
    }

@register(
        key="like_term",
        subject="数学I",
        unit="数と式",
        sub_unit="同類項の整理と次数・定数項",
        label="同類項を整理する",
        title="数と式 同類項の整理と次数・定数項",
        instruction="次の多項式の同類項を整理せよ. また, [ ]内の文字に関して着目したとき,その次数と定数項をいえ.",
        example="ax^2 + bxy + cy^2 + dx^2 + exy + f \\quad [x]",
        per_page=10,
)
def like_term_problem(rng: random.Random):
    v = like_term_value(rng)

    # 辞書から一度取り出しておく（f-string の中に " をネストしないため）
    terms = v["terms"]
    total, focus  = v["total"], v["focus"]
    degree        = v["degree"]
    constant      = v["constant"]
    monomials     = v["monomials"]
    left_coeffs   = v["left_coeffs"]
    right_coeffs  = v["right_coeffs"]
    singles = v["singles"]

    # 問題文: left と right を足さずに並べる（right が負で始まるかで繋ぎ方を変える）
    body = terms_to_latex(terms)
    focus_tex = "\\text{ と }".join(latex(f) for f in focus)
    question = f"{body} \\quad [{focus_tex}]"

    # 途中式: (a + b)m の形。SymPy は足すと計算してしまうので文字列で組み立てる
    parts = []
    for a, b, m in zip(left_coeffs, right_coeffs, monomials):
        sign = "+" if b >= 0 else "-"
        coeff = f"({a} {sign} {abs(b)})"
        parts.append(coeff if m == 1 else coeff + latex(m))
    mid_equation = " + ".join(parts)

    for c,m in singles:
        single_tex = str(abs(c)) if m==1 else str(abs(c)) + latex(m)
        mid_equation += ("+" if c>0 else "-") + single_tex

    # 整理後の式は太字にする（青チャートの体裁）
    step = [
        f"${body}$",
        f"$={mid_equation}$",
        f"$= \\boldsymbol{{{latex(total)}}}$",
    ]

    # 着目する文字について降順に整理した形。1文字のときは total と同じなので省く
    ordered = focus_ordered_latex(total,focus)
    if ordered != latex(total):
        step.append(f"${focus_tex}$ に着目すると ${ordered}$")

    answer = f"次数 ${degree}$, 定数項 ${latex(constant)}$"

    return Problem(question, step, answer)
