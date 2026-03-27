'use client';

import React from 'react';
import { Analytics as AnalyticsType } from '@/lib/types';
import { cn } from '@/lib/utils';

import { PieChart } from 'lucide-react';

interface AnalyticsProps {
  data: AnalyticsType | null;
}

export default function Analytics({ data }: AnalyticsProps) {
  if (!data) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4 shadow-[0_4px_12px_rgba(59,130,246,0.1)]">
          <PieChart className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">No telemetry available</h3>
        <p className="text-[13px] font-bold text-gray-400">Extract requirements to generate metrics.</p>
      </div>
    );
  }

  const metrics = [
    { label: 'Processing time', value: `${data.processingTime}ms`, emoji: '⏱️' },
    { label: 'Tokens processed', value: data.tokensProcessed.toLocaleString(), emoji: '🔢' },
    { label: 'Confidence score', value: '88%', emoji: '✅' },
  ];

  const maxCat = Math.max(...data.categoryBreakdown.map(c => c.value), 1);
  const maxConf = Math.max(...data.confidenceDistribution.map(c => c.value), 1);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-10 pb-32">
      {/* Metric Cards */}
      <div className="grid grid-cols-3 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="p-4 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[12px] text-[rgba(55,53,47,0.45)]">{m.label}</span>
              <span className="text-[16px]">{m.emoji}</span>
            </div>
            <p className="text-[24px] font-bold text-[rgba(55,53,47,1)] tracking-tight">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Confidence Distribution — Bar Chart */}
      <div className="p-5 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-[14px]">📈</span>
          <h3 className="text-[14px] font-semibold text-[rgba(55,53,47,1)]">Confidence distribution</h3>
        </div>
        <div className="space-y-3">
          {data.confidenceDistribution.map((item) => (
            <div key={item.label} className="flex items-center gap-3">
              <span className="text-[12px] text-[rgba(55,53,47,0.5)] w-28 shrink-0 text-right whitespace-nowrap">{item.label}</span>
              <div className="flex-1 h-6 bg-[#f7f7f5] rounded overflow-hidden border border-[rgba(55,53,47,0.06)]">
                <div className="h-full bg-[#2383e2] rounded transition-all duration-700" style={{ width: `${(item.value / maxConf) * 100}%` }} />
              </div>
              <span className="text-[12px] font-mono text-[rgba(55,53,47,0.65)] w-8">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* MoSCoW Distribution — Bar Chart (Conditional) */}
      {data.moscow_distribution && (
        <div className="p-5 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg">
          <div className="flex items-center gap-2 mb-5">
            <span className="text-[14px]">🎯</span>
            <h3 className="text-[14px] font-semibold text-[rgba(55,53,47,1)]">MoSCoW distribution</h3>
          </div>
          <div className="space-y-3">
            {Object.entries(data.moscow_distribution).map(([key, value]) => {
              const maxVal = Math.max(...Object.values(data.moscow_distribution!), 1);
              const colorClass = 
                key === 'Must' ? 'bg-[#ff6b6b]' : 
                key === 'Should' ? 'bg-[#ffa94d]' : 
                key === 'Could' ? 'bg-[#ffd43b]' : 
                'bg-[#adb5bd]';

              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-[12px] text-[rgba(55,53,47,0.5)] w-28 shrink-0 text-right whitespace-nowrap">{key}</span>
                  <div className="flex-1 h-6 bg-[#f7f7f5] rounded overflow-hidden border border-[rgba(55,53,47,0.06)]">
                    <div className={cn("h-full transition-all duration-700", colorClass)} style={{ width: `${(value / maxVal) * 100}%` }} />
                  </div>
                  <span className="text-[12px] font-mono text-[rgba(55,53,47,0.65)] w-8">{value}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      <div className="p-5 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-[14px]">🏷️</span>
          <h3 className="text-[14px] font-semibold text-[rgba(55,53,47,1)]">Category breakdown</h3>
        </div>
        <div className="space-y-3">
          {data.categoryBreakdown.map((item) => (
            <div key={item.name} className="flex items-center gap-3">
              <span className="text-[12px] text-[rgba(55,53,47,0.5)] w-28 shrink-0 text-right whitespace-nowrap">{item.name}</span>
              <div className="flex-1 h-6 bg-[#f7f7f5] rounded overflow-hidden border border-[rgba(55,53,47,0.06)]">
                <div className="h-full bg-[#e8deee] rounded transition-all duration-700" style={{ width: `${(item.value / maxCat) * 100}%` }} />
              </div>
              <span className="text-[12px] font-mono text-[rgba(55,53,47,0.65)] w-8">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
