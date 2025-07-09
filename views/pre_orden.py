import streamlit as st
from forms.pre_orden_form import *
import pytz
from utils.helpers import *
from datetime import datetime
from services.sheets_writer import save_order_submission, register_new_client
from services.pdf_generator.generate_preorden import generate_archives

def show():

    colombia_timezone = pytz.timezone('America/Bogota')

    if "client_finance" not in st.session_state:
        st.session_state["client_finance"] = None

    if "clients_list_finance" not in st.session_state:
        try:
            st.session_state["clients_list_finance"] = load_clients_finance()
        except Exception as e:
            st.error(f"Error al cargar la lista de clientes: {e}")
            st.session_state["clients_list_finance"] = []

    if "start_time" not in st.session_state or st.session_state["start_time"] is None:
        st.session_state["start_time"] = datetime.now(colombia_timezone)

    clients_list_finance = st.session_state["clients_list_finance"]
    start_time = st.session_state["start_time"]

    order_info = forms(clients_list_finance)

    if st.button("Generar PDFs"):
        save_order_submission(order_info)
        register_new_client(order_info.get("client_finance"), st.session_state["clients_list_finance"])
        pdf_ventas = generate_archives(order_info, "ventas")
        pdf_costos = generate_archives(order_info, "costos")

        st.session_state["pdf_paths"] = (pdf_ventas, pdf_costos)
        st.success("Archivos creados exitosamente")

    if "pdf_paths" in st.session_state:
        pdf_ventas, pdf_costos = st.session_state["pdf_paths"]

        no_solicitud = order_info.get("no_solicitud", "")

        col1, col2 = st.columns(2)

        with col1:
            with open(pdf_ventas, "rb") as f:
                st.download_button(
                    label="Descargar Orden de Venta",
                    data=f,                       
                    file_name=f"ORDEN {no_solicitud}.pdf",
                    mime="application/pdf",
                    key="dl_ventas"
                )

        with col2:
            with open(pdf_costos, "rb") as f:
                st.download_button(
                    label=f"Descargar Pre-orden Costo.pdf",
                    data=f,
                    file_name=f"COSTO {no_solicitud}.pdf",
                    mime="application/pdf",
                    key="dl_costos"
                )
