import { FunctionalReq, NFR, Stakeholder, BRDState, PipelineStep } from './types';

export const initialPipeline: PipelineStep[] = [
  { id: 'ingest', label: 'Ingest Source', status: 'idle' },
  { id: 'classify', label: 'Classify Type', status: 'idle' },
  { id: 'rag', label: 'RAG Retrieval', status: 'idle' },
  { id: 'extract', label: 'Entity Extraction', status: 'idle' },
  { id: 'timeline', label: 'Timeline Creation', status: 'idle' },
  { id: 'critique', label: 'Critique & Refine', status: 'idle' },
  { id: 'score', label: 'Priority Scoring', status: 'idle' },
];

export const sampleText = `Project Zenith - Global Payments Dashboard
Overview:
Replace legacy dashboard to support 10k transactions per second.
Functional Requirements:
FR1: Monitor transactions in real time.
FR2: Calculate mid-market exchange rates for 40+ currencies.
Stakeholders:
Manager Sarah (Product), Developer John (Engineering), Finance Admin Mike (Accounting).
Constraints:
Maintain 99.9% uptime. Ensure sub-second dashboard loads. Encrypt data at rest.`;

export const sampleBRDSlow: Partial<BRDState> = {
  functional: [
    { id: 'FR1', title: 'Monitor transactions in real time', description: '', priority: 'high', moscow: 'Must', confidence: 0.94, sourceRef: 'section 1.2' },
    { id: 'FR2', title: 'Calculate mid-market exchange rates', description: '', priority: 'medium', moscow: 'Should', confidence: 0.88, sourceRef: 'section 2.1' },
  ],
  nfr: [
    { id: 'NFR1', category: 'Reliability', description: 'Maintain 99.9% uptime', constraints: ['Active-active deployment', 'Chaos testing'] },
    { id: 'NFR2', category: 'Security', description: 'Ensure SOC2 Type II compliance', constraints: ['AES-256 encryption', 'TLS 1.3'] },
  ],
  stakeholders: [
    { id: 'S1', name: 'Sarah Miller', role: 'Head of Product', impact: 'High' },
    { id: 'S2', name: 'Mike Robinson', role: 'VP of Engineering', impact: 'Medium' },
  ],
  decisions: [
    { id: 'D1', decision: 'Micro-frontend architecture', rationale: 'Isolate scaling logic.', implications: ['Increased DevOps overhead', 'Faster independent deployments'] }
  ],
  timeline: [
    { id: 'T1', phase: 'Data ingestion', activity: 'Setup connectors', deliverable: 'Source streams', duration: '2 weeks' },
    { id: 'T2', phase: 'Processing block', activity: 'Implement rule engine', deliverable: 'Real-time analyzer', duration: '4 weeks' }
  ],
  scope: {
    inScope: ['Cloud infrastructure', 'Real-time dashboard', 'API Gateway'],
    outOfScope: ['Mobile app', 'Offline processing']
  },
  gaps: [
    { id: 'G1', description: 'Missing error logic', consequence: 'Fails silently on downtime.', suggestedAction: 'Clarify with finance team.' }
  ],
  priorities: [
    { requirementId: 'FR1', impact: 9, effort: 7, urgency: 10, total: 26 },
    { requirementId: 'FR2', impact: 8, effort: 5, urgency: 4, total: 17 }
  ],
  analytics: {
    confidenceDistribution: [
      { label: 'High (>90%)', value: 45 },
      { label: 'Medium (70-90%)', value: 30 },
      { label: 'Low (<70%)', value: 15 },
    ],
    categoryBreakdown: [
      { name: 'Functional', value: 60 },
      { name: 'NFR', value: 20 },
      { name: 'Stakeholders', value: 10 },
      { name: 'Decisions', value: 10 },
    ],
    moscow_distribution: {
      Must: 5,
      Should: 3,
      Could: 2,
      Wont: 0,
    },
    processingTime: 12.4,
    tokensProcessed: 4520,
  }
};
