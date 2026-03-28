'use client';

import React, { useState } from 'react';
import { domainSamples } from '@/lib/samples';
import { cn } from '@/lib/utils';
import FileUploadZone from './FileUploadZone';

import { Code, HeartPulse, Settings, BarChart3, ChevronDown } from 'lucide-react';

interface InputPanelProps {
  onExtract: (text: string, domain: 'software' | 'healthcare' | 'mechanical' | 'business') => void;
  isLoading: boolean;
}

const domains = [
  { id: 'software', label: 'Software', icon: Code, color: 'text-purple-500', bg: 'bg-purple-50' },
  { id: 'healthcare', label: 'Healthcare', icon: HeartPulse, color: 'text-green-500', bg: 'bg-green-50' },
  { id: 'mechanical', label: 'Mechanical', icon: Settings, color: 'text-amber-500', bg: 'bg-amber-50' },
  { id: 'business', label: 'Business', icon: BarChart3, color: 'text-blue-500', bg: 'bg-blue-50' },
] as const;

export default function InputPanel({ onExtract, isLoading }: InputPanelProps) {
  const [text, setText] = useState('');
  const [domain, setDomain] = useState<typeof domains[number]['id']>('software');
  const [showDomainMenu, setShowDomainMenu] = useState(false);

  const handleSample = () => setText(domainSamples[domain] || domainSamples.software);

  const handleExtract = () => {
    if (!text.trim() || isLoading) return;
    onExtract(text, domain);
  };

  const selectedDomain = domains.find(d => d.id === domain)!;

  return (
    <div className="flex flex-col gap-4">
      {/* Domain Switcher */}
      <div className="relative">
        <button
          onClick={() => setShowDomainMenu(!showDomainMenu)}
          disabled={isLoading}
          className={cn(
            "w-full flex items-center justify-between px-3.5 py-2 bg-white border border-gray-200/60 rounded-lg text-[13px] font-medium transition-all hover:bg-gray-50/80",
            isLoading && "opacity-50 pointer-events-none"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn("w-6 h-6 rounded-md flex items-center justify-center", selectedDomain.bg)}>
              <selectedDomain.icon className={cn("w-3.5 h-3.5", selectedDomain.color)} />
            </div>
            <span className="text-gray-700">{selectedDomain.label} Mode</span>
          </div>
          <ChevronDown className={cn("w-3.5 h-3.5 text-gray-400 transition-transform duration-200", showDomainMenu && "rotate-180")} />
        </button>

        {showDomainMenu && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowDomainMenu(false)} />
            <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200/60 rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.04)] z-20 py-1.5 overflow-hidden animate-in fade-in slide-in-from-top-1">
              {domains.map((d) => (
                <button
                  key={d.id}
                  onClick={() => {
                    setDomain(d.id);
                    setShowDomainMenu(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-3 px-3.5 py-2 text-[13px] font-medium transition-colors hover:bg-gray-50",
                    domain === d.id ? "text-purple-600 bg-purple-50/50" : "text-gray-600"
                  )}
                >
                  <div className={cn("w-6 h-6 rounded flex items-center justify-center", d.bg)}>
                    <d.icon className={cn("w-3.5 h-3.5", d.color)} />
                  </div>
                  {d.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`Paste your ${domain} requirements here...`}
        className={cn(
          "w-full min-h-[160px] max-h-[220px] bg-[#F9F9F8] border border-gray-200/60 p-4 rounded-lg text-[13px] leading-relaxed",
          "focus:outline-none focus:ring-2 focus:ring-purple-500/10 focus:border-purple-500/30 transition-all",
          "resize-none placeholder:text-gray-400 text-gray-700 scrollbar-notion"
        )}
      />

      <FileUploadZone onFileLoaded={(content: string) => setText(content)} isLoading={isLoading} />

      <button
        onClick={handleExtract}
        disabled={isLoading || !text.trim()}
        className={cn(
          "w-full py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all text-[13px] font-semibold",
          "bg-purple-600 text-white hover:bg-purple-500 active:scale-[0.99] shadow-sm",
          "disabled:opacity-40 disabled:pointer-events-none disabled:shadow-none",
        )}
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <span>Process Extraction</span>
        )}
      </button>

      <div className="flex justify-between items-center px-1">
        <button
          onClick={handleSample}
          disabled={isLoading}
          className="text-[11px] font-medium text-gray-400 hover:text-purple-600 transition-colors disabled:pointer-events-none"
        >
          Use demo snippet
        </button>
        <span className="text-[9px] font-bold text-gray-300 uppercase tracking-widest opacity-80">Extraction System v2.1</span>
      </div>
    </div>
  );
}
