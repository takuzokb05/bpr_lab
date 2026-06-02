"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  cancelSession,
  closeSession,
  fetchHealth,
  fetchIntake,
  fetchPersonas,
  finishSession,
  sendFollowup,
  startSession,
  type Health,
} from "@/lib/sse";
import { fetchPresets } from "@/lib/api";
import {
  FOLLOWUP_DISABLED_PHASES,
  type IntakeQA,
  type Persona,
  type Preset,
  type Turn,
} from "@/lib/types";
import {
  getUserKey,
  setUserKey,
  getProvider,
  setProvider,
  LLM_PROVIDERS,
  type LlmProvider,
} from "@/lib/config";
import { PersonaPicker } from "@/components/PersonaPicker";
import { PresetBar } from "@/components/PresetBar";
import { LlmToggle } from "@/components/LlmToggle";
import { KeyEntry } from "@/components/KeyEntry";
import { PersonaManagerDrawer } from "@/components/PersonaManagerDrawer";
import { PresetSaveDialog } from "@/components/PresetSaveDialog";
import { Timeline } from "@/components/Timeline";
import { MinutesPanel } from "@/components/MinutesPanel";
import { OnAir } from "@/components/OnAir";
import { Chyron } from "@/components/Chyron";
import {
  Play,
  Square,
  AlertCircle,
  Send,
  FileText,
  CircleStop,
  Paperclip,
  ListChecks,
  Globe,
  Search,
} from "lucide-react";

// 準備フェーズ: クライアント側で読み込む資料の拡張子（PDF/Office は MVP 対象外）。
const MATERIAL_FILE_ACCEPT = ".txt,.md,.csv,.json";

// "paused" = 議場開放（floor-open）。本編後に自動 synthesis せず入力待ちで停止した状態。
type Status = "idle" | "running" | "paused" | "done" | "error";

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

  // 準備フェーズ（idle のみ）: 資料・前提と主訴確認。討論中/paused/done では一切出さない。
  const [materials, setMaterials] = useState("");
  // 主訴確認トグル（Web 検索と同じ作法）。ON にすると議題から確認質問を自動生成する。
  // 既定 OFF で従来同一（質問なしで即開始できる）。
  const [intakeEnabled, setIntakeEnabled] = useState(false);
  // 確認質問（fetchIntake の結果）と各質問への回答。回答は任意・スキップ可。
  const [intakeQuestions, setIntakeQuestions] = useState<string[]>([]);
  const [intakeAnswers, setIntakeAnswers] = useState<Record<number, string>>({});
  const [intakeLoading, setIntakeLoading] = useState(false);
  // 自動生成済みの議題（同じ議題で二重生成・課金しないためのガード）。
  const intakeTopicRef = useRef<string | null>(null);

  // Web 検索（調査役）。既定 false で従来と完全同一（mock/キー未設定なら canned で無料）。
  // true のとき調査役が序盤と「要調査:」マーカーで検索し、結果を全員に共有する（コスト増）。
  const [research, setResearch] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [streamingTurnId, setStreamingTurnId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const [useLlm, setUseLlm] = useState(false); // GAP5: 既定は mock（無料）
  const [health, setHealth] = useState<Health | null>(null);
  // BYOK: 各自のキー＋プロバイダ。localStorage が実体（SSR/export 時は空なので mount 後に読む）。
  const [userKey, setUserKeyState] = useState("");
  const [provider, setProviderState] = useState<LlmProvider>("anthropic");

  const [manageOpen, setManageOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  // 入力欄（議題／追い質問の兼用コンポーザー）。内容に応じて高さを自動可変にし、送信前に
  // 入力全体を見返せるようにする（max-h まで伸び、それ以上はスクロール）。
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  const loadPersonas = () => {
    fetchPersonas()
      .then(setPersonas)
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    loadPersonas();
    setUserKeyState(getUserKey()); // localStorage は client のみ。mount 後に読む
    setProviderState(getProvider());
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

  // BYOK キーの更新（localStorage に保存し state も同期）。空文字で保存＝クリア。
  function updateUserKey(key: string) {
    setUserKey(key);
    setUserKeyState(key.trim());
  }

  // プロバイダ切替（localStorage に保存し state も同期）。キーのクリアは KeyEntry 側で行う。
  function updateProvider(p: LlmProvider) {
    setProvider(p);
    setProviderState(p);
  }

  const looks = useMemo(() => {
    const m: Record<string, { accent: string; monogram: string }> = {};
    for (const p of personas) m[p.id] = { accent: p.accent, monogram: p.monogram };
    return m;
  }, [personas]);

  const synthesis = useMemo(
    () => turns.find((t) => t.phase === "synthesis") ?? null,
    [turns]
  );

  // 最新ターンのフェーズ（Chyron 表示・追い質問可否の判定に使う）。
  const currentPhase = turns.length ? turns[turns.length - 1].phase : null;

  const running = status === "running";
  // 準備フェーズ（資料接地＋主訴確認）を出すのは idle のときだけ。running/paused/done/error では出さない。
  const idle = status === "idle";
  // floor-open（議場開放）= 本編後の入力待ち。追い質問の主戦場。
  const paused = status === "paused";
  // セッション稼働中（編成は固定・入力欄は追い質問モード）。running または paused。
  const active = running || paused;

  // BYOK モードか（サーバが共有/公開設定）。実 LLM のキー所在が分岐する。
  const byok = health?.byok ?? false;
  // 実 LLM に使えるキーがあるか: BYOK は各自のキー（localStorage）、個人運用はサーバキー。
  const keyAvailable = byok ? userKey.trim().length > 0 : (health?.api_key_set ?? false);
  // 実 LLM が実際に使われるか（mock = NOT(useLlm AND keyAvailable)。キーが無ければ常に mock）。
  const willUseRealLlm = useLlm && keyAvailable;
  // 対応プロバイダ（health から。未取得時は全 3 社）。
  const availableProviders = (health?.providers as LlmProvider[] | undefined) ?? LLM_PROVIDERS;
  // Web 検索（調査役）は anthropic のみ対応。非 anthropic では研究トグルを無効化する。
  const researchProvider = health?.research_provider ?? "anthropic";
  const researchAvailable = provider === researchProvider;

  // 追い質問の処理中（人間ターンのエコー・司会再提示・パネリスト応答が流れている間）。
  const processingFollowup =
    currentPhase === "human" || currentPhase === "followup";

  // 追い質問が出せる状態か:
  //  - paused（floor-open）: 常に true。議場開放は追い質問の主戦場。
  //  - running: フェーズ確定済み・本編フェーズ・処理中でない（本編フェーズ中の注入）。
  const canFollowup =
    sessionId !== null &&
    (paused ||
      (running &&
        currentPhase !== null &&
        !(FOLLOWUP_DISABLED_PHASES as readonly string[]).includes(currentPhase) &&
        !processingFollowup));

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
    setStatus((s: Status) => (s === "running" || s === "paused" ? "done" : s));
    setStreamingTurnId(null);
  }

  // 準備フェーズ: 主訴を固める確認質問を 2〜4 個取得。トグル ON＋議題確定で自動的に呼ばれる。
  // 失敗しても討論自体は妨げない（資料だけ／質問なしで開始できる）。mock は討論設定に追従。
  async function loadIntake() {
    const topic = topicInput.trim();
    if (!topic || intakeLoading || active) return;
    setIntakeLoading(true);
    setError(null);
    try {
      const questions = await fetchIntake(topic, materials, !willUseRealLlm);
      setIntakeQuestions(questions);
      setIntakeAnswers({}); // 質問が差し替わったら回答もリセット
      intakeTopicRef.current = topic; // この議題は生成済み（二重生成を防ぐ）
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIntakeLoading(false);
    }
  }

  // 主訴確認トグル。OFF にしたら生成済みの質問・回答を破棄（資料・議題はそのまま）。
  function toggleIntake() {
    setIntakeEnabled((v) => {
      const next = !v;
      if (!next) {
        setIntakeQuestions([]);
        setIntakeAnswers({});
        intakeTopicRef.current = null;
      }
      return next;
    });
  }

  // トグル ON のとき、議題が確定したら確認質問を自動生成（Web 検索トグルと同じ「ON にすれば後は自動」）。
  // 議題が変わるたびに作り直す。入力中の連打を避けるため 700ms デバウンス。同一議題は再生成しない。
  useEffect(() => {
    if (!intakeEnabled || active) return;
    const topic = topicInput.trim();
    if (!topic || intakeTopicRef.current === topic) return;
    const t = setTimeout(() => {
      loadIntake();
    }, 700);
    return () => clearTimeout(t);
    // loadIntake は最新クロージャを使うため deps から除外（topicInput 変化で再設定される）。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intakeEnabled, topicInput, active]);

  // Web 検索が使えない provider（非 Anthropic）に切り替わったら研究トグルを強制 off。
  // （ON のまま残ると、サーバ側でも強制 off だが UI の表示と挙動が食い違うのを防ぐ）
  useEffect(() => {
    if (!researchAvailable && research) setResearch(false);
  }, [researchAvailable, research]);

  // 入力欄の高さを内容に追従させる（送信前の見返し用）。一旦 0 に潰してから scrollHeight を測り、
  // CSS の max-h でクランプ＋それ以上はスクロール。topicInput が変わるたびに再計算。
  useLayoutEffect(() => {
    const el = composerRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${el.scrollHeight}px`;
  }, [topicInput]);

  // 準備フェーズ: ファイル添付（.txt/.md/.csv/.json）をクライアント側で読み、資料欄に取り込む。
  // PDF/Office は対象外。複数選択時は区切って連結。読み込み後は input をリセットして同じ
  // ファイルを再選択できるようにする。
  function onAttachFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const readers = Array.from(files).map(
      (file) =>
        new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve(`【${file.name}】\n${String(reader.result ?? "")}`);
          reader.onerror = () => resolve(""); // 読めないファイルは黙って飛ばす（他は活かす）
          reader.readAsText(file);
        })
    );
    Promise.all(readers).then((texts) => {
      const chunk = texts.filter((t) => t.trim()).join("\n\n");
      if (!chunk) return;
      setMaterials((prev) => (prev.trim() ? `${prev}\n\n${chunk}` : chunk));
    });
    e.target.value = ""; // 同じファイルを続けて選べるようにする
  }

  async function start() {
    const topic = topicInput.trim();
    if (!topic || selected.size === 0 || active) return;

    const ordered = personas.filter((p) => selected.has(p.id)).map((p) => p.id);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // 準備フェーズの確定値を組む。回答済み（trim 後 非空）の Q&A だけを intake に載せる。
    // 質問未取得でも materials だけで開始できる。
    const trimmedMaterials = materials.trim();
    const intake: IntakeQA[] = intakeQuestions
      .map((question, i) => ({ question, answer: (intakeAnswers[i] ?? "").trim() }))
      .filter((qa) => qa.answer !== "");

    setActiveTopic(topic);
    setTurns([]);
    setError(null);
    setStatus("running");
    setStreamingTurnId(null);
    setSessionId(null);
    setTopicInput("");
    // 準備フェーズの入力は開始時に確定済み。idle に戻ったとき前回分が残らないようクリア。
    setMaterials("");
    setIntakeQuestions([]);
    setIntakeAnswers({});

    try {
      await startSession({
        topic,
        personaIds: ordered,
        roundsPerPhase, // GAP6
        redTeam, // GAP6
        redTeamId, // GAP6
        mock: !willUseRealLlm, // GAP5: NOT(useLlm AND api_key_set)
        materials: trimmedMaterials, // 準備フェーズ: 資料接地（空なら body に載らない）
        intake, // 準備フェーズ: 回答済み確認 Q&A（空なら body に載らない）
        research, // 準備フェーズ: Web 検索（調査役）。false なら body に載らない＝従来同一
        interactive: true, // Web は floor-open（本編後に一時停止して入力を待つ）
        signal: ctrl.signal,
        onEvent: (e) => {
          if (e.type === "start") {
            setSessionId(e.sessionId);
          } else if (e.type === "turn_start") {
            // floor-open から再開（追い質問 deepen / 締め synthesis）。running に戻す。
            setStatus((s: Status) => (s === "paused" ? "running" : s));
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
          } else if (e.type === "paused") {
            // floor-open に入った。入力待ちへ。ストリーミング表示はクリアする。
            setStatus("paused");
            setStreamingTurnId(null);
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

  // 議場開放（floor-open）: 「議事録を作る」＝議長に synthesis を生成させる。
  // 締めても議場は開いたまま＝終了後の深掘りも同機構（status は paused→running→paused）。
  async function makeMinutes() {
    if (!paused || !sessionId) return;
    try {
      await closeSession(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  // 議場開放（floor-open）: 「終了」＝floor-open ループを抜けて done。
  async function finishCouncil() {
    if (!paused || !sessionId) return;
    try {
      await finishSession(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function onComposerKeyDown(e: React.KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      if (active) {
        // running/paused とも、追い質問が出せる状態なら送信。
        if (canFollowup) sendQuestion();
      } else {
        start();
      }
    }
  }

  // 入力欄が追い質問モードのとき、無効なら理由 microcopy を出す。
  // paused（floor-open）は常に追い質問可なので理由は出さない。
  const followupBlockReason =
    running && !canFollowup
      ? currentPhase === null
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
            disabled={active}
          />

          {byok && (
            <KeyEntry
              provider={provider}
              onProviderChange={updateProvider}
              value={userKey}
              onChange={updateUserKey}
              providers={availableProviders}
              disabled={active}
            />
          )}

          <LlmToggle
            useLlm={useLlm}
            keyAvailable={keyAvailable}
            byok={byok}
            onChange={setUseLlm}
            disabled={active}
          />

          <PersonaPicker
            personas={personas}
            selected={selected}
            onToggle={toggle}
            disabled={active}
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
          {willUseRealLlm && !active && (
            <p className="mx-6 mb-2 text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
              実 LLM で討論します。開始後は画面を閉じても完走し、API 利用料が発生します。
            </p>
          )}

          {/* 準備フェーズ（idle のみ）: 資料・前提（任意）＋ 主訴確認（任意）。
              討論中/paused/done/error では出さない＝既存の討論 UI は不変。 */}
          {idle && (
            <div className="mx-6 mb-2 max-h-[42vh] space-y-3 overflow-y-auto rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3.5 py-3">
              {/* 資料・前提 */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-muted)]">
                    資料・前提（任意）
                  </span>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-2.5 py-1 text-[11px] text-[var(--color-ink-muted)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
                  >
                    <Paperclip size={12} /> ファイルを取り込む
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={MATERIAL_FILE_ACCEPT}
                    multiple
                    onChange={onAttachFiles}
                    className="hidden"
                  />
                </div>
                <textarea
                  value={materials}
                  onChange={(e) => setMaterials(e.target.value)}
                  rows={3}
                  placeholder="討論で踏まえてほしい資料・前提・数字を貼り付け（全ペルソナが共有します）"
                  className="max-h-40 min-h-[60px] w-full resize-y rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-2 text-sm outline-none focus:border-[var(--color-accent)]"
                />
                <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                  取り込めるファイル: .txt / .md / .csv / .json（PDF・Office は対象外）。
                </p>
              </div>

              {/* 主訴確認（トグル）。ON にすると議題から確認質問を自動生成し、回答（任意）を
                  討論に渡して論点の逸脱を防ぐ。OFF（既定）では一切生成しない＝従来同一。
                  議題入力欄（最下部）が空でもトグルは操作でき、議題を入れると自動生成される。 */}
              <div className="flex flex-col gap-1.5 border-t border-[var(--color-line)] pt-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={intakeEnabled}
                  onClick={toggleIntake}
                  className={`flex items-center justify-between gap-3 rounded-md border px-2.5 py-2 text-left transition-colors ${
                    intakeEnabled
                      ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)]"
                      : "border-[var(--color-line)] hover:border-[var(--color-ink-muted)]"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <ListChecks
                      size={14}
                      className={
                        intakeEnabled
                          ? "text-[var(--color-accent)]"
                          : "text-[var(--color-ink-muted)]"
                      }
                    />
                    <span
                      className={`text-xs ${
                        intakeEnabled
                          ? "text-[var(--color-accent)]"
                          : "text-[var(--color-ink)]"
                      }`}
                    >
                      主訴確認で論点の逸脱を防ぐ
                    </span>
                  </span>
                  <span
                    aria-hidden="true"
                    className={`inline-flex h-4 w-7 shrink-0 items-center rounded-full p-0.5 transition-colors ${
                      intakeEnabled
                        ? "bg-[var(--color-accent)]"
                        : "bg-[var(--color-line)]"
                    }`}
                  >
                    <span
                      className={`h-3 w-3 rounded-full bg-[var(--color-surface)] transition-transform ${
                        intakeEnabled ? "translate-x-3" : "translate-x-0"
                      }`}
                    />
                  </span>
                </button>

                {intakeEnabled &&
                  (!topicInput.trim() ? (
                    <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                      <ListChecks size={12} className="mt-0.5 shrink-0" />
                      下の入力欄に議題を入れると、主訴を固める確認質問を自動で作成します（回答は任意）。
                    </p>
                  ) : intakeLoading ? (
                    <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                      確認質問を作成中…
                    </p>
                  ) : intakeQuestions.length === 0 ? (
                    <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                      確認質問を準備しています…
                    </p>
                  ) : (
                    <ul className="space-y-2.5">
                      {intakeQuestions.map((q, i) => (
                        <li key={i} className="flex flex-col gap-1">
                          <span className="text-xs leading-relaxed text-[var(--color-ink)]">
                            {q}
                          </span>
                          <textarea
                            value={intakeAnswers[i] ?? ""}
                            onChange={(e) =>
                              setIntakeAnswers((prev) => ({ ...prev, [i]: e.target.value }))
                            }
                            rows={1}
                            placeholder="回答（任意・空欄のまま開始してもよい）"
                            className="max-h-28 min-h-[34px] w-full resize-y rounded-md border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm outline-none focus:border-[var(--color-accent)]"
                          />
                        </li>
                      ))}
                    </ul>
                  ))}
              </div>

              {/* Web 検索（調査役）。既定 OFF。ON のとき調査役が序盤と「要調査:」で
                  事実を調べ全員に共有する＝コスト増（mock/キー未設定なら canned で無料）。 */}
              <div className="flex flex-col gap-1.5 border-t border-[var(--color-line)] pt-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={research}
                  disabled={!researchAvailable}
                  title={
                    researchAvailable
                      ? undefined
                      : "Web 検索は Anthropic 選択時のみ対応です"
                  }
                  onClick={() => researchAvailable && setResearch((v) => !v)}
                  className={`flex items-center justify-between gap-3 rounded-md border px-2.5 py-2 text-left transition-colors disabled:opacity-40 ${
                    research
                      ? "border-[var(--color-accent)] bg-[var(--color-accent-weak)]"
                      : "border-[var(--color-line)] hover:border-[var(--color-ink-muted)]"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Globe
                      size={14}
                      className={
                        research
                          ? "text-[var(--color-accent)]"
                          : "text-[var(--color-ink-muted)]"
                      }
                    />
                    <span
                      className={`text-xs ${
                        research
                          ? "text-[var(--color-accent)]"
                          : "text-[var(--color-ink)]"
                      }`}
                    >
                      Web 検索で事実を調べる（コスト増）
                    </span>
                  </span>
                  <span
                    aria-hidden="true"
                    className={`inline-flex h-4 w-7 shrink-0 items-center rounded-full p-0.5 transition-colors ${
                      research
                        ? "bg-[var(--color-accent)]"
                        : "bg-[var(--color-line)]"
                    }`}
                  >
                    <span
                      className={`h-3 w-3 rounded-full bg-[var(--color-surface)] transition-transform ${
                        research ? "translate-x-3" : "translate-x-0"
                      }`}
                    />
                  </span>
                </button>
                <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                  <Search size={12} className="mt-0.5 shrink-0" />
                  {researchAvailable
                    ? "調査役が序盤と「要調査」の問いだけを検索し、出典付きで全員に共有します。重複は省きます。"
                    : "Web 検索は Anthropic 選択時のみ対応です（OpenAI/Google では検索なしで進めます）。"}
                </p>
              </div>
            </div>
          )}

          {/* 議場開放（floor-open）コントロール。本編が終わり入力待ちのときだけ出す。
              追い質問は下の入力バーが主戦場。ここでは「議事録を作る」「終了」を提示する。 */}
          {paused && (
            <div className="mx-6 mb-2 rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2.5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
                  本編が終わり、議場を開いています。追い質問を続けるか、議事録を作るか、終了できます。
                </p>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    onClick={makeMinutes}
                    className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
                  >
                    <FileText size={13} /> 議事録を作る
                  </button>
                  <button
                    onClick={finishCouncil}
                    className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs hover:border-[var(--color-ink-muted)]"
                  >
                    <CircleStop size={13} /> 終了
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 入力バー（active 中＝running/paused は同じ textarea を追い質問モードに切替） */}
          <div className="border-t border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
            {followupBlockReason && (
              <p className="mb-1.5 text-[11px] text-[var(--color-ink-muted)]">
                {followupBlockReason}
              </p>
            )}
            <div className="flex items-end gap-2">
              <textarea
                ref={composerRef}
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                onKeyDown={onComposerKeyDown}
                rows={1}
                placeholder={
                  active
                    ? canFollowup
                      ? "追い質問を入力（⌘/Ctrl+Enter で送信）"
                      : "いまは追い質問を受け付けていません"
                    : "議題を入力（⌘/Ctrl+Enter で開始）"
                }
                disabled={active && !canFollowup}
                className="max-h-[40vh] min-h-[40px] flex-1 resize-none overflow-y-auto rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-2 text-sm leading-relaxed outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
              />
              {active ? (
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
          <MinutesPanel synthesis={synthesis} status={status} />
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
