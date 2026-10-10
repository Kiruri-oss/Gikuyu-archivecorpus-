"use client";

import { useRef, useState } from "react";

interface AudioPlayerProps {
  src: string;
  title: string;
}

export function AudioPlayer({ src, title }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      void audio.play();
      setIsPlaying(true);
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  };

  return (
    <div className="flex items-center gap-3 p-4 bg-earth-50 rounded-lg">
      <button
        type="button"
        onClick={toggle}
        aria-label={isPlaying ? `Pause ${title}` : `Play ${title}`}
        className="w-12 h-12 rounded-full bg-earth-500 text-white"
      >
        {isPlaying ? "❚❚" : "▶"}
      </button>
      <audio
        ref={audioRef}
        src={src}
        onEnded={() => setIsPlaying(false)}
        preload="metadata"
      />
      <span className="font-medium">{title}</span>
    </div>
  );
}