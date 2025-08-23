// frontend/src/lib/date.ts
// Date formatting and parsing utilities

import { format, parse, isValid, addDays, startOfDay } from 'date-fns';

// Display format for inputs: dd/mm/yyyy
export const DISPLAY_FORMAT = 'dd/MM/yyyy';

// ISO format for API: yyyy-mm-dd
export const API_FORMAT = 'yyyy-MM-dd';

/**
 * Format a Date object for display in inputs (dd/mm/yyyy)
 */
export function formatForDisplay(date: Date): string {
  return format(date, DISPLAY_FORMAT);
}

/**
 * Format a Date object for API consumption (yyyy-mm-dd)
 */
export function formatForAPI(date: Date): string {
  return format(date, API_FORMAT);
}

/**
 * Parse a display format string (dd/mm/yyyy) to Date
 */
export function parseDisplayDate(dateString: string): Date | null {
  if (!dateString || dateString.trim() === '') return null;
  
  try {
    const parsed = parse(dateString, DISPLAY_FORMAT, new Date());
    return isValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Parse an API format string (yyyy-mm-dd) to Date
 */
export function parseAPIDate(dateString: string): Date | null {
  if (!dateString || dateString.trim() === '') return null;
  
  try {
    const parsed = parse(dateString, API_FORMAT, new Date());
    return isValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Convert API format (yyyy-mm-dd) to display format (dd/mm/yyyy)
 */
export function apiToDisplay(apiDate: string): string {
  const parsed = parseAPIDate(apiDate);
  return parsed ? formatForDisplay(parsed) : '';
}

/**
 * Convert display format (dd/mm/yyyy) to API format (yyyy-mm-dd)
 */
export function displayToAPI(displayDate: string): string {
  const parsed = parseDisplayDate(displayDate);
  return parsed ? formatForAPI(parsed) : '';
}

/**
 * Validate if a date range is valid (from <= to)
 */
export function isValidDateRange(from: string, to: string): boolean {
  if (!from || !to) return true; // Empty dates are considered valid
  
  const fromDate = parseAPIDate(from);
  const toDate = parseAPIDate(to);
  
  if (!fromDate || !toDate) return false;
  
  return fromDate <= toDate;
}

/**
 * Get preset date ranges
 */
export function getPresetRanges() {
  const today = startOfDay(new Date());
  
  return {
    'Next 7 days': {
      from: today,
      to: addDays(today, 6)
    },
    'Next 14 days': {
      from: today,
      to: addDays(today, 13)
    }
  };
}

/**
 * Normalize a date to start of day to avoid timezone issues
 */
export function normalizeDate(date: Date): Date {
  return startOfDay(date);
}