import React from 'react';
import { FNOL, TriState } from '../types';
import { IndexedQuote } from '../utils/evidence';

interface FindingsTableProps {
  fnol: FNOL;
  quotes: IndexedQuote[];
}

export const FindingsTable: React.FC<FindingsTableProps> = ({ fnol, quotes }) => {
  const quoteMap = new Map<string, number>();
  for (const q of quotes) {
    quoteMap.set(q.text.trim(), q.index);
  }

  const renderResultChip = (field: 'drivable' | 'towing' | 'injury', val: TriState) => {
    if (val === 'UNKNOWN') {
      return (
        <span className="border border-dotted border-line text-muted bg-panel px-2 py-0.5 rounded-[4px] text-[12px]">
          Not stated
        </span>
      );
    }

    if (field === 'drivable') {
      if (val === 'FALSE') {
        return (
          <span className="border border-accent text-text px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
            Not drivable
          </span>
        );
      }
      return (
        <span className="border border-tag text-tag px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
          Drivable
        </span>
      );
    }

    if (field === 'towing') {
      if (val === 'TRUE') {
        return (
          <span className="border border-accent text-text px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
            Towing required
          </span>
        );
      }
      return (
        <span className="border border-tag text-tag px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
          No tow needed
        </span>
      );
    }

    // third party / injury
    if (val === 'TRUE') {
      return (
        <span className="border border-accent text-text px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
          Reported
        </span>
      );
    }
    return (
      <span className="border border-tag text-tag px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
        None
      </span>
    );
  };

  const renderSourceCell = (quoteText: string | undefined) => {
    const trimmed = quoteText?.trim();
    if (!trimmed) {
      return <span className="text-muted/60">—</span>;
    }
    const idx = quoteMap.get(trimmed);
    if (!idx) {
      return <span className="text-muted/60">—</span>;
    }

    return (
      <div className="relative inline-block group">
        <button
          type="button"
          tabIndex={0}
          className="font-mono text-[11px] text-link hover:underline focus:underline cursor-help"
          aria-label={`Evidence quote ${idx}: "${trimmed}"`}
        >
          [{idx}]
        </button>
        {/* Tooltip on hover and keyboard focus */}
        <div
          role="tooltip"
          className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 hidden group-hover:block group-focus-within:block z-20 w-max max-w-[280px] p-2 bg-surface border border-line text-text text-[12px] rounded-[4px] whitespace-normal italic font-devanagari pointer-events-none"
        >
          "{trimmed}"
        </div>
      </div>
    );
  };

  return (
    <section className="space-y-4">
      <div>
        <h3 className="text-[13px] font-semibold text-muted mb-2">
          Findings
        </h3>
        <div className="border border-line rounded-[4px] overflow-hidden">
          <table className="w-full text-left text-[13px] border-collapse">
            <thead>
              <tr className="bg-panel border-b border-line text-muted text-[12px]">
                <th className="py-2 px-3 font-semibold w-1/3">Finding</th>
                <th className="py-2 px-3 font-semibold w-1/3">Result</th>
                <th className="py-2 px-3 font-semibold w-1/3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60 bg-surface">
              <tr>
                <td className="py-2 px-3 font-medium text-text">Vehicle drivable</td>
                <td className="py-2 px-3">{renderResultChip('drivable', fnol.vehicle_drivable)}</td>
                <td className="py-2 px-3">{renderSourceCell(fnol.vehicle_drivable_evidence)}</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium text-text">Towing required</td>
                <td className="py-2 px-3">{renderResultChip('towing', fnol.towing_required)}</td>
                <td className="py-2 px-3">{renderSourceCell(fnol.towing_evidence)}</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium text-text">Third party / injury</td>
                <td className="py-2 px-3">{renderResultChip('injury', fnol.third_party_or_injury)}</td>
                <td className="py-2 px-3">{renderSourceCell(fnol.third_party_evidence)}</td>
              </tr>
              {Array.isArray(fnol.damage_zones) &&
                fnol.damage_zones.map((dz, i) => (
                  <tr key={`dz-${dz.zone}-${i}`}>
                    <td className="py-2 px-3 font-medium text-text">{dz.zone}</td>
                    <td className="py-2 px-3">
                      <span className="border border-tag text-tag px-2 py-0.5 rounded-[4px] text-[12px] font-medium">
                        Damaged
                      </span>
                    </td>
                    <td className="py-2 px-3">{renderSourceCell(dz.evidence)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Under the table: Quotes from the call */}
      <div>
        <h4 className="text-[13px] font-semibold text-muted mb-1.5">
          Quotes from the call
        </h4>
        {quotes.length === 0 ? (
          <div className="text-[13px] text-muted italic">
            No quotes identified
          </div>
        ) : (
          <ol className="space-y-1 text-[13px] text-text font-devanagari">
            {quotes.map((q) => (
              <li key={`quote-${q.index}`} className="flex items-baseline gap-2">
                <span className="font-mono text-[11px] text-muted select-none w-5">
                  [{q.index}]
                </span>
                <span className="italic">"{q.text}"</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
};

