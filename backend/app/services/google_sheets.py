import os
import pathlib
import gspread

# We assume credentials.json is at backend/credentials.json
_CREDENTIALS_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "credentials.json"

def _get_worksheet():
    """Authenticates and returns the first worksheet of the specified Google Sheet."""
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID environment variable is not set")
    
    if not _CREDENTIALS_PATH.exists():
        raise FileNotFoundError(f"Credentials file not found at {_CREDENTIALS_PATH}")

    # Authenticate using the service account credentials file
    gc = gspread.service_account(filename=str(_CREDENTIALS_PATH))
    
    # Open the spreadsheet by its ID and return the first sheet
    sh = gc.open_by_key(spreadsheet_id)
    return sh.sheet1

def append_assessment_row(row_dict: dict, headers: list[str]) -> None:
    """
    Appends a new assessment row to the Google Sheet.
    Uses the provided headers list to ensure columns are ordered correctly.
    """
    try:
        ws = _get_worksheet()
        # Ensure row values match the exact order of the CSV headers
        row_values = [str(row_dict.get(col, "")) for col in headers]
        
        # Append the row
        ws.append_row(row_values)
        print(f"[google_sheets] Successfully appended row for assessment_id={row_dict.get('assessment_id')}")
    except Exception as exc:
        print(f"[google_sheets] ⚠️ Failed to append row to Google Sheets: {exc}")
        # We re-raise the exception so the caller can catch it and log if needed,
        # but the caller MUST NOT let it crash the main assessment flow.
        raise

def update_email_by_assessment_id(assessment_id: str, email: str) -> None:
    """
    Finds the row corresponding to the given assessment_id and updates its email column.
    Assumes assessment_id is in the 1st column and email is in the 4th column.
    """
    try:
        ws = _get_worksheet()
        
        # Find the cell containing the assessment_id in the first column
        cell = ws.find(assessment_id, in_column=1)
        if cell:
            # Email is the 4th column (index 4 in 1-based indexing of Google Sheets)
            ws.update_cell(cell.row, 4, email)
            print(f"[google_sheets] Successfully updated email for assessment_id={assessment_id}")
        else:
            print(f"[google_sheets] ⚠️ assessment_id={assessment_id} not found in Google Sheets. Update skipped.")
    except Exception as exc:
        print(f"[google_sheets] ⚠️ Failed to update email in Google Sheets: {exc}")
        raise
