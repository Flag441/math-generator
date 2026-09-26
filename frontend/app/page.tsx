import Generator from "./components/Generator";
import type { ProblemType } from "./components/Generator";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default async function Page() {
  let types: ProblemType[] = [];

  try {
    const res = await fetch(`${API_BASE_URL}/api/problem-types`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) types = await res.json();
  } catch {
    // 取得できなくてもビルドは止めない。空のまま Generator に渡す
  }

  return <Generator initialTypes={types} />;
}