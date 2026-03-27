'use client';

import React, { useCallback, useState } from 'react';

interface FileUploadZoneProps {
  onFileLoaded: (content: string) => void;
  isLoading: boolean;
}

export default function FileUploadZone({ onFileLoaded, isLoading }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setFileName(file.name);
      onFileLoaded("Extracted from " + file.name);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`py-4 border border-dashed rounded-md flex items-center justify-center cursor-pointer transition-all ${
        isDragging
          ? 'border-[#2383e2] bg-[rgba(35,131,226,0.04)]'
          : 'border-[rgba(55,53,47,0.12)] hover:border-[rgba(55,53,47,0.25)] hover:bg-[rgba(55,53,47,0.02)]'
      } ${isLoading ? 'pointer-events-none opacity-40' : ''}`}
    >
      <div className="flex items-center gap-2 text-[12px] text-[rgba(55,53,47,0.45)]">
        <span>📎</span>
        <span>{fileName || 'Drop a file here'}</span>
      </div>
    </div>
  );
}
