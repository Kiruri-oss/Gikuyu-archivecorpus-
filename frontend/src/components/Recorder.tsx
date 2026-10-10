"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface RecorderProps {
  onRecordingComplete: (blob: Blob, durationSeconds: number) => void;
}

export function Recorder({ onRecordingComplete }: RecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 48000 },
      });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];
      startTimeRef.current = Date.now();

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const duration = (Date.now() - startTimeRef.current) / 1000;
        onRecordingComplete(blob, duration);
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start(1000);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      setError("Microphone access denied. Enable it in your browser settings.");
    }
  }, [onRecordingComplete]);

  const stop = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    stopTimer();
  }, [stopTimer]);

  useEffect(() => () => stopTimer(), [stopTimer]);

  return (
    <div className="flex flex-col items-center gap-4 p-6 border rounded-lg">
      <button
        type="button"
        onClick={isRecording ? stop : start}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
        className={`w-24 h-24 rounded-full text-white font-semibold transition ${
          isRecording ? "bg-red-600 animate-pulse" : "bg-earth-500 hover:bg-earth-900"
        }`}
      >
        {isRecording ? `Stop ${seconds}s` : "Record"}
      </button>
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}
    </div>
  );
}