// プリセット / ペルソナ CRUD クライアント。SSE と同様、Next の rewrite プロキシを
// 通さず apiUrl() でバックエンドへ直結する。失敗時は FastAPI の {detail} を日本語にして throw。

import { apiUrl, apiHeaders } from "./config";
import { errorDetail } from "./sse";
import type { Persona, PersonaDetail, Preset } from "./types";

// -- プリセット -------------------------------------------------------------
export async function fetchPresets(): Promise<Preset[]> {
  const res = await fetch(apiUrl("/presets"), { headers: apiHeaders() });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

export async function fetchPreset(id: string): Promise<Preset> {
  const res = await fetch(apiUrl(`/presets/${encodeURIComponent(id)}`), {
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

// 作成 = POST（201）。id 衝突 409 / 未知 persona 400 は detail を throw。
export async function createPreset(body: {
  id: string;
  name: string;
  description?: string;
  persona_ids: string[];
  rounds_per_phase?: number;
  red_team?: boolean;
  red_team_id?: string | null;
}): Promise<Preset> {
  const res = await fetch(apiUrl("/presets"), {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (res.status !== 201) throw new Error(await errorDetail(res));
  return res.json();
}

// 更新 = PUT（200）。builtin は 409「builtin preset is read-only」。
export async function updatePreset(
  id: string,
  body: Partial<Omit<Preset, "id" | "builtin">>
): Promise<Preset> {
  const res = await fetch(apiUrl(`/presets/${encodeURIComponent(id)}`), {
    method: "PUT",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

// 削除 = DELETE（204）。builtin は 409。
export async function deletePreset(id: string): Promise<void> {
  const res = await fetch(apiUrl(`/presets/${encodeURIComponent(id)}`), {
    method: "DELETE",
    headers: apiHeaders(),
  });
  if (res.status !== 204) throw new Error(await errorDetail(res));
}

// -- ペルソナ ---------------------------------------------------------------
export async function fetchPersonaDetail(id: string): Promise<PersonaDetail> {
  const res = await fetch(apiUrl(`/personas/${encodeURIComponent(id)}`), {
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

// 作成 = POST（201）。id 衝突 409 / 検証 ValueError→400 は detail を throw。
export async function createPersona(body: Record<string, unknown>): Promise<Persona> {
  const res = await fetch(apiUrl("/personas"), {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (res.status !== 201) throw new Error(await errorDetail(res));
  return res.json();
}

// 更新 = PUT（200）。404 は detail を throw。
export async function updatePersona(
  id: string,
  body: Record<string, unknown>
): Promise<Persona> {
  const res = await fetch(apiUrl(`/personas/${encodeURIComponent(id)}`), {
    method: "PUT",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

// 削除 = DELETE（204）。404 は detail を throw。
export async function deletePersona(id: string): Promise<void> {
  const res = await fetch(apiUrl(`/personas/${encodeURIComponent(id)}`), {
    method: "DELETE",
    headers: apiHeaders(),
  });
  if (res.status !== 204) throw new Error(await errorDetail(res));
}
