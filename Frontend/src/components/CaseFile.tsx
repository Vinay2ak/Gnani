import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Claim } from '../types';
import { approveClaim, fetchReadbackAudio } from '../api';
import { getVerdictSentence, getConfirmationQuestions } from '../utils/verdict';
import { extractDistinctQuotes, buildTranscriptIntervals } from '../utils/evidence';
import { NeedsConfirmation } from './NeedsConfirmation';
import { FindingsTable } from './FindingsTable';

interface CaseFileProps {
  claim: Claim;
  onClaimUpdated: (updated: Claim) => void;
}

export const CaseFile: React.FC<CaseFileProps> = ({ claim, onClaimUpdated }) => {
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [selectedVoice, setSelectedVoice] = useState<'Nalini' | 'Gaurav' | 'Vikrant'>('Nalini');
  const [actionError, setActionError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<Record<string, string>>({});

  // Cleanup audio urls on unmount or claim switch
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      Object.values(audioUrlRef.current).forEach((url) => {
        try {
          URL.revokeObjectURL(url);
        } catch {
          // Ignore
        }
      });
      audioUrlRef.current = {};
    };
  }, [claim.id]);

  const verdictSentence = useMemo(
    () => getVerdictSentence(claim.fnol),
    [claim.fnol]
  );

  const confirmationQuestions = useMemo(
    () => getConfirmationQuestions(claim.fnol),
    [claim.fnol]
  );

  const distinctQuotes = useMemo(
    () => extractDistinctQuotes(claim.fnol),
    [claim.fnol]
  );

  const intervals = useMemo(
    () => buildTranscriptIntervals(claim.transcript, distinctQuotes),
    [claim.transcript, distinctQuotes]
  );

  const handleApprove = async () => {
    if (claim.status !== 'pending' || isApproving) return;
    setActionError(null);
    try {
      setIsApproving(true);
      const updated = await approveClaim(claim.id);
      onClaimUpdated(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Approval failed';
      setActionError(msg);
    } finally {
      setIsApproving(false);
    }
  };

  const handlePlayReadback = async () => {
    setActionError(null);

    // If currently playing, pause it
    if (isPlayingAudio && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
      return;
    }

    // Replay cached audio if already fetched for selected voice
    const cachedUrl = audioUrlRef.current[selectedVoice];
    if (cachedUrl) {
      try {
        if (audioRef.current) {
          audioRef.current.pause();
        }
        const audio = new Audio(cachedUrl);
        audioRef.current = audio;

        audio.onended = () => {
          setIsPlayingAudio(false);
        };
        audio.onerror = () => {
          setIsPlayingAudio(false);
          setActionError('Failed to playback audio confirmation');
        };

        await audio.play();
        setIsPlayingAudio(true);
        return;
      } catch (e) {
        console.error(e);
      }
    }

    try {
      setIsLoadingAudio(true);
      const blob = await fetchReadbackAudio(claim.id, selectedVoice);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current[selectedVoice] = url;

      if (audioRef.current) {
        audioRef.current.pause();
      }
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingAudio(false);
      };
      audio.onerror = () => {
        setIsPlayingAudio(false);
        setActionError('Failed to playback audio confirmation');
      };

      await audio.play();
      setIsPlayingAudio(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve read-back';
      setActionError(msg);
    } finally {
      setIsLoadingAudio(false);
    }
  };

  // Render transcript with highlighted evidence quotes followed by superscripts
  const renderedTranscript = useMemo(() => {
    if (!claim.transcript) {
      return <span className="text-muted italic">No transcript recorded</span>;
    }

    if (intervals.length === 0) {
      return <span>{claim.transcript}</span>;
    }

    const nodes: React.ReactNode[] = [];
    let lastIndex = 0;

    intervals.forEach((interval, idx) => {
      if (interval.start > lastIndex) {
        nodes.push(
          <span key={`plain-${lastIndex}`}>
            {claim.transcript.slice(lastIndex, interval.start)}
          </span>
        );
      }

      nodes.push(
        <span key={`hl-${idx}-${interval.start}`}>
          <mark
            className="text-text rounded-none px-0.5"
            style={{
              backgroundColor: 'var(--hl)',
              borderBottom: '2px solid var(--accent)',
            }}
          >
            {claim.transcript.slice(interval.start, interval.end)}
          </mark>
          <sup className="font-mono text-[10px] text-muted ml-0.5 select-none font-semibold">
            [{interval.indices.join(',')}]
          </sup>
        </span>
      );

      lastIndex = interval.end;
    });

    if (lastIndex < claim.transcript.length) {
      nodes.push(
        <span key={`plain-${lastIndex}`}>
          {claim.transcript.slice(lastIndex)}
        </span>
      );
    }

    return nodes;
  }, [claim.transcript, intervals]);

  const holder = claim.policy?.holder_name || 'Unknown driver';
  const vehicle = claim.policy?.vehicle_make_model || 'Unknown vehicle';
  const plate = claim.policy?.registration_number || 'No plate';

  return (
    <article className="p-6 space-y-6 bg-surface min-h-[500px]">
      {/* 1. Header line */}
      <section className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="font-mono text-[14px] font-semibold text-text">
            {claim.id}
          </span>
          <span className="text-muted">·</span>
          <span className="text-[13px] text-text font-medium">
            {holder} · {vehicle} · {plate}
          </span>
          <span className="border border-line text-muted text-[11px] px-1.5 py-0.5 rounded-[4px]">
            Synthetic
          </span>
        </div>

        <div>
          {claim.status === 'approved' ? (
            <span className="border border-tag text-tag px-2.5 py-0.5 rounded-[4px] text-[12px] font-medium bg-panel/30">
              Approved
            </span>
          ) : (
            <span className="border border-line text-muted px-2.5 py-0.5 rounded-[4px] text-[12px]">
              Pending review
            </span>
          )}
        </div>
      </section>

      {actionError && (
        <div
          role="alert"
          className="p-2.5 bg-panel border-l-[3px] border-[#E53E3E] text-text text-[13px]"
        >
          {actionError}
        </div>
      )}

      {/* 2. Verdict sentence */}
      <section>
        <p className="text-[16px] font-semibold text-text leading-snug">
          {verdictSentence}
        </p>
      </section>

      {/* 3. Needs confirmation block (only when something is not stated) */}
      <NeedsConfirmation questions={confirmationQuestions} />

      {/* 4. Call transcript */}
      <section className="border-t border-line/60 pt-5 space-y-2">
        <h3 className="text-[13px] font-semibold text-muted">
          Call transcript
        </h3>
        <p className="text-[15px] leading-[1.7] text-text font-devanagari whitespace-pre-wrap">
          {renderedTranscript}
        </p>
      </section>

      {/* 5. Findings table & quotes */}
      <section className="border-t border-line/60 pt-5">
        <FindingsTable fnol={claim.fnol} quotes={distinctQuotes} />
      </section>

      {/* 6. Timings line */}
      <section className="border-t border-line/60 pt-4">
        <div className="font-mono text-[12px] text-muted">
          STT: {claim.timings.stt_seconds.toFixed(3)}s · LLM: {claim.timings.llm_seconds.toFixed(3)}s · Total: {claim.timings.total_seconds.toFixed(3)}s
        </div>
      </section>

      {/* 7. Actions */}
      <section className="border-t border-line/60 pt-4 flex flex-wrap items-center gap-3">
        {claim.status === 'pending' ? (
          <button
            type="button"
            onClick={handleApprove}
            disabled={isApproving}
            className="bg-accent text-on-accent hover:brightness-95 border border-[#d98f1f] font-semibold text-[13px] py-1.5 px-3.5 rounded-[4px] cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed select-none"
          >
            {isApproving ? 'Approving...' : 'Approve and assign workshop'}
          </button>
        ) : (
          <div className="text-[13px] text-text">
            <span className="font-semibold text-tag">Approved.</span> Workshop: {claim.workshop} <span className="text-muted">(demo list)</span>
          </div>
        )}

        <div className="flex items-center gap-2 border border-line bg-surface rounded-[4px] px-2.5 py-1 text-[13px]">
          <span className="text-muted text-[12px] font-medium">Voice:</span>
          <select
            value={selectedVoice}
            onChange={(e) => {
              const nextVoice = e.target.value as 'Nalini' | 'Gaurav' | 'Vikrant';
              if (isPlayingAudio && audioRef.current) {
                audioRef.current.pause();
                setIsPlayingAudio(false);
              }
              setSelectedVoice(nextVoice);
            }}
            className="bg-transparent text-text font-medium text-[12px] cursor-pointer outline-none border-none py-0.5"
          >
            <option value="Nalini" className="bg-surface text-text">
              Female (Nalini)
            </option>
            <option value="Gaurav" className="bg-surface text-text">
              Male (Gaurav - Deep)
            </option>
            <option value="Vikrant" className="bg-surface text-text">
              Male (Vikrant)
            </option>
          </select>
        </div>

        <button
          type="button"
          onClick={handlePlayReadback}
          disabled={isLoadingAudio}
          className="border border-line bg-surface hover:bg-panel text-text font-medium text-[13px] py-1.5 px-3.5 rounded-[4px] cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed select-none"
        >
          {isLoadingAudio
            ? `Generating ${selectedVoice === 'Nalini' ? 'Female' : 'Male'} audio...`
            : isPlayingAudio
            ? 'Stop read-back'
            : `Play read-back (${selectedVoice === 'Nalini' ? 'Female' : 'Male'})`}
        </button>
      </section>
    </article>
  );
};

