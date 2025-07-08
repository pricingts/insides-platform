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
ORDEN_ID = st.secrets["general"]["orden_sheet"]
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

def get_or_create_worksheet_orden(sheet_name: str, headers: list = None):
    try:
        sheet = client_gcp.open_by_key(ORDEN_ID)
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

def save_order_submission(order_info: dict):

    SHEET_NAME = "ORDEN"
    headers = [
        "Comercial", "Fecha", "No Solicitud", "Datos Cliente",
        "BL/AWB", "Shipper", "Consignee", "Ruta (POL -> POD)", "Referencia",
        "Tipo Carga", "Detalles de la Carga",
        "Seguro",
        "Recargos Venta", "Total Venta", "Recargos Costo", "Total Costo", "Profit",
        "Comentarios Finales"
    ]

    worksheet = get_or_create_worksheet_orden(SHEET_NAME, headers)
    if not worksheet:
        return

    try:
        commercial = order_info["commercial"]
        no_solicitud = order_info["no_solicitud"]

        datos_cliente = (
            f"Nombre: {order_info['client']}\n"
            f"Teléfono: {order_info['customer_phone']}\n"
            f"Dirección: {order_info['customer_address']}\n"
            f"Cuenta: {order_info['customer_account']}\n"
            f"NIT: {order_info['customer_nit']}\n"
            f"Contacto: {order_info['customer_contact']}\n"
            f"Email: {order_info['customer_email']}"
        )

        bl_awb = order_info["bl_awb"]
        shipper = order_info["shipper"]
        consignee = order_info["consignee"]
        ruta = f"{order_info['pol_aol']} -> {order_info['pod_aod']}"
        reference = order_info["reference"]

        cargo_type = order_info["cargo_type"]
        container_details = order_info["container_details"]
        unidad_medida = order_info["unidad_medida"]
        cantidad_suelta = order_info["cantidad_suelta"]

        if container_details:
            carga_lines = []
            for c_type, details in container_details.items():
                for name in details["names"]:
                    carga_lines.append(f"{c_type}: {name}")
            carga_str = '\n'.join(carga_lines)
        else:
            carga_str = f"{cantidad_suelta} {unidad_medida}"

        insurance_required = order_info["insurance_required"]
        valor_carga = order_info["valor_carga"]
        porcentaje_seguro = order_info["porcentaje_seguro"]

        if insurance_required:
            valor_asegurado = float(valor_carga) * float(porcentaje_seguro) / 100
            seguro_str = f"Sí\nValor carga: {valor_carga}\nPorcentaje seguro: {porcentaje_seguro}%\nValor asegurado: {valor_asegurado:.2f}"
        else:
            seguro_str = "No"

        sales_totals = {}
        sales_lines = []
        for s in order_info["sales_surcharges"]:
            total = s.get("total", 0.0)
            currency = s.get("currency", "")
            sales_lines.append(f"{s.get('concept', '')}: {s.get('quantity', 0)} × {s.get('rate', 0)} = {total:.2f} {currency}")
            sales_totals[currency] = sales_totals.get(currency, 0.0) + total
        sales_surcharge_str = '\n'.join(sales_lines)
        total_venta_str = '\n'.join(f"{currency}: {amount:.2f}" for currency, amount in sales_totals.items())

        cost_totals = {}
        cost_lines = []
        for s in order_info["cost_surcharges"]:
            total = s.get("total", 0.0)
            currency = s.get("currency", "")
            cost_lines.append(f"{s.get('concept', '')}: {s.get('quantity', 0)} × {s.get('rate', 0)} = {total:.2f} {currency}")
            cost_totals[currency] = cost_totals.get(currency, 0.0) + total
        cost_surcharge_str = '\n'.join(cost_lines)
        total_costo_str = '\n'.join(f"{currency}: {amount:.2f}" for currency, amount in cost_totals.items())

        profit_str = '\n'.join(
            f"{currency}: {sales_totals.get(currency, 0.0) - cost_totals.get(currency, 0.0):.2f}"
            for currency in set(sales_totals) | set(cost_totals)
        )

        timestamp = datetime.now(pytz.utc).astimezone(colombia_timezone).strftime('%Y-%m-%d %H:%M:%S')

        row = [
            commercial, timestamp, no_solicitud, datos_cliente,
            bl_awb, shipper, consignee, ruta, reference,
            cargo_type, carga_str,
            seguro_str,
            sales_surcharge_str, total_venta_str,
            cost_surcharge_str, total_costo_str,
            profit_str,
            order_info["final_comments"]
        ]

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        st.success("Datos de la ORDEN guardados correctamente.")

    except Exception as e:
        st.error(f"Error guardando datos en hoja ORDEN: {e}")

