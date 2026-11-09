import React, { useState, useRef, useEffect } from 'react';
import { Claim } from '../types';
import { approveClaim, fetchReadbackAudio } from '../api';
import { TranscriptHighlight } from './TranscriptHighlight';
import { FieldsTable } from './FieldsTable';

interface ClaimCardProps {
  claim: Claim;
  onClaimUpdated: (updated: Claim) => void;
}

export const ClaimCard: React.FC<ClaimCardProps> = ({ claim, onClaimUpdated }) => {
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  // Cleanup audio url on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
      }
    };
  }, []);

  // Collect all evidence quotes for highlighting in the transcript
  const allQuotes = [
    claim.fnol.vehicle_drivable_evidence,
    claim.fnol.towing_evidence,
    claim.fnol.third_party_evidence,
    ...(claim.fnol.damage_zones || []).map((z) => z.evidence),
  ];

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

    // If we already cached the Audio instance for this card, replay it
    if (audioRef.current && audioUrlRef.current) {
      try {
        audioRef.current.currentTime = 0;
        await audioRef.current.play();
        setIsPlayingAudio(true);
        return;
      } catch (e) {
        console.error(e);
      }
    }

    try {
      setIsLoadingAudio(true);
      const blob = await fetchReadbackAudio(claim.id);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;

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

  return (
    <article className="bg-surface border border-line rounded-card p-5 space-y-4">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[15px] font-semibold text-text tracking-wide">
            {claim.id}
          </span>
          {claim.policy && (
            <span className="text-[12px] text-muted">
              {claim.policy.holder_name} · {claim.policy.vehicle_make_model} ({claim.policy.registration_number})
            </span>
          )}
        </div>

        <div>
          {claim.status === 'approved' ? (
            <span className="border border-tag text-tag px-2.5 py-0.5 rounded-chip text-[12px] font-medium bg-tag/10">
              Approved
            </span>
          ) : (
            <span className="border border-line text-muted px-2.5 py-0.5 rounded-chip text-[12px]">
              Pending review
            </span>
          )}
        </div>
      </div>

      {actionError && (
        <div className="p-2.5 bg-panel border border-[#E53E3E]/60 rounded-chip text-[12px] text-[#FC8181]">
          {actionError}
        </div>
      )}

      {/* Transcript with merged evidence highlights */}
      <TranscriptHighlight transcript={claim.transcript} quotes={allQuotes} />

      {/* Structured Fields Table */}
      <div>
        <div className="text-[11px] font-mono uppercase tracking-wider text-muted mb-1.5">
          Structured Claim Extraction
        </div>
        <FieldsTable fnol={claim.fnol} />
      </div>

      {/* Damage Zones Row */}
      <div>
        <div className="text-[11px] font-mono uppercase tracking-wider text-muted mb-1.5">
          Damage zones
        </div>
        {claim.fnol.damage_zones && claim.fnol.damage_zones.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {claim.fnol.damage_zones.map((dz, idx) => (
              <div
                key={`${dz.zone}-${idx}`}
                className="inline-flex items-center gap-1.5 border border-line bg-panel/40 px-2.5 py-1 rounded-chip text-[12px]"
              >
                <span className="text-tag font-medium">{dz.zone}</span>
                {dz.evidence && (
                  <span className="text-muted italic border-l border-line pl-1.5">
                    "{dz.evidence}"
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[13px] text-muted italic">
            No damage zones identified
          </div>
        )}
      </div>

      {/* Timing line */}
      <div className="font-mono text-[12px] text-muted pt-1 border-t border-line/60">
        STT: {claim.timings.stt_seconds.toFixed(3)}s · LLM: {claim.timings.llm_seconds.toFixed(3)}s · Total: {claim.timings.total_seconds.toFixed(3)}s
      </div>

      {/* Assigned workshop note after approval */}
      {claim.status === 'approved' && claim.workshop && (
        <div className="bg-panel border border-line rounded-chip p-3 text-[13px]">
          <span className="text-muted">Assigned workshop: </span>
          <span className="text-text font-medium">{claim.workshop}</span>
        </div>
      )}

      {/* Action Row */}
      <div className="flex flex-wrap items-center gap-3 pt-2">
        {claim.status === 'pending' && (
          <button
            type="button"
            onClick={handleApprove}
            disabled={isApproving}
            className="bg-accent text-[#1A1A1F] hover:bg-[#e09520] border border-[#d98f1f] font-semibold text-[13px] py-1.5 px-3.5 rounded-chip cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none select-none"
          >
            {isApproving ? 'Approving...' : 'Approve towing and assign workshop'}
          </button>
        )}

        <button
          type="button"
          onClick={handlePlayReadback}
          disabled={isLoadingAudio}
          className="border border-line bg-panel/30 hover:bg-panel hover:border-link/70 text-text font-medium text-[13px] py-1.5 px-3.5 rounded-chip cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed select-none"
        >
          {isLoadingAudio
            ? 'Generating audio...'
            : isPlayingAudio
            ? 'Stop read-back'
            : 'Play read-back'}
        </button>
      </div>
    </article>
  );
};
