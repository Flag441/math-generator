# 問題形式を, 「問題,解答の途中式,答え」の3つをメンバ変数に持つクラスで定義する.

class Problem:
    def __init__(self,question,step,answer):
        self.question = question # 問題文
        self.step = step # 解答の過程をまとめたリスト
        self.answer = answer # 解答として表示するもの