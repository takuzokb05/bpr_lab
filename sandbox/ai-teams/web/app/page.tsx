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
  resumeSession,
  type Health,
  type StreamEvent,
} from "@/lib/sse";
import { fetchPresets } from "@/lib/api";
import {
  FOLLOWUP_DISABLED_PHASES,
  customToPersona,
  type IntakeQA,
  type Persona,
  type Preset,
  type Turn,
  type CustomPersona,
} from "@/lib/types";
import {
  getUserKey,
  setUserKey,
  getProvider,
  setProvider,
  getVerbosity,
  setVerbosity,
  getCustomPersonas,
  setCustomPersonas,
  getHistory,
  saveHistoryEntry,
  deleteHistoryEntry,
  LLM_PROVIDERS,
  type LlmProvider,
  type Verbosity,
  type HistoryEntry,
} from "@/lib/config";
import { PersonaPicker } from "@/components/PersonaPicker";
import { PresetBar } from "@/components/PresetBar";
import { LlmToggle } from "@/components/LlmToggle";
import { KeyEntry } from "@/components/KeyEntry";
import { VerbositySelect } from "@/components/VerbositySelect";
import { MyPersonasDrawer } from "@/components/MyPersonasDrawer";
import { HistoryDrawer } from "@/components/HistoryDrawer";
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
  History,
} from "lucide-react";

// 準備フェーズ: クライアント側で読み込む資料の拡張子（PDF/Office は MVP 対象外）。
const MATERIAL_FILE_ACCEPT = ".txt,.md,.csv,.json";

// "paused" = 議場開放（floor-open）。本編後に自動 synthesis せず入力待ちで停止した状態。
type Status = "idle" | "running" | "paused" | "done" | "error";

// 司会(facilitation)・議長(chair)は進行の固定役として自動で含める（ユーザーは選ばない）。
// 書記(scribe)は発言しないので編成から除外。ピッカーで選ぶのはパネリストだけ。
const STRUCTURAL_CATS = ["facilitation", "chair"];
// 既定で選択するパネリスト（構造役は自動付与するので含めない）。
const DEFAULT_SELECTED = ["logic", "idea", "empathy"];

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
  // 応答の長さ（既定 standard）。トークン数ではなく質感で選ぶ。
  const [verbosity, setVerbosityState] = useState<Verbosity>("standard");
  // 自分のペルソナ（クライアント定義・localStorage・サーバ非保存）。
  const [customPersonas, setCustomPersonasState] = useState<CustomPersona[]>([]);
  const [myPersonasOpen, setMyPersonasOpen] = useState(false);
  // 討論履歴（クライアント保存・サーバ非依存）。見返し・再開の入口。
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  // 「この討論を続ける」時に前回討論をどれだけ文脈に載せるか。既定=軽量（議事録＋直近）。
  const [continueScope, setContinueScope] = useState<"light" | "full">("light");
  const restoredRef = useRef(false); // 初回マウントの自動再開を一度だけ行う

  const [manageOpen, setManageOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  // ストリーム（SSE）が生きているか。モバイルのバックグラウンド化で切れた後、フォアグラウンド
  // 復帰時に再接続すべきか判定する（生きている間は二重接続しない）。
  const streamAliveRef = useRef(false);
  // visibilitychange ハンドラから最新のセッション状態を参照する（delta 毎の購読し直しを避ける）。
  const sessionStateRef = useRef<{
    sessionId: string | null;
    status: Status;
    activeTopic: string | null;
    turns: Turn[];
  }>({ sessionId: null, status: "idle", activeTopic: null, turns: [] });
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
    setVerbosityState(getVerbosity());
    setCustomPersonasState(getCustomPersonas());
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

  // 履歴の読込＋復帰。直近の running/paused かつ最近（30分以内）の討論は自動で再接続を試みる
  // （ページ再読込・ロード失敗からの復帰）。サーバが失っていれば保存済み transcript を凍結表示。
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    const h = getHistory();
    setHistory(h);
    const last = h[0];
    const RECENT_MS = 30 * 60 * 1000;
    // running/paused だけでなく error（接続断で誤って error 記録された可能性）も再接続を試みる。
    // done は完了済みなので自動再開しない。
    if (
      last &&
      last.status !== "done" &&
      Date.now() - last.updatedAt < RECENT_MS
    ) {
      resumeOrLoad(last);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 進行中/完了の討論を localStorage に保存（見返し・再開用）。delta 毎の重い書込を避けるため
  // turns.length と status の変化時に保存する（保存値は最新の turns 全体＝確定後の本文も入る）。
  useEffect(() => {
    // 空の turns では保存しない（resume/launch のクリア中に保存済み transcript を空で
    // 上書きしてしまうのを防ぐ＝履歴消失の防御）。
    if (!sessionId || !activeTopic || turns.length === 0) return;
    saveHistoryEntry({ id: sessionId, topic: activeTopic, status, turns });
    setHistory(getHistory());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, activeTopic, status, turns.length]);

  // 最新セッション状態を ref に同期（visibilitychange ハンドラが参照する）。
  sessionStateRef.current = { sessionId, status, activeTopic, turns };

  // モバイルでバックグラウンド化→フォアグラウンド復帰したとき、進行中セッションのストリームが
  // 切れていたら再接続する（cursor=0 で replay 再構築）。購読は一度だけ（ref で最新値を読む）。
  useEffect(() => {
    function onVisible() {
      if (typeof document === "undefined") return;
      if (document.visibilityState !== "visible") return;
      if (streamAliveRef.current) return; // まだ繋がっている
      const s = sessionStateRef.current;
      if (!s.sessionId) return;
      if (s.status !== "running" && s.status !== "paused") return;
      void resumeOrLoad({
        id: s.sessionId,
        topic: s.activeTopic ?? "",
        startedAt: Date.now(),
        updatedAt: Date.now(),
        status: s.status,
        turns: s.turns,
      });
    }
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // 応答の長さ切替（localStorage に保存し state も同期）。
  function updateVerbosity(v: Verbosity) {
    setVerbosity(v);
    setVerbosityState(v);
  }

  // 自分のペルソナの更新（localStorage 保存＋state 同期）。削除されたペルソナは選択からも外す。
  function updateCustomPersonas(list: CustomPersona[]) {
    setCustomPersonas(list);
    setCustomPersonasState(list);
    const ids = new Set(list.map((p) => p.id));
    setSelected((prev) => {
      const next = new Set<string>();
      for (const id of prev) {
        // サーバのパネリスト or 残っているカスタムだけ選択に残す。
        if (personas.some((p) => p.id === id) || ids.has(id)) next.add(id);
      }
      return next;
    });
  }

  // サーバのペルソナ＋自分のペルソナ（クライアント定義）を統合。ピッカー・looks・編成で使う。
  const allPersonas = useMemo(
    () => [...personas, ...customPersonas.map(customToPersona)],
    [personas, customPersonas]
  );

  const looks = useMemo(() => {
    const m: Record<string, { accent: string; monogram: string }> = {};
    for (const p of allPersonas) m[p.id] = { accent: p.accent, monogram: p.monogram };
    return m;
  }, [allPersonas]);

  // 進行役（司会・議長）= 各カテゴリの先頭ペルソナ。常に自動で編成へ含める（ユーザーは選ばない）。
  const autoRoles = useMemo(
    () =>
      STRUCTURAL_CATS.map((c) => personas.find((p) => p.category === c)).filter(
        (p): p is Persona => Boolean(p)
      ),
    [personas]
  );
  const autoRoleIds = useMemo(() => autoRoles.map((p) => p.id), [autoRoles]);
  // 編成 CRUD が書込可能か（readonly な共有インスタンスでは「管理」UI を出さない）。
  const canManage = !(health?.readonly ?? false);

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
    // プリセットの persona_ids からパネリストだけ採用（司会・議長・書記は自動付与/除外）。
    const byId = new Map(personas.map((p) => [p.id, p]));
    const panelistIds = preset.persona_ids.filter((id) => {
      const p = byId.get(id);
      return p && !STRUCTURAL_CATS.includes(p.category) && p.category !== "scribe";
    });
    setSelected(new Set(panelistIds));
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

  // トップ（idle）へ戻る＝新規討論。準備パネル（資料添付・主訴確認・編成）は idle でのみ出るため、
  // 討論後に添付付きの新規開始ができるようにする入口。ヘッダの「AI COUNCIL」から呼ぶ。
  // running 中は生成を止めてコストを抑える。paused は止めない（サーバに残し履歴から再開可能）。
  function resetToIdle() {
    if (running && sessionId) cancelSession(sessionId);
    abortRef.current?.abort();
    streamAliveRef.current = false;
    setStatus("idle");
    setTurns([]);
    setActiveTopic(null);
    setSessionId(null);
    setStreamingTurnId(null);
    setError(null);
    setTopicInput("");
    setMaterials("");
    setIntakeQuestions([]);
    setIntakeAnswers({});
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

  // SSE イベント → 画面状態の反映。start（新規）と resume（再接続）で共有する。
  function handleEvent(e: StreamEvent) {
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
          const idx = base.findIndex((t) => t.phase === "human" && t.turn_id < 0);
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
            query: e.query, // 調査役: 検索クエリ（「『〇〇』を調べています…」表示用）
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
  }

  // 既存セッションへ再接続して再生（ページ再読込・ロード失敗からの復帰）。サーバが持っていれば
  // ライブ継続、無ければ（再起動/TTL）保存済み transcript を凍結表示する。履歴クリックからも使う。
  async function resumeOrLoad(entry: HistoryEntry) {
    setActiveTopic(entry.topic);
    setSessionId(entry.id);
    setError(null);
    setHistoryOpen(false);
    // 完了済みは再生せず保存済み transcript をそのまま表示（再アニメ不要）。
    if (entry.status === "done") {
      setTurns(entry.turns);
      setStatus("done");
      setStreamingTurnId(null);
      return;
    }
    // running/paused/error: まずサーバに繋ぎ直して**真の状態**を取りに行く。クライアントが
    // 接続断で error と記録していても、サーバにまだ running/paused で残っていれば再開でき、
    // 投げかけ（追い質問）も再び使える。replay（cursor=0）で作り直すので一旦クリア。
    setTurns([]);
    setStatus("running");
    setStreamingTurnId(null);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    streamAliveRef.current = true;
    try {
      const ok = await resumeSession({
        sessionId: entry.id,
        signal: ctrl.signal,
        onEvent: handleEvent,
      });
      if (!ok && !ctrl.signal.aborted) {
        // サーバが持っていない（再起動/TTL）→ 保存済み transcript を凍結表示。
        setTurns(entry.turns);
        setStatus(entry.status === "error" ? "error" : "done");
        setError(
          entry.turns.length
            ? "このセッションはサーバ側で失われたため再開できません。ここまでの記録を表示しています。"
            : "このセッションはサーバから失われ、記録もありませんでした。"
        );
      }
    } catch (err) {
      if (!ctrl.signal.aborted) {
        setTurns(entry.turns);
        setStatus("done");
        setError(String(err));
      }
    } finally {
      streamAliveRef.current = false;
    }
  }

  // セッション起動の共通核（新規 start と「続ける」continue で共有）。topic/personas/materials/
  // customPersonas を明示で受け、その他（rounds/redTeam/verbosity/research/LLM）は現在の設定を使う。
  async function launchSession(opts: {
    topic: string;
    personaIds: string[];
    customPersonas: CustomPersona[];
    materials: string;
    intake?: IntakeQA[];
  }) {
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setActiveTopic(opts.topic);
    setTurns([]);
    setError(null);
    setStatus("running");
    setStreamingTurnId(null);
    setSessionId(null);
    setTopicInput("");
    setMaterials("");
    setIntakeQuestions([]);
    setIntakeAnswers({});
    setHistoryOpen(false);
    streamAliveRef.current = true;
    try {
      await startSession({
        topic: opts.topic,
        personaIds: opts.personaIds,
        roundsPerPhase, // GAP6
        redTeam, // GAP6
        redTeamId, // GAP6
        mock: !willUseRealLlm, // GAP5: NOT(useLlm AND key)
        materials: opts.materials,
        intake: opts.intake ?? [],
        research,
        verbosity,
        customPersonas: opts.customPersonas,
        interactive: true,
        signal: ctrl.signal,
        onEvent: handleEvent,
      });
    } catch (err) {
      // 接続前（POST 失敗等）の例外。生の "TypeError: Load failed" でなく分かりやすい案内に
      // （セッション確立後の切断は再接続ループ側で復帰）。
      if (!ctrl.signal.aborted) {
        setError("接続に失敗しました。通信環境を確認して、もう一度お試しください。");
        setStatus("error");
      }
    } finally {
      streamAliveRef.current = false;
    }
  }

  async function start() {
    const topic = topicInput.trim();
    if (!topic || selected.size === 0 || active) return;
    // 進行役（司会・議長）を先頭に自動付与し、続けて選択パネリスト（カスタム含む）。重複は除く。
    const panelistIds = allPersonas.filter((p) => selected.has(p.id)).map((p) => p.id);
    const ordered = Array.from(new Set([...autoRoleIds, ...panelistIds]));
    const selectedCustom = customPersonas.filter((cp) => selected.has(cp.id));
    const trimmedMaterials = materials.trim();
    const intake: IntakeQA[] = intakeQuestions
      .map((question, i) => ({ question, answer: (intakeAnswers[i] ?? "").trim() }))
      .filter((qa) => qa.answer !== "");
    await launchSession({
      topic,
      personaIds: ordered,
      customPersonas: selectedCustom,
      materials: trimmedMaterials,
      intake,
    });
  }

  // 前回討論の文脈テキスト（資料）を組む。scope="light"=議事録＋直近、"full"=全文（budget 内）。
  // materials の上限（サーバ 20000 字）に収めるため、全文は新しい発言から詰めて古いものから落とす。
  // focusText があれば「特に深めたい点」として末尾指示に織り込む（コンポーザーから続ける時）。
  function buildContinuationContext(
    entry: HistoryEntry,
    scope: "light" | "full",
    focusText = ""
  ): string {
    const fmt = (t: Turn) => `【${t.speaker_name}】\n${t.content}`;
    const synthesis = entry.turns.find((t) => t.phase === "synthesis");
    // 発言（議事録・要約・調査メモは除く。人間の追い質問は含める）。
    const body = entry.turns.filter(
      (t) => t.phase !== "synthesis" && t.phase !== "summary" && t.speaker_id !== "researcher"
    );
    const head = `【前回の討論（議題: ${entry.topic}）${scope === "full" ? "全文" : "の要点"}】`;
    const focus = focusText.trim()
      ? `特に次の点を深めてください: ${focusText.trim()}。`
      : "";
    const tail =
      "\n\n【ここから続き】上記の前回討論を踏まえ、続きとして議論を深めてください。" +
      focus +
      "同じ結論の蒸し返しは避け、未解決の論点や新しい角度を進めること。";
    const budget = 19000 - head.length - tail.length - 200;
    const parts: string[] = [];
    if (scope === "full") {
      const chosen: string[] = [];
      let used = 0;
      for (let i = body.length - 1; i >= 0; i--) {
        const s = fmt(body[i]);
        if (used + s.length > budget) {
          chosen.unshift("…（これより前の発言は長いため省略）");
          break;
        }
        chosen.unshift(s);
        used += s.length + 2;
      }
      parts.push(...chosen);
    } else {
      if (synthesis) parts.push(`◆議事録\n${synthesis.content}`);
      parts.push("◆直近の発言", ...body.slice(-5).map(fmt));
    }
    let text = `${head}\n\n${parts.join("\n\n")}${tail}`;
    if (text.length > 19500) text = text.slice(0, 19500) + "\n…（長いため省略）";
    return text;
  }

  // 終了/凍結した討論を「続ける（深掘る）」。前回のパネリストを transcript から復元し、前回討論を
  // 文脈（資料）として読み込ませた新セッションを立てる＝同じ顔ぶれで続きから議論する。
  async function continueDiscussion(
    entry: HistoryEntry,
    scope: "light" | "full",
    focusText = ""
  ) {
    if (active) return;
    const priorIds = Array.from(new Set(entry.turns.map((t) => t.speaker_id))).filter((id) => {
      const p = allPersonas.find((x) => x.id === id);
      return p && !STRUCTURAL_CATS.includes(p.category) && p.category !== "scribe";
    });
    if (priorIds.length === 0) {
      setError("続けられる発言者が記録から復元できませんでした。");
      return;
    }
    const ordered = Array.from(new Set([...autoRoleIds, ...priorIds]));
    const usedCustom = customPersonas.filter((cp) => priorIds.includes(cp.id));
    await launchSession({
      topic: entry.topic,
      personaIds: ordered,
      customPersonas: usedCustom,
      materials: buildContinuationContext(entry, scope, focusText),
    });
  }

  // 終了/凍結した討論を見ている時にコンポーザーから送る＝この討論を続ける（前回を引き継ぐ）。
  // 入力テキストは「特に深めたい点」になる。新規ブランク討論はロゴ（resetToIdle）からのみ。
  function continueFromComposer() {
    if (!activeTopic || turns.length === 0) return;
    continueDiscussion(
      { id: sessionId ?? "", topic: activeTopic, turns, status, startedAt: 0, updatedAt: 0 },
      continueScope,
      topicInput.trim()
    );
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
      } else if (finishedWithTranscript) {
        // 終了済み討論への入力＝続ける（履歴をクリアして新規にしない）。
        if (topicInput.trim()) continueFromComposer();
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

  // 完了/エラーで transcript を表示中か。この時コンポーザー送信は「新規ブランク」でなく
  // 「この討論を続ける（前回を引き継ぐ）」に流す＝履歴が消えない。新規はロゴ（resetToIdle）から。
  const finishedWithTranscript =
    (status === "done" || status === "error") && turns.length > 0;
  const finishedNote = finishedWithTranscript
    ? "この討論は終了しています。下に続けたい点を書いて送信すると、前回を引き継いで深掘りします（新規討論はロゴ『AI COUNCIL』から）。"
    : null;

  return (
    <div className="flex h-screen flex-col">
      {/* ヘッダー */}
      <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
        <button
          onClick={resetToIdle}
          title="新規討論（トップへ戻る）"
          className="font-display text-base tracking-widest transition-opacity hover:opacity-70"
        >
          AI COUNCIL
        </button>
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              setHistory(getHistory());
              setHistoryOpen(true);
            }}
            className="flex items-center gap-1 text-[11px] text-[var(--color-ink-muted)] hover:text-[var(--color-accent)]"
          >
            <History size={14} /> 履歴
          </button>
          <OnAir status={status} />
        </div>
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

          <VerbositySelect
            value={verbosity}
            onChange={updateVerbosity}
            disabled={active}
          />

          <PersonaPicker
            personas={allPersonas}
            selected={selected}
            onToggle={toggle}
            disabled={active}
            autoRoles={autoRoles}
            onManage={canManage ? () => setManageOpen(true) : undefined}
            onAddOwn={() => setMyPersonasOpen(true)}
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
            {finishedNote && (
              <div className="mb-2 flex flex-col gap-1.5">
                <p className="text-[11px] text-[var(--color-ink-muted)]">{finishedNote}</p>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() =>
                      activeTopic &&
                      continueDiscussion(
                        {
                          id: sessionId ?? "",
                          topic: activeTopic,
                          turns,
                          status,
                          startedAt: 0,
                          updatedAt: 0,
                        },
                        continueScope
                      )
                    }
                    className="flex items-center gap-1.5 rounded-md border border-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent-weak)]"
                  >
                    <Play size={13} /> そのまま続ける
                  </button>
                  <span className="text-[10px] text-[var(--color-ink-muted)]">文脈:</span>
                  <div className="flex rounded-md border border-[var(--color-line)] p-0.5">
                    <button
                      onClick={() => setContinueScope("light")}
                      className={`rounded px-2 py-0.5 text-[10px] transition-colors ${
                        continueScope === "light"
                          ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                          : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
                      }`}
                    >
                      議事録＋直近（推奨）
                    </button>
                    <button
                      onClick={() => setContinueScope("full")}
                      className={`rounded px-2 py-0.5 text-[10px] transition-colors ${
                        continueScope === "full"
                          ? "bg-[var(--color-accent-weak)] text-[var(--color-accent)]"
                          : "text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
                      }`}
                    >
                      全文
                    </button>
                  </div>
                </div>
              </div>
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
                    : finishedWithTranscript
                      ? "この討論に続けて深めたい点を入力（送信で続ける）"
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
              ) : finishedWithTranscript ? (
                <button
                  onClick={continueFromComposer}
                  disabled={!topicInput.trim()}
                  className="flex items-center gap-1.5 rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
                >
                  <Play size={14} /> 続けて質問
                </button>
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

      {/* ペルソナ管理ドロワー（サーバ CRUD・readonly では非表示の入口） */}
      <PersonaManagerDrawer
        open={manageOpen}
        personas={personas}
        onClose={() => setManageOpen(false)}
        onChanged={loadPersonas}
      />

      {/* 自分のペルソナ（クライアント定義・localStorage・サーバ非保存） */}
      <MyPersonasDrawer
        open={myPersonasOpen}
        onClose={() => setMyPersonasOpen(false)}
        items={customPersonas}
        onSave={updateCustomPersonas}
        disabled={active}
      />

      {/* 討論履歴（クライアント保存・見返し/再開） */}
      <HistoryDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        entries={history}
        currentId={sessionId}
        onOpen={resumeOrLoad}
        onDelete={(id) => {
          deleteHistoryEntry(id);
          setHistory(getHistory());
        }}
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
