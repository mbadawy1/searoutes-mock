from fastapi import APIRouter, Query
from fastapi.responses import Response
from typing import Optional
import csv
import io
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from ..providers.base import ScheduleFilter, Page, ScheduleProvider

router = APIRouter()
provider: ScheduleProvider = None  # Will be injected by main.py


def set_provider(schedule_provider: ScheduleProvider):
    """Inject the schedule provider instance."""
    global provider
    provider = schedule_provider


def extract_locode(location: str) -> str:
    """
    Extract LOCODE from location string.
    Maps full location names to UN/LOCODEs for CSV export.
    """
    locode_map = {
        "Alexandria, EG": "EGALY",
        "Tanger, MA": "MATNG", 
        "Rotterdam, NL": "NLRTM",
        "Damietta, EG": "EGDAM",
        "Valencia, ES": "ESVLC",
        "Port Said, EG": "EGPSD",
        "Barcelona, ES": "ESBCN",
        "Hamburg, DE": "DEHAM",
        "Le Havre, FR": "FRLEH",
        "Genoa, IT": "ITGOA",
        "Piraeus, GR": "GRPIR",
        "Antwerp, BE": "BEANR",
        "Singapore, SG": "SGSIN",
        "Dubai, AE": "AEDXB",
        "Jeddah, SA": "SAJED",
        # Add more mappings as needed
    }
    
    return locode_map.get(location, location.split(',')[0][:5].upper())


@router.get("/api/schedules")
def list_schedules(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    equipment: Optional[str] = None,
    routingType: Optional[str] = None,
    carrier: Optional[str] = None,
    sort: str = "etd",
    page: int = 1,
    pageSize: int = 50,
):
    """
    List schedules with filtering, sorting, and pagination.

    Query parameters:
    - origin: Origin port (partial match)
    - destination: Destination port (partial match)
    - from: Start date for ETD window (alias for date_from)
    - to: End date for ETD window (alias for date_to)
    - equipment: Container equipment type
    - routingType: Direct or Transshipment
    - carrier: Shipping line/carrier name (partial match)
    - sort: Sort field (etd|transit)
    - page: Page number (1-based)
    - pageSize: Items per page

    Returns:
    - items: List of schedule objects
    - total: Total number of items matching filters
    - page: Current page number
    - pageSize: Items per page
    """
    filt = ScheduleFilter(
        origin=origin,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        equipment=equipment,
        routingType=routingType,
        carrier=carrier,
        sort=sort,
    )

    page_params = Page(page=page, pageSize=pageSize)
    items, meta = provider.list(filt, page_params)

    # Return the exact envelope format specified in the contract
    return {
        "items": [item.model_dump() for item in items],
        "total": meta.total,
        "page": meta.page,
        "pageSize": meta.pageSize,
    }


@router.get("/api/schedules.csv")
def export_schedules_csv(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    equipment: Optional[str] = None,
    routingType: Optional[str] = None,
    carrier: Optional[str] = None,
    sort: str = "etd",
):
    """
    Export schedules as CSV with filtering and sorting.
    
    This endpoint uses the same filters and sorting as the main schedules endpoint,
    but ignores pagination and returns all matching results in CSV format.
    
    CSV columns (in order):
    originLocode,destinationLocode,etd,eta,vessel,voyage,carrier,routingType,transitDays,service
    """
    # Use same filter logic as main endpoint
    filt = ScheduleFilter(
        origin=origin,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        equipment=equipment,
        routingType=routingType,
        carrier=carrier,
        sort=sort,
    )

    # Get ALL results (ignore pagination for exports)
    page_params = Page(page=1, pageSize=10000)  # Large page size to get all results
    items, meta = provider.list(filt, page_params)

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row with exact column order from spec
    writer.writerow([
        "originLocode",
        "destinationLocode", 
        "etd",
        "eta",
        "vessel",
        "voyage",
        "carrier",
        "routingType",
        "transitDays",
        "service"
    ])
    
    # Write data rows
    for item in items:
        writer.writerow([
            extract_locode(item.origin),
            extract_locode(item.destination),
            item.etd,
            item.eta,
            item.vessel,
            item.voyage,
            item.carrier,
            item.routingType,
            item.transitDays,
            item.service or ""  # Handle None values
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    # Return CSV with proper headers
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=schedules.csv"
        }
    )


@router.get("/api/schedules.xlsx")
def export_schedules_xlsx(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
    equipment: Optional[str] = None,
    routingType: Optional[str] = None,
    carrier: Optional[str] = None,
    sort: str = "etd",
):
    """
    Export schedules as Excel (.xlsx) with filtering and sorting.
    
    This endpoint uses the same filters and sorting as the main schedules endpoint,
    but ignores pagination and returns all matching results in Excel format.
    
    Creates a workbook with a "Schedules" sheet containing the same columns as CSV:
    originLocode,destinationLocode,etd,eta,vessel,voyage,carrier,routingType,transitDays,service
    """
    # Use same filter logic as main endpoint
    filt = ScheduleFilter(
        origin=origin,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        equipment=equipment,
        routingType=routingType,
        carrier=carrier,
        sort=sort,
    )

    # Get ALL results (ignore pagination for exports)
    page_params = Page(page=1, pageSize=10000)  # Large page size to get all results
    items, meta = provider.list(filt, page_params)

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Schedules"
    
    # Define headers with exact column order from spec
    headers = [
        "originLocode",
        "destinationLocode", 
        "etd",
        "eta",
        "vessel",
        "voyage",
        "carrier",
        "routingType",
        "transitDays",
        "service"
    ]
    
    # Write header row
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=header)
    
    # Write data rows
    for row_idx, item in enumerate(items, 2):  # Start from row 2 (after header)
        ws.cell(row=row_idx, column=1, value=extract_locode(item.origin))
        ws.cell(row=row_idx, column=2, value=extract_locode(item.destination))
        ws.cell(row=row_idx, column=3, value=item.etd)
        ws.cell(row=row_idx, column=4, value=item.eta)
        ws.cell(row=row_idx, column=5, value=item.vessel)
        ws.cell(row=row_idx, column=6, value=item.voyage)
        ws.cell(row=row_idx, column=7, value=item.carrier)
        ws.cell(row=row_idx, column=8, value=item.routingType)
        ws.cell(row=row_idx, column=9, value=item.transitDays)
        ws.cell(row=row_idx, column=10, value=item.service or "")
    
    # Auto-adjust column widths
    for col_idx in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_idx)
        ws.column_dimensions[column_letter].auto_size = True
    
    # Save to BytesIO buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    excel_content = output.getvalue()
    output.close()
    
    # Return Excel with proper headers
    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=schedules.xlsx"
        }
    )
