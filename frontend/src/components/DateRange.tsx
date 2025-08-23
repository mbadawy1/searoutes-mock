// frontend/src/components/DateRange.tsx
import React, { useState, useRef, useEffect } from "react";
import { DayPicker, DateRange as DayPickerDateRange } from "react-day-picker";
import { 
  formatForDisplay, 
  formatForAPI, 
  parseAPIDate, 
  apiToDisplay, 
  displayToAPI, 
  getPresetRanges,
  normalizeDate
} from "../lib/date";
import "react-day-picker/dist/style.css";
import "./DateRange.css";

type Props = {
  fromDate: string;
  toDate: string;
  onFromChange: (date: string) => void;
  onToChange: (date: string) => void;
  disabled?: boolean;
};

export default function DateRange({
  fromDate,
  toDate,
  onFromChange,
  onToChange,
  disabled = false,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [fromDisplay, setFromDisplay] = useState(apiToDisplay(fromDate));
  const [toDisplay, setToDisplay] = useState(apiToDisplay(toDate));
  const [activeField, setActiveField] = useState<'from' | 'to'>('from');
  const containerRef = useRef<HTMLDivElement>(null);
  const fromInputRef = useRef<HTMLInputElement>(null);
  const toInputRef = useRef<HTMLInputElement>(null);

  // Update display values when props change
  useEffect(() => {
    setFromDisplay(apiToDisplay(fromDate));
    setToDisplay(apiToDisplay(toDate));
  }, [fromDate, toDate]);

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Handle manual input changes
  const handleFromInputChange = (value: string) => {
    setFromDisplay(value);
    const apiDate = displayToAPI(value);
    if (apiDate || value === '') {
      onFromChange(apiDate);
    }
  };

  const handleToInputChange = (value: string) => {
    setToDisplay(value);
    const apiDate = displayToAPI(value);
    if (apiDate || value === '') {
      onToChange(apiDate);
    }
  };

  // Handle input focus to open popover
  const handleInputFocus = (field: 'from' | 'to') => {
    if (!disabled) {
      setActiveField(field);
      setIsOpen(true);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      if (activeField === 'from') {
        fromInputRef.current?.blur();
      } else {
        toInputRef.current?.blur();
      }
    }
  };

  // Get current selected range for day picker
  const getSelectedRange = (): DayPickerDateRange | undefined => {
    const fromParsed = parseAPIDate(fromDate);
    const toParsed = parseAPIDate(toDate);
    
    if (fromParsed && toParsed) {
      return { from: fromParsed, to: toParsed };
    } else if (fromParsed) {
      return { from: fromParsed, to: undefined };
    }
    return undefined;
  };

  // Handle date selection from calendar
  const handleRangeSelect = (range: DayPickerDateRange | undefined) => {
    if (!range) return;

    if (range.from) {
      const fromAPI = formatForAPI(normalizeDate(range.from));
      onFromChange(fromAPI);
      setFromDisplay(formatForDisplay(normalizeDate(range.from)));
    }

    if (range.to) {
      const toAPI = formatForAPI(normalizeDate(range.to));
      onToChange(toAPI);
      setToDisplay(formatForDisplay(normalizeDate(range.to)));
      
      // Close popover when both dates are selected
      if (range.from && range.to) {
        setTimeout(() => setIsOpen(false), 100);
      }
    }
  };

  // Handle preset selection
  const handlePresetSelect = (preset: keyof ReturnType<typeof getPresetRanges>) => {
    const ranges = getPresetRanges();
    const range = ranges[preset];
    
    const fromAPI = formatForAPI(range.from);
    const toAPI = formatForAPI(range.to);
    
    onFromChange(fromAPI);
    onToChange(toAPI);
    setFromDisplay(formatForDisplay(range.from));
    setToDisplay(formatForDisplay(range.to));
    setIsOpen(false);
  };

  // Validate that from <= to
  const isValid = !fromDate || !toDate || fromDate <= toDate;

  const inputStyle = {
    width: "100%",
    borderRadius: 12,
    background: "#0b1020",
    border: "1px solid rgba(255,255,255,.12)",
    color: "#e5e7eb",
    padding: "10px 12px",
    outline: "none",
    fontSize: "14px",
    cursor: disabled ? "not-allowed" : "pointer",
  };

  const labelStyle = {
    display: "block" as const,
    fontSize: 12,
    color: "#94a3b8",
    marginBottom: 6,
  };

  const errorStyle = {
    fontSize: 12,
    color: "#ef4444",
    marginTop: 4,
    minHeight: 18,
  };

  const popoverStyle = {
    position: "absolute" as const,
    top: "100%",
    left: 0,
    zIndex: 50,
    background: "#0b1222",
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 16,
    padding: "16px",
    marginTop: 8,
    boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
    minWidth: "600px",
  };

  const presetButtonStyle = {
    background: "#1F2937", // var(--grid)
    color: "#CBD5E1", // var(--text)
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 8,
    padding: "8px 12px",
    fontSize: "12px",
    cursor: "pointer",
    marginRight: "8px",
    marginBottom: "8px",
    fontWeight: "500",
    transition: "all 0.2s ease",
  };

  const presets = getPresetRanges();

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <div style={{ display: "flex", gap: 16, alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}>
          <label htmlFor="date-from" style={labelStyle}>
            Departure From
          </label>
          <input
            ref={fromInputRef}
            id="date-from"
            type="text"
            placeholder="dd/mm/yyyy"
            value={fromDisplay}
            disabled={disabled}
            onChange={(e) => handleFromInputChange(e.target.value)}
            onFocus={() => handleInputFocus('from')}
            onKeyDown={handleKeyDown}
            style={inputStyle}
          />
        </div>

        <div style={{ flex: 1 }}>
          <label htmlFor="date-to" style={labelStyle}>
            Departure To
          </label>
          <input
            ref={toInputRef}
            id="date-to"
            type="text"
            placeholder="dd/mm/yyyy"
            value={toDisplay}
            disabled={disabled}
            onChange={(e) => handleToInputChange(e.target.value)}
            onFocus={() => handleInputFocus('to')}
            onKeyDown={handleKeyDown}
            style={inputStyle}
          />
        </div>

        <div style={{ flex: 1 }}>
          <div style={errorStyle}>
            {!isValid && fromDate && toDate && (
              <span>From date must be before or equal to To date</span>
            )}
          </div>
        </div>
      </div>

      {isOpen && !disabled && (
        <div style={popoverStyle}>
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
              Quick Select
            </div>
            <div style={{ display: "flex", flexWrap: "wrap" }}>
              {Object.keys(presets).map((presetKey) => (
                <button
                  key={presetKey}
                  type="button"
                  onClick={() => handlePresetSelect(presetKey as keyof typeof presets)}
                  style={presetButtonStyle}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#273549"; // Improved hover state
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "#1F2937"; // Match var(--grid)
                  }}
                >
                  {presetKey}
                </button>
              ))}
            </div>
          </div>
          
          <div 
            className="date-range-picker"
            style={{ 
              "--rdp-cell-size": "40px",
            } as React.CSSProperties}
          >
            <DayPicker
              mode="range"
              selected={getSelectedRange()}
              onSelect={handleRangeSelect}
              numberOfMonths={2}
              disabled={{ before: new Date() }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Export validation helper
export const isValidDateRange = (fromDate: string, toDate: string): boolean => {
  return !fromDate || !toDate || fromDate <= toDate;
};