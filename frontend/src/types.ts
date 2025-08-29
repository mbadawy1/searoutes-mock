// frontend/src/types.ts
// Shared TypeScript types for the shipping schedule application

export interface ScheduleLeg {
  legNumber: number;
  fromLocode: string;
  fromPort: string;
  toLocode: string;
  toPort: string;
  etd: string; // ISO datetime string
  eta: string; // ISO datetime string
  vessel: string;
  voyage: string;
  transitDays: number;
}

export interface Schedule {
  id: string;
  origin: string;
  destination: string;
  etd: string; // ISO datetime string
  eta: string; // ISO datetime string
  vessel: string;
  voyage: string;
  imo?: string;
  routingType: string; // "Direct" | "Transshipment"
  transitDays: number;
  carrier: string;
  service?: string;
  equipment?: string; // "20DC", "40DC", "40HC", "40RF", etc.
  legs?: ScheduleLeg[]; // Detailed leg information for multi-leg journeys
  hash?: string; // Searoutes itinerary hash for CO2 details lookup
}

export interface PortItem {
  name: string;
  locode: string;
  country: string;
  countryName?: string;
  aliases?: string[];
}

export interface CarrierItem {
  name: string;
  scac: string;
  id?: string;
}

export interface SearchParams {
  origin?: string;
  destination?: string;
  from?: string; // ISO date string
  to?: string; // ISO date string
  equipment?: string;
  carrier?: string;
  routingType?: string;
  sort?: 'etd' | 'transit';
  page?: number;
  pageSize?: number;
  nContainers?: number; // Number of containers (default 1, affects CO₂ calculations)
}

export interface SchedulesResponse {
  items: Schedule[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiError {
  code?: string;
  message: string;
}