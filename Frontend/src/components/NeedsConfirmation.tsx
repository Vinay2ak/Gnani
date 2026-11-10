import React from 'react';

interface NeedsConfirmationProps {
  questions: string[];
}

export const NeedsConfirmation: React.FC<NeedsConfirmationProps> = ({ questions }) => {
  if (questions.length === 0) return null;

  return (
    <section className="border-l-[3px] border-accent bg-panel/30 py-2.5 px-3.5 space-y-1">
      <h3 className="text-[13px] font-semibold text-muted">
        Needs confirmation
      </h3>
      <ul className="space-y-0.5 text-[13px] text-text">
        {questions.map((q, idx) => (
          <li key={idx} className="leading-relaxed">
            {q}
          </li>
        ))}
      </ul>
    </section>
  );
};

