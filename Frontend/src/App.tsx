import React, { useState, useEffect } from 'react';
import { Claim } from './types';
import { fetchClaims, uploadClaim } from './api';
import { Header, ConnectionStatus } from './components/Header';
import { IntakePanel } from './components/IntakePanel';
import { ClaimCard } from './components/ClaimCard';

export const App: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 3-second polling of GET /claims with responsive 2.5s abort timeout
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2500);
        const data = await fetchClaims(controller.signal);
        clearTimeout(timeoutId);
        if (isMounted) {
          // Present claims newest first
          setClaims([...data].reverse());
          setConnectionStatus('connected');
        }
      } catch {
        if (isMounted) {
          setConnectionStatus('disconnected');
        }
      }
    };

    poll();
    const interval = setInterval(poll, 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleUpload = async (file: File, phone?: string) => {
    setIsUploading(true);
    setErrorMessage(null);

    try {
      const created = await uploadClaim(file, phone);
      setClaims((prev) => [created, ...prev]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Intake failed';
      setErrorMessage(msg);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const handleClaimUpdated = (updated: Claim) => {
    setClaims((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  };

  return (
    <div className="min-h-screen bg-bg text-text">
      <Header connectionStatus={connectionStatus} />

      <main className="max-w-[1100px] mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 items-start">
          {/* Left Column: Intake Panel (sticky from 1024px) */}
          <aside>
            <IntakePanel
              onUpload={handleUpload}
              isUploading={isUploading}
              errorMessage={errorMessage}
              onClearError={() => setErrorMessage(null)}
            />
          </aside>

          {/* Right Column: Claim Queue */}
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-2 mb-2">
              <h1 className="text-[16px] font-semibold text-text tracking-tight">
                Claim Queue
              </h1>
              <span className="font-mono text-[12px] text-muted">
                {claims.length} {claims.length === 1 ? 'case' : 'cases'}
              </span>
            </div>

            {claims.length === 0 ? (
              <div className="py-12 text-center text-muted text-[13px]">
                No claims submitted yet.
              </div>
            ) : (
              claims.map((claim) => (
                <ClaimCard
                  key={claim.id}
                  claim={claim}
                  onClaimUpdated={handleClaimUpdated}
                />
              ))
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

export default App;
