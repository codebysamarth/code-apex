import { BRDState, HealthResponse, ModelStats, ExtractionEvent } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'; // Direct to backend

export interface ExtractBRDParams {
  text: string;
  sourceType: 'email' | 'meeting' | 'chat' | 'document';
  domain: 'software' | 'healthcare' | 'mechanical' | 'business';
  onEvent: (event: ExtractionEvent) => void;
  onError: (error: string) => void;
  onDone: (finalState: BRDState) => void;
}

export const getHealth = async (): Promise<HealthResponse> => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) throw new Error('Backend offline');
    return await res.json();
  } catch (error) {
    return { status: 'offline', timestamp: new Date().toISOString() };
  }
};

export const getModelStats = async (): Promise<ModelStats[]> => {
  const res = await fetch(`${API_BASE_URL}/api/model-stats`);
  if (!res.ok) return [];
  return await res.json();
};

const mapBackendToFrontendState = (raw: any): BRDState => {
  return {
    functional: (raw.functional_reqs || []).map((r: any) => ({
       id: r.id,
       title: r.text || r.title,
       description: r.description || r.text || '',
       priority: (r.moscow?.toLowerCase() === 'must' ? 'high' : r.moscow?.toLowerCase() === 'should' ? 'medium' : 'low') as any,
       moscow: r.moscow,
       confidence: r.confidence || 0.9,
       sourceRef: r.source_span || ''
    })),
    nfr: (raw.nfrs || []).map((r: any) => ({
       id: r.id,
       category: r.category,
       description: r.text || r.description,
       constraints: r.constraints || []
    })),
    stakeholders: (raw.stakeholders || []).map((r: any) => ({
       id: r.name,
       name: r.name,
       role: r.role,
       impact: r.influence_score > 0.8 ? 'High' : 'Medium',
       sentiment: r.sentiment || 'neutral'
    })),
    decisions: (raw.decisions || []).map((r: any) => ({
       id: r.id,
       decision: r.text || r.decision,
       rationale: r.rationale || '',
       implications: r.implications || []
    })),
    timeline: (raw.timeline || []).map((r: any, i: number) => ({
       id: `t-${i}`,
       phase: r.type || 'Phase',
       activity: r.milestone,
       deliverable: r.dependencies?.join(', ') || 'N/A',
       duration: r.date
    })),
    scope: {
      inScope: raw.scope?.in_scope || [],
      outOfScope: raw.scope?.out_of_scope || []
    },
    gaps: (raw.gaps || []).map((r: any, i: number) => ({
       id: `g-${i}`,
       description: r.gap || r.description,
       consequence: r.severity || 'Medium risk',
       suggestedAction: r.suggestion || r.suggestedAction
    })),
    priorities: (raw.priority_scores || []).map((r: any) => ({
       requirementId: r.req_id,
       impact: r.value_score * 10,
       effort: r.effort_score * 10,
       urgency: r.priority,
       total: (r.value_score + r.effort_score) * 5
    })),
    analytics: raw.analytics ? {
      confidenceDistribution: Object.entries(raw.analytics.confidence_distribution || {}).map(([label, value]) => ({ label, value: value as number })),
      categoryBreakdown: Object.entries(raw.analytics.req_type_breakdown || {}).map(([name, value]) => ({ name, value: value as number })),
      moscow_distribution: raw.analytics.moscow_distribution,
      processingTime: raw.analytics.total_processing_time || 0,
      tokensProcessed: raw.analytics.total_sentences_classified || 0
    } : null,
    pipeline: [],
    domain: raw.domain || 'software',
    domain_data: raw.domain_data || null,
    sourceMap: raw.source_map || {},
    sentiment_metrics: raw.sentiment_metrics || null,
    summary_labels: raw.summary_labels || null,
    logs: [],
    isExtracting: false,
    error: null,
    suggestions: raw.suggestions || [],
    matched_brds: raw.matched_brds || [],
    suggestion_count: raw.suggestion_count || 0
  };
};

export const getDemo = async (): Promise<BRDState> => {
  const res = await fetch('http://127.0.0.1:8000/api/demo');
  if (!res.ok) throw new Error('Failed to fetch demo data');
  const raw = await res.json();
  return mapBackendToFrontendState(raw);
};

export const extractBRD = async ({ text, sourceType, domain, onEvent, onError, onDone }: ExtractBRDParams) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, source_type: sourceType, domain }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Extraction failed');
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported or no body in response');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the incomplete line in the buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.replace('data: ', '').trim();
          if (!jsonStr) continue;

          try {
            const event: any = JSON.parse(jsonStr);
            
            // Map event data if necessary
            if (event.type === 'node_complete' && event.data) {
              onEvent({
                type: 'node_complete',
                payload: { id: event.agent, status: 'done' }
              });
            } else if (event.type === 'done') {
              onDone(mapBackendToFrontendState(event.data));
            } else if (event.type === 'error') {
              onError(event.message || 'Server error');
            }
          } catch (e) {
            console.error('Error parsing SSE event:', e, jsonStr);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message || 'Network error');
  }
};
