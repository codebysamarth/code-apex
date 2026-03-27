'use client';

import React from 'react';

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 h-[44px] border-b border-[rgba(55,53,47,0.09)] bg-white z-[100] px-4 flex items-center justify-between select-none">
      <div className="flex items-center gap-2 h-full">
        {/* Logo */}
        <div className="flex items-center gap-2 pr-3 border-r border-[rgba(55,53,47,0.06)] h-5">
           <div className="w-5 h-5 rounded bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white text-[10px] font-bold shadow-sm">A</div>
           <span className="text-[13px] font-semibold text-[rgba(55,53,47,1)] tracking-[-0.01em]">ApexBRD</span>
        </div>
        
        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 ml-2">
          <span className="text-[12px] text-[rgba(55,53,47,0.45)]">Workspace</span>
          <span className="text-[12px] text-[rgba(55,53,47,0.25)]">/</span>
          <span className="text-[12px] text-[rgba(55,53,47,0.65)] font-medium">Extraction Dashboard</span>
        </div>
      </div>

      <div className="flex items-center gap-3 h-full">
        {/* Search */}
        <button className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[12px] text-[rgba(55,53,47,0.5)] hover:bg-[rgba(55,53,47,0.04)] transition-colors border border-[rgba(55,53,47,0.09)]">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <span>Search</span>
          <kbd className="text-[10px] bg-[rgba(55,53,47,0.06)] px-1 py-0.5 rounded text-[rgba(55,53,47,0.35)] font-mono">⌘K</kbd>
        </button>

        {/* Status */}
        <div className="flex items-center gap-1.5 px-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[#1c7636]" />
          <span className="text-[11px] font-medium text-[rgba(55,53,47,0.45)]">Ready</span>
        </div>

        {/* Share */}
        <button className="px-3 py-1 rounded-md text-[12px] text-[rgba(55,53,47,0.65)] hover:bg-[rgba(55,53,47,0.04)] transition-colors font-medium">
          Share
        </button>

        {/* Menu */}
        <button className="p-1 rounded hover:bg-[rgba(55,53,47,0.04)] transition-colors">
          <svg className="w-4 h-4 text-[rgba(55,53,47,0.45)]" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" /></svg>
        </button>
      </div>
    </header>
  );
}
