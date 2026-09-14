import logging
import os
from pathlib import Path
from typing import Optional, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class GoogleSheetsExporter:
    """Exporter for syncing local CSV/database entity data to Google Sheets using gspread."""

    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json")

    def export_csv_to_sheets(self, csv_dir: str = "data/exports", spreadsheet_title: str = "AI Data Intelligence Output") -> Optional[str]:
        """
        Upload local CSV files to Google Sheets tabs if gspread and service account credentials are provided.
        Returns web URL of the created/updated Google Sheet if successful.
        """
        if not Path(self.credentials_path).is_file():
            logger.warning(
                f"Google Sheets credentials file '{self.credentials_path}' not found. "
                "To enable automatic Google Sheets export, place your Service Account credentials JSON file "
                "and set GOOGLE_SHEETS_CREDENTIALS_PATH in your .env file."
            )
            return None

        try:
            import gspread
            gc = gspread.service_account(filename=self.credentials_path)
            sh = gc.open_or_create(spreadsheet_title)

            csv_folder = Path(csv_dir)
            for csv_file in csv_folder.glob("*.csv"):
                df = pd.read_csv(csv_file)
                sheet_name = csv_file.stem.replace("_", " ").title()

                try:
                    worksheet = sh.worksheet(sheet_name)
                    worksheet.clear()
                except gspread.WorksheetNotFound:
                    worksheet = sh.add_worksheet(title=sheet_name, rows=len(df)+10, cols=len(df.columns)+5)

                worksheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
                logger.info(f"Successfully updated Google Sheets tab '{sheet_name}' ({len(df)} rows)")

            sheet_url = f"https://docs.google.com/spreadsheets/d/{sh.id}"
            logger.info(f"Google Sheets Export Complete: {sheet_url}")
            return sheet_url

        except ImportError:
            logger.warning("gspread library not installed. Install via 'pip install gspread' to enable automated Google Sheets export.")
            return None
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {e}")
            return None
