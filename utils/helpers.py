import streamlit as st
import gspread
import pandas as pd

@st.cache_data(ttl=3600)
def load_clients():
    sheet_name = "clientes"
    time_sheet_id = st.secrets["general"]["time_sheet_id"]

    credentials = st.secrets["google_sheets_credentials"]
    gc = gspread.service_account_from_dict(credentials)

    try:
        sheet = gc.open_by_key(time_sheet_id)
        if sheet_name not in [ws.title for ws in sheet.worksheets()]:
            return []

        worksheet = sheet.worksheet(sheet_name)
        clientes = worksheet.col_values(1)
        return clientes[1:]
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("No se encontró la hoja de cálculo con el ID proporcionado.")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"No se encontró la pestaña '{sheet_name}' en la hoja de cálculo.")
    except Exception as e:
        st.error(f"Error al cargar los clientes desde Google Sheets: {e}")
    
    return []

def user_data(commercial):
    users = {
        "Sharon Zuñiga": {
            "name": "Sharon Zuñiga",
            "tel": "+57 (300) 510 0295",
            "position": "Business Development Manager Latam & USA",
            "email": "sales2@tradingsolutions.com"
        },
        "Irina Paternina": {
            "name": "Irina Paternina",
            "tel": "+57 (301) 3173340",
            "position": "Business Executive",
            "email": "sales1@tradingsolutions.com"
        },
        "Johnny Farah": {
            "name": "Johnny Farah",
            "tel": "+57 (301) 6671725",
            "position": "Manager of Americas",
            "email": "sales3@tradingsolutions.com"
        },
        "Jorge Sánchez": {
            "name": "Jorge Sánchez",
            "tel": "+57 (301) 7753510",
            "position": "Reefer Department Manager",
            "email": "sales4@tradingsolutions.com"
        },
        "Pedro Luis Bruges": {
            "name": "Pedro Luis Bruges",
            "tel": "+57 (304) 4969358",
            "position": "Global Sales Manager",
            "email": "sales@tradingsolutions.com"
        },
        "Ivan Zuluaga": {
            "name": "Ivan Zuluaga",
            "tel": "+57 (300) 5734657",
            "position": "Business Development Manager Latam & USA",
            "email": "sales5@tradingsolutions.com"
        },
        "Andrés Consuegra": { 
            "name": "Andrés Consuegra",
            "tel": "+57 (301) 7542622",
            "position": "CEO",
            "email": "manager@tradingsolutions.com"
        },
        "Stephanie Bruges": {
            "name": "Stephanie Bruges",
            "tel": "+57 300 4657077",
            "position": "Business Development Specialist",
            "email": "bds@tradingsolutions.com"
        },
        "Catherine Silva": {
            "name": "Catherine Silva",
            "tel": "+57 304 4969351",
            "position": "Inside Sales",
            "email": "insidesales@tradingsolutions.com"
        }
    }

    return users.get(commercial, {"name": commercial, "position": "N/A", "tel": "N/A", "email": "N/A"})

def safe_strip(value):
    return str(value).strip() if value else ""

def validate_request_data(data):
    errors = []
    requires_trm = False

    if not safe_strip(data.get("no_solicitud")):
        errors.append("⚠️ The 'Request Number (M)' field is required.")

    if not safe_strip(data.get("commercial")) or data["commercial"] == " ":
        errors.append("⚠️ Please select a Sales Representative.")

    if not safe_strip(data.get("client")) or data["client"] == " ":
        errors.append("⚠️ Please select a Client.")

    if not safe_strip(data.get("customer_name")):
        errors.append("⚠️ The 'Customer Name' field is required.")

    if not data.get("container_type"):
        errors.append("⚠️ Please select at least one Container Type.")

    if not data.get("transport_type"):
        errors.append("⚠️ Please select at least one Transport Service.")

    if not safe_strip(data.get("operation_type")):
        errors.append("⚠️ The 'Operation Type' field is required.")

    for cont, surcharges in data.get("additional_surcharges", {}).items():
        for i, surcharge in enumerate(surcharges):
            if not safe_strip(surcharge.get("concept")):
                errors.append(f"⚠️ Surcharge concept in '{cont}' #{i+1} is required.")
            if surcharge.get("currency") not in ['USD', 'COP']:
                errors.append(f"⚠️ Please select a valid currency for surcharge in '{cont}' #{i+1}.")
            if surcharge.get("cost", 0.0) <= 0:
                errors.append(f"⚠️ The surcharge amount in '{cont}' #{i+1} must be greater than 0.")

    return errors

def load_client_finance():
    data = pd.read_excel('resources/data/datos finanzas.xlsx')
    return data