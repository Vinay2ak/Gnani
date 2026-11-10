import React, { useState, useEffect } from 'react';
import { Claim } from './types';
import { fetchClaims, uploadClaim } from './api';
import { Header } from './components/Header';
import { IntakeRow } from './components/IntakeRow';
import { ClaimsQueue } from './components/ClaimsQueue';
import { CaseFile } from './components/CaseFile';

export const App: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 3-second heartbeat polling of GET /claims
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2500);
        const data = await fetchClaims(controller.signal);
        clearTimeout(timeoutId);

        if (isMounted) {
          // Newest claims first
          const reversed = [...data].reverse();
          setClaims(reversed);
          setApiConnected(true);

          // Select newest claim by default if none selected or previous selection no longer exists
          setSelectedClaimId((prev) => {
            if (prev && reversed.some((c) => c.id === prev)) {
              return prev;
            }
            return reversed.length > 0 ? reversed[0].id : null;
          });
        }
      } catch {
        if (isMounted) {
          setApiConnected(false);
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
      // Select the newly uploaded claim immediately
      setSelectedClaimId(created.id);
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

  const selectedClaim = claims.find((c) => c.id === selectedClaimId) || null;

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col justify-between">
      <div>
        <Header apiConnected={apiConnected} />
        <IntakeRow
          onUpload={handleUpload}
          isUploading={isUploading}
          errorMessage={errorMessage}
          onClearError={() => setErrorMessage(null)}
        />

        <main className="max-w-[1100px] mx-auto px-4 py-5">
          <div className="border border-line rounded-[4px] bg-surface overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr]">
              <ClaimsQueue
                claims={claims}
                selectedClaimId={selectedClaimId}
                onSelectClaim={setSelectedClaimId}
              />

              <div className="min-h-[500px]">
                {selectedClaim ? (
                  <CaseFile
                    claim={selectedClaim}
                    onClaimUpdated={handleClaimUpdated}
                  />
                ) : (
                  <div className="p-12 text-center text-muted text-[13px]">
                    No claims submitted yet. Use the intake row above to start.
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      <footer className="border-t border-line/60 bg-surface/40 py-3 text-center text-[12px] text-muted">
        Synthetic demo data. A human adjuster approves every claim.
      </footer>
    </div>
  );
};

export default App;
