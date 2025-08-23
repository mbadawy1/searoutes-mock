// frontend/src/ScheduleTable.tsx
import React, { useState, useEffect, useRef } from "react";
import PortSelect from "./components/PortSelect";
import DateRange, { isValidDateRange } from "./components/DateRange";
import ResultsTable from "./components/ResultsTable";
import { listSchedules, searchCarriers } from "./api";
import { Schedule, SchedulesResponse, SearchParams, CarrierItem } from "./types";

const EQUIPMENT_OPTIONS = [
  { value: "", label: "All Equipment" },
  { value: "20DC", label: "20' Dry Container" },
  { value: "40DC", label: "40' Dry Container" },
  { value: "40HC", label: "40' High Cube" },
  { value: "40RF", label: "40' Refrigerated" },
  { value: "45HC", label: "45' High Cube" },
  { value: "53HC", label: "53' High Cube" },
];

const STATIC_CARRIERS = [
  { scac: "", name: "All Carriers" },
  { scac: "HLCU", name: "Hapag-Lloyd" },
  { scac: "CMAU", name: "CMA CGM" },
  { scac: "MSCU", name: "MSC" },
  { scac: "ONEY", name: "Ocean Network Express (ONE)" },
];

export default function ScheduleTable() {
  // Form state
  const [originLocode, setOriginLocode] = useState("");
  const [destinationLocode, setDestinationLocode] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [equipment, setEquipment] = useState("");
  const [carrier, setCarrier] = useState("");
  const [routingType, setRoutingType] = useState("");
  const [sort, setSort] = useState<'etd' | 'transit'>('etd');

  // Results state
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Status line state
  const [lastSearchTime, setLastSearchTime] = useState<string | null>(null);
  const [lastSearchStatus, setLastSearchStatus] = useState<'success' | 'error' | null>(null);

  // Carrier search state
  const [carrierQuery, setCarrierQuery] = useState("");
  const [carrierOptions, setCarrierOptions] = useState<CarrierItem[]>(STATIC_CARRIERS);
  const [showCarrierDropdown, setShowCarrierDropdown] = useState(false);
  const carrierRef = useRef<HTMLDivElement>(null);

  const isDateValid = isValidDateRange(fromDate, toDate);
  const canSearch = isDateValid;

  // LocalStorage key for persistence
  const STORAGE_KEY = "searoutes-last-search";

  // Save search parameters to localStorage
  const saveSearchParams = () => {
    try {
      const params = {
        originLocode,
        destinationLocode,
        fromDate,
        toDate,
        equipment,
        carrier,
        routingType,
        sort,
        carrierQuery,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(params));
    } catch (err) {
      console.warn("Failed to save search params to localStorage:", err);
    }
  };

  // Restore search parameters from localStorage
  const restoreSearchParams = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const params = JSON.parse(saved);
        setOriginLocode(params.originLocode || "");
        setDestinationLocode(params.destinationLocode || "");
        setFromDate(params.fromDate || "");
        setToDate(params.toDate || "");
        setEquipment(params.equipment || "");
        setCarrier(params.carrier || "");
        setRoutingType(params.routingType || "");
        setSort(params.sort || "etd");
        setCarrierQuery(params.carrierQuery || "");
      }
    } catch (err) {
      console.warn("Failed to restore search params from localStorage:", err);
    }
  };

  // Get default date range (today to today + 21 days)
  const getDefaultDateRange = () => {
    const today = new Date();
    const endDate = new Date();
    endDate.setDate(today.getDate() + 21);
    
    return {
      from: today.toISOString().split('T')[0],
      to: endDate.toISOString().split('T')[0],
    };
  };

  // Quick link handler
  const handleQuickLink = async (origin: string, destination: string) => {
    const dates = getDefaultDateRange();
    setOriginLocode(origin);
    setDestinationLocode(destination);
    setFromDate(dates.from);
    setToDate(dates.to);
    
    // Clear any existing carrier selection for fresh search
    setCarrier("");
    setCarrierQuery("");
    setEquipment("");
    setRoutingType("");
    setSort("etd");
    
    // Trigger search after a short delay to ensure state is updated
    setTimeout(async () => {
      if (!loading) {
        await handleSearch();
      }
    }, 100);
  };

  // Restore search params on component mount
  useEffect(() => {
    restoreSearchParams();
  }, []);

  // Carrier search debouncing
  useEffect(() => {
    if (!carrierQuery || carrierQuery.length < 2) {
      setCarrierOptions(STATIC_CARRIERS);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const results = await searchCarriers(carrierQuery);
        const mappedResults = results.map(r => ({ scac: r.scac, name: r.name }));
        setCarrierOptions([{ scac: "", name: "All Carriers" }, ...mappedResults]);
      } catch {
        setCarrierOptions(STATIC_CARRIERS);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [carrierQuery]);

  // Auto-refetch when sort changes (if we have previous search results)
  useEffect(() => {
    if (lastSearchStatus === 'success' && schedules.length > 0) {
      handleSearch();
    }
  }, [sort]);

  // Close carrier dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (carrierRef.current && !carrierRef.current.contains(event.target as Node)) {
        setShowCarrierDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = async () => {
    if (!canSearch) return;

    setLoading(true);
    setError(null);
    setLastSearchStatus(null);

    try {
      const params: SearchParams = {
        origin: originLocode || undefined,
        destination: destinationLocode || undefined,
        from: fromDate || undefined,
        to: toDate || undefined,
        equipment: equipment || undefined,
        carrier: carrier || undefined,
        routingType: routingType || undefined,
        sort,
        page,
        pageSize,
      };

      const response: SchedulesResponse = await listSchedules(params);
      setSchedules(response.items);
      setTotal(response.total);
      
      // Update status line with success
      const now = new Date();
      const timeString = now.toTimeString().slice(0, 5); // HH:MM format
      setLastSearchTime(timeString);
      setLastSearchStatus('success');
      
      // Save search params to localStorage
      saveSearchParams();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "An error occurred";
      setError(errorMsg);
      setSchedules([]);
      setTotal(0);
      setLastSearchStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleCarrierSelect = (scac: string, name: string) => {
    setCarrier(scac);
    setCarrierQuery(name);
    setShowCarrierDropdown(false);
  };

  // Build export URL with current filters and sort (ignoring pagination)
  const buildExportUrl = (format: 'csv' | 'xlsx') => {
    const params = new URLSearchParams();
    
    if (originLocode) params.set('origin', originLocode);
    if (destinationLocode) params.set('destination', destinationLocode);
    if (fromDate) params.set('from', fromDate);
    if (toDate) params.set('to', toDate);
    if (equipment) params.set('equipment', equipment);
    if (carrier) params.set('carrier', carrier);
    if (routingType) params.set('routingType', routingType);
    if (sort) params.set('sort', sort);
    
    // Note: Exports ignore pagination - include all matching results
    const baseUrl = 'http://localhost:8003'; // Use the same API base
    return `${baseUrl}/api/schedules.${format}?${params.toString()}`;
  };


  const containerStyle = {
    maxWidth: "1400px",
    margin: "0 auto",
    padding: "20px",
    fontFamily: "system-ui, sans-serif",
    background: "#0a0f1a",
    color: "#e5e7eb",
    minHeight: "100vh",
  };

  const formStyle = {
    background: "#0b1222",
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 16,
    padding: "24px",
    marginBottom: "24px",
  };

  const gridStyle = {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "20px",
    marginBottom: "20px",
  };

  const inputStyle = {
    width: "100%",
    borderRadius: 12,
    background: "#0b1020",
    border: "1px solid rgba(255,255,255,.12)",
    color: "#e5e7eb",
    padding: "10px 12px",
    outline: "none",
    fontSize: "14px",
  };

  const selectStyle = {
    ...inputStyle,
    cursor: "pointer",
  };

  const buttonStyle = {
    background: canSearch ? "#3b82f6" : "#374151",
    color: canSearch ? "#ffffff" : "#9ca3af",
    border: "none",
    borderRadius: 12,
    padding: "12px 24px",
    fontSize: "14px",
    fontWeight: 600,
    cursor: canSearch ? "pointer" : "not-allowed",
    transition: "all 0.2s",
  };


  const quickLinkStyle = {
    background: "#1e293b",
    color: "#e5e7eb",
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 8,
    padding: "8px 16px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.2s",
    marginRight: "12px",
  };

  const exportButtonStyle = {
    background: "#1e40af",
    color: "#ffffff", 
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 8,
    padding: "10px 20px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.2s",
    marginRight: "12px",
    marginBottom: "8px",
    textDecoration: "none",
    display: "inline-block",
  };

  const exportButtonDisabledStyle = {
    ...exportButtonStyle,
    background: "#374151",
    color: "#9ca3af",
    cursor: "not-allowed",
    pointerEvents: "none" as const,
  };

  const statusLineStyle = {
    background: "#0b1222",
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 8,
    padding: "12px 16px",
    marginBottom: "16px",
    fontSize: "14px",
    fontFamily: "monospace",
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ marginBottom: "24px", fontSize: "28px", fontWeight: 700 }}>
        Shipping Schedule Search
      </h1>

      {/* Quick Links */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ marginBottom: "12px", fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>
          Quick Links
        </div>
        <div style={{ display: "flex", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => handleQuickLink("EGALY", "MATNG")}
            disabled={loading}
            style={{
              ...quickLinkStyle,
              opacity: loading ? 0.6 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.background = "#334155";
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.background = "#1e293b";
            }}
          >
            EGALY → MATNG
          </button>
          <button
            type="button"
            onClick={() => handleQuickLink("EGDAM", "NLRTM")}
            disabled={loading}
            style={{
              ...quickLinkStyle,
              opacity: loading ? 0.6 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.background = "#334155";
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.background = "#1e293b";
            }}
          >
            EGDAM → NLRTM
          </button>
        </div>
      </div>

      <form style={formStyle} onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
        <div style={gridStyle}>
          <PortSelect
            label="From Port"
            value={originLocode}
            onChange={setOriginLocode}
            placeholder="Start typing a country, city, or LOCODE"
            disabled={loading}
          />
          <PortSelect
            label="To Port"
            value={destinationLocode}
            onChange={setDestinationLocode}
            placeholder="Start typing a country, city, or LOCODE"
            disabled={loading}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <DateRange
            fromDate={fromDate}
            toDate={toDate}
            onFromChange={setFromDate}
            onToChange={setToDate}
            disabled={loading}
          />
        </div>

        <div style={gridStyle}>
          <div>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
              Equipment Type
            </label>
            <select
              value={equipment}
              onChange={(e) => setEquipment(e.target.value)}
              disabled={loading}
              style={selectStyle}
            >
              {EQUIPMENT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div ref={carrierRef} style={{ position: "relative" }}>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
              Carrier
            </label>
            <input
              type="text"
              value={carrierQuery}
              onChange={(e) => {
                setCarrierQuery(e.target.value);
                setShowCarrierDropdown(true);
              }}
              onFocus={() => setShowCarrierDropdown(true)}
              placeholder="Search carriers or select from dropdown"
              disabled={loading}
              style={inputStyle}
            />
            {showCarrierDropdown && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  right: 0,
                  zIndex: 10,
                  background: "#0b1222",
                  border: "1px solid rgba(255,255,255,.12)",
                  borderRadius: 12,
                  maxHeight: 200,
                  overflowY: "auto",
                  marginTop: 4,
                }}
              >
                {carrierOptions.map((option) => (
                  <div
                    key={option.scac}
                    onClick={() => handleCarrierSelect(option.scac, option.name)}
                    style={{
                      padding: "8px 12px",
                      cursor: "pointer",
                      background: "transparent",
                      borderBottom: "1px solid rgba(255,255,255,.06)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#1e293b";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "transparent";
                    }}
                  >
                    {option.name} {option.scac && `(${option.scac})`}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={gridStyle}>
          <div>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
              Routing Type
            </label>
            <select
              value={routingType}
              onChange={(e) => setRoutingType(e.target.value)}
              disabled={loading}
              style={selectStyle}
            >
              <option value="">All Routing Types</option>
              <option value="Direct">Direct</option>
              <option value="Transshipment">Transshipment</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
              Sort By
            </label>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as 'etd' | 'transit')}
              disabled={loading}
              style={selectStyle}
            >
              <option value="etd">Departure Date (ETD)</option>
              <option value="transit">Transit Time</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "24px" }}>
          <button
            type="submit"
            disabled={!canSearch || loading}
            style={buttonStyle}
          >
            {loading ? "Searching..." : "Search Schedules"}
          </button>
        </div>
      </form>

      {/* Status Line */}
      {/* Status Line */}
      {(loading || lastSearchStatus || error) && (
        <div style={statusLineStyle}>
          {loading ? (
            <span style={{ color: "#fbbf24" }}>Searching...</span>
          ) : lastSearchStatus === 'success' && lastSearchTime ? (
            <span style={{ color: "#10b981" }}>
              OK • {lastSearchTime} • {total} itineraries
            </span>
          ) : lastSearchStatus === 'error' ? (
            <span style={{ color: "#ef4444" }}>
              Error {error ? `• ${error}` : ''}
            </span>
          ) : null}
        </div>
      )}

      {/* Export Buttons */}
      {(schedules.length > 0 || lastSearchStatus === 'success') && (
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
            Export Results
          </div>
          <div style={{ display: "flex", flexWrap: "wrap" }}>
            <a
              href={buildExportUrl('csv')}
              style={loading || schedules.length === 0 ? exportButtonDisabledStyle : exportButtonStyle}
              download
              onClick={(e) => {
                if (loading || schedules.length === 0) {
                  e.preventDefault();
                }
              }}
            >
              📄 Download CSV
            </a>
            <a
              href={buildExportUrl('xlsx')}
              style={loading || schedules.length === 0 ? exportButtonDisabledStyle : exportButtonStyle}
              download
              onClick={(e) => {
                if (loading || schedules.length === 0) {
                  e.preventDefault();
                }
              }}
            >
              📊 Download Excel
            </a>
          </div>
          <div style={{ fontSize: "12px", color: "#6b7280", marginTop: "4px" }}>
            Exports include all results matching your filters (ignores pagination)
          </div>
        </div>
      )}

      {/* Results Table */}
      <ResultsTable
        schedules={schedules}
        loading={loading}
        error={error}
        total={total}
      />
    </div>
  );
}