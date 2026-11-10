import React from 'react';
import { ThemeSwitch } from './ThemeSwitch';

interface HeaderProps {
  apiConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ apiConnected }) => {
  return (
    <header className="border-b border-line bg-surface sticky top-0 z-30">
      <div className="max-w-[1100px] mx-auto px-4 py-2.5 flex items-center justify-between gap-4">
        <div className="flex items-baseline gap-2.5">
          <span className="text-[16px] font-semibold text-text tracking-tight">
            Bima-Setu
          </span>
          <span className="text-[13px] text-muted">
            Claims intake
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-[12px] font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                apiConnected ? 'bg-[#48BB78]' : 'bg-[#E53E3E]'
              }`}
              aria-hidden="true"
            />
            <span className="text-muted">
              {apiConnected ? 'API connected' : 'API offline'}
            </span>
          </div>

          <ThemeSwitch />
        </div>
      </div>
    </header>
  );
};
