'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lightbulb, Info, FileText, Check, Plus } from 'lucide-react';
import { Suggestion, MatchedBRD } from '@/lib/types';
import { cn } from '@/lib/utils';

interface SuggestionsPanelProps {
  suggestions?: Suggestion[];
  matchedBrds?: MatchedBRD[];
  isStandalone?: boolean;
}

export default function SuggestionsPanel({ suggestions, matchedBrds, isStandalone }: SuggestionsPanelProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!suggestions || suggestions.length === 0) {
    if (!isStandalone) return null;
    return (
      <div className={cn("px-6 md:px-20 py-20", isStandalone && "h-full flex items-center justify-center p-0")}>
        <div className="max-w-md text-center">
           <div className="w-16 h-16 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-6 text-indigo-400">
              <Lightbulb className="w-8 h-8 opacity-40" />
           </div>
           <h3 className="text-xl font-bold text-gray-900 mb-2">No Suggestions Yet</h3>
           <p className="text-sm text-gray-500 font-normal leading-relaxed">
             Our AI needs a requirements draft to compare against. Paste your project details and run a "Process Extraction" first to see predictive suggestions.
           </p>
        </div>
      </div>
    );
  }

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.7) return 'bg-emerald-500';
    if (score >= 0.4) return 'bg-amber-500';
    return 'bg-gray-400';
  };

  const getConfidenceBg = (score: number) => {
    if (score >= 0.7) return 'bg-emerald-50';
    if (score >= 0.4) return 'bg-amber-50';
    return 'bg-gray-50';
  };

  const getConfidenceText = (score: number) => {
    if (score >= 0.7) return 'text-emerald-700';
    if (score >= 0.4) return 'text-amber-700';
    return 'text-gray-500';
  };

  return (
    <div className={cn("mx-auto max-w-4xl px-6 md:px-20 pb-20", !isStandalone && "mt-16")}>
      <div className="bg-indigo-50/40 rounded-3xl border border-indigo-100/50 overflow-hidden shadow-sm">
        {/* Header */}
        <div className="p-8 border-b border-indigo-100/40 bg-white/40">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200">
                <Lightbulb className="w-5 h-4" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">AI Predictive Suggestions</h2>
                <p className="text-[12px] font-medium text-gray-500/80 uppercase tracking-wider">FAISS Knowledge Base Analysis</p>
              </div>
            </div>
            <div className="px-3 py-1 bg-white border border-indigo-100 rounded-full text-[11px] font-bold text-indigo-600 shadow-sm">
              {suggestions.length} suggestions
            </div>
          </div>
          <p className="text-[14px] text-gray-600 leading-relaxed font-normal italic">
            Based on similar past projects, we've identified requirements that may be missing from your current draft.
          </p>
        </div>

        {/* Similar Projects Section */}
        {matchedBrds && matchedBrds.length > 0 && (
          <div className="px-8 py-6 bg-white/20 border-b border-indigo-100/20">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest leading-none pt-0.5">Similar Projects Found</span>
            </div>
            <div className="flex flex-wrap gap-4">
              {matchedBrds.map((brd, i) => (
                <div key={i} className="bg-white/60 border border-indigo-50 px-4 py-2.5 rounded-xl flex flex-col gap-2 min-w-[200px] shadow-sm">
                  <div className="flex justify-between items-center gap-4">
                    <span className="text-[13px] font-bold text-gray-800 line-clamp-1">{brd.project_name}</span>
                    <span className="text-[10px] font-bold bg-indigo-50 text-indigo-500 px-1.5 py-0.5 rounded uppercase">{brd.domain}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${brd.similarity_score * 100}%` }}
                        className="h-full bg-indigo-500"
                        transition={{ duration: 1, ease: 'easeOut' }}
                      />
                    </div>
                    <span className="text-[11px] font-bold text-indigo-600 tabular-nums">
                      {Math.round(brd.similarity_score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggestions List */}
        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 gap-4">
            {suggestions.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="group relative p-6 bg-white border border-indigo-50 rounded-2xl shadow-sm hover:shadow-md hover:border-indigo-100 transition-all duration-200"
              >
                <div className="flex items-start justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-4">
                      {s.from_project === 'pattern_database' ? (
                        <span className="text-[10px] font-bold bg-amber-50 text-amber-600 px-2 py-0.5 rounded-md border border-amber-100/50 uppercase tracking-wider">
                          Industry Pattern
                        </span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-md border border-indigo-100/50 uppercase tracking-wider whitespace-nowrap">
                            Past Project Reference
                          </span>
                          <span className="text-[11px] font-medium text-gray-400 italic line-clamp-1">
                            from {s.from_project}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <p className="text-[15px] font-semibold text-gray-800 leading-relaxed mb-6">
                      {s.text}
                    </p>

                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Confidence</span>
                        <div className={cn("flex items-center gap-2 px-2.5 py-1 rounded-full", getConfidenceBg(s.confidence))}>
                          <div className={cn("w-2 h-2 rounded-full", getConfidenceColor(s.confidence))} />
                          <span className={cn("text-[11px] font-bold", getConfidenceText(s.confidence))}>
                            {Math.round(s.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleCopy(s.text, `s-${i}`)}
                    className={cn(
                      "shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-[12px] font-bold transition-all duration-200",
                      copiedId === `s-${i}`
                        ? "bg-emerald-500 text-white shadow-lg shadow-emerald-200"
                        : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-100"
                    )}
                  >
                    {copiedId === `s-${i}` ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        Add to BRD
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
          
          <div className="flex items-center gap-2 pt-2 text-[#37352F]/40">
             <Info className="w-3.5 h-3.5" />
             <span className="text-[11px] font-medium italic">Clicking "Add to BRD" copies the text to your clipboard for manual insertion.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
