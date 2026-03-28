'use client';

import React from 'react';
import { Analytics as AnalyticsType } from '@/lib/types';
import { cn } from '@/lib/utils';

import { PieChart, Activity } from 'lucide-react';

interface AnalyticsProps {
  data: AnalyticsType | null;
}

export default function Analytics({ data }: AnalyticsProps) {
  if (!data) {
    return (
      <div className="h-full min-h-[440px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-slate-50 text-slate-400 rounded-2xl flex items-center justify-center mb-5 border border-slate-100 shadow-sm">
          <PieChart className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-1.5">No telemetry available</h3>
        <p className="text-[13px] font-normal text-slate-400">Extract requirements to generate metrics.</p>
      </div>
    );
  }

  const metrics = [
    { label: 'Processing time', value: `${data.processingTime}ms`, icon: '⏱️' },
    { label: 'Tokens processed', value: data.tokensProcessed.toLocaleString(), icon: '🔢' },
    { label: 'Confidence score', value: '88%', icon: '✅' },
  ];

  const maxCat = Math.max(...data.categoryBreakdown.map(c => c.value), 1);
  const maxConf = Math.max(...data.confidenceDistribution.map(c => c.value), 1);

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-12 pb-32 font-sans antialiased">
      {/* Metric Cards */}
      <div className="grid grid-cols-3 gap-6">
        {metrics.map((m) => (
          <div key={m.label} className="p-6 bg-white border border-gray-100 rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest leading-relaxed">{m.label}</span>
              <span className="text-[14px] opacity-40">{m.icon}</span>
            </div>
            <p className="text-2xl font-bold text-[#111827] tracking-tight tabular-nums">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Confidence Distribution — Bar Chart */}
      <div className="p-8 bg-white border border-gray-100 rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2.5 mb-8">
          <Activity className="w-3.5 h-3.5 text-gray-400" />
          <h3 className="text-[13px] font-bold text-gray-900 tracking-tight">Confidence distribution</h3>
        </div>
        <div className="space-y-4">
          {data.confidenceDistribution.map((item) => (
            <div key={item.label} className="flex items-center gap-4">
              <span className="text-[11px] font-medium text-gray-400 w-32 shrink-0 truncate" title={item.label}>{item.label}</span>
              <div className="flex-1 h-2 bg-gray-50 rounded-full overflow-hidden border border-gray-100/50">
                <div className="h-full bg-indigo-500/80 rounded-full transition-all duration-700" style={{ width: `${(item.value / maxConf) * 100}%` }} />
              </div>
              <span className="text-[11px] font-bold text-gray-500 w-8 tabular-nums">{item.value}</span>
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
          <div className="space-y-1.5">
            {Object.entries(data.moscow_distribution).map(([key, value]) => {
              const maxVal = Math.max(...Object.values(data.moscow_distribution!), 1);
              const colorClass = 
                key === 'Must' ? 'bg-[#ff6b6b]' : 
                key === 'Should' ? 'bg-[#ffa94d]' : 
                key === 'Could' ? 'bg-[#ffd43b]' : 
                'bg-[#adb5bd]';

              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-[10px] text-[rgba(55,53,47,0.5)] w-64 shrink-0 text-right truncate" title={key}>{key}</span>
                  <div className="flex-1 h-3.5 bg-[#f7f7f5] rounded overflow-hidden border border-[rgba(55,53,47,0.06)]">
                    <div className={cn("h-full transition-all duration-700", colorClass)} style={{ width: `${(value / maxVal) * 100}%` }} />
                  </div>
                  <span className="text-[10px] font-mono text-[rgba(55,53,47,0.65)] w-8">{value}</span>
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
        <div className="space-y-1.5">
          {data.categoryBreakdown.map((item) => (
            <div key={item.name} className="flex items-center gap-3">
              <span className="text-[10px] text-[rgba(55,53,47,0.5)] w-64 shrink-0 text-right truncate" title={item.name}>{item.name}</span>
              <div className="flex-1 h-3.5 bg-[#f7f7f5] rounded overflow-hidden border border-[rgba(55,53,47,0.06)]">
                <div className="h-full bg-[#e8deee] rounded transition-all duration-700" style={{ width: `${(item.value / maxCat) * 100}%` }} />
              </div>
              <span className="text-[10px] font-mono text-[rgba(55,53,47,0.65)] w-8">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
