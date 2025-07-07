import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import streamlit as st
from datetime import datetime
import pytz

# ============ AUTENTICACIÓN GCP ============

credentials = Credentials.from_service_account_info(
    st.secrets["google_sheets_credentials"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
)

client_gcp = gspread.authorize(credentials)
sheets_service = build("sheets", "v4", credentials=credentials)
SPREADSHEET_ID = st.secrets["general"]["time_sheet_id"]
colombia_timezone = pytz.timezone('America/Bogota')

def get_or_create_worksheet(sheet_name: str, headers: list = None):
    try:
        sheet = client_gcp.open_by_key(SPREADSHEET_ID)
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=sheet_name, rows="1000", cols="30")
            if headers:
                worksheet.append_row(headers)
            st.warning(f"Worksheet '{sheet_name}' was created.")
        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("No se encontró la hoja de cálculo.")
        return None

def save_anticipo_submission(data: dict):
    SHEET_NAME = "SOLICITUD DE ANTICIPO"
    headers = [
        "Comercial", "Fecha", "Cliente", "Nombre Cliente", "Teléfono Cliente", "Email Cliente", "Contenedores", 
        "Tipo Servicio", "Tipo Operación", "Referencia", "Recargos", "Total USD", "Total COP", "TRM", "Total COP TRM"
    ]

    worksheet = get_or_create_worksheet(SHEET_NAME, headers)
    if not worksheet:
        return

    try:
        # Extraer campos
        commercial = data["commercial"]
        client = data["client"]
        customer_name = data["customer_name"]
        customer_phone = data["customer_phone"]
        customer_email = data["customer_email"]
        operation_type = data["operation_type"]
        reference = data["reference"]
        trm = data["trm"]
        total_cop_trm = data["total_cop_trm"]

        # Contenedores y servicios
        containers = '\n'.join(
            '\n'.join(x) if isinstance(x, list) else x
            for x in data['container_type']
        )
        services = '\n'.join(
            '\n'.join(x) if isinstance(x, list) else x
            for x in data['transport_type']
        )

        # Recargos
        usd_total = 0.0
        cop_total = 0.0
        surcharge_lines = []
        for container_type, surcharges in data["additional_surcharges"].items():
            for surcharge in surcharges:
                cost = surcharge['cost']
                currency = surcharge['currency']
                concept = surcharge['concept']
                surcharge_lines.append(f"{container_type} - {concept}: ${cost:.2f} {currency}")
                if currency == "USD":
                    usd_total += cost
                elif currency == "COP":
                    cop_total += cost

        surcharge_str = '\n'.join(surcharge_lines)

        # Timestamp
        end_time = datetime.now(pytz.utc).astimezone(colombia_timezone)
        timestamp = end_time.strftime('%Y-%m-%d %H:%M:%S')

        # Escribir fila
        row = [
            commercial, timestamp, client, customer_name, customer_phone, customer_email, containers,
            services, operation_type, reference, surcharge_str, usd_total, cop_total, trm, total_cop_trm
        ]

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        st.success("Datos de solicitud de anticipo guardados correctamente.")
    except Exception as e:
        st.error(f"Error guardando datos en hoja de anticipo: {e}")

def register_new_client(client_name, clients_list):
    from utils.helpers import load_clients
    if not client_name: return

    client_normalized = client_name.strip().lower()
    normalized_existing = [c.strip().lower() for c in clients_list]

    if client_normalized not in normalized_existing:
        sheet = client_gcp.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet("clientes")
        worksheet.append_row([client_name])
        st.session_state["clients_list"].append(client_name)
        st.session_state["client"] = None
        load_clients.clear()
        st.rerun()


