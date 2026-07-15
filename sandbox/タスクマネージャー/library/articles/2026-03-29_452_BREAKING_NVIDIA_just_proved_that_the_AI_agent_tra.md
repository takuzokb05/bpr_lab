# BREAKING: NVIDIA just proved that the AI agent training bottleneck everyone blam...

- URL: https://x.com/rryssf_/status/2037122412236648835
- ソース: x
- 言語: en
- テーマ: ai-news
- 取得日: 2026-03-29
- いいね: 378 / RT: 75 / リプライ: 14
- 投稿者: @rryssf_ / フォロワー 38,740

## 投稿内容

BREAKING: NVIDIA just proved that the AI agent training bottleneck everyone blamed on model capability was actually an infrastructure design error.

Every framework SkyRL, VeRL-Tool, Agent Lightning, rLLM, GEM embeds rollout inside the training loop. I/O-intensive execution fighting GPU-intensive optimization. Nobody separated them.

> Treat rollout as a service. Qwen 8B nearly doubles on SWE-Bench. The compute was always there. It was just fighting itself.

> Training an AI agent with reinforcement learning requires two fundamentally different workloads running simultaneously. Rollout is I/O-intensive spinning up sandboxed environments, executing tool calls, waiting on shell commands, scoring outcomes. Training is GPU-intensive forward passes, backward passes, gradient synchronization. Every existing framework runs both inside the same process. The result is constant resource contention: rollout workers block on disk I/O while GPU compute sits idle, and gradient updates stall while environments finish executing.

> NVIDIA audited every major agentic RL framework and found the same architectural decision in all of them. SkyRL keeps rollout control inside the training driver. Agent Lightning embeds rollout workers as child processes of the trainer if training stops, rollout stops. VeRL-Tool, rLLM, and GEM all keep environment management and trajectory collection inside the training stack. Not because it's the right design. Because it was easier to build that way and nobody had fixed it yet.

> ProRL Agent separates them completely. The rollout system runs as a standalone HTTP service. The trainer sends a task instance. The rollout server handles environment initialization, multi-turn agent execution, tool calls, reward computation, and returns a completed trajectory. The trainer never touches the execution environment. The two systems communicate through one interface and run on separate machines optimized for their respective workloads.

> The results are not subtle. Qwen 8B: 9.6% on SWE-Bench Verified under standard training. ProRL Agent: 18.0%. That's close to 2x on the benchmark the entire software engineering AI field uses to measure progress. Qwen 14B goes from 15.4% to 23.6%. Qwen 4B goes from 14.8% to 21.2%. Same models. Same data. Different infrastructure.

→ Qwen 8B on SWE-Bench Verified: 9.6% baseline → 18.0% with ProRL Agent
→ Qwen 14B: 15.4% → 23.6%
→ Qwen 4B: 14.8% → 21.2%
→ Throughput scales near-linearly with compute nodes added
→ Efficient bash optimization alone: shell command latency drops from 0.78s to 0.42s per action
→ GPU utilization with full system: 78% vs 42% without load balancing
→ Every existing framework audited: zero had decoupled rollout from training

The engineering insight that gets buried in the results: the problem compounds at every tool call. A typical software engineering rollout spans dozens of sequential environment interactions. Each one blocks. Each one accumulates latency. At scale with hundreds of parallel rollouts, tool execution becomes the dominant bottleneck not model inference, not gradient computation. The entire field was measuring model capability while the infrastructure was quietly eating half the compute budget.

## 要約

（要約は次回 /curate 時に追記）
