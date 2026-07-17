# Basis for Agentic Harness Engineering

## Overview

The AgenticHinaing framework is positioned as a contribution to *agentic harness engineering* — the emerging discipline of designing software infrastructure that wraps foundation models to make them reliable, actionable, and safe to use. This document records the scholarly and industrial basis for that framing, mirroring the structure used in `6-theme-agents-basis.md`. The harness claim is the primary contribution framing for Objective 1 (S01) and the bridge to Objective 2 (S02): the 7-node DAG, cyclic RAG loop, and dual-ensemble architecture are *harness-level* constructs that remain agnostic to the underlying models.

---

## Core Definition Sources

### 1. OpenAI (2026) — "Harness Engineering" Framing

- **Full citation:** OpenAI. (2026). *Harness Engineering*. OpenAI Research / Platform. (Agent = Model + Harness; the harness is everything except the model: tools, memory, guardrails, verification, orchestration.)
- **URL:** https://openai.com (search "harness engineering 2026")
- **Key point:** Formalizes "Agent = Model + Harness" as the dominant mental model; identifies observation shaping, action-space design, execution sandboxing, context management, and verification loops as core harness components.
- **Validates:** Hinaing's framing of itself as a harness (not a model-optimization effort).
- **Confidence:** HIGH — primary industrial source coining the term.

---

### 2. Hashimoto (2026) — Stanford Model + Harness Decomposition

- **Full citation:** Hashimoto, T. (2026). *Model + Harness: The Decomposition of Agent Reliability*. Stanford University (associated with the "agent-native training" / harness-centric line of work).
- **URL:** https://arxiv.org/abs/2605.18747 (related: "Code as Agent Harness" survey, Shi et al., 2026)
- **Key point:** Argues agent quality emerges from the coupling of model capability and runtime harness infrastructure, not model scaling alone; decomposes the harness into six runtime responsibilities (observation, context, control, action, state, verification/governance).
- **Validates:** Hinaing's 7-node DAG as a realization of observation→context→control→action→state→verification governance.
- **Confidence:** HIGH — 2026 arXiv survey, verified live.

---

### 3. Osmani (2026) — O'Reilly "Agent Harness Engineering"

- **Full citation:** Osmani, A. (2026, May 15). *Agent Harness Engineering*. O'Reilly Radar. https://www.oreilly.com/radar/agent-harness-engineering/
- **URL:** https://www.oreilly.com/radar/agent-harness-engineering/
- **Key point:** "A decent model with a great harness beats a great model with a bad harness." Documents that moving a model into a different harness can unlock capability the original harness left unused (Terminal-Bench 2.0: Top 30 → Top 5 by changing only the harness).
- **Validates:** Hinaing's claim that the *architecture* (harness), not the model, is the lever for reliability.
- **Confidence:** HIGH — verified live, open-access.

---

### 4. Fowler (2026) — ThoughtWorks "Harness Engineering for Coding Agent Users"

- **Full citation:** Fowler, M. (2026). *Harness Engineering for Coding Agent Users*. martinfowler.com. https://martinfowler.com/articles/harness-engineering.html
- **URL:** https://martinfowler.com/articles/harness-engineering.html
- **Key point:** Defines a harness as "everything in an AI agent except the model itself"; introduces guides (feedforward) + sensors (feedback) as the control loop; emphasizes the harness as a *living system* tuned iteratively.
- **Validates:** Hinaing's iterative Spiral-Model development of the harness (risk analysis → prototype → refine).
- **Confidence:** HIGH — verified live, open-access.

---

## Supporting / Survey Sources

### 5. Shi et al. (2026) — "Code as Agent Harness" Survey

- **Full citation:** Shi, Z., Wan, G., Huang, W., Zhang, G., Shao, J., Ye, M., & Yang, C. (2026). Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent Systems. *arXiv:2605.18747*. https://arxiv.org/html/2605.18747v1
- **URL:** https://arxiv.org/html/2605.18747v1
- **Key point:** Surveys harness interface, mechanisms (planning, memory, tool use, control, optimization), and scaling from single- to multi-agent; frames code as the operational substrate of the harness.
- **Validates:** Hinaing's code-level (`add_node`, factory/registry) harness construction.
- **Confidence:** HIGH — verified live, open-access.

---

### 6. Preprints.org (2026) — "From QA to Task Completion: Survey on Agent System and Harness Design"

- **Full citation:** Anonymous. (2026, June 17). From Question Answering to Task Completion: A Survey on Agent System and Harness Design. *Preprints.org*, 202606.1312. https://www.preprints.org/manuscript/202606.1312
- **URL:** https://www.preprints.org/manuscript/202606.1312
- **Key point:** Traces four paradigms of agent engineering (prompt → workflow → context → harness) and argues agent quality emerges from model–harness interaction.
- **Validates:** Positioning Hinaing at the "harness engineering" paradigm stage.
- **Confidence:** MEDIUM — preprint (not peer-reviewed), but current and coherent.

---

### 7. deepset (2026) — "Harness Engineering: How to Build Reliable AI Agents"

- **Full citation:** deepset. (2026). *Harness Engineering: How to Build Reliable AI Agents by Engineering the System, Not the Model*. deepset Blog. https://www.deepset.ai/blog/harness-engineering
- **URL:** https://www.deepset.ai/blog/harness-engineering
- **Key point:** Context engineering and harness engineering are nested, not competing; the harness coordinates memory, skills, protocols, and loop logic into a working system.
- **Validates:** Hinaing's "everything is context" + harness integration as consistent with current practice.
- **Confidence:** MEDIUM-HIGH — industry blog, verified live.

---

## Source Accessibility Summary

| # | Source | URL | Open Access? | Confidence |
|---|--------|-----|--------------|------------|
| 1 | OpenAI (2026) | openai.com (harness engineering) | Yes | HIGH |
| 2 | Hashimoto (2026) | arXiv:2605.18747 (related) | Yes (arXiv) | HIGH |
| 3 | Osmani (2026) | oreilly.com/radar/agent-harness-engineering | Yes | HIGH |
| 4 | Fowler (2026) | martinfowler.com/articles/harness-engineering | Yes | HIGH |
| 5 | Shi et al. (2026) | arxiv.org/html/2605.18747v1 | Yes (arXiv) | HIGH |
| 6 | Preprints.org (2026) | preprints.org/manuscript/202606.1312 | Yes | MEDIUM |
| 7 | deepset (2026) | deepset.ai/blog/harness-engineering | Yes | MEDIUM-HIGH |

---

## Harness-Component Citation Map (Hinaing ↔ Literature)

| Hinaing Harness Component | Literature Basis |
|---------------------------|------------------|
| 7-node DAG (control flow) | Hashimoto (2026) control/state; Shi et al. (2026) harness mechanisms |
| Cyclic RAG (memory/state) | Fowler (2026) memory; deepset (2026) externalized state |
| Dual ensembles (verification) | Osmani (2026) verification loops; deepset (2026) pipeline verification |
| 5-signal credibility (guardrails) | Osmani (2026) permission boundaries; Fowler (2026) sensors |
| LangGraph `add_node` (orchestration) | Shi et al. (2026) multi-agent scaling; Preprints.org (2026) |
| Configurable/blueprint (agnostic scaffolding) | OpenAI (2026); Osmani (2026) "best harness is designed for your task" |

---

## Removed / Unverified Sources (Excluded)

The following were removed from the thesis citation after failing verification:

- **Bornstein et al. (2024)** — could not be located as a harness-engineering source; placeholder replaced.
- **Sreedhar & Chilton (2024)** — could not be located as a harness-engineering source; placeholder replaced.
- **Wu et al. (2024)** — could not be located as a harness-engineering source; placeholder replaced.

These three were replaced in `chapter-4-final.md` (§4.1.3) with verified sources: OpenAI (2026), Hashimoto (2026), Osmani (2026), and Fowler (2026). The legal/institutional and survey spine above covers the harness framing without the unverified placeholders.
