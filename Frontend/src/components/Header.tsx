import React from 'react';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
}

export const Header: React.FC<HeaderProps> = ({ connectionStatus }) => {
  return (
    <header className="border-b border-line bg-surface sticky top-0 z-30">
      <div className="max-w-[1100px] mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <span className="text-[17px] font-semibold text-text tracking-tight">
            Bima-Setu
          </span>
          <span className="text-[13px] text-muted">
            FNOL intake console
          </span>
        </div>
        <div className="flex items-center text-[13px]">
          {connectionStatus === 'connected' && (
            <span className="text-[#48BB78] font-mono text-[12px] font-medium tracking-tight">
              Connected
            </span>
          )}
          {connectionStatus === 'disconnected' && (
            <span className="text-[#FC8181] font-mono text-[12px] font-medium tracking-tight">
              Not connected
            </span>
          )}
          {connectionStatus === 'connecting' && (
            <span className="text-muted font-mono text-[12px] tracking-tight">
              Connecting...
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
