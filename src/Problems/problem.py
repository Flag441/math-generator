# 問題形式を, 「問題,解答の途中式,答え」の3つをメンバ変数に持つクラスで定義する.

class Problem:
    def __init__(self,question,step,answer):
        self.question = question # 問題文
        self.step = step # 解答の過程をまとめたリスト
        self.answer = answer # 解答として表示するもの

REGISTRY = {} # APIで使用する問題名簿

# key : REGISTRYに登録する用のタグ
# subject : 科目名
# unit : 単元名
# sub_unit : 問題名
# label : 人間が読む用のタグ。 例:「グラフと共有点を求める」
# title : pdfの見出し
# instruction : 問題文 「次の問題を解け」など
# per_page : 1ページ当たりの問題数
def register(key, subject, unit, sub_unit,label,title,instruction,example,per_page=12):
    def decorator(fn):
        REGISTRY[key]={
            "generate":fn,
            "subject":subject,
            "unit":unit,
            "sub_unit":sub_unit,
            "label":label,
            "title":title,
            "instruction":instruction,
            "example": example,
            "per_page":per_page,
            }
        return fn
    return decorator