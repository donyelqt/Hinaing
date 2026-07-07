# Chapter 3
## METHODOLOGY

This chapter proceeds with the research design methodology, software development methodology, scope and delimitation, data gathering techniques, sources of data, treatment of data, and software development tools.

## Research Design Methodology

This research adopted the design science research (DSR) paradigm. 

### Three Cycle Model of Design Science Research

Design Science Research is a research paradigm focused on creating innovative artifacts to solve practical problems while maintaining scientific rigor. The method is characterized by its dual strength in balancing research relevance and rigor, with information systems researchers largely adopting and accepting it (Akoka et al., 2023). It applies to the study to generate innovative solutions to real-world problems(Tuunanen et al., 2024). The core of this approach is to design, build, and evaluate a novel multi-agent AI system for public opinion analysis and generate a contribution to the knowledge base for artificial intelligence in governance. 

To use this design, the project is structured across the (1) relevance cycle, (2) rigor cycle, and (3) design cycle. Each cycle bridges the study's specific objectives with its technical parameters and architectural frameworks. 

#### Relevance Cycle

The first cycle establishes real-world civic communication gaps as the core problem domain, thereby addressing Objective 2 regarding real-time ingestion and pipeline implementation. Specific parameters, including the geographical coordinates of Baguio City, local language structures, and platform-specific ingestion rates across public government-affiliated Facebook pages and community-driven forum streams, govern the operational boundaries of this cycle.

#### Rigor Cycle

The rigor cycle provides scientific grounding with existing theories, reference works, and methodologies from the broader knowledge base. This satisfies Objective 1, which requires a comprehensive literature review and component grounding before any code construction. The critical parameters guiding the rigor cycle include strict hardware and model size limitations, specifically matching a 184-million-parameter DeBERTa model, enforcing Natural Language Inference classification confidence scores greater than or equal to 0.75, and maintaining a dense embedding dimensionality of 1024.

#### Design Cycle

The central core is executed within the design cycle, where specialized system artifacts are iteratively built, evaluated, and refined. This cycle serves as the engineering bridge linking the artifact construction tasks of Objective 2 to the contextual faithfulness, thematic accountability, and cost-efficiency metrics required by Objective 3. 

## Software Development Methodology

The project adopted the spiral model for its software development lifecycle. This iterative methodology was selected as it is exceptionally well-suited for complex, experimental research projects where requirements evolve, and risks need to be managed. It is a modification of the combination of the waterfall model and prototyping model, with an emphasis on evaluation carried out systematically. 

### The Spiral Model

It is focused on carrying out risk analysis at each stage, as sentiment analysis requires continuous refinement of classification algorithms and feature extraction methods while also managing the complexity of the Agentic AI because of its non-deterministic and autonomous behavior that makes development and debugging harder. The Spiral Model's iterative nature allows developers to integrate additions by determining accuracy based on requirements(Sari et al., 2022). 

Each development cycle consisted of four key phases:

1. **Identifying Objectives**
   This phase determines system constraints, goals, and specific metrics. For Objective 1, it maps out the technical tool stack requirements. Objective 2 sets the requirements for localized data filters targeting Baguio City.

2. **Analyzing Risks Through Experimentation and Prototyping**
   The second phase deals directly with the non-deterministic and autonomous behavior of agentic workflows. Early prototypes evaluated hosting infrastructures, leading to a migration away from Railway's Free Tier to HuggingFace Spaces due to parallel processing Out-Of-Memory errors. It also tests token parsing limits on raw web data.

3. **Developing the System Components**
   This phase implements the core software components using LangChain and LangGraph to build directed acyclic graphs for stateful multi-agent workflows. System components like the CredibilityAgent and FaithfulnessAgent are built, componentized, and compiled into Dockerized microservices.

4. **Evaluating the Results to Plan the Next Iteration**
   This phase measures framework performance against project objectives. Telemetry markers assess cost metrics and context reuse counters. The outcome of this evaluation forms the baseline requirements for the subsequent spiral iteration, refining the heuristic 40/60 ensemble weights.

During the development phase of each spiral, principles from agent-oriented software engineering (AOSE) were applied to design the specialized agents that form the public opinion analysis system. 

In AOSE, each worker is an autonomous agent with distinct roles, responsibilities, and capabilities. This process provides a method for complex system development using agent-based modelling, which effectively supports public opinion sentiment analysis projects through goal-oriented and autonomous agent architectures. It addresses ontological gaps between systems and their environments using organizational concepts as development fundamentals (Wautelet et al., 2021). Agent-oriented software engineering agent-based paradigm enables autonomous agents to mine, classify, and report sentimental data while maintaining human oversight, bridging the gap between complex analytical requirements and stakeholder expectations on sentiment analysis.

## Scope and Delimitation

The primary focus of this study lies in the design, development, and system evaluation of an multi-agent artificial intelligence framework engineered for civic listening. To ensure a robust, high-fidelity implementation while operating within realistic constraints, the precise boundaries of the research are defined along geographic, platform-specific, data-handling, and linguistic parameters. 

The geographic scope of data acquisition is delimited strictly to Baguio City, Benguet, Philippines. Because public social media data contains substantial geographical noise—wherein approximately 25% of geotagged content or location tags may stem from non-local accounts, tourists, or generalized national metadata—the ingestion layer does not rely solely on raw GPS coordinates. Instead, the boundary is enforced using a dual-filtering pipeline consisting of location-specific string queries and localized keyword clustering. Target search terms are confined to explicitly recognized local landmarks and administrative points, including but not limited to "Baguio", "Session Road", "Magsaysay", and "Burnham Park".

To isolate localized systemic issues from general public sentiment, the text data is processed through theme-specific keyword clusters. For example, local code-switched terms such as "traffic", "trapik", and "Session Road gridlock" are programmatically mapped into a dedicated "Mobility" cluster. This mechanism isolates public opinion regarding local public infrastructure and transit adjustments from unrelated global or national trends.

Platform ingestion is explicitly bounded by data accessibility and the structural availability of public APIs. The system gathers public civic sentiment across three distinct source channels, each selected to represent a unique layer of public discourse: formal public opinion and news tracking via the LangSearch and Tavily APIs, which gather regional news articles, local blogs, and community forums; structured municipal discourse collected from public, government-affiliated Facebook pages via the Apify cloud scraping platform, capturing official policy announcements and the subsequent citizen responses left in public comment sections; and hyper-local, long-form community interaction extracted via the Python Reddit API Wrapper, focusing on active regional subreddits, specifically r/baguio, r/Philippines, and r/CasualPH. Data collection from these platforms is strictly delimited to public domains. 

Private chat logs, direct messages, locked user profiles, and restricted community groups are completely excluded from the data stream to protect individual privacy and maintain compliance with data governance standards. Furthermore, thread ingestion via the PRAW pipeline is capped at first-tier comments to capture direct public reactions while preventing deep, circular nested comment noise from degrading the analytical clarity of the pipeline.

Linguistically, the analytical agents are optimized primarily for English-language prose and English-Filipino code-switching, commonly referred to as "Taglish". While the system's foundational models (specifically the RoBERTa and DeBERTa variants utilized within the text classification and Natural Language Inference modules) implicitly accommodate basic Taglish semantic structures, the primary focus of this phase is not the deep syntactic or morphological parsing of localized regional Cordilleran dialects, such as Ilocano or Ibaloi. Expressions entirely written in regional dialects that fall outside the tokenization vocabulary of the pre-trained foundational models are excluded from the core sentiment mapping node to avoid introducing downstream categorization errors.

Regarding data verification and performance bounds, this research does not claim to establish an absolute, universal "ground truth" for real-world factual validation, as a unified, pre-labeled civic misinformation dataset tailored specifically to Philippine municipal discourse does not exist. Rather, the validation scope is strictly internal and architectural, evaluating the system's contextual faithfulness, thematic accountability, and compliance rate. This is accomplished by extracting up to three atomic claims per document and validating them using an NLI verification threshold where entailment scores below 0.75 are flagged as unverified to monitor and isolate algorithmic hallucinations. Finally, the systemic execution is bound by real-time infrastructure limits, operating under a heuristic 40/60 ensemble weight distribution for data processing without executing external automated hyperparameter adjustments. 

Storage persistence is confined to managed vector indexes within Qdrant Cloud. Live runtime execution is bound by API call limits, restricted to 15 requests per minute for Google Gemini endpoints, 1,000 requests per month for Tavily search queries, and 16 GB of RAM capacity on HuggingFace Spaces to maintain operational balance without triggering parallel thread memory errors.

## Data Gathering Techniques

Data is retrieved through four acquisition methods, each tied to an objective: (1) semantic search and reranking, (2) Apify scraper integration, (3) PRAW API, and (4) Qdrant Vector Store.

### Existing Components for Multi-Agentic AI and RAG

For the initial objective, the study acquires the scholarly literature through structured academic search. This serves to ground the framework design in established DSR, AOSE, RAG, and Agentic AI literature, and to justify the chosen tool stack documented in the software development tools section.

### Framework for Autonomous Real-Time Search and Retrieval

To satisfy the second objective, three production-grade acquisition streams are implemented. Each stream is described as a method used by the agentic pipeline. Formal public-opinion content is retrieved through the LangSearch API, which performs semantic search across news outlets, blogs, and forums. The returned documents are re-ranked before being stored in the document repository.

Structured public-opinion content from Facebook is collected through the Apify cloud platform. The scraper targets public government pages to capture official announcements and the citizen sentiment expressed in their public comment sections. Long-form, hyper-local community discussion is collected through the Python Reddit API Wrapper (PRAW), targeting the `r/baguio`, `r/Philippines`, and `r/CasualPH` subreddits. Previously analyzed documents are stored as embeddings in the Qdrant Cloud vector store so that they can be retrieved as part of the system's Retrieval-Augmented Generation loop, ensuring that the search is grounded in historical context and existing internal data.

### Evaluation of Contextual Faithfulness, Thematic Accountability, and Cost Efficiency

To evaluate the framework's contextual faithfulness, thematic accountability, and cost efficiency, the study collects three types of evidence. First, it captures live runtime telemetry directly from the deployed agents during normal operation. Second, it utilizes a labeled ground-truth benchmark to measure correctness. Finally, it integrates an external online evaluation stream that runs exclusively during the evaluation phase to assess performance without impacting regular operations. 

During each production run, the FaithfulnessAgent verifies the generated summary's atomic claims against the retrieved source documents using an NLI model, and emits its verification results as part of the framework's runtime metrics.

During each production run, the Context Augmentation Agent, the Smart Reuse layer, and the VSEE bypass mechanism emit cost- and reuse-related counters as part of the same framework runtime metrics.

For the Evaluation chapter, the study uses an offline evaluation stream that is not part of the production data-acquisition path: an independent expert validation conducted by a former US-based IBM Senior Software Engineer, in which an external LLM judge (Claude Sonnet 4) independently scored agent outputs across 46 stress-test scenarios to produce groundedness, thematic-actionability, safety, efficiency, and trajectory metrics that cross-validate the framework's own runtime telemetry. 

## Sources of Data

The study identified six streams of source material presented below as a sub-section tied to the data-gathering technique. 

### Academic and Component-Level Literature

The sources consist of peer-reviewed journal articles, conference papers, pre-prints, and seminal reference works covering Design Science Research, Agent-Oriented Software Engineering, multi-agentic AI systems, Retrieval-Augmented Generation, natural-language-inference-based faithfulness evaluation, and civic-listening architectures.

### Formal Public-Opinion Stream

The formal-discourse source layer consists of news articles, blog posts, and forum threads surfaced by the LangSearch semantic-search API and re-ranked before storage. Each document carries a URL, a publisher domain, a publication timestamp, and a relevance score.

### Public-Government Facebook Channel

The civic-government source layer consists of posts and public comments on government-affiliated Facebook pages collected through the Apify scraper pipeline. Each item carries post text, public comment text, timestamp, and engagement metadata.

### Hyper-Local Reddit Communities

The hyper-local community source layer consists of submissions and top-level comments from `r/baguio`, `r/Philippines`, and `r/CasualPH`, collected from the PRAW pipeline. Longer thread context is captured when a submission is initially posted; the framework retains only the first-tier comments for analysis.

### Qdrant Cloud Cyclic RAG Stores

The long-term memory source layer consists of previously analyzed documents that have been embedded and stored in the Qdrant Cloud vector store and are surfaced on subsequent runs through the Retrieval-Augmented Generation loop. These documents are not externally acquired for each run and are reused as internal history.

### Custom Runtime Telemetry Streams

The runtime-telemetry source layer consists of the verification metrics emitted by the FaithfulnessAgent and the efficiency counters emitted by the cyclic-RAG, Smart Reuse, and VSEE mechanisms. These are recorded on each production run. 

## Treatment of Data

This section describes how each stream is normalized before downstream analysis. 

1. Unicode and Encoding Sanitization from Semantic Search, Apify, PRAW, and Qdrant Vector Store
   All acquired documents, regardless of whether they enter through LangSearch, Apify, PRAW, or the cyclic-RAG read path, are first passed through a Unicode sanitization routine that removes surrogate characters, control characters, and zero-width formatting glyphs before any tokenization or embedding step. This prevents tokenizers from raising errors on malformed UTF-16 sequences that occasionally arrive from web-scraped content.

2. Semantic Chunking into Bounded Blocks from Semantic Search, Apify, PRAW, and Qdrant Vector Store
   After sanitization, each document is split into semantic chunks with overlapping context windows for downstream embedding retrieval. Each chunk carries the parent document's URL, title, and timestamp metadata so that the citation path is preserved.

3. Embedding, Storage, and Vector-Index Maintenance from Qdrant Vector Store
   Once chunked, documents are embedded and added to the Qdrant Cloud vector store along with citation-ready metadata. This is the gate that allows cyclic-RAG memory reuse on subsequent runs.

4. Credibility Pre-Filtering via the 5-Signal Source-Quality Filter from Semantic Search, Apify, PRAW, and Qdrant Vector Store
   Before downstream sentiment and clustering agents run, every retrieved document is scored by the 5-signal source-quality filter. Documents below the credibility threshold are de-prioritized before reaching the sentiment and credibility nodes. 

5. Runtime-Metrics Persistence from Custom Runtime Telemetry Techniques
   The runtime telemetry emitted by the FaithfulnessAgent and the cyclic-RAG or Smart Reuse or VSEE mechanisms is persisted as structured metric records on each production run, then aggregated into the per-run metrics trail.

## Software Development Tools

The following tools and frameworks were used to develop the software to assist in developing the objectives:

AgenticHinaing Evaluation Framework. An external stress-testing and validation scorecard framework designed and built by the validator (former US-based IBM Senior Software Engineer) to independently evaluate the AgenticHinaing system against 46 agentic-evaluation scenarios drawn from published benchmarks (AgentDiagnose, TRAJECT-Bench, ToolSandbox, AgentHarm). It was used in this study as the primary external expert-validation instrument, producing the attested scorecard and independent LLM-judge metrics.

Apify. A cloud platform for web scraping and data extraction that provides pre-built actors for structured social media collection. It was used to collect structured Facebook data from public government pages for sentiment and topic analysis.

CredibilityAgent - Subagent as a tool (5-Signal Source-Quality Filter). A specialized verification agent that combines five concurrent signals — Domain Trust (25%), Internal Semantic Cross-Reference via BGE-large embeddings (20%), Google Fact Check Tools API (`factchecktools.googleapis.com`, 15%), LLM-based quality analysis via Google Gemini 2.5 Flash Lite (20%), and Tavily-based real-time web verification (20%) — to score whether retrieved source documents can be trusted before they propagate through the pipeline. It was used in this study to enforce a source-quality threshold on every retrieved document, extracting up to three verifiable claims per document and flagging misinformation indicators so that fabricated or rumour-grade content cannot reach the sentiment or NLI faithfulness stages.

Docker. A containerization platform that packages applications and their dependencies into standardized units for consistent execution. It was used to build reproducible container images for both the backend and frontend services across development and production environments.

FastAPI. A high-performance Python web framework for building APIs based on standard Python type hints. It was used to expose the multi-agent orchestration endpoints and serve the system's analysis results to the frontend.

Git / GitHub. A distributed version control system and cloud-based hosting platform for tracking code changes and collaborating on software projects. It was used to manage source code, document iterations of the Spiral Model, and synchronize deployments to HuggingFace Spaces and Vercel.

Google Gemini (2.5 Flash/Lite). A family of highly capable multimodal models optimized for speed and efficiency across a variety of reasoning tasks. It was used to power the language reasoning, planning, and synthesis steps performed by the multi-agent workflows.

HuggingFace Spaces. A platform for hosting machine learning–powered web applications with automatic GPU provisioning. It currently serves as the active backend hosting solution, where the `backend/` folder is deployed via `ship.ps1` to provide 16 GB of RAM for memory-intensive multi-agent workloads.

HuggingFace Transformers (DeBERTa-v3 NLI). A library providing state-of-the-art transformer architectures, specifically using `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33` — a compact (~184M-parameter) zero-shot Natural Language Inference model. It was used to label each extracted claim as *entailed*, *neutral*, or *contradicted* against retrieved source documents, with entailment scores below 0.75 flagged as unverified.

FaithfulnessAgent - Agent as a tool (NLI-based Verification). A specialized verification agent that extracts individual claims from generated summaries and validates each one against its source documents using the DeBERTa-v3 NLI model. It was used as the Node 7 verification stage of the orchestration pipeline to compute the faithfulness score, citation accuracy rate, and hallucination rate that gate the final insights before they are persisted into Qdrant memory. The FaithfulnessAgent is positioned as an internal consistency check rather than as a benchmarked measurement of "real" truth.

LangChain / LangGraph. Frameworks for developing applications powered by language models that use directed acyclic graphs to orchestrate multi-agent, stateful workflows. They were used to define the agent roles, responsibilities, and state transitions that implement the AOSE design.

LangSmith. A platform for debugging, testing, and monitoring large language model applications. It was used during development to trace agent executions, evaluate prompts, and ensure production-grade reliability of the multi-agent pipeline.

Lucide React. An open-source icon library that provides a collection of lightweight, tree-shakable React components built from scalable vector graphics. It was used in the frontend interface to render consistent, accessible iconography across dashboard components.

Next.js 15 with React 19 and TypeScript. A high-performance React framework for production that leverages Server Components, the React Compiler, and static typing to streamline full-stack web development. It was used to build the user-facing web application that consumes the FastAPI backend.

PRAW (Python Reddit API Wrapper). A Python interface for the Reddit API used to collect social media data for analysis. It was used to fetch posts and comments from hyper-local subreddits such as r/baguio, r/Philippines, and r/CasualPH for public opinion retrieval.

Python 3.11+ with Poetry. Python is the primary programming language of the study, while Poetry is a modern dependency management tool that ensures reproducible environments via a deterministic lockfile. They were used to implement the backend services and to manage all project dependencies consistently across machines.

Qdrant Cloud/Vector Search. A managed vector database designed for high-performance similarity search of high-dimensional embeddings. It was used as the study's vector storage layer to persist embedded documents and support Retrieval-Augmented Generation queries.

Railway. A platform for deploying web applications with straightforward setup and GitHub integration. It was initially used in early prototyping iterations but was later replaced after experiencing Out of Memory (OOM) issues caused by high parallelization under the Free tier's RAM limits.

Google Cloud Run. A fully managed compute platform that automatically scales stateless containers in the asia-southeast1 (Singapore) region, providing a serverless environment for backend services. It was evaluated for production deployment due to its autoscaling capabilities, but account access expired during development.

Sentence Transformers (BGE-large-en-v1.5). A framework for state-of-the-art sentence and text embeddings that hosts the BGE (BAAI General Embedding) model family for semantic accuracy. It was used to encode documents and queries into 1024-dimensional dense vectors prior to storage and retrieval in Qdrant Cloud.

Tailwind CSS. A utility-first CSS framework that enables rapid UI development through low-level, composable classes applied directly within markup. It was used to style the frontend interface, eliminating the need for custom external stylesheets while keeping the design system consistent.

Tavily / LangSearch. A pair of specialized search engines optimized for large language model agents to perform real-time fact-checking and semantic web retrieval. They were used to surface news articles, blogs, and forum posts relevant to Baguio City–related public discourse.

Vercel. A cloud platform designed for frontend developers that provides automated deployment, global edge scaling, and optimized hosting tailored for Next.js applications. It was used to host and deploy the public-facing web interface of the system.

Stale-While-Revalidate (SWR). A React Hooks library for remote data fetching that implements the "stale-while-revalidate" strategy to keep user interfaces fast, reactive, and synchronized with the server. It was used on the frontend to fetch analysis results from the backend while caching previous responses for a responsive UX.

ship.ps1 (Custom Deployment Script). A PowerShell automation script that orchestrates dual-platform deployment of the project. It synchronizes staged files to the GitHub `main` branch and extracts or pushes the `backend/` folder to HuggingFace Spaces via Git subtree split, and it supports a `-pull` flag for pulling the latest changes from GitHub before deployment.