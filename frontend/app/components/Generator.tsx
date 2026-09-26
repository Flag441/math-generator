"use client";

import { useEffect, useState } from "react";
import "katex/dist/katex.min.css";
import { InlineMath } from "react-katex";
import { useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ProblemType={
  key: string;
  subject: string;
  unit: string;
  sub_unit: string;
  label: string;
  instruction: string;
  per_page: number;
  example: string;
}

const safe = (s: string) => s.replace(/[\\/:*?"<>|]/g, "_");

export default function Generator({ initialTypes }: { initialTypes: ProblemType[] }) {
  //画面の全状態を管理している.
  const [step, setStep] = useState<number>(0); //今どの画面にいるか
  
  //選択した内容
  const [selectedSubject, setSelectedSubject] = useState<string>(""); 
  const [selectedUnit, setSelectedUnit] = useState<string>("");
  const [selectedSubUnit, setSelectedSubUnit] = useState<string>("");
  const [selectedProblem, setSelectedProblem] = useState<string>("");

  // 問題数と枚数
  const [numPrints, setNumPrints] = useState<number>(1);

  //生成中か、結果があるか、エラーがあるか
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [printError, setPrintError] = useState<string>("");
  const [listState,setListState] = useState<"loading" | "ready" | "error">(
    initialTypes.length > 0 ? "ready" : "loading"
  );

  const [types,setTypes] = useState<ProblemType[]>(initialTypes);

  const loadTypes = useCallback(() => {
    setListState("loading");
    fetch(`${API_BASE_URL}/api/problem-types`) //通信して
    .then((res) => {
      if(res.ok === true) return res.json();
      else throw new Error();
    })
    .then((data) => {
      setListState("ready");
      setTypes(data);
    })
    .catch(() => setListState("error"));
  },[]);

  useEffect(() => {
    if(initialTypes.length === 0) loadTypes();
  },[loadTypes,initialTypes.length]);

  const subjectOptions = Array.from(new Set(types.map((t) => t.subject)))
    .map((name) => ({ name, implemented: true}));

  const unitOptions = Array.from(
    new Set(
      types.filter((t) => t.subject === selectedSubject).map((t) => t.unit)
    )
  ).map((name) => ({ name, implemented: true}));

  const subUnitOptions = Array.from(
    new Set(
      types.filter((t) => t.subject === selectedSubject && t.unit === selectedUnit).map((t) => t.sub_unit)
    )
  ).map((name) => ({ name, implemented: true}));

  const problemOptions = Array.from(
    new Set(
      types.filter((t) => t.subject===selectedSubject && t.unit === selectedUnit && t.sub_unit === selectedSubUnit).map((t) => t.label)
    )
  ).map((name) => ({ name, implemented: true}))

  const selectedType = types.find(
    (t) =>
      t.subject === selectedSubject &&
      t.unit === selectedUnit &&
      t.sub_unit === selectedSubUnit &&
      t.label === selectedProblem
  )

  // アロー関数で書いている. asyncはこの関数内でawaitを使うため必要.
  const handleGeneratePDF = async () => {
    if (numPrints > 100) {
      setPrintError("エラー：上限の100枚を超えています。100枚以内で指定してください。");
      return;
    }

    if (!selectedType){
      setPrintError("エラー : 問題の種類が選択されていません。");
      return;
    }

    // エラー表示を消して, 生成中に切り替える. Reactはこの2つをまとめて1回の再描画にする.
    setPrintError("");
    setIsGenerating(true);
    
    // 前回生成したデータを消す処理
    if (pdfUrl) {
      window.URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }

    try {

      const seed = Math.floor(Math.random()*1000000000)
      const response = await fetch(`${API_BASE_URL}/api/generate?num_problems=${selectedType.per_page}&num_prints=${numPrints}&seed=${seed}&problem_type=${selectedType.key}`)
        .catch(() => {
            throw new Error("サーバーに接続できませんでした。時間をおいて再度お試しください。");
        });
      
      // fetchは404や500ときも例外を投げないので自分で確認する必要がある.
      if (!response.ok) {
        let message = `サーバーがエラーを返しました (HTTP ${response.status})`;
        try
        {
          const data = await response.json();
          if(data.detail) message = data.detail;
        }catch
        {

        }
        throw new Error(message);
      }
      
      const blob = await response.blob(); // 受信したデータをバイナリの形として取り出す
      const url = window.URL.createObjectURL(blob); // 取り出したものをブラウザ内だけで有効な仮URLを発行
      setPdfUrl(url); // 状態に保存

    } catch (error) {
      console.error(error);
      setPrintError(error instanceof Error ? error.message : "予期しないエラーが発生しました");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBack = () => {
    if(step === 0) return;

    if(step === 4){
      if(pdfUrl) window.URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
      setPrintError("");
    }

    setStep((prev) => prev-1);
  };

  const renderOptions = (options: { name: string; implemented: boolean }[], onSelect: (name: string) => void) => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto mt-6">
        {options.map((option) => (
          <button
            key={option.name}
            disabled={!option.implemented}
            onClick={() => onSelect(option.name)}
            className={`relative p-6 rounded-xl border-2 text-xl font-bold transition-all duration-200 ${
              option.implemented ? "bg-white border-slate-700 text-slate-800 hover:bg-slate-100 hover:shadow-md" : "bg-gray-300 border-gray-400 text-gray-500 cursor-not-allowed"
            }`}
          >
            {option.name}
            {!option.implemented && (
              <span className="absolute top-2 right-2 bg-gray-600 text-white text-xs px-2 py-1 rounded">Coming Soon</span>
            )}
          </button>
        ))}
      </div>
    );
  };

  const renderWithMath = (text: string) =>
    text.split("$").map((part,i) =>
      i%2 === 1 ? <InlineMath key={i} math={part} /> : <span key={i}>{part}</span>
    );

  return (
      <main className="w-full max-w-6xl mx-auto p-8 mt-6 relative pb-10">
        {step > 0 && (
          <button onClick={handleBack} className="mb-4 flex items-center text-slate-600 hover:text-slate-900 font-bold transition-colors">
            <span className="mr-2 text-xl">◀</span> 戻る
          </button>
        )}

        <div className="text-center mb-8 space-y-2">
          {step > 0 && <h2 className="text-4xl font-bold">{selectedSubject}</h2>}
          {step > 1 && <h3 className="text-2xl text-gray-700">{selectedUnit}</h3>}
          {step > 2 && <h4 className="text-xl text-gray-600">{selectedSubUnit}</h4>}
          {step > 3 && <p className="text-lg text-gray-500 font-medium">{selectedProblem}</p>}
        </div>

        {step==0 && listState=="loading" &&
          <div className="mt-6 text-center">
            <p className="text-lg text-gray-700 font-medium mb-2">読み込み中…</p>
            <p className="text-sm text-gray-600">しばらくアクセスが無いとサーバーが停止するため、最初の読み込みに1分ほどかかることがあります。</p>
          </div>
        }
        {step==0 && listState=="error" && 
          <div className="mt-6 text-center">
              <p className="text-lg text-gray-700 font-medium mb-4">問題の一覧を取得できませんでした。</p>
              <button onClick={loadTypes} className="bg-slate-700 hover:bg-slate-800 text-white font-bold py-3 px-8 rounded-full shadow-md transition-colors">再試行</button>
          </div>
        }
        {step==0 && listState=="ready" && renderOptions(subjectOptions, (name) => { setSelectedSubject(name); setStep(1); })}
        {step === 1 && renderOptions(unitOptions, (name) => { setSelectedUnit(name); setStep(2); })}
        {step === 2 && renderOptions(subUnitOptions, (name) => { setSelectedSubUnit(name); setStep(3); })}
        {step === 3 && renderOptions(problemOptions, (name) => { setSelectedProblem(name); setStep(4); })}

        {step === 4 && (
          <div className="bg-white shadow-lg rounded-xl p-8">
            <div className="flex flex-col md:flex-row gap-10">
              <div className="flex-1 space-y-8">
                <div>
                  <label className="block font-bold text-lg mb-2 text-gray-500">
                    1枚のプリントに何問生成しますか？ <span className="text-sm font-normal">※現在、問題によって個数を固定しています。</span>
                  </label>
                  <input
                    type="number" 
                    value={selectedType ? selectedType.per_page : 10}
                    disabled
                    className="border-2 border-gray-300 rounded-lg p-3 w-full text-lg bg-gray-200 text-gray-500 cursor-not-allowed" 
                  />
                </div>
                <div>
                  <label className="block font-bold text-lg mb-2">何枚のプリントを生成しますか？</label>
                  <input
                    type="number" 
                    value={numPrints} 
                    onChange={(e) => {
                      setNumPrints(Number(e.target.value));
                      if (Number(e.target.value) <= 100) setPrintError("");
                    }}
                    className={`border-2 rounded-lg p-3 w-full text-lg focus:outline-none focus:border-slate-500 ${
                      printError ? "border-red-500 bg-red-50" : "border-gray-300"
                    }`} 
                    min="1" max="100"
                  />
                  <p className="text-sm text-gray-500 mt-2">※上限は100枚です</p>
                  {printError && (
                    <p className="text-red-500 font-bold mt-2">{printError}</p>
                  )}
                </div>
              </div>

              <div className="flex-1 border-2 border-slate-700 p-2 rounded-xl bg-gray-50 flex flex-col shadow-inner h-150 overflow-hidden">
                {/* ★変更：生成中（isGenerating）の時はローディング画面を表示する */}
                {isGenerating ? (
                  <div className="flex flex-col justify-center items-center h-full text-center p-6">
                    <div className="animate-pulse flex flex-col items-center">
                      <span className="text-6xl mb-6">⏳</span>
                      <span className="text-2xl font-bold text-slate-700">PDFを生成中...</span>
                    </div>
                    <div className="mt-8 border border-amber-300 bg-amber-50 p-4 rounded text-amber-800 text-sm">
                      <p className="font-bold mb-1">※サーバー起動中のため時間がかかる場合があります</p>
                      <p>そのまま最大1〜2分ほどお待ちください。</p>
                    </div>
                  </div>
                ) : pdfUrl ? (
                  <iframe 
                    src={`${pdfUrl}#toolbar=0&view=FitH`} 
                    className="w-full h-full rounded" 
                    title="PDF Preview"
                  />
                ) : (
                  <div className="flex flex-col justify-center items-center h-full text-center p-6">
                    <div className="text-lg mb-6 font-medium leading-relaxed px-4">
                      {selectedType && renderWithMath(selectedType.instruction)}
                    </div>
                    <div className="text-xl mb-6 px-4">
                      {selectedType && <InlineMath math={selectedType.example} />}
                    </div>
                    <div className="border border-gray-400 p-4 rounded bg-white shadow-sm">
                      <p className="text-sm text-gray-600 leading-relaxed">
                        左のボタンから「PDFを生成」をクリックすると、<br />
                        ここに完成したプリントのプレビューが表示されます。
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-12 flex flex-col items-center gap-4">
              <button
                onClick={handleGeneratePDF}
                disabled={isGenerating || numPrints > 100}
                className="bg-slate-700 hover:bg-slate-800 text-white font-bold py-4 px-20 rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95 disabled:bg-gray-400 text-xl"
              >
                {isGenerating ? "PDF生成中..." : "PDFを生成"}
              </button>
              
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  download={`${safe(selectedType?.unit ?? "数学")}_${safe(selectedType?.sub_unit ?? "")}_${numPrints}枚.pdf`}
                  className="inline-block text-center bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 px-20 rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95 text-xl mt-4"
                >
                  📥 プレビューのPDFをダウンロード
                </a>
              )}
            </div>
          </div>
        )}
      </main>
  );
}