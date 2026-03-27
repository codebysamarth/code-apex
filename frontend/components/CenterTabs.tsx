'use client';

import React, { useState } from 'react';
import { BRDState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import BRDOutput from './BRDOutput';
import Analytics from './Analytics';
import Timeline from './Timeline';
import Priorities from './Priorities';
import SourceTrace from './SourceTrace';

interface CenterTabsProps {
  data: BRDState;
  sourceText: string;
}

const tabs = [
  { id: 'brd', label: 'Requirements', emoji: '📋' },
  { id: 'analytics', label: 'Analytics', emoji: '📊' },
  { id: 'timeline', label: 'Roadmap', emoji: '🗓️' },
  { id: 'priorities', label: 'Strategy', emoji: '🎯' },
  { id: 'trace', label: 'Source Trace', emoji: '🔗' },
];

export default function CenterTabs({ data, sourceText }: CenterTabsProps) {
  const [activeTab, setActiveTab] = useState('brd');

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-[rgba(55,53,47,0.09)] overflow-hidden">
      {/* Notion-style Tab Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-[rgba(55,53,47,0.06)] shrink-0 select-none bg-white">
        <div className="flex items-center gap-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors",
                activeTab === tab.id 
                  ? "bg-[rgba(55,53,47,0.08)] text-[rgba(55,53,47,1)]" 
                  : "text-[rgba(55,53,47,0.45)] hover:bg-[rgba(55,53,47,0.04)] hover:text-[rgba(55,53,47,0.65)]"
              )}
            >
              <span className="text-[14px]">{tab.emoji}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[rgba(55,53,47,0.09)] text-[12px] text-[rgba(55,53,47,0.5)] hover:bg-[rgba(55,53,47,0.04)] transition-colors font-medium">
          <span>↓</span>
          <span>Export</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-notion bg-white">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {activeTab === 'brd' && <BRDOutput data={data} />}
            {activeTab === 'analytics' && <Analytics data={data.analytics} />}
            {activeTab === 'timeline' && <Timeline data={data.timeline} />}
            {activeTab === 'priorities' && <Priorities priorities={data.priorities} functional={data.functional} />}
            {activeTab === 'trace' && <SourceTrace data={data} sourceText={sourceText} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
