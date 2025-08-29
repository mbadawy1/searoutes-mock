from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ScheduleLeg(BaseModel):
    """ScheduleLeg model representing a single leg of a journey."""

    legNumber: int
    fromLocode: str
    fromPort: str
    toLocode: str
    toPort: str
    etd: str  # ISO datetime string
    eta: str  # ISO datetime string
    vessel: str
    voyage: str
    transitDays: int


class Schedule(BaseModel):
    """Schedule model representing a shipping itinerary."""

    id: str
    origin: str
    destination: str
    etd: str  # ISO datetime string
    eta: str  # ISO datetime string
    vessel: str
    voyage: str
    imo: Optional[str] = None
    routingType: str  # "Direct" | "Transshipment"
    transitDays: int
    carrier: str
    service: Optional[str] = None
    equipment: Optional[str] = None  # "20DC", "40DC", "40HC", "40RF", etc.
    legs: Optional[List[ScheduleLeg]] = None  # Detailed leg information for multi-leg journeys
    hash: Optional[str] = None  # Searoutes itinerary hash for CO2 details lookup
