// frontend/src/components/ResultsTable.tsx
import React, { useState } from "react";
import { Schedule, ScheduleLeg } from "../types";

interface ResultsTableProps {
  schedules: Schedule[];
  loading: boolean;
  error?: string | null;
  total?: number;
}

// Helper function to extract LOCODE from location string
const extractLocode = (location: string): string => {
  // Try to extract LOCODE from patterns like "Alexandria, EG" -> "EGALY"
  // or "Rotterdam, NL" -> "NLRTM"
  // For now, we'll use a simple mapping for common ports
  const locodeMap: Record<string, string> = {
    "Alexandria, EG": "EGALY",
    "Tanger, MA": "MATNG", 
    "Rotterdam, NL": "NLRTM",
    "Damietta, EG": "EGDAM",
    "Valencia, ES": "ESVLC",
    // Add more as needed
  };
  
  return locodeMap[location] || location.split(',')[0].slice(0, 5).toUpperCase();
};

// Helper function to extract carrier SCAC from carrier string
const extractCarrierScac = (carrier: string): string => {
  // Try to extract SCAC from patterns like "CMA CGM" -> "CMAU"
  const scacMap: Record<string, string> = {
    "CMA CGM": "CMAU",
    "MSC": "MSCU", 
    "Hapag-Lloyd": "HLCU",
    "Ocean Network Express": "ONEY",
    "Maersk": "MAEU",
    "COSCO": "COSU",
    // Add more as needed
  };
  
  return scacMap[carrier] || carrier.slice(0, 4).toUpperCase();
};

// Function to get legs data for a schedule
const getScheduleLegs = (schedule: Schedule): ScheduleLeg[] => {
  // If schedule has legs data, use it
  if (schedule.legs && schedule.legs.length > 0) {
    return schedule.legs;
  }
  
  // For schedules without legs (direct routes), create a single leg
  return [
    {
      legNumber: 1,
      fromLocode: extractLocode(schedule.origin),
      fromPort: schedule.origin.split(',')[0],
      toLocode: extractLocode(schedule.destination),
      toPort: schedule.destination.split(',')[0],
      etd: schedule.etd,
      eta: schedule.eta,
      vessel: schedule.vessel,
      voyage: schedule.voyage,
      transitDays: schedule.transitDays
    }
  ];
};

// Helper function to format date/time consistently
const formatDateTime = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoString;
  }
};

const formatDate = (isoString: string): string => {
  try {
    return new Date(isoString).toLocaleDateString();
  } catch {
    return isoString;
  }
};

export default function ResultsTable({ schedules, loading, error, total }: ResultsTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRowExpansion = (scheduleId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(scheduleId)) {
      newExpanded.delete(scheduleId);
    } else {
      newExpanded.add(scheduleId);
    }
    setExpandedRows(newExpanded);
  };

  // Common styles matching the existing theme
  const tableContainerStyle = {
    overflowX: "auto" as const,
    maxHeight: "70vh",
    overflowY: "auto" as const,
    border: "1px solid rgba(255,255,255,.12)",
    borderRadius: 12,
    background: "#0b1222",
  };

  const tableStyle = {
    width: "100%",
    borderCollapse: "collapse" as const,
    background: "transparent",
  };

  const stickyHeaderStyle = {
    position: "sticky" as const,
    top: 0,
    background: "#1e293b",
    color: "#f1f5f9",
    padding: "12px",
    textAlign: "left" as const,
    fontWeight: 600,
    fontSize: "14px",
    borderBottom: "1px solid rgba(255,255,255,.12)",
    zIndex: 10,
  };

  const thStyle = {
    ...stickyHeaderStyle,
    whiteSpace: "nowrap" as const,
  };

  const tdStyle = {
    padding: "12px",
    borderBottom: "1px solid rgba(255,255,255,.06)",
    fontSize: "14px",
    verticalAlign: "top" as const,
    color: "#e5e7eb",
  };

  const expanderButtonStyle = {
    background: "transparent",
    border: "none",
    color: "#3b82f6",
    cursor: "pointer",
    padding: "4px",
    borderRadius: 4,
    marginRight: 8,
    fontSize: "12px",
    fontWeight: 600,
  };

  const expandedRowStyle = {
    ...tdStyle,
    background: "#0f172a",
    borderLeft: "3px solid #3b82f6",
  };

  const legTableStyle = {
    width: "100%",
    borderCollapse: "collapse" as const,
    marginTop: 8,
  };

  const legThStyle = {
    background: "#374151",
    color: "#d1d5db",
    padding: "8px",
    textAlign: "left" as const,
    fontWeight: 500,
    fontSize: "12px",
    borderBottom: "1px solid rgba(255,255,255,.1)",
  };

  const legTdStyle = {
    padding: "8px",
    borderBottom: "1px solid rgba(255,255,255,.05)",
    fontSize: "12px",
    color: "#d1d5db",
  };

  const loadingSpinnerStyle = {
    display: "inline-block",
    width: "20px",
    height: "20px",
    border: "3px solid rgba(59, 130, 246, 0.3)",
    borderRadius: "50%",
    borderTopColor: "#3b82f6",
    animation: "spin 1s ease-in-out infinite",
  };

  // Loading state
  if (loading) {
    return (
      <div style={{ 
        textAlign: "center", 
        padding: "48px", 
        color: "#94a3b8", 
        fontSize: "16px",
        background: "#0b1222",
        border: "1px solid rgba(255,255,255,.12)",
        borderRadius: 12,
      }}>
        <div style={loadingSpinnerStyle}></div>
        <div style={{ marginTop: "16px" }}>Loading schedules...</div>
        <style>
          {`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{
        textAlign: "center",
        padding: "48px",
        color: "#ef4444",
        fontSize: "16px",
        background: "#0b1222",
        border: "1px solid rgba(239, 68, 68, 0.3)",
        borderRadius: 12,
      }}>
        <div style={{ fontSize: "24px", marginBottom: "8px" }}>⚠</div>
        <div>Error loading schedules</div>
        <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
          {error}
        </div>
      </div>
    );
  }

  // Empty state
  if (schedules.length === 0) {
    return (
      <div style={{
        textAlign: "center",
        padding: "48px",
        color: "#94a3b8",
        fontSize: "16px",
        background: "#0b1222",
        border: "1px solid rgba(255,255,255,.12)",
        borderRadius: 12,
      }}>
        <div style={{ fontSize: "48px", marginBottom: "16px", opacity: 0.5 }}>📋</div>
        <div>No schedules found</div>
        <div style={{ fontSize: "14px", marginTop: "8px" }}>
          Try adjusting your search criteria or date range
        </div>
      </div>
    );
  }

  // Results count header
  const resultsHeader = total !== undefined && (
    <div style={{ 
      marginBottom: "16px", 
      fontSize: "14px", 
      color: "#94a3b8",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    }}>
      <span>Showing {schedules.length} of {total} schedules</span>
      <span style={{ fontSize: "12px" }}>
        Click "Legs" button to expand transshipment details
      </span>
    </div>
  );

  return (
    <div>
      {resultsHeader}
      <div style={tableContainerStyle}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Actions</th>
              <th style={thStyle}>Departure (LOCODE)</th>
              <th style={thStyle}>Arrival (LOCODE)</th>
              <th style={thStyle}>Carrier+SCAC</th>
              <th style={thStyle}>Service</th>
              <th style={thStyle}>Vessel/Voyage/IMO</th>
              <th style={thStyle}>ETD</th>
              <th style={thStyle}>ETA</th>
              <th style={thStyle}>Transit (days)</th>
              <th style={thStyle}>Routing</th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((schedule) => {
              const isExpanded = expandedRows.has(schedule.id);
              const legs = getScheduleLegs(schedule);
              const hasLegsData = schedule.legs && schedule.legs.length > 0;
              
              return (
                <React.Fragment key={schedule.id}>
                  <tr style={{ cursor: "pointer" }} onClick={() => toggleRowExpansion(schedule.id)}>
                    <td style={tdStyle}>
                      {hasLegsData ? (
                        <button
                          style={expanderButtonStyle}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleRowExpansion(schedule.id);
                          }}
                          aria-label={isExpanded ? "Collapse leg details" : "Expand leg details"}
                        >
                          {isExpanded ? "▼" : "▶"} Legs
                        </button>
                      ) : (
                        <span style={{ ...expanderButtonStyle, opacity: 0.5, cursor: "not-allowed" }}>
                          -
                        </span>
                      )}
                    </td>
                    <td style={tdStyle}>
                      <div>{schedule.origin}</div>
                      <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "monospace" }}>
                        {extractLocode(schedule.origin)}
                      </div>
                    </td>
                    <td style={tdStyle}>
                      <div>{schedule.destination}</div>
                      <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "monospace" }}>
                        {extractLocode(schedule.destination)}
                      </div>
                    </td>
                    <td style={tdStyle}>
                      <div>{schedule.carrier}</div>
                      <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "monospace" }}>
                        {extractCarrierScac(schedule.carrier)}
                      </div>
                    </td>
                    <td style={tdStyle}>{schedule.service || "-"}</td>
                    <td style={tdStyle}>
                      <div>{schedule.vessel}</div>
                      <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                        Voyage: {schedule.voyage}
                      </div>
                      {schedule.imo && (
                        <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "monospace" }}>
                          IMO: {schedule.imo}
                        </div>
                      )}
                    </td>
                    <td style={tdStyle}>{formatDate(schedule.etd)}</td>
                    <td style={tdStyle}>{formatDate(schedule.eta)}</td>
                    <td style={tdStyle}>
                      <span style={{ fontWeight: 600 }}>{schedule.transitDays}</span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ 
                        color: schedule.routingType === "Direct" ? "#10b981" : "#f59e0b",
                        fontWeight: 500,
                      }}>
                        {schedule.routingType}
                      </span>
                    </td>
                  </tr>
                  
                  {isExpanded && hasLegsData && (
                    <tr>
                      <td colSpan={10} style={expandedRowStyle}>
                        <div style={{ padding: "8px" }}>
                          <h4 style={{ 
                            margin: "0 0 12px 0", 
                            color: "#3b82f6", 
                            fontSize: "14px",
                            fontWeight: 600,
                          }}>
                            Journey Legs ({legs.length} leg{legs.length !== 1 ? 's' : ''})
                          </h4>
                          
                          <table style={legTableStyle}>
                            <thead>
                              <tr>
                                <th style={legThStyle}># Leg</th>
                                <th style={legThStyle}>From LOCODE → To LOCODE</th>
                                <th style={legThStyle}>Ports</th>
                                <th style={legThStyle}>Vessel/Voyage</th>
                                <th style={legThStyle}>ETD</th>
                                <th style={legThStyle}>ETA</th>
                                <th style={legThStyle}>Transit Days</th>
                              </tr>
                            </thead>
                            <tbody>
                              {legs.map((leg, index) => (
                                <tr key={index}>
                                  <td style={legTdStyle}>
                                    <strong>#{leg.legNumber}</strong>
                                  </td>
                                  <td style={legTdStyle}>
                                    <span style={{ fontFamily: "monospace", color: "#3b82f6" }}>
                                      {leg.fromLocode} → {leg.toLocode}
                                    </span>
                                  </td>
                                  <td style={legTdStyle}>
                                    <div>{leg.fromPort}</div>
                                    <div style={{ fontSize: "11px", color: "#94a3b8" }}>to</div>
                                    <div>{leg.toPort}</div>
                                  </td>
                                  <td style={legTdStyle}>
                                    <div>{leg.vessel}</div>
                                    <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                                      Voyage: {leg.voyage}
                                    </div>
                                  </td>
                                  <td style={legTdStyle}>{formatDateTime(leg.etd)}</td>
                                  <td style={legTdStyle}>{formatDateTime(leg.eta)}</td>
                                  <td style={legTdStyle}>
                                    <span style={{ fontWeight: 600, color: "#10b981" }}>
                                      {leg.transitDays} day{leg.transitDays !== 1 ? 's' : ''}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}