'use client';

import React, { useState } from 'react';
import { sampleText } from '@/lib/samples';
import { cn } from '@/lib/utils';
import FileUploadZone from './FileUploadZone';

interface InputPanelProps {
  onExtract: (text: string) => void;
  isLoading: boolean;
}

export default function InputPanel({ onExtract, isLoading }: InputPanelProps) {
  const [text, setText] = useState('');

  const handleSample = () => setText(sampleText);

  const handleExtract = () => {
    if (!text.trim() || isLoading) return;
    onExtract(text);
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste your PRD, specification, or requirements document here..."
        className={cn(
          "w-full min-h-[160px] bg-[#f7f7f5] border border-gray-100 p-3 rounded-lg text-sm leading-relaxed",
          "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all",
          "resize-none placeholder:text-gray-400 text-gray-800 scrollbar-notion shadow-inner"
        )}
      />

      <FileUploadZone onFileLoaded={(content: string) => setText(content)} isLoading={isLoading} />

      <button
        onClick={handleExtract}
        disabled={isLoading || !text.trim()}
        className={cn(
          "w-full py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all text-sm font-bold shadow-[0_4px_12px_rgba(59,130,246,0.25)]",
          "bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.98]",
          "disabled:opacity-30 disabled:pointer-events-none disabled:shadow-none",
        )}
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <span>Extract Requirements &rarr;</span>
        )}
      </button>

      <div className="flex justify-between items-center mt-1">
        <button
          onClick={handleSample}
          disabled={isLoading}
          className="text-xs font-bold text-gray-400 hover:text-blue-500 transition-colors disabled:pointer-events-none"
        >
          Load preview sample
        </button>
        <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wide">Model: GPT-4 Turbo</span>
      </div>
    </div>
  );
}
