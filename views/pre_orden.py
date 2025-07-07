import streamlit as st
from forms.pre_orden_form import *
import pytz
from utils.helpers import *
from datetime import datetime
from services.sheets_writer import *
from services.pdf_generator.generate_preorden import generate_archives

def show():

    colombia_timezone = pytz.timezone('America/Bogota')

    if "client" not in st.session_state:
        st.session_state["client"] = None

    if "clients_list" not in st.session_state:
        try:
            st.session_state["clients_list"] = load_clients()
            #st.session_state["clients_list"] = load_client_finance()
        except Exception as e:
            st.error(f"Error al cargar la lista de clientes: {e}")
            st.session_state["clients_list"] = []

    if "start_time" not in st.session_state or st.session_state["start_time"] is None:
        st.session_state["start_time"] = datetime.now(colombia_timezone)

    clients_list = st.session_state["clients_list"]
    start_time = st.session_state["start_time"]

    order_info = forms(clients_list)
    st.write(order_info)

    if st.button("Generar PDFs"):
        # save_anticipo_submission(order_info, start_time)
        register_new_client(order_info.get("client"), st.session_state["clients_list"])
        pdf_ventas = generate_archives(order_info, "ventas")
        pdf_costos = generate_archives(order_info, "costos")

        st.session_state["pdf_paths"] = (pdf_ventas, pdf_costos)
        st.success("Archivos creados exitosamente")

    if "pdf_paths" in st.session_state:
        pdf_ventas, pdf_costos = st.session_state["pdf_paths"]

        col1, col2 = st.columns(2)

        with col1:
            with open(pdf_ventas, "rb") as f:
                st.download_button(
                    label="Descargar Orden de Venta",
                    data=f,                           # puedes pasar el file-like
                    file_name="Orden_Venta.pdf",
                    mime="application/pdf",
                    key="dl_ventas"
                )

        with col2:
            with open(pdf_costos, "rb") as f:
                st.download_button(
                    label="Descargar Pre-orden Costo",
                    data=f,
                    file_name="Pre_orden_costo.pdf",
                    mime="application/pdf",
                    key="dl_costos"
                )
