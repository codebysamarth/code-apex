'use client';

import React, { useState, useEffect } from 'react';
import { Brain, Database, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FaissStatsBadgeProps {
  refreshTrigger?: number;
}

interface FaissStats {
  total_brds: number;
  per_domain: Record<string, number>;
}

export default function FaissStatsBadge({ refreshTrigger }: FaissStatsBadgeProps) {
  const [stats, setStats] = useState<FaissStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/faiss-stats');
      if (!res.ok) throw new Error('Failed to fetch stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('FAISS Stats Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [refreshTrigger]);

  if (!stats) return null;

  return (
    <div className="flex items-center gap-2.5 px-4 py-2 bg-indigo-50/50 rounded-xl border border-indigo-100/50 shadow-sm shadow-indigo-500/5 group cursor-help transition-all duration-300 hover:bg-white hover:border-indigo-200">
      <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-100 group-hover:bg-indigo-700 transition-colors">
        <Brain className="w-4 h-4" />
      </div>
      <div>
        <div className="flex items-center gap-1.5 leading-none mb-0.5">
           <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest leading-none">Knowledge Base</span>
           {loading && <RefreshCw className="w-2.5 h-2.5 text-indigo-300 animate-spin" />}
        </div>
        <p className="text-[13px] font-bold text-gray-800 leading-tight tabular-nums">
          {stats.total_brds} <span className="text-gray-400 font-medium ml-0.5">Projects Indexed</span>
        </p>
      </div>
    </div>
  );
}
