import React, { useEffect, useState } from 'react';
import { ThemeMode } from '../types';

export const ThemeSwitch: React.FC = () => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    try {
      const saved = localStorage.getItem('bs-theme');
      if (saved === 'light' || saved === 'dark' || saved === 'system') {
        return saved;
      }
    } catch {
      // ignore
    }
    return 'system';
  });

  const applyTheme = (targetMode: ThemeMode) => {
    let resolved = targetMode;
    if (targetMode === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    }
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.style.colorScheme = resolved;
  };

  useEffect(() => {
    applyTheme(mode);
    try {
      localStorage.setItem('bs-theme', mode);
    } catch {
      // ignore
    }

    if (mode === 'system') {
      const mql = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = (e: MediaQueryListEvent) => {
        const resolved = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', resolved);
        document.documentElement.style.colorScheme = resolved;
      };
      mql.addEventListener('change', handler);
      return () => mql.removeEventListener('change', handler);
    }
  }, [mode]);

  const handleSelect = (selected: ThemeMode) => {
    setMode(selected);
  };

  return (
    <div
      role="group"
      aria-label="Theme selection"
      className="inline-flex items-center border border-line rounded-[4px] bg-surface p-0.5 text-[12px]"
    >
      <button
        type="button"
        onClick={() => handleSelect('light')}
        className={`px-2 py-0.5 rounded-[4px] font-medium transition-colors ${
          mode === 'light'
            ? 'bg-panel text-text'
            : 'text-muted hover:text-text'
        }`}
        aria-pressed={mode === 'light'}
      >
        Light
      </button>
      <button
        type="button"
        onClick={() => handleSelect('dark')}
        className={`px-2 py-0.5 rounded-[4px] font-medium transition-colors ${
          mode === 'dark'
            ? 'bg-panel text-text'
            : 'text-muted hover:text-text'
        }`}
        aria-pressed={mode === 'dark'}
      >
        Dark
      </button>
      <button
        type="button"
        onClick={() => handleSelect('system')}
        className={`px-2 py-0.5 rounded-[4px] font-medium transition-colors ${
          mode === 'system'
            ? 'bg-panel text-text'
            : 'text-muted hover:text-text'
        }`}
        aria-pressed={mode === 'system'}
      >
        System
      </button>
    </div>
  );
};

