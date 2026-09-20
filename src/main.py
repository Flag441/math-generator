import subprocess
import random
import tempfile # 並列処理時に一時的にファイルを生成するために必要
from fastapi import FastAPI #フレームワーク
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pathlib import Path
from fastapi.responses import Response
from .Problems import problem

# FastAPIアプリケーションの立ち上げ
app = FastAPI(title="数学プリント自動生成API")

TEMPLATE_DIR = Path(__file__).parent.parent/"latex_templates"
DOCUMENT = (TEMPLATE_DIR / "document.tex").read_text(encoding="utf-8")
PAGE = (TEMPLATE_DIR / "page.tex").read_text(encoding="utf-8")

# フロントエンド(Next.js)と通信するための設定（CORS）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://math-generator-puce.vercel.app", #本番のフロントエンド
        "http://localhost:3000", #開発中
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ここからがAPIの窓口（エンドポイント） ---

@app.get("/api/generate")
# 一旦,問題生成パターンが132通りしかないのでプリント1枚に132問を上限に設定 今後は問題によってここは変える
def generate_pdf(num_problems: int = Query(10,ge=1,le=132), num_prints: int = Query(1,ge=1,le=100),seed: int = 0,problem_type: str="quadratic_axis"):
    """
    指定された問題数と枚数でLaTeXファイルを作成し、
    PDFに変換してフロントエンドに返すAPI
    """

    spec = problem.REGISTRY.get(problem_type)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail = f"未知の問題種別です: {problem_type}"
        )

    # 2段組みにしたいため問題数を2分割
    midpoint = (num_problems + 1) // 2 - 1

    pages = []

    # 指定されたプリント枚数（num_prints）分だけループ処理
    for print_idx in range(num_prints):

        rng = random.Random(seed + print_idx)
        # 1. このプリント用の問題データを作成
        quiz = []
        seen = set() # 過去に出現した問題
        attempts = 0
        while len(quiz) < num_problems:
            attempts += 1
            if attempts>num_problems*50:
                raise HTTPException(
                    status_code = 500,
                    detail = f"問題の生成に失敗しました ({attempts}回試行)",
                )
            p = spec["generate"](rng)
            if p.question not in seen: # まだ出現していない問題なら追加をする
                seen.add(p.question)
                quiz.append(p)

        items = ""
        for i, p in enumerate(quiz):
            items += f"  \\item ${p.question}$\n"
            if i == midpoint:
                items += "  \\vspace*{\\fill}\n  \\columnbreak\n"
            elif i == num_problems - 1:
                items += "  \\vspace*{\\fill}\n"
            else:
                items += "  \\vspace{35mm}\n"

        ans_items = ""
        for i, p in enumerate(quiz):
            steps_tex = "".join(f" {s} \\\\\n" for s in p.step)
            ans_block = (
                f" \\item ${p.question}$ \\\\\n"
                f" {{\\color{{red}}\n"
                f"{steps_tex}"
                f" 答. {p.answer}\n"
                f" }}\n"
            )

            ans_items += ans_block
            if i == midpoint:
                ans_items += "  \\vspace*{\\fill}\n  \\columnbreak\n"
            elif i == num_problems - 1:
                ans_items += "  \\vspace*{\\fill}\n"
            else:
                ans_items += "  \\vspace{12mm}\n"

        question_page = ( PAGE
            .replace("%%TITLE%%",spec["title"])
            .replace("%%INSTRUCTION%%",spec["instruction"])
            .replace("%%ITEMS%%",items)
        )

        ans_page = ( PAGE
            .replace("%%TITLE%%",spec["title"]+"【解答】")
            .replace("%%INSTRUCTION%%",spec["instruction"])
            .replace("%%ITEMS%%",ans_items)
        )

        pages.append(question_page)
        pages.append(ans_page)

    body = "\n\\newpage\n".join(pages)

    tex_content = DOCUMENT.replace("%%BODY%%",body)

    # リソースを奪い合わないように使い捨てファイルを作成
    with tempfile.TemporaryDirectory() as tempdir:
        tmp = Path(tempdir) 
        tex_path= tmp / "output.tex"
        tex_path.write_text(tex_content, encoding="utf-8")

        try:
            result = subprocess.run(
                ["platex","-interaction=nonstopmode","output.tex"],
                cwd=tmp,capture_output=True,text=True,errors="replace",
                stdin=subprocess.DEVNULL, timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code = 504,
                detail = "platexの処理が30秒を超えました。問題数を減らして再試行してください。",
            )

        if result.returncode != 0:
            raise HTTPException(status_code=500,detail=f"platexに失敗しました:\n{result.stdout[-2000:]}")

        try:
            result = subprocess.run(
                ["dvipdfmx","output.dvi"],
                cwd=tmp,capture_output=True,text=True,errors="replace",
                stdin=subprocess.DEVNULL, timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail="dvipdfmxの処理が30秒を超えました。問題数を減らして再試行してください。"
            )

        if result.returncode != 0:
            raise HTTPException(status_code=500,detail = f"dvipdfmxに失敗しました:\n{result.stdout[-2000:]}")

        # 生成したファイルをメモリへ読み込む
        pdf_bytes = (tmp / "output.pdf").read_bytes()

    # 読み込んだデータを返す
    return Response(
        content = pdf_bytes,
        media_type = "application/pdf",
        headers = {
            "Content-Disposition": f'attachment; filename="math_print_{num_problems}problems_{num_prints}prints.pdf"'
        },
    )

@app.get("/api/problem-types")
def list_problem_types():
    """登録されている問題種別の一覧を返す"""
    return [
        {
            "key": key,
            "subject": spec["subject"],
            "unit": spec["unit"],
            "sub_unit": spec["sub_unit"],
            "label": spec["label"],
            "per_page": spec["per_page"],
        }
        for key, spec in problem.REGISTRY.items()
    ]