import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Ambil kredensial dari environment variable
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]

def update_cell(range_name, value):
    service = build("sheets", "v4", credentials=creds)

    body = {
        "values": [[value]]
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    return result