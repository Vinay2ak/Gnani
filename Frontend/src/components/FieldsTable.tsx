import React from 'react';
import { FNOL, TriState } from '../types';

interface FieldsTableProps {
  fnol: FNOL;
}

interface RowDef {
  label: string;
  value: TriState;
  evidence: string;
  renderValue: (val: TriState) => React.ReactNode;
}

export const FieldsTable: React.FC<FieldsTableProps> = ({ fnol }) => {
  const rows: RowDef[] = [
    {
      label: 'Vehicle drivable',
      value: fnol.vehicle_drivable,
      evidence: fnol.vehicle_drivable_evidence,
      renderValue: (val: TriState) => {
        if (val === 'TRUE') {
          return (
            <span className="border border-tag text-tag px-2 py-0.5 rounded-chip text-[12px] font-medium">
              Drivable
            </span>
          );
        }
        if (val === 'FALSE') {
          return (
            <span className="border border-accent text-accent px-2 py-0.5 rounded-chip text-[12px] font-medium">
              Not drivable
            </span>
          );
        }
        return (
          <span className="border border-line text-muted px-2 py-0.5 rounded-chip text-[12px]">
            Not stated
          </span>
        );
      },
    },
    {
      label: 'Towing required',
      value: fnol.towing_required,
      evidence: fnol.towing_evidence,
      renderValue: (val: TriState) => {
        if (val === 'TRUE') {
          return (
            <span className="border border-accent text-accent px-2 py-0.5 rounded-chip text-[12px] font-medium">
              Towing required
            </span>
          );
        }
        if (val === 'FALSE') {
          return (
            <span className="border border-tag text-tag px-2 py-0.5 rounded-chip text-[12px] font-medium">
              No tow needed
            </span>
          );
        }
        return (
          <span className="border border-line text-muted px-2 py-0.5 rounded-chip text-[12px]">
            Not stated
          </span>
        );
      },
    },
    {
      label: 'Third party / injury',
      value: fnol.third_party_or_injury,
      evidence: fnol.third_party_evidence,
      renderValue: (val: TriState) => {
        if (val === 'TRUE') {
          return (
            <span className="border border-accent text-accent px-2 py-0.5 rounded-chip text-[12px] font-medium">
              Reported
            </span>
          );
        }
        if (val === 'FALSE') {
          return (
            <span className="border border-tag text-tag px-2 py-0.5 rounded-chip text-[12px] font-medium">
              None
            </span>
          );
        }
        return (
          <span className="border border-line text-muted px-2 py-0.5 rounded-chip text-[12px]">
            Not stated
          </span>
        );
      },
    },
  ];

  return (
    <div className="border border-line rounded-chip overflow-hidden">
      <table className="w-full text-left text-[13px] border-collapse">
        <thead>
          <tr className="bg-panel border-b border-line text-muted text-[12px]">
            <th className="py-2 px-3 font-semibold w-1/4">Field</th>
            <th className="py-2 px-3 font-semibold w-1/4">Value</th>
            <th className="py-2 px-3 font-semibold w-1/2">Evidence quote</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line bg-surface">
          {rows.map((row) => (
            <tr key={row.label} className="hover:bg-panel/30">
              <td className="py-2 px-3 font-medium text-text">{row.label}</td>
              <td className="py-2 px-3">{row.renderValue(row.value)}</td>
              <td className="py-2 px-3 text-muted">
                {row.evidence && row.evidence.trim() ? (
                  <span className="text-text/90 italic">
                    "{row.evidence.trim()}"
                  </span>
                ) : (
                  <span className="text-muted/60">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

