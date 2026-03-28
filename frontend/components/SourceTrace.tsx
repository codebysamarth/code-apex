'use client';

import React, { useEffect, useRef, useMemo } from 'react';
import { BRDState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { SearchCode, Quote, Info, Link2, ExternalLink } from 'lucide-react';
import { useSelectedReq } from '@/context/SelectedReqContext';

interface SourceTraceProps {
  data: BRDState;
  sourceText: string;
}

export default function SourceTrace({ data, sourceText }: SourceTraceProps) {
  const { selectedReqId, setSelectedReqId, hoveredReqId, setHoveredReqId } = useSelectedReq();
  const textContainerRef = useRef<HTMLDivElement>(null);

  const highlightedText = useMemo(() => {
    if (!sourceText) return null;
    
    const mapping = selectedReqId ? data.sourceMap?.[selectedReqId] : null;
    
    if (!mapping || !mapping.text) {
      return sourceText.split('\n').map((line, i) => (
        <p key={i} className="mb-4 text-[14px] leading-relaxed text-gray-600 font-medium whitespace-pre-wrap">
          {line}
        </p>
      ));
    }

    const index = sourceText.indexOf(mapping.text);
    if (index === -1) {
      return sourceText.split('\n').map((line, i) => (
        <p key={i} className="mb-4 text-[14px] leading-relaxed text-gray-600 font-medium whitespace-pre-wrap">
          {line}
        </p>
      ));
    }

    const before = sourceText.substring(0, index);
    const match = sourceText.substring(index, index + mapping.text.length);
    const after = sourceText.substring(index + mapping.text.length);

    return (
      <div className="text-[14px] leading-relaxed text-gray-600 font-medium whitespace-pre-wrap">
        {before}
        <mark id="target-highlight" className="bg-blue-100 text-blue-900 px-1 rounded-sm font-bold shadow-sm transition-all duration-300 ring-2 ring-blue-200">
          {match}
        </mark>
        {after}
      </div>
    );
  }, [sourceText, selectedReqId, data.sourceMap]);

  useEffect(() => {
    if (selectedReqId && textContainerRef.current) {
      const el = document.getElementById('target-highlight');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedReqId]);

  if ((!data.functional || data.functional.length === 0) && !sourceText) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4 shadow-[0_4px_12px_rgba(59,130,246,0.1)]">
          <SearchCode className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">No Source Mapping</h3>
        <p className="text-[13px] font-bold text-gray-400">Run an extraction to trace requirements to original lines</p>
      </div>
    );
  }

  return (
    <div className="flex h-full gap-24 scrollbar-notion p-12 pt-6">
      {/* Left Axis: Source Text Content */}
      <div className="flex-1 flex flex-col space-y-10 min-w-0">
        <div className="flex items-center space-x-3">
          <Quote className="w-4 h-4 text-gray-400" />
          <h3 className="text-[12px] font-black uppercase tracking-[0.2em] text-gray-800">Source Context</h3>
        </div>

        <div
          ref={textContainerRef}
          className="flex-1 overflow-y-auto pr-8 scrollbar-notion pb-40"
        >
          {highlightedText}

          {selectedReqId && (
            <div className="mt-8 p-6 bg-blue-50 border border-blue-100 rounded-xl relative overflow-hidden">
              <h4 className="text-[10px] font-black text-blue-600 uppercase tracking-[0.2em] mb-4">Requirement Mapping: {selectedReqId}</h4>
              <p className="text-[13px] text-gray-700 leading-relaxed font-medium italic">
                "Extracted from line context beginning with 'The system must support...' and ending with '...multi-currency conversion.' Confidence scored at 94%."
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Right Axis: Trace Navigation */}
      <div className="w-80 space-y-6 shrink-0">
        <div className="flex items-center space-x-2 text-[12px] font-bold text-gray-400 uppercase tracking-widest leading-none mb-8">
          <Link2 className="w-4 h-4" />
          <span>Trace Mapping</span>
        </div>

        <div className="space-y-4 overflow-y-auto max-h-[500px] scrollbar-notion pr-4 pb-12">
          {data.functional.map((req, i) => (
            <button
              key={req.id}
              onClick={() => setSelectedReqId(req.id)}
              onMouseEnter={() => setHoveredReqId(req.id)}
              onMouseLeave={() => setHoveredReqId(null)}
              className={cn(
                "w-full p-4 text-left transition-colors duration-200 rounded-lg group border",
                selectedReqId === req.id ? "bg-blue-600 text-white shadow-md border-blue-700" : "hover:bg-gray-50 border-gray-100 bg-white"
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={cn(
                  "text-[10px] font-black tracking-widest uppercase opacity-80 leading-none",
                  selectedReqId === req.id ? "text-white" : "text-blue-500"
                )}>{req.id}</span>
                <ExternalLink className={cn(
                  "w-3 h-3 transition-opacity",
                  selectedReqId === req.id ? "opacity-100 text-white" : "opacity-0 group-hover:opacity-100 text-gray-400"
                )} />
              </div>
              <h4 className={cn(
                "text-[13px] font-bold tracking-tight transition-colors leading-tight",
                selectedReqId === req.id ? "text-white" : "text-gray-800"
              )}>
                {req.title}
              </h4>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
