// frontend/src/components/PortSelect.tsx
import React, {useEffect, useMemo, useRef, useState} from "react";
import { searchPorts } from "../api";

type PortItem = {
  name: string;
  locode: string;
  country: string;
  countryName?: string;
  aliases?: string[];
};

type Props = {
  label: string;
  value: string;                       // selected LOCODE (e.g., "EGALY")
  onChange: (locode: string) => void;  // called with LOCODE
  placeholder?: string;
  country?: string;                    // optional ISO2 filter (e.g., "EG")
  disabled?: boolean;
  id?: string;
};

type ErrorState = {
  hasError: boolean;
  message: string;
  canRetry: boolean;
};

// Simple in-memory cache for query results
const queryCache = new Map<string, PortItem[]>();
const CACHE_SIZE = 10;

const isLocode = (s: string) => /^[A-Z]{2}[A-Z]{3}$/.test(s.toUpperCase());

export default function PortSelect({
  label,
  value,
  onChange,
  placeholder = "Start typing a country, city, or LOCODE",
  country,
  disabled,
  id,
}: Props) {
  const [query, setQuery] = useState<string>(value || "");
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<PortItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState<number>(-1);
  const [error, setError] = useState<ErrorState>({ hasError: false, message: "", canRetry: false });
  const boxRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cache management helpers
  const getCachedResults = (cacheKey: string): PortItem[] | null => {
    return queryCache.get(cacheKey) || null;
  };

  const setCachedResults = (cacheKey: string, results: PortItem[]) => {
    if (queryCache.size >= CACHE_SIZE) {
      const firstKey = queryCache.keys().next().value;
      queryCache.delete(firstKey);
    }
    queryCache.set(cacheKey, results);
  };

  const clearError = () => {
    setError({ hasError: false, message: "", canRetry: false });
  };

  const setErrorState = (err?: unknown, canRetry: boolean = true) => {
    // Swallow aborts (typing fast cancels older requests)
    if ((err as any)?.name === "AbortError") return;

    // Normalize the message safely (no axios assumptions)
    let msg = "Unknown error searching ports";
    if (typeof err === "string") msg = err;
    else if (err && typeof err === "object" && "message" in err) {
      msg = (err as Error).message || msg;
    }

    console.error("PortSelect fixed error:", err);

    setError({ hasError: true, message: msg, canRetry });
    setLoading(false);
    setItems([]);
    setOpen(false);
  };

  // Keep input in sync if parent changes value externally
  useEffect(() => {
    if (value && value !== query) setQuery(value);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close when clicking outside
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!boxRef.current) return;
      if (!boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Enhanced debounced search with timeout, caching, and error handling
  useEffect(() => {
    const q = query.trim();
    
    // Clear error when starting new search
    if (error.hasError) {
      clearError();
    }

    // Reset state for short queries or direct LOCODEs
    if (q.length < 2 || isLocode(q)) {
      setItems([]);
      setOpen(false);
      setLoading(false);
      return;
    }

    // Create cache key
    const cacheKey = `${q}${country ? `_${country}` : ''}`;
    
    // Check cache first
    const cached = getCachedResults(cacheKey);
    if (cached) {
      setItems(cached);
      setOpen(cached.length > 0);
      setLoading(false);
      return;
    }

    setLoading(true);
    setActive(-1);

    // Abort previous request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // Set up 6-second timeout
    const hardTimeout = setTimeout(() => {
      ctrl.abort();
      setErrorState("Search timed out. Please check your connection and try again.", true);
    }, 6000);

    const debounceTimeout = setTimeout(async () => {
      try {
        const results = await searchPorts(q, 15);
        
        // Cache successful results
        setCachedResults(cacheKey, results);
        
        setItems(results);
        setOpen(results.length > 0);
        setLoading(false);
        
      } catch (err) {
        setErrorState(err, true);
      } finally {
        clearTimeout(hardTimeout);
      }
    }, 250);

    return () => {
      clearTimeout(debounceTimeout);
      clearTimeout(hardTimeout);
      ctrl.abort();
    };
  }, [query, country, error.hasError]);

  const pick = (locode: string) => {
    onChange(locode.toUpperCase());
    setQuery(locode.toUpperCase()); // display LOCODE after pick
    setOpen(false);
    setActive(-1);
    inputRef.current?.blur();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      setActive(-1);
      return;
    }

    if (!open || items.length === 0) return;
    
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i <= 0 ? items.length - 1 : i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const choice = items[active] || items[0];
      if (choice) pick(choice.locode);
    } else if (e.key === "Tab") {
      // Tab confirms highlighted item if available
      if (active >= 0 && items[active]) {
        e.preventDefault();
        pick(items[active].locode);
      }
    }
  };

  const handleRetry = () => {
    clearError();
    setQuery(""); // Clear and re-trigger search
    setTimeout(() => setQuery(query.trim()), 10);
  };

  const helper = useMemo(() => {
    if (error.hasError) {
      return { text: error.message, isError: true, canRetry: error.canRetry };
    }
    if (isLocode(query)) {
      return { text: "Valid UN/LOCODE", isError: false, canRetry: false };
    }
    if (loading) {
      return { text: "Searching…", isError: false, canRetry: false };
    }
    if (open && items.length === 0 && query.length >= 2) {
      return { text: "No matches found", isError: false, canRetry: false };
    }
    return { text: "", isError: false, canRetry: false };
  }, [query, loading, open, items, error]);

  const highlightMatch = (text: string, query: string): React.ReactNode => {
    if (!query || query.length < 2) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.slice(0, index)}
        <strong style={{ fontWeight: 600, color: "#3b82f6" }}>
          {text.slice(index, index + query.length)}
        </strong>
        {text.slice(index + query.length)}
      </>
    );
  };

  return (
    <div ref={boxRef} style={{ position: "relative" }}>
      <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
        {label}
      </label>
      <input
        ref={inputRef}
        id={id}
        type="text"
        inputMode="latin"
        autoComplete="off"
        spellCheck={false}
        placeholder={placeholder}
        value={query}
        disabled={disabled}
        onChange={(e) => {
          const v = e.target.value;
          setQuery(v);
          if (isLocode(v)) {
            // Accept direct LOCODE entry immediately
            onChange(v.toUpperCase());
          }
        }}
        onFocus={() => setOpen(items.length > 0)}
        onKeyDown={onKeyDown}
        style={{
          width: "100%",
          borderRadius: 12,
          background: "#0b1020",
          border: "1px solid rgba(255,255,255,.12)",
          color: "#e5e7eb",
          padding: "10px 12px",
          outline: "none",
        }}
      />
      <div style={{ fontSize: 12, marginTop: 4, minHeight: 18, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: helper.isError ? "#ef4444" : "#94a3b8" }}>
          {helper.text}
        </span>
        {helper.canRetry && (
          <button
            type="button"
            onClick={handleRetry}
            style={{
              background: "transparent",
              border: "1px solid #ef4444",
              color: "#ef4444",
              borderRadius: 4,
              padding: "2px 6px",
              fontSize: 10,
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Retry
          </button>
        )}
      </div>

      {open && items.length > 0 && (
        <div
          role="listbox"
          aria-label="Port suggestions"
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            zIndex: 20,
            background: "#0b1222",
            border: "1px solid rgba(255,255,255,.12)",
            borderRadius: 12,
            maxHeight: 240,
            overflowY: "auto",
          }}
        >
          {items.map((p, i) => {
            const isActive = i === active;
            const q = query.trim();
            return (
              <div
                key={`${p.locode}-${i}`}
                role="option"
                aria-selected={isActive}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(p.locode)}
                onMouseEnter={() => setActive(i)}
                style={{
                  padding: "10px 12px",
                  cursor: "pointer",
                  background: isActive ? "#1e293b" : "transparent",
                  borderBottom: "1px solid rgba(255,255,255,.06)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "14px", fontWeight: 500, marginBottom: 2 }}>
                      {highlightMatch(p.name, q)} ({p.country})
                    </div>
                    <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "monospace" }}>
                      {p.locode}
                    </div>
                  </div>
                  {p.countryName && (
                    <div style={{ fontSize: "12px", color: "#64748b", fontStyle: "italic" }}>
                      {p.countryName}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
