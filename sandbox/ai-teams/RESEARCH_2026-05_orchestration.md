# 調査レポート: マルチエージェント討論オーケストレーションの実装パターン

調査日: 2026-05-31 / 対象期間: 主に 2025-12 〜 2026-05
目的: AI Teams v3 のオーケストレーター設計を、実在するフレームワーク・プロダクトの実装に基づいて現実的にする。
方法: 5アングルで並列Web調査 → 出典つきで照合。各主張にURLを付す。

---

## 0. エグゼクティブ・サマリ（結論先出し）

1. **私が挫折した2バグは、業界の主流フレームワークが「設計で」解いている。**
   - **人格混線**（あるエージェントが他人のセリフを書き出す/なりきりが崩れる）→ **コンテキスト分離**で解決。
     主流の解は「各ペルソナの発言生成では、**自分の過去発言だけを `assistant`、他者の発言は話者名つきの `user` 側**として渡す」。AutoGen がまさにこれ。Claude Agent SDK は更に強く「サブエージェントごとに**独立コンテキスト窓**、親に戻るのは最終メッセージだけ」。
   - **沈黙エージェント**（指名されず一度も喋らない）→ **発言順をLLMでなくコードが決める（ラウンドロビン）**で解決。AutoGen `RoundRobinGroupChat` は modulo で全員に必ず順番が回る。LangGraph/CrewAI は router/manager 主導で**保証なし**＝自分で組む必要あり。
   → v3 計画（4.5節）の方針は、実装パターンとして裏付けられた。

2. **ただし重大な但し書き: 「単一モデルで全ペルソナ」は別の失敗＝“均質化”を招く。**
   2025-2026 の研究が繰り返し報告: 同一モデルに役割プロンプトだけ変えて複数ペルソナを作ると、出力が**ほぼ同一に収束**（committee で平均コサイン類似度 ~0.888、実効ランク 2.17/3.0）[arXiv:2604.03809]。さらに討論を重ねると**同調（sycophancy）で精度が下がる**ことすらある [arXiv:2509.05396]。
   → **混線（impersonation）と均質化（collapse）は別問題**。前者はコンテキスト分離で解くが、後者は分離では解けない。前回 `REBUILD_PLAN.md` で「単一プロバイダーでOK」と書いたのは**混線対策としては正しいが、多様性（discッションの質）の観点では不十分**。Q2 の結論を下記5節で補正する。

3. **「討論させれば賢くなる」は神話に近い。** Du et al. の元論文でも +5〜7%程度 [arXiv:2305.14325]、以降の研究はむしろ劣化リスクを警告。コストは 3〜15倍。**ラウンドを増やすより多様性を強制し、最後に統合役（chairman/judge）で締める**のが定石。

---

## 1. フレームワーク横断比較表

| 観点 | AutoGen / MS Agent Framework | LangGraph | OpenAI Agents SDK | Claude Agent SDK | CrewAI |
|---|---|---|---|---|---|
| **発言者選択** | `RoundRobinGroupChat`（modulo順）/ `SelectorGroupChat`（LLMが選ぶ）/ `Swarm`（handoff）/ `selector_func`（コード上書き） | supervisor(LLM router) or swarm(直接handoff)。**round-robinは自作** | handoffs（`transfer_to_X`ツール）or agents-as-tools（manager） | 親=オーケストレーター、`Agent`ツールでsubagent起動。1段のみ（再帰不可） | sequential（記述順）/ hierarchical（manager LLMが委譲） |
| **沈黙の防止** | round-robinは**全員保証**。selectorは`allow_repeated_speaker=False`(0.4既定)で連続防止＋失敗時フォールバック | **保証なし**（router任せ）。recursion_limit=25 | 保証なし（routing次第） | 保証なし（親が明示的にspawn） | 保証なし（manager任せ・委譲は不安定報告あり） |
| **コンテキスト分離（混線対策）** | 各agentは自分の発言=`AssistantMessage`、他者=`source`付き`UserMessage`。選択用historyは`"source: content"`行 | 既定は**共有transcript**（混線リスク）。Deep Agentsは**独立窓** | 既定は**全履歴共有**（混線リスク）。`input_filter`/nested-handoffで制限 | **既定で独立コンテキスト窓**。親履歴は渡らず、戻るのは最終メッセージのみ（最強の分離） | role/goal/backstoryで別プロンプト。出力は`context=[...]`やメモリで共有 |
| **会話状態/永続化** | termination条件群＋`max_turns`。MAFはcheckpoint/pause/resume | checkpointer（thread_id）＋`BaseStore`（長期）。swarmは`active_agent`保持 | Sessions（`SQLiteSession`/ファイル/Redis） | サブエージェントtranscriptを独立保存・resume可 | Flowsの共有state（dict/Pydantic）＋crew memory |
| **決定的制御** | selector_func/manual | Command(goto)で明示edge | code-driven orchestration | Workflowツール（大規模） | **Flows**（`@start/@listen/@router`） |
| **2026の現況** | MAF 1.0 GA（2026-04-03、AutoGen+SK統合） | langgraph-swarm v0.1.0(2025-12)、Deep Agents v0.5(2026-04, 非同期subagent) | Swarmは廃止→Agents SDKへ。nested-handoff betaほか | "Claude Code SDK"→"Claude Agent SDK"改名(2025-09-29)、`Task`→`Agent`(v2.1.63) | OSS 1.0 GA |

> フェッチ制限の注記: anthropic.com / openai.github.io / docs.crewai.com / arXiv は自動取得が403になる場面が多く、その分は公式GitHubソース・公式リファレンス・複数二次情報で裏取りした。AutoGenの主要主張は `main` ブランチのソース直読で確認済み。

---

## 2. 私の「バグ①: 人格混線」への各社の解

- **AutoGen（最も参考になる）**: `AssistantAgent` は、自分の過去ターンを `AssistantMessage`、**他エージェントのターンを発信元 `source` 付きの `UserMessage`** としてモデルに与える。つまり「他人は user 側からの入力」として見せるので、モデルが他人の人格を自分の声として継続しにくい。発言者選択LLMにも履歴は `"source: content"` 行で渡す。
  - 出典: https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.messages.html , chat_agent_container/_selector_group_chat ソース
- **Claude Agent SDK（最強の分離）**: サブエージェントは**自分専用のコンテキスト窓**を持ち、親の会話履歴・システムプロンプトを継承しない。戻るのは最終メッセージのみ。構造的に混線が起きない。
  - 出典: https://code.claude.com/docs/en/agent-sdk/subagents , https://www.anthropic.com/engineering/multi-agent-research-system
- **LangGraph / OpenAI**: 既定は**全履歴共有＝混線リスク高**。LangGraphは Deep Agents（独立窓）、OpenAIは `input_filter`/agents-as-tools で対処する＝**分離はオプトイン**。
- **私の旧実装の誤り**: 全員の発言を `role: assistant` で1配列に詰め、stopシーケンスで境界を切ろうとした（OpenAI 4個制限で破綻）。**正しくは「1ペルソナ=1コール、他者は話者名つきで user 側」**。AutoGen と同じ形にすればよい。

→ **v3 採用案**: AutoGen 流の「自分=assistant / 他者=name付きuser」を基本にしつつ、重要ペルソナや並列探索には Claude Agent SDK 流の独立コンテキストも使える二段構え。

---

## 3. 私の「バグ②: 沈黙エージェント」への各社の解

- **AutoGen `RoundRobinGroupChat`**: `self._next_speaker_index = (current+1) % len(participants)` で**全員に必ず順番が回る＝沈黙が構造的に不可能**。
  - 出典: https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_round_robin_group_chat.py
- **AutoGen `SelectorGroupChat`**: LLM選択だが `allow_repeated_speaker=False`(0.4既定)で**直前話者を候補から除外**、`candidate_func` で候補集合を毎ターン絞れる、`max_selector_attempts`(既定3)失敗で前話者/先頭にフォールバック。ただし**「全員必ず1回」までは保証しない**ので、それは `selector_func` を自作する。
- **LangGraph / CrewAI**: router/manager 任せで**保証なし**。LangGraph公式も「決定的round-robinは自分で edge を組め」。CrewAI hierarchical の委譲は**実運用で不安定との報告**（issue #4783, TDS批判記事）。
- **私の旧実装の誤り**: 指名駆動（前話者の `【指名】` 次第）＝指名漏れで永久に沈黙。救済ロジックは後付けで不安定だった。

→ **v3 採用案**: **コード側のラウンドロビンを基盤**にし、各フェーズで全員1回の強制ロールコールを保証。司会の指名は「順番の提案」までで、最終的な発言権配分はコードが担保（AutoGen の selector_func 相当を自前で）。

---

## 4. 研究が示す「第3の罠」: 均質化・同調・討論の劣化（要注意）

前回の計画には無かった観点。査読系・preprintで繰り返し確認された失敗モード:

- **Representational collapse（均質化）**: 同一モデル＋役割プロンプトの committee は出力が収束（平均コサイン ~0.888、実効ランク 2.17/3.0）。多様な証拠を出さず冗長になる。出典: https://arxiv.org/pdf/2604.03809
- **同調・追従（sycophancy）で精度低下**: 仲間の答えに引きずられ、正→誤に変える。強いモデルが多数でも討論で精度が**下がる**ことがある。出典: https://arxiv.org/abs/2509.05396
- **過信で更新しない**: 「2体が討論すると両者とも勝つと思い込む」＝意見を更新せず真実探索を阻害。出典: https://arxiv.org/abs/2505.19184
- **元祖の効果は限定的**: Du et al. の multiagent debate でも +5〜7%。出典: https://arxiv.org/abs/2305.14325
- **コスト**: マルチエージェントはチャットの ~15倍トークン、トークン量が性能分散の ~80% を説明（Anthropic）。「答えが高価値・サブタスク独立・大規模」のときだけ割に合う。出典: https://www.anthropic.com/engineering/multi-agent-research-system

**確立された対策（＝v3で採るべき多様性メカニズム）:**
1. **異種性**: ペルソナごとに**異なるモデル**を割り当てる（最も効く）。OSSの "Council of High Intelligence" は人格ごとに別プロバイダーへルーティング＋「polarity pairs（対立ペア）」「dissent quota（反対意見ノルマ）」「novelty gate」で同質化を防ぐ最良設計。出典: https://github.com/0xNyk/council-of-high-intelligence
2. **匿名化＋反同調プロンプト**: 誰の発言か伏せて評価、「安易に同意するな」を明示。
3. **疎な通信トポロジ**: 全対全でなく一部だけ共有。出典: https://aclanthology.org/2024.findings-emnlp.427.pdf
4. **統合役（chairman/judge）＋停止条件**: ラウンドを無限に増やさず、収束検知で止め、最後に1つに統合。

---

## 5. Q2の補正: 「複数API使う意味あるか」への更新版回答

前回「混線対策としては単一プロバイダーで十分」と述べたが、調査を踏まえ**2つの問題を分けて**結論を更新する:

| 問題 | 単一モデルで解けるか | 結論 |
|---|---|---|
| 人格混線（impersonation） | ✅ 解ける（コンテキスト分離が本質。モデル数は無関係） | 単一でOK |
| 均質化（collapse / echo chamber） | ❌ 解けない（同一モデルは収束しやすい） | **多様性メカニズムが必要** |

**更新版の推奨（ハイブリッド）:**
- **エンジン基盤は単一プロバイダー（Claude）デフォルトのまま**で良い（安定・実装容易・混線に強い）。
- ただし**「思考の多様性が要るペルソナ」には別モデルを割り当てられる**ように `persona.model` の上書きを実用機能として残す（前回は"任意"扱いだったが、**collapse対策として格上げ**）。例: 論理担当=Claude、逆張り=GPT、直感=Gemini。
- モデルを分けない場合でも、**反同調プロンプト・対立ペア・温度差・反対意見ノルマ**をオーケストレーターに組み込んで均質化を抑える。
- つまり「複数APIは“安定のため”には不要だが、“多様性のため”には有効」。前回の私の単純化は半分正しく半分不足だった。

---

## 6. 類似プロダクト/OSS の俯瞰（v3のUX参考）

- **Karpathy "llm-council"**（2025末, OSS）: 独立回答 → 匿名ピアランキング → "Chairman" が統合、の3段。多くのフォロワーの雛形。 https://github.com/karpathy/llm-council
- **Perplexity "Model Council"**（2026-02, 最大規模の商用）: 3モデル並列 → 議長モデルが**合意/不一致を明示**して統合、モデル別タブ。 https://www.perplexity.ai/hub/blog/introducing-model-council
- **Opper "AI Roundtable"**（2026-03, Show HN前面）: 最大50モデルが回答→討論ラウンドで相互批判・投票変更→レビュアが要約。 https://opper.ai/ai-roundtable
- **Council of High Intelligence**（OSS）: 18名の著名人格（Socrates/Feynman/Munger/Sun Tzu…）を7段審議。**人格ごと別プロバイダー＋dissent quota** が最良の同質化対策。 https://github.com/0xNyk/council-of-high-intelligence
- **Moot: AI Decision Maker**（iOS/Android）: 5アーキタイプ（将軍/賢者/懐疑家/外交官/設計者）が対立→統合→投票。私の「アーキタイプ討論で意思決定支援」に最も近い消費者アプリ。 https://apps.apple.com/us/app/moot-ai-decision-maker/id6758050094
- **観察**: 「常駐モデレーター」より「**事後の議長/統合役**」を置く構成が主流。実在の有名人名を使う消費者アプリは少なく（法務・忠実度の都合）、多くは**アーキタイプ**を使う。著名人なりきりはOSS/DIYが中心。
- **忠実度の劣化**: ペルソナは長い対話（100ターン超）で**素のモデルに回帰**する測定結果あり。 https://www.emergentmind.com/topics/persona-fidelity → 長時間討論では定期的にペルソナを再注入する設計が要る。

---

## 7. v3 再構築への具体的示唆（アクション）

1. **オーケストレーターのデフォルトは「コード制御ラウンドロビン」**（AutoGen `RoundRobinGroupChat` 相当）。沈黙を構造的に潰す。司会指名は提案レイヤに格下げ。
2. **発言生成は「自分=assistant / 他者=name付きuser側」**で1ペルソナ1コール（AutoGen方式）。stopシーケンス依存をやめる。
3. **重要ペルソナ/並列探索は Claude Agent SDK 的な独立コンテキスト**も選べる二段構え。
4. **`persona.model` 上書きを“多様性機能”として正式採用**（collapse対策）。最低限、反同調プロンプト＋対立ペア＋温度差は必須。
5. **討論は短く＋統合役で締める**: 無限ラウンドにせず、収束検知で停止し、最後に chairman が「合意/不一致/ネクストアクション」を1枚に統合（Perplexity/Karpathy方式）。`generate_audit_report` の資産はこの統合役に流用可。
6. **長時間討論ではペルソナ定義を定期再注入**（fidelity decay対策）。
7. **「賢くするため」でなく「視点を網羅するため」に討論を使う**と割り切る（コスト15倍・精度向上は限定的という現実を前提に）。

---

## 付録: 主要出典一覧

**オーケストレーション基盤**
- AutoGen teams/selector/round-robin: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html , .../selector-group-chat.html , GitHub `_round_robin_group_chat.py` / `_selector_group_chat.py` / `_chat_agent_container.py`
- MS Agent Framework orchestrations: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/ , .../group-chat , .../magentic
- LangGraph multi-agent/persistence/swarm/deepagents: https://docs.langchain.com/oss/python/langchain/multi-agent , .../langgraph/persistence , https://github.com/langchain-ai/langgraph-swarm-py , https://docs.langchain.com/oss/python/deepagents/overview , https://www.langchain.com/blog/deep-agents-v0-5
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/multi_agent/ , .../handoffs/ , .../sessions/ , https://github.com/openai/swarm
- Claude Agent SDK / Anthropic: https://code.claude.com/docs/en/agent-sdk/subagents , https://www.anthropic.com/engineering/multi-agent-research-system , https://www.anthropic.com/research/building-effective-agents
- CrewAI: https://docs.crewai.com/en/concepts/processes , .../learn/hierarchical-process , .../concepts/flows , https://blog.crewai.com/crewai-oss-1-0-we-are-going-ga/

**討論の失敗モードと対策（研究）**
- Du et al. Multiagent Debate: https://arxiv.org/abs/2305.14325
- Talk Isn't Always Cheap（同調で劣化）: https://arxiv.org/abs/2509.05396
- When Two LLMs Debate（過信）: https://arxiv.org/abs/2505.19184
- Representational Collapse: https://arxiv.org/pdf/2604.03809
- Sparse Communication Topology: https://aclanthology.org/2024.findings-emnlp.427.pdf
- Persona fidelity decay: https://www.emergentmind.com/topics/persona-fidelity

**類似プロダクト**
- https://github.com/karpathy/llm-council , https://www.perplexity.ai/hub/blog/introducing-model-council , https://opper.ai/ai-roundtable , https://github.com/0xNyk/council-of-high-intelligence , https://apps.apple.com/us/app/moot-ai-decision-maker/id6758050094
