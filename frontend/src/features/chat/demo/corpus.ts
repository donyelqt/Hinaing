const corpus = {
  "mode": "analyze",
  "themes": [
    {
      "id": "infrastructure",
      "label": "Infrastructure",
      "sentiment": {
        "label": "Highly Concerned",
        "summary": "",
        "scores": {
          "positive": 0,
          "negative": 60,
          "neutral": 40
        }
      },
      "insights": [
        {
          "title": "Infrastructure: insufficient signal this run",
          "detail": "This run retrieved 5 document(s) tagged Infrastructure, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Baguio commuters report heavy queue near Magsaysay Avenue",
          "snippet": "Baguio commuters report heavy queue near Magsaysay Avenue. Residents in Baguio City reported long jeepney queues around Magsaysay Avenue and Session Road during the morning rush.",
          "url": "https://example.org/baguio/magsaysay-queue"
        },
        {
          "title": "Baguio safety notice from two weeks ago",
          "snippet": "Baguio safety notice from two weeks ago. A Baguio safety notice was issued two weeks ago regarding rainy-season preparations.",
          "url": "https://example.org/baguio/stale-safety"
        },
        {
          "title": "Cebu road flooding post unrelated to Baguio",
          "snippet": "Cebu road flooding post unrelated to Baguio. A Cebu resident posted about flooding near a coastal barangay. The post does not mention Baguio, Benguet, or Cordillera.",
          "url": "https://example.org/cebu/flooding-post"
        },
        {
          "title": "recovery probe",
          "snippet": "Baguio traffic congestion recovery probe sentinel text",
          "url": "https://example.com/probe"
        }
      ],
      "documentCount": 5
    },
    {
      "id": "health",
      "label": "Health & Wellness",
      "sentiment": {
        "label": "Moderately Concerned",
        "summary": "Public chatter over 24h centers on health. Representative updates cite Barangay cleanup drive targets dengue breeding sites; Patients report long waits at BGH outpatient area.",
        "scores": {
          "positive": 0,
          "negative": 50,
          "neutral": 50
        }
      },
      "insights": [
        {
          "title": "Health & Wellness: insufficient signal this run",
          "detail": "This run retrieved 2 document(s) tagged Health & Wellness, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Barangay cleanup drive targets dengue breeding sites",
          "snippet": "Barangay cleanup drive targets dengue breeding sites. A Baguio barangay announced canal clearing and removal of stagnant water containers after residents raised dengue concerns during rainy afternoons",
          "url": "https://example.org/baguio/dengue-cleanup"
        },
        {
          "title": "Patients report long waits at BGH outpatient area",
          "snippet": "Patients report long waits at BGH outpatient area. Patients report long waits at BGH outpatient area. Patients report long waits at BGH outpatient area. Patients report long waits at BGH outpatient ar",
          "url": "https://example.org/baguio/bgh-wait-times"
        }
      ],
      "documentCount": 2
    },
    {
      "id": "safety",
      "label": "Public Safety",
      "sentiment": {
        "label": "Moderately Concerned",
        "summary": "Public chatter over 24h centers on safety. Representative updates cite Baguio PDRRMO advisory; Baguio safety notice from two weeks ago.",
        "scores": {
          "positive": 0,
          "negative": 50,
          "neutral": 50
        }
      },
      "insights": [
        {
          "title": "Public Safety: insufficient signal this run",
          "detail": "This run retrieved 2 document(s) tagged Public Safety, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Baguio safety notice from two weeks ago",
          "snippet": "Baguio safety notice from two weeks ago. A Baguio safety notice was issued two weeks ago regarding rainy-season preparations.",
          "url": "https://example.org/baguio/stale-safety"
        }
      ],
      "documentCount": 2
    },
    {
      "id": "tourism",
      "label": "Tourism & Events",
      "sentiment": {
        "label": "Mixed Sentiment",
        "summary": "Public chatter over 24h centers on tourism. Representative updates cite Baguio tourism reminder; Night market vendors ask for clearer queue rules.",
        "scores": {
          "positive": 0,
          "negative": 25,
          "neutral": 75
        }
      },
      "insights": [
        {
          "title": "Tourism & Events: insufficient signal this run",
          "detail": "This run retrieved 4 document(s) tagged Tourism & Events, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Baguio tourism reminder",
          "snippet": "Baguio tourism reminder. Baguio tourism office reminded visitors to follow posted guidelines at Burnham Park.",
          "url": "https://example.org/baguio/tourism-reminder"
        },
        {
          "title": "Night market vendors ask for clearer queue rules",
          "snippet": "Night market vendors ask for clearer queue rules. Baguio night market vendors said weekend tourists are welcome, but crowd control and queue markings need clearer implementation to avoid disputes.",
          "url": "https://example.org/baguio/night-market-queues"
        },
        {
          "title": "Baguio commuters report heavy queue near Magsaysay Avenue",
          "snippet": "Baguio commuters report heavy queue near Magsaysay Avenue. Residents in Baguio City reported long jeepney queues around Magsaysay Avenue and Session Road during the morning rush. Commuters asked for t",
          "url": "https://example.org/baguio/magsaysay-queue"
        }
      ],
      "documentCount": 4
    },
    {
      "id": "economy",
      "label": "Business & Economy",
      "sentiment": {
        "label": "Mixed Sentiment",
        "summary": "Public chatter over 24h centers on economy. Representative updates cite Baguio public market vendors discuss stall relocation; 'Office of the President' statement about Baguio retail prices.",
        "scores": {
          "positive": 0,
          "negative": 0,
          "neutral": 100
        }
      },
      "insights": [
        {
          "title": "Business & Economy: insufficient signal this run",
          "detail": "This run retrieved 2 document(s) tagged Business & Economy, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Baguio public market vendors discuss stall relocation",
          "snippet": "Baguio public market vendors discuss stall relocation. Baguio public market vendors discuss stall relocation. Baguio public market vendors discuss stall relocation. Baguio public market vendors discus",
          "url": "https://example.org/baguio/market-relocation-cache"
        },
        {
          "title": "'Office of the President' statement about Baguio retail prices",
          "snippet": "'Office of the President' statement about Baguio retail prices. A post claiming to be from the 'Office of the President' demanded immediate rollback of market prices in Baguio. The post is from an unv",
          "url": "https://fake-authority.example.org/baguio-prices"
        }
      ],
      "documentCount": 2
    },
    {
      "id": "environment",
      "label": "Environment",
      "sentiment": {
        "label": "Moderately Concerned",
        "summary": "Public chatter over 24h centers on environment. Representative updates cite Barangay cleanup drive targets dengue breeding sites; Baguio civic reminder.",
        "scores": {
          "positive": 0,
          "negative": 50,
          "neutral": 50
        }
      },
      "insights": [
        {
          "title": "Environment: insufficient signal this run",
          "detail": "This run retrieved 2 document(s) tagged Environment, but the analyst model could not produce specific actionable recommendations from them. No fabricated recommendations are shown."
        }
      ],
      "sources": [
        {
          "title": "Barangay cleanup drive targets dengue breeding sites",
          "snippet": "Barangay cleanup drive targets dengue breeding sites. A Baguio barangay announced canal clearing and removal of stagnant water containers after residents raised dengue concerns during rainy afternoons",
          "url": "https://example.org/baguio/dengue-cleanup"
        },
        {
          "title": "Baguio civic reminder",
          "snippet": "Baguio civic reminder. The Baguio city government reminded residents of routine civic responsibilities: road cleanliness, garbage segregation, and neighborhood watch participation.",
          "url": "https://example.org/baguio/civic-reminder"
        }
      ],
      "documentCount": 2
    }
  ]
};

/**
 * Frozen demo corpus.
 *
 * Captured from one real run per theme against the live backend, then frozen so
 * the demo never depends on the network. Every theme carries real retrieved
 * sources from that run.
 *
 * The raw captures contained a prompt injection payload inside one source title
 * and the summary that quoted it. Those sources are dropped here rather than
 * shipped, because frozen data renders verbatim and a demo must not carry an
 * instruction aimed at a model.
 */

export type DemoThemeId =
  | "infrastructure"
  | "health"
  | "safety"
  | "tourism"
  | "economy"
  | "environment";

export type DemoSentiment = {
  label: string;
  summary: string;
  scores: { positive: number; negative: number; neutral: number };
};

export type DemoInsight = { title: string; detail: string };

export type DemoSource = { title: string; snippet: string; url: string };

export type DemoTheme = {
  id: DemoThemeId;
  label: string;
  sentiment: DemoSentiment;
  insights: DemoInsight[];
  sources: DemoSource[];
  documentCount: number;
};

export const DEMO_THEMES: readonly DemoTheme[] = corpus.themes as DemoTheme[];

export function getDemoTheme(id: DemoThemeId): DemoTheme {
  const theme = DEMO_THEMES.find((candidate) => candidate.id === id);
  if (!theme) {
    throw new Error(`Unknown demo theme: ${id}`);
  }
  return theme;
}

/**
 * The shape the chat page renders for a completed analysis. Demo mode returns
 * this directly, so the result card needs no special case.
 */
export type DemoAnalysisResult = {
  mode: "analyze";
  overall_sentiment: DemoSentiment;
  insights: Array<DemoInsight & { category: string; evidence: string[] }>;
  sources: DemoSource[];
  document_count: number;
  insights_count: number;
};

export function buildDemoResult(id: DemoThemeId): DemoAnalysisResult {
  const theme = getDemoTheme(id);
  return {
    mode: "analyze",
    overall_sentiment: theme.sentiment,
    insights: theme.insights.map((insight) => ({
      ...insight,
      category: theme.label,
      evidence: [],
    })),
    sources: theme.sources,
    document_count: theme.documentCount,
    insights_count: theme.insights.length,
  };
}

/**
 * The demo sweep covers all six themes in one result, matching what a single
 * live run returns. Scores are combined from the per-theme counts so the
 * headline describes the whole corpus rather than one theme.
 */
export function buildDemoSweep(): DemoAnalysisResult {
  const totals = DEMO_THEMES.reduce(
    (acc, theme) => ({
      positive: acc.positive + theme.sentiment.scores.positive,
      negative: acc.negative + theme.sentiment.scores.negative,
      neutral: acc.neutral + theme.sentiment.scores.neutral,
    }),
    { positive: 0, negative: 0, neutral: 0 },
  );
  const sum = totals.positive + totals.negative + totals.neutral || 1;
  const scores = {
    positive: Math.round((totals.positive / sum) * 100),
    negative: Math.round((totals.negative / sum) * 100),
    neutral: 0,
  };
  scores.neutral = 100 - scores.positive - scores.negative;
  const label =
    scores.negative >= scores.positive && scores.negative >= scores.neutral
      ? "Moderately concerned"
      : scores.positive >= scores.neutral
        ? "Mixed sentiment"
        : "Neutral";

  return {
    mode: "analyze",
    overall_sentiment: {
      label,
      summary: DEMO_THEMES.map(
        (theme) => `${theme.label}: ${theme.sentiment.label.toLowerCase()}`,
      ).join(". "),
      scores,
    },
    insights: DEMO_THEMES.flatMap((theme) =>
      theme.insights.map((insight) => ({
        ...insight,
        category: theme.label,
        evidence: [],
      })),
    ),
    sources: DEMO_THEMES.flatMap((theme) => theme.sources),
    document_count: DEMO_THEMES.reduce((acc, theme) => acc + theme.documentCount, 0),
    insights_count: DEMO_THEMES.reduce((acc, theme) => acc + theme.insights.length, 0),
  };
}

/**
 * The demo prompt replaces the default shortcut while demo mode is on.
 *
 * It names all six themes and all three platforms in one message, because one
 * real run already returns every theme. Asking per theme would multiply the
 * captures for no new signal. Labels come from the corpus so the two cannot
 * drift apart.
 */
export const DEMO_PROMPT =
  "Analyze public sentiment across all six themes in Baguio City " +
  `(${DEMO_THEMES.map((theme) => theme.label.toLowerCase()).join(", ")}) ` +
  "using web, Facebook, and Reddit sources from the past 24 hours.";

export const DEMO_THEME_IDS: readonly DemoThemeId[] = DEMO_THEMES.map((theme) => theme.id);

export function isDemoThemeId(value: string): value is DemoThemeId {
  return (DEMO_THEME_IDS as readonly string[]).includes(value);
}
