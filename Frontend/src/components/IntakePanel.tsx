import React, { useState, useRef, useEffect } from 'react';

interface IntakePanelProps {
  onUpload: (file: File, phone?: string) => Promise<void>;
  isUploading: boolean;
  errorMessage: string | null;
  onClearError: () => void;
}

const ALLOWED_EXTENSIONS = ['.ogg', '.m4a', '.mp3', '.wav'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

const SAMPLE_PHONES = [
  { phone: '9876543210', label: '9876543210 (Aarav Sharma - Swift)' },
  { phone: '9876543211', label: '9876543211 (Priya Verma - Creta)' },
  { phone: '9876543212', label: '9876543212 (Rajesh Patel - Nexon)' },
  { phone: '9876543213', label: '9876543213 (Sunita Rao - XUV700)' },
  { phone: '9876543214', label: '9876543214 (Vikram Singh - City)' },
];

export const IntakePanel: React.FC<IntakePanelProps> = ({
  onUpload,
  isUploading,
  errorMessage,
  onClearError,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [phone, setPhone] = useState<string>('9876543210');
  const [localError, setLocalError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Timer for elapsed seconds during processing
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;
    if (isUploading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isUploading]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalError(null);
    onClearError();
    const files = e.target.files;
    if (!files || files.length === 0) {
      setSelectedFile(null);
      return;
    }

    const file = files[0];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setLocalError(`Unsupported format '${extension}'. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
      setSelectedFile(null);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setLocalError(`File size exceeds 5 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB)`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setLocalError('Select an audio recording to process.');
      return;
    }
    setLocalError(null);
    onClearError();

    try {
      await onUpload(selectedFile, phone);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch {
      // Error is handled and surfaced by parent in errorMessage
    }
  };

  const activeError = errorMessage || localError;

  return (
    <div className="bg-surface border border-line rounded-card p-4 lg:sticky lg:top-16">
      <h2 className="text-[15px] font-semibold text-text mb-3">
        New FNOL Intake
      </h2>

      {activeError && (
        <div
          role="alert"
          className="mb-4 p-3 bg-panel border border-[#E53E3E]/60 text-text rounded-chip text-[13px] flex flex-col gap-1"
        >
          <div className="font-semibold text-[#FC8181] text-[12px] uppercase tracking-wide">
            Intake Error
          </div>
          <div className="text-[13px] break-words">{activeError}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="audio-file-input"
            className="block text-[12px] font-medium text-muted mb-1.5"
          >
            Driver audio clip (.ogg, .m4a, .mp3, .wav, max 5 MB)
          </label>
          <input
            id="audio-file-input"
            ref={fileInputRef}
            type="file"
            accept=".ogg,.m4a,.mp3,.wav"
            onChange={handleFileChange}
            disabled={isUploading}
            className="w-full text-[13px] text-text bg-panel/60 border border-line rounded-chip px-2.5 py-2 file:mr-3 file:py-1.5 file:px-3 file:rounded-chip file:border file:border-line file:text-[12px] file:font-medium file:bg-surface file:text-text hover:file:bg-panel file:cursor-pointer file:active:translate-y-[1px] disabled:opacity-50"
          />
          {selectedFile && (
            <div className="mt-1 font-mono text-[11px] text-muted truncate">
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        <div>
          <label
            htmlFor="phone-select"
            className="block text-[12px] font-medium text-muted mb-1.5"
          >
            Caller phone (policy match)
          </label>
          <select
            id="phone-select"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={isUploading}
            className="w-full text-[13px] text-text bg-panel border border-line rounded-chip px-2.5 py-2 disabled:opacity-50"
          >
            <option value="">None / Unknown caller</option>
            {SAMPLE_PHONES.map((p) => (
              <option key={p.phone} value={p.phone}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <button
            type="submit"
            disabled={isUploading || !selectedFile}
            className="w-full bg-[#272548] hover:bg-[#322f5c] border border-[#3E3B68] text-text font-semibold text-[13px] py-2 px-3 rounded-chip cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none select-none text-center"
          >
            {isUploading
              ? `Transcribing and extracting... (${elapsedSeconds}s)`
              : 'Submit for FNOL extraction'}
          </button>
        </div>
      </form>

      <div className="mt-5 pt-3 border-t border-line text-[11px] text-muted leading-normal">
        Synthetic demo data. A human adjuster approves every claim.
      </div>
    </div>
  );
};
