"use client";

import { useEffect, useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export function SearchBar({ onSearch, placeholder = "Search..." }: SearchBarProps) {
  const [value, setValue] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => onSearch(value.trim()), 300);
    return () => clearTimeout(timer);
  }, [value, onSearch]);

  return (
    <input
      type="search"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={placeholder}
      aria-label="Search archive"
      className="w-full p-4 border rounded-lg text-lg"
    />
  );
}