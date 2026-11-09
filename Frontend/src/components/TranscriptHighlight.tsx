import React, { useMemo } from 'react';

interface TranscriptHighlightProps {
  transcript: string;
  quotes: (string | undefined | null)[];
}

interface Interval {
  start: number;
  end: number;
}

export const TranscriptHighlight: React.FC<TranscriptHighlightProps> = ({
  transcript,
  quotes,
}) => {
  const renderedContent = useMemo(() => {
    if (!transcript) {
      return <span className="text-muted italic">No transcript available</span>;
    }

    // Collect all valid quotes
    const validQuotes = quotes
      .filter((q): q is string => typeof q === 'string' && q.trim().length > 0)
      .map((q) => q.trim());

    if (validQuotes.length === 0) {
      return <span>{transcript}</span>;
    }

    // Find all exact occurrences of each quote in the transcript
    const rawIntervals: Interval[] = [];
    for (const quote of validQuotes) {
      let startIndex = 0;
      while (startIndex < transcript.length) {
        const foundIndex = transcript.indexOf(quote, startIndex);
        if (foundIndex === -1) break;
        rawIntervals.push({
          start: foundIndex,
          end: foundIndex + quote.length,
        });
        startIndex = foundIndex + Math.max(1, quote.length);
      }
    }

    if (rawIntervals.length === 0) {
      return <span>{transcript}</span>;
    }

    // Sort intervals by start ascending
    rawIntervals.sort((a, b) => a.start - b.start || b.end - a.end);

    // Merge overlapping and contiguous intervals
    const merged: Interval[] = [rawIntervals[0]];
    for (let i = 1; i < rawIntervals.length; i++) {
      const current = rawIntervals[i];
      const prev = merged[merged.length - 1];

      if (current.start <= prev.end) {
        prev.end = Math.max(prev.end, current.end);
      } else {
        merged.push({ ...current });
      }
    }

    // Build segment nodes
    const nodes: React.ReactNode[] = [];
    let lastIndex = 0;

    merged.forEach((interval, idx) => {
      if (interval.start > lastIndex) {
        nodes.push(
          <span key={`plain-${lastIndex}`}>
            {transcript.slice(lastIndex, interval.start)}
          </span>
        );
      }
      nodes.push(
        <mark
          key={`mark-${idx}-${interval.start}`}
          className="text-text font-normal rounded-none px-0.5"
          style={{
            backgroundColor: 'rgba(244, 166, 42, 0.22)',
            borderBottom: '2px solid #F4A62A',
          }}
        >
          {transcript.slice(interval.start, interval.end)}
        </mark>
      );
      lastIndex = interval.end;
    });

    if (lastIndex < transcript.length) {
      nodes.push(
        <span key={`plain-${lastIndex}`}>
          {transcript.slice(lastIndex)}
        </span>
      );
    }

    return nodes;
  }, [transcript, quotes]);

  return (
    <div className="bg-panel/40 border border-line rounded-chip p-3 text-[13px] leading-relaxed text-text">
      <div className="text-[11px] font-mono uppercase tracking-wider text-muted mb-1.5">
        Caller Transcript
      </div>
      <p className="whitespace-pre-wrap">{renderedContent}</p>
    </div>
  );
};

