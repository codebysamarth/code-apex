export interface FunctionalReq {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  moscow?: 'Must' | 'Should' | 'Could' | 'Wont';
  confidence: number;
  sourceRef: string;
}

export interface NFR {
  id: string;
  category: string;
  description: string;
  constraints: string[];
}

export interface Stakeholder {
  id: string;
  name: string;
  role: string;
  impact: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
}

export interface Decision {
  id: string;
  decision: string;
  rationale: string;
  implications: string[];
}

export interface TimelineItem {
  id: string;
  phase: string;
  activity: string;
  deliverable: string;
  duration: string;
}

export interface Scope {
  inScope: string[];
  outOfScope: string[];
}

export interface Gap {
  id: string;
  description: string;
  consequence: string;
  suggestedAction: string;
}

export interface Suggestion {
  text: string;
  from_project: string;
  domain: string;
  confidence: number;
  source_brd_id: string;
}

export interface MatchedBRD {
  project_name: string;
  domain: string;
  similarity_score: number;
}

export interface PriorityScore {
  requirementId: string;
  impact: number;
  effort: number;
  urgency: number;
  total: number;
}

export interface Analytics {
  confidenceDistribution: { label: string; value: number }[];
  categoryBreakdown: { name: string; value: number }[];
  moscow_distribution?: {
    Must: number;
    Should: number;
    Could: number;
    Wont: number;
  };
  processingTime: number;
  tokensProcessed: number;
}

export interface PipelineStep {
  id: 'ingest' | 'classify' | 'rag' | 'extract' | 'timeline' | 'critique' | 'score' | 'domain_extractor' | 'render';
  label: string;
  status: 'idle' | 'running' | 'done' | 'error';
  timestamp?: string;
}

export interface BRDState {
  functional: FunctionalReq[];
  nfr: NFR[];
  stakeholders: Stakeholder[];
  decisions: Decision[];
  timeline: TimelineItem[];
  scope: Scope;
  gaps: Gap[];
  priorities: PriorityScore[];
  analytics: Analytics | null;
  pipeline: PipelineStep[];
  domain: 'software' | 'healthcare' | 'mechanical' | 'business';
  domain_data: any;
  sourceMap?: Record<string, { start: number; end: number; text: string }>;
  sentiment_metrics?: {
    overall_sentiment: number;
    positivity_ratio: number;
  };
  summary_labels?: {
    card1: string;
    card2: string;
    card3: string;
    card4: string;
  };
  logs: string[];
  isExtracting: boolean;
  error: string | null;
  suggestions?: Suggestion[];
  matched_brds?: MatchedBRD[];
  suggestion_count?: number;
}

export interface ModelStats {
  model: string;
  latency: number;
  costEstimate: number;
  requests: number;
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'offline';
  timestamp: string;
}

export type ExtractionEventPayload = 
  | Partial<BRDState> 
  | string 
  | { id: PipelineStep['id']; status: PipelineStep['status'] }
  | {};

export interface ExtractionEvent {
  type: 'node_complete' | 'done' | 'error' | 'log';
  payload: ExtractionEventPayload;
}
