import React, { useState, useRef, useEffect } from 'react';

interface IntakeRowProps {
  onUpload: (file: File, phone?: string) => Promise<void>;
  isUploading: boolean;
  errorMessage: string | null;
  onClearError: () => void;
}

const ALLOWED_EXTENSIONS = ['.ogg', '.m4a', '.mp3', '.wav'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

const SAMPLE_PHONES = [
  { phone: '9876543210', label: '9876543210 · Aarav Sharma (Swift)' },
  { phone: '9876543211', label: '9876543211 · Priya Verma (Creta)' },
  { phone: '9876543212', label: '9876543212 · Rajesh Patel (Nexon)' },
  { phone: '9876543213', label: '9876543213 · Sunita Rao (XUV700)' },
  { phone: '9876543214', label: '9876543214 · Vikram Singh (City)' },
];

export const IntakeRow: React.FC<IntakeRowProps> = ({
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

  // Elapsed seconds timer during pipeline execution
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
      setLocalError(`Unsupported file format '${extension}'. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
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
      setLocalError('Select an audio clip to process.');
      return;
    }
    setLocalError(null);
    onClearError();

    try {
      await onUpload(selectedFile, phone);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch {
      // Backend error is surfaced by parent
    }
  };

  const activeError = errorMessage || localError;

  return (
    <div className="border-b border-line bg-surface py-3">
      <div className="max-w-[1100px] mx-auto px-4 space-y-2.5">
        <form
          onSubmit={handleSubmit}
          className="flex flex-wrap items-center gap-3 text-[13px]"
        >
          {/* File Picker */}
          <div className="flex items-center gap-2 flex-1 min-w-[240px]">
            <input
              id="intake-file"
              ref={fileInputRef}
              type="file"
              accept=".ogg,.m4a,.mp3,.wav"
              onChange={handleFileChange}
              disabled={isUploading}
              aria-label="Upload call audio"
              className="w-full text-[13px] text-text bg-panel/40 border border-line rounded-[4px] px-2 py-1 file:mr-2.5 file:py-1 file:px-2.5 file:rounded-[4px] file:border file:border-line file:text-[12px] file:font-medium file:bg-surface file:text-text hover:file:bg-panel file:cursor-pointer disabled:opacity-50"
            />
          </div>

          {/* Caller phone select */}
          <div className="min-w-[210px]">
            <select
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isUploading}
              aria-label="Caller phone"
              className="w-full text-[13px] text-text bg-surface border border-line rounded-[4px] px-2.5 py-1.5 disabled:opacity-50 cursor-pointer"
            >
              <option value="" className="bg-surface text-text">
                Unknown caller
              </option>
              {SAMPLE_PHONES.map((p) => (
                <option key={p.phone} value={p.phone} className="bg-surface text-text">
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="border border-line bg-panel hover:bg-panel/80 hover:border-link text-text font-medium text-[13px] px-3.5 py-1.5 rounded-[4px] cursor-pointer active:translate-y-[1px] disabled:opacity-40 disabled:cursor-not-allowed select-none whitespace-nowrap"
            >
              {isUploading
                ? `Transcribing and extracting... (${elapsedSeconds}s)`
                : 'Submit'}
            </button>
          </div>
        </form>

        {/* API Error Banner */}
        {activeError && (
          <div
            role="alert"
            className="p-2.5 bg-panel border-l-[3px] border-[#E53E3E] text-text text-[13px] flex items-center justify-between gap-2"
          >
            <span>{activeError}</span>
            <button
              type="button"
              onClick={() => {
                setLocalError(null);
                onClearError();
              }}
              className="text-muted hover:text-text text-[12px] font-mono px-1"
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

