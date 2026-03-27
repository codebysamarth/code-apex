'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SelectedReqContextType {
  selectedReqId: string | null;
  setSelectedReqId: (id: string | null) => void;
  hoveredReqId: string | null;
  setHoveredReqId: (id: string | null) => void;
}

const SelectedReqContext = createContext<SelectedReqContextType | undefined>(undefined);

export function SelectedReqProvider({ children }: { children: ReactNode }) {
  const [selectedReqId, setSelectedReqId] = useState<string | null>(null);
  const [hoveredReqId, setHoveredReqId] = useState<string | null>(null);

  return (
    <SelectedReqContext.Provider value={{ selectedReqId, setSelectedReqId, hoveredReqId, setHoveredReqId }}>
      {children}
    </SelectedReqContext.Provider>
  );
}

export function useSelectedReq() {
  const context = useContext(SelectedReqContext);
  if (context === undefined) {
    throw new Error('useSelectedReq must be used within a SelectedReqProvider');
  }
  return context;
}
