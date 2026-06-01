"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  cancelSession,
  fetchHealth,
  fetchPersonas,
  sendFollowup,
  startSession,
  type Health,
} from "@/lib/sse";
import { fetchPresets } from "@/lib/api";
import {
  FOLLOWUP_DISABLED_PHASES,
  type Persona,
  type Preset,
  type Turn,
} from "@/lib/types";
import { PersonaPicker } from "@/components/PersonaPicker";
import { PresetBar } from "@/components/PresetBar";
import { LlmToggle } from "@/components/LlmToggle";
import { PersonaManagerDrawer } from "@/components/PersonaManagerDrawer";
import { PresetSaveDialog } from "@/components/PresetSaveDialog";
import { Timeline } from "@/components/Timeline";
import { MinutesPanel } from "@/components/MinutesPanel";
import { OnAir } from "@/components/OnAir";
import { Chyron } from "@/components/Chyron";
import { Play, Square, AlertCircle, Send } from "lucide-react";

type Status = "idle" | "running" | "done" | "error";

const DEFAULT_SELECTED = ["moderator", "logic", "idea", "empathy", "chair"];

// 楽観的エコー用の負の turn_id を払い出す（サーバ採番は 0 以上なので衝突しない）。
let echoSeq = -1;

export default function Home() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set(DEFAULT_SELECTED));
  const [roundsPerPhase, setRoundsPerPhase] = useState(1);
  const [redTeam, setRedTeam] = useState(true);
  const [redTeamId, setRedTeamId] = useState<string | null>(null);

  const [topicInput, setTopicInput] = useState("");
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [streamingTurnId, setStreamingTurnId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const [useLlm, setUseLlm] = useState(false); // GAP5: 既定は mock（無料）
  const [health, setHealth] = useState<Health | null>(null);

  const [manageOpen, setManageOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const loadPersonas = () => {
    fetchPersonas()
      .then(setPersonas)
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    loadPersonas();
    fetchPresets()
      .then(setPresets)
      .catch(() => {
        /* プリセット未提供でも本体は動かす */
      });
    fetchHealth()
      .then(setHealth)
      .catch(() => {
        /* health 取得失敗時は mock 既定のまま動かす */
      });
  }, []);

  const looks = useMemo(() => {
    const m: Record<string, { accent: string; monogram: string }> = {};
    for (const p of personas) m[p.id] = { accent: p.accent, monogram: p.monogram };
    return m;
  }, [personas]);

  const synthesis = useMemo(
    () => turns.find((t) => t.phase === "synthesis") ?? null,
    [turns]
  );
  const summary = useMemo(
    () => turns.find((t) => t.phase === "summary") ?? null,
    [turns]
  );

  // 最新ターンのフェーズ（Chyron 表示・追い質問可否の判定に使う）。
  const currentPhase = turns.length ? turns[turns.length - 1].phase : null;

  const running = status === "running";

  // 実 LLM が実際に使われるか（GAP5: NOT(useLlm AND key_set) が mock）。
  const willUseRealLlm = useLlm && (health?.api_key_set ?? false);

  // 追い質問の処理中（人間ターンのエコー・司会再提示・パネリスト応答が流れている間）。
  const processingFollowup =
    currentPhase === "human" || currentPhase === "followup";

  // 追い質問が出せる状態か: running 中・フェーズ確定済み・本編フェーズ・処理中でない。
  const canFollowup =
    running &&
    sessionId !== null &&
    currentPhase !== null &&
    !(FOLLOWUP_DISABLED_PHASES as readonly string[]).includes(currentPhase) &&
    !processingFollowup;

  function toggle(id: string) {
    setSelectedPresetId(null); // 手動変更したらプリセット選択を解除
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function applyPreset(preset: Preset | null) {
    if (!preset) {
      setSelectedPresetId(null);
      return;
    }
    setSelectedPresetId(preset.id);
    const known = new Set(personas.map((p) => p.id));
    setSelected(new Set(preset.persona_ids.filter((id) => known.has(id))));
    setRoundsPerPhase(preset.rounds_per_phase);
    setRedTeam(preset.red_team);
    setRedTeamId(preset.red_team_id ?? null);
  }

  function stop() {
    // 表示の購読を止めるだけでなく、バックエンドにも協調キャンセルを伝える
    // （実 LLM の発注を次のターン前に止めて課金を抑える）。
    if (sessionId) cancelSession(sessionId);
    abortRef.current?.abort();
    setStatus((s: Status) => (s === "running" ? "done" : s));
    setStreamingTurnId(null);
  }

  async function start() {
    const topic = topicInput.trim();
    if (!topic || selected.size === 0 || running) return;

    const ordered = personas.filter((p) => selected.has(p.id)).map((p) => p.id);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setActiveTopic(topic);
    setTurns([]);
    setError(null);
    setStatus("running");
    setStreamingTurnId(null);
    setSessionId(null);
    setTopicInput("");

    try {
      await startSession({
        topic,
        personaIds: ordered,
        roundsPerPhase, // GAP6
        redTeam, // GAP6
        redTeamId, // GAP6
        mock: !willUseRealLlm, // GAP5: NOT(useLlm AND api_key_set)
        signal: ctrl.signal,
        onEvent: (e) => {
          if (e.type === "start") {
            setSessionId(e.sessionId);
          } else if (e.type === "turn_start") {
            setTurns((prev) => {
              let base = prev;
              // GAP4: サーバの human ターンが来たら、未確定(turn_id<0)の human エコーを
              // FIFO 先頭から1件だけ除去する（turn_start 時点で本文未着＝content 照合不可）。
              if (e.speakerId === "human") {
                const idx = base.findIndex(
                  (t) => t.phase === "human" && t.turn_id < 0
                );
                if (idx !== -1) {
                  base = [...base.slice(0, idx), ...base.slice(idx + 1)];
                }
              }
              return [
                ...base,
                {
                  turn_id: e.turnId,
                  speaker_id: e.speakerId,
                  speaker_name: e.speakerName,
                  content: "",
                  phase: e.phase,
                  round: e.round,
                  ts: e.ts,
                },
              ];
            });
            setStreamingTurnId(e.turnId);
          } else if (e.type === "delta") {
            setTurns((prev) =>
              prev.map((t) =>
                t.turn_id === e.turnId ? { ...t, content: t.content + e.text } : t
              )
            );
          } else if (e.type === "turn_end") {
            setStreamingTurnId((cur) => (cur === e.turnId ? null : cur));
          } else if (e.type === "error") {
            setError(e.message);
            setStatus("error");
            setStreamingTurnId(null);
          } else if (e.type === "done") {
            setStatus("done");
            setStreamingTurnId(null);
          }
        },
      });
    } catch (err) {
      if (!ctrl.signal.aborted) {
        setError(String(err));
        setStatus("error");
      }
    }
  }

  // 追い質問の送信。楽観エコー → POST → 失敗ならロールバック（UIはクラッシュしない）。
  async function sendQuestion() {
    const text = topicInput.trim();
    if (!text || !canFollowup || !sessionId) return;

    const echoId = echoSeq--;
    setTurns((prev) => [
      ...prev,
      {
        turn_id: echoId,
        speaker_id: "human",
        speaker_name: "あなた",
        content: text,
        phase: "human",
        round: 0,
        ts: Date.now() / 1000,
      },
    ]);
    setTopicInput("");

    try {
      await sendFollowup(sessionId, text);
    } catch (err) {
      // 送信失敗: 楽観エコーを取り消し、理由を表示（未実装 backend の 404 でも安全）。
      setTurns((prev) => prev.filter((t) => t.turn_id !== echoId));
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function onComposerKeyDown(e: React.KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      if (running) {
        if (canFollowup) sendQuestion();
      } else {
        start();
      }
    }
  }

  // 入力欄が追い質問モードのとき、無効なら理由 microcopy を出す。
  const followupBlockReason = running
    ? canFollowup
      ? null
      : currentPhase === null
        ? "討論の開始を待っています。"
        : processingFollowup
          ? "前の追い質問を処理中です。応答が出そろうと送信できます。"
          : "このフェーズ（要約・統合・冒頭）では追い質問を受け付けられません。"
    : null;

  return (
    <div className="flex h-screen flex-col">
      {/* ヘッダー */}
      <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
        <h1 className="font-display text-base tracking-widest">AI COUNCIL</h1>
        <OnAir status={status} />
      </header>

      {/* 3レーン */}
      <div className="grid min-h-0 flex-1 grid-cols-[260px_1fr_320px]">
        {/* 左：編成 */}
        <aside className="flex flex-col gap-5 overflow-y-auto border-r border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-5">
          <PresetBar
            presets={presets}
            personas={personas}
            selectedPresetId={selectedPresetId}
            onApply={applyPreset}
            onSaveCurrent={() => setSaveOpen(true)}
            disabled={running}
          />

          <LlmToggle
            useLlm={useLlm}
            health={health}
            onChange={setUseLlm}
            disabled={running}
          />

          <PersonaPicker
            personas={personas}
            selected={selected}
            onToggle={toggle}
            disabled={running}
            onManage={() => setManageOpen(true)}
          />
        </aside>

        {/* 中央：討論 */}
        <main className="flex min-h-0 flex-col">
          <Chyron phase={currentPhase} status={status} />

          <div className="min-h-0 flex-1">
            <Timeline
              topic={activeTopic}
              turns={turns}
              streamingTurnId={streamingTurnId}
              looks={looks}
              status={status}
            />
          </div>

          {error && (
            <div className="mx-6 mb-2 flex items-center gap-2 rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2 text-xs text-[var(--color-onair)]">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          {/* 実 LLM 選択時のみ、控えめにコスト注記（GAP5） */}
          {willUseRealLlm && !running && (
            <p className="mx-6 mb-2 text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
              実 LLM で討論します。開始後は画面を閉じても完走し、API 利用料が発生します。
            </p>
          )}

          {/* 入力バー（running 中は同じ textarea を追い質問モードに切替） */}
          <div className="border-t border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
            {followupBlockReason && (
              <p className="mb-1.5 text-[11px] text-[var(--color-ink-muted)]">
                {followupBlockReason}
              </p>
            )}
            <div className="flex items-end gap-2">
              <textarea
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                onKeyDown={onComposerKeyDown}
                rows={1}
                placeholder={
                  running
                    ? canFollowup
                      ? "追い質問を入力（⌘/Ctrl+Enter で送信）"
                      : "いまは追い質問を受け付けていません"
                    : "議題を入力（⌘/Ctrl+Enter で開始）"
                }
                disabled={running && !canFollowup}
                className="max-h-32 min-h-[40px] flex-1 resize-none rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
              />
              {running ? (
                <>
                  <button
                    onClick={sendQuestion}
                    disabled={!canFollowup || !topicInput.trim()}
                    className="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
                  >
                    <Send size={14} /> 送信
                  </button>
                  <button
                    onClick={stop}
                    className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-4 py-2 text-sm hover:border-[var(--color-ink-muted)]"
                  >
                    <Square size={14} /> 停止
                  </button>
                </>
              ) : (
                <button
                  onClick={start}
                  disabled={!topicInput.trim() || selected.size === 0}
                  className="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
                >
                  <Play size={14} /> 討論を開始
                </button>
              )}
            </div>
          </div>
        </main>

        {/* 右：成果 */}
        <aside className="overflow-hidden border-l border-[var(--color-line)] bg-[var(--color-surface)]">
          <MinutesPanel summary={summary} synthesis={synthesis} status={status} />
        </aside>
      </div>

      {/* ペルソナ管理ドロワー */}
      <PersonaManagerDrawer
        open={manageOpen}
        personas={personas}
        onClose={() => setManageOpen(false)}
        onChanged={loadPersonas}
      />

      {/* プリセット保存ダイアログ */}
      {saveOpen && (
        <PresetSaveDialog
          personaIds={personas.filter((p) => selected.has(p.id)).map((p) => p.id)}
          roundsPerPhase={roundsPerPhase}
          redTeam={redTeam}
          redTeamId={redTeamId}
          onClose={() => setSaveOpen(false)}
          onSaved={(p) => {
            setPresets((prev) => [...prev, p]);
            setSelectedPresetId(p.id);
            setSaveOpen(false);
          }}
        />
      )}
    </div>
  );
}
