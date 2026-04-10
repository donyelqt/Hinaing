export type ToggleOption = {
  value: string;
  label: string;
  hint?: string;
};

export type PresetOption = {
  id: string;
  name: string;
  description: string;
  platforms: string[];
  focusAreas: string[];
  window: string;
};

export type GeneratorStep = {
  title: string;
  description: string;
};

export type SentimentState = {
  platforms: string[];
  timeWindow: string;
  focusAreas: string[];
  includeAlerts: boolean;
  isGenerating: boolean;
  isRefreshing: boolean;
  showMobileFilters: boolean;
};

export type AblationPreset = 'full' | 'ablated';

export type SentimentActions = {
  setPlatforms: (updater: (prev: string[]) => string[]) => void;
  setTimeWindow: (value: string) => void;
  setFocusAreas: (updater: (prev: string[]) => string[]) => void;
  setIncludeAlerts: (value: boolean) => void;
  setIsGenerating: (value: boolean) => void;
  setIsRefreshing: (value: boolean) => void;
  setShowMobileFilters: (value: boolean) => void;
  toggleSelection: (value: string, setState: (updater: (prev: string[]) => string[]) => void) => void;
  applyPreset: (presetId: string) => void;
  setAblationPreset: (preset: AblationPreset) => void;
};

// Faithfulness Verification Types (NEW - Best Practice)
export type HallucinationType = 
  | "fabricated_claim"
  | "contradicted_claim"
  | "numerical_hallucination";

export type HallucinationAnalysis = {
  hallucination_count: number;
  hallucination_rate: number;
  hallucination_types: Record<HallucinationType, number>;
  is_hallucination_free: boolean;
  hallucination_details?: Array<{
    type: HallucinationType;
    claim: string;
    category: string;
    entailment_score: number;
    reason: string;
  }>;
};

export type MisattributionAnalysis = {
  misattribution_count: number;
  misattribution_rate: number;
  misattribution_details?: Array<{
    type: "misattribution";
    claim: string;
    citation: string;
    accuracy_score: number;
    reason: string;
  }>;
};

export type NumericalHallucinationAnalysis = {
  count: number;
  rate: number;
  details?: Array<{
    claim: string;
    category: string;
    unsupported_numbers: string[];
    reason: string;
  }>;
};

export type CitationVerification = {
  total_citations: number;
  valid_citations: number;
  invalid_citations: number;
  citation_accuracy_rate: number;
  citation_details?: Array<{
    citation: string;
    domain: string;
    is_valid: boolean;
    accuracy_score: number;
    credibility_match: boolean;
    sentiment_match: boolean;
    source_url: string | null;
  }>;
};

export type FaithfulnessVerification = {
  total_claims: number;
  verified_claims: number;
  unverified_claims: number;
  faithfulness_score: number;
  faithfulness_rate: number;
  claim_details?: Array<{
    claim: string;
    category: string;
    entailment_score: number;
    status: "verified" | "unverified" | "contradicted";
    supporting_sources: string[];
  }>;
  // NEW - Best Practice Separation
  citation_verification?: CitationVerification;
  hallucination_analysis?: HallucinationAnalysis;
  misattribution_analysis?: MisattributionAnalysis;
  numerical_hallucinations?: NumericalHallucinationAnalysis;
};
