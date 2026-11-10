import React from 'react';
import { Claim } from '../types';
import { getQueueVerdictLine } from '../utils/verdict';

interface ClaimsQueueProps {
  claims: Claim[];
  selectedClaimId: string | null;
  onSelectClaim: (claimId: string) => void;
}

export const ClaimsQueue: React.FC<ClaimsQueueProps> = ({
  claims,
  selectedClaimId,
  onSelectClaim,
}) => {
  return (
    <aside className="border-r border-line/60 bg-surface min-h-[400px]">
      <div className="px-3.5 py-2.5 border-b border-line flex items-center justify-between">
        <h2 className="text-[13px] font-semibold text-muted">
          Open claims
        </h2>
        <span className="font-mono text-[11px] text-muted">
          {claims.length}
        </span>
      </div>

      {claims.length === 0 ? (
        <div className="p-4 text-[13px] text-muted">
          No claims available.
        </div>
      ) : (
        <ul className="divide-y divide-line/40">
          {claims.map((claim) => {
            const isSelected = claim.id === selectedClaimId;
            const verdictLine = getQueueVerdictLine(claim.fnol);
            const holder = claim.policy?.holder_name || 'Unknown driver';
            const statusLabel =
              claim.status === 'approved' ? 'Approved' : 'Pending review';

            return (
              <li key={claim.id}>
                <button
                  type="button"
                  onClick={() => onSelectClaim(claim.id)}
                  className={`w-full text-left px-3.5 py-3 transition-colors cursor-pointer select-none border-l-2 ${
                    isSelected
                      ? 'border-link bg-panel text-text'
                      : 'border-transparent hover:bg-panel/30 text-text'
                  }`}
                  aria-current={isSelected ? 'true' : undefined}
                >
                  <div className="flex items-center justify-between gap-1 text-[12px] mb-1">
                    <span className="font-mono text-[12px] font-semibold">
                      {claim.id}
                    </span>
                    <span
                      className={`text-[11px] ${
                        claim.status === 'approved'
                          ? 'text-tag font-medium'
                          : 'text-muted'
                      }`}
                    >
                      {statusLabel}
                    </span>
                  </div>

                  <div className="text-[13px] font-medium text-text truncate mb-0.5">
                    {holder}
                  </div>

                  {verdictLine && (
                    <div className="text-[12px] text-muted truncate">
                      {verdictLine}
                    </div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
};

