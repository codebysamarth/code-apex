import { FunctionalReq, NFR, Stakeholder, BRDState, PipelineStep } from './types';

export const initialPipeline: PipelineStep[] = [
  { id: 'ingest', label: 'Ingest Source', status: 'idle' },
  { id: 'classify', label: 'Classify Type', status: 'idle' },
  { id: 'rag', label: 'RAG Retrieval', status: 'idle' },
  { id: 'extract', label: 'Entity Extraction', status: 'idle' },
  { id: 'timeline', label: 'Timeline Creation', status: 'idle' },
  { id: 'critique', label: 'Critique & Refine', status: 'idle' },
  { id: 'score', label: 'Priority Scoring', status: 'idle' },
  { id: 'render', label: 'Generate BRD', status: 'idle' },
];

export const domainPipelines: Record<string, PipelineStep[]> = {
  software: initialPipeline,
  healthcare: [
    { id: 'ingest', label: 'Ingest HIPAA Docs', status: 'idle' },
    { id: 'classify', label: 'Clinical Classifier', status: 'idle' },
    { id: 'rag', label: 'Medical RAG', status: 'idle' },
    { id: 'domain_extractor', label: 'Clinical Expert Agent', status: 'idle' },
    { id: 'timeline', label: 'Healthcare Timeline', status: 'idle' },
    { id: 'critique', label: 'Compliance Audit', status: 'idle' },
    { id: 'score', label: 'Requirement Scoring', status: 'idle' },
    { id: 'render', label: 'Finalize Clinical BRD', status: 'idle' },
  ],
  mechanical: [
    { id: 'ingest', label: 'Ingest CAD/Spec', status: 'idle' },
    { id: 'classify', label: 'Hardware Classifier', status: 'idle' },
    { id: 'rag', label: 'Engineering RAG', status: 'idle' },
    { id: 'domain_extractor', label: 'Hardware Design Agent', status: 'idle' },
    { id: 'timeline', label: 'Design Milestones', status: 'idle' },
    { id: 'critique', label: 'Safety Critique', status: 'idle' },
    { id: 'score', label: 'Engineering Scoring', status: 'idle' },
    { id: 'render', label: 'Generate Engineering BRD', status: 'idle' },
  ],
  business: [
    { id: 'ingest', label: 'Ingest Strategy', status: 'idle' },
    { id: 'classify', label: 'Market Classifier', status: 'idle' },
    { id: 'rag', label: 'Strategy RAG', status: 'idle' },
    { id: 'domain_extractor', label: 'Strategy Consultant Agent', status: 'idle' },
    { id: 'timeline', label: 'Strategic Roadmap', status: 'idle' },
    { id: 'critique', label: 'GAP Analysis', status: 'idle' },
    { id: 'score', label: 'Business Value Scoring', status: 'idle' },
    { id: 'render', label: 'Finalize Business Case', status: 'idle' },
  ],
};

export const domainSamples: Record<string, string> = {
  software: `Project Zenith - Global Payments Dashboard
Overview: Replace legacy dashboard to support 10k TPS.
Functional Requirements:
FR1: Monitor transactions in real time.
FR2: Calculate FX rates for 40+ currencies.
Constraints: 99.9% uptime. Sub-second load times.`,

  healthcare: `Clinical Patient Portal - St. Jude Medical
Objective: Secure platform for patient-clinician EHR access.
Requirements:
- HIPAA Compliance: All data must be encrypted with AES-256.
- Integration: Support HL7 FHIR for EHR interoperability.
- Safety: Patient drug-allergy alerts must trigger in <200ms.
Stakeholders: Clinical Staff, IT Security, Hospital Admin.`,

  mechanical: `HVAC Compressor Housing - Rev 4.0
Specs: Aluminum Alloy 6061 casing for industrial refrigeration.
Engineering Requirements:
- Material: High-grade aerospace grade Aluminum (6061-T6).
- Tolerance: Precision milling to +/- 0.05mm on all mount points.
- Pressure: Must withstand 450 PSI internal pressure at 80°C.
- Safety: Factor of safety must be >= 2.5.`,

  business: `GTM Strategy: European Expansion Plan
Goal: Gain 15% market share in the EU fintech space by 2025.
Strategic Levers:
- Market entry via Berlin and Paris hubs.
- Compliance: Full MiFID II and GDPR alignment.
- Financials: Target ROI of 22% within 18 months.
- Risk: Euro-volatility mitigation using hedge strategies.`
};

export const sampleText = domainSamples.software;

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
