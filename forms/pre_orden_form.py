import streamlit as st
import pandas as pd
from services.sheets_writer import save_new_client_finance

def forms(df_clients):
    if "client_new" in st.session_state:
        st.session_state["client"] = st.session_state.pop("client_new")

    df_clients = df_clients.drop_duplicates(subset="CLIENTE")
    clients_list = df_clients["CLIENTE"].dropna().unique().tolist()
    client_lookup = df_clients.set_index("CLIENTE").to_dict(orient="index")

    customer_phone   = ""
    customer_address = ""
    customer_account = ""
    customer_nit     = ""
    customer_contact = ""
    customer_email   = ""
    new_client_name  = ""

    col1, col2 = st.columns(2)

    commercial_op = [" ","Pedro Luis Bruges", "Andrés Consuegra", "Ivan Zuluaga", "Sharon Zuñiga",
            "Johnny Farah", "Felipe Hoyos", "Jorge Sánchez",
            "Irina Paternina", "Stephanie Bruges"]
    
    paises = ["Colombia", "Estados Unidos", "Ecuador", "Mexico"]

    with col1:
        commercial = st.selectbox("Comercial*", commercial_op, key="commercial")
    with col2:
        no_solicitud = st.text_input("Número del Caso (M)*", key="no_solicitud")

    with st.expander("**Información del Cliente**", expanded=True):
        client = st.selectbox("Selecciona el cliente*", [" "] + ["+ Add New"] + clients_list, key="client")

        if client in client_lookup:
            client_info = client_lookup[client]

            col1, col2, col3 = st.columns(3)
            with col1:
                customer_phone = st.text_input("Teléfono", value=client_info.get("TELEFONO CONTACTO", ""), key="customer_phone")
            with col2:
                customer_address = st.text_input("Dirección", value="", key="customer_address")  # No está en DB
            with col3:
                customer_account = st.selectbox("País de Emisión", paises, key="customer_account")

            col4, col5, col6 = st.columns(3)
            with col4:
                customer_nit = st.text_input("NIT", value=client_info.get("NIT", ""), key="customer_nit")
            with col5:
                customer_contact = st.text_input("Contact", value=client_info.get("CONTACTO", ""), key="customer_contact")
            with col6:
                customer_email = st.text_input("Email", value=client_info.get("CORREO ELECTRONICO CONTACTO", ""), key="customer_email")

        elif client == "+ Add New":
            st.write("### Agregar Nuevo Cliente")

            new_client_name = st.text_input("Nombre del Cliente*", key="new_client_name")

            col1, col2, col3 = st.columns(3)
            with col1:
                customer_phone = st.text_input("Teléfono*", key="customer_phone")
            with col2:
                customer_address = st.text_input("Dirección", key="customer_address")
            with col3:
                customer_account = st.selectbox("País de Emisión", paises, key="customer_account")

            col4, col5, col6 = st.columns(3)
            with col4:
                customer_nit = st.text_input("NIT*", key="customer_nit")
            with col5:
                customer_contact = st.text_input("Contacto*", key="customer_contact")
            with col6:
                customer_email = st.text_input("Correo Electrónico*", key="customer_email")

            if st.button("Guardar Nuevo Cliente"):
                campos_ok = all([
                    new_client_name, customer_nit, customer_email,
                    customer_contact, customer_phone, customer_address,
                ])

                if not campos_ok:
                    st.error("⚠️ Por favor completa todos los campos obligatorios marcados con *.")
                elif new_client_name in clients_list:
                    st.warning("⚠️ Este cliente ya existe.")
                else:
                    new_row = [
                        customer_nit,
                        new_client_name,
                        new_client_name,
                        customer_email,
                        customer_contact,
                        customer_phone,
                        customer_email,   
                        customer_address,
                    ]
                    try:
                        save_new_client_finance(new_row)          
                        st.success(f"✅ Cliente '{new_client_name}' guardado con éxito.")

                        st.session_state["client_new"] = new_client_name
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")

    with st.expander("**Información de la Carga**", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            bl_awb = st.text_input("BL/AWB*", key="bl_awb")
        with col2:
            shipper = st.text_input("Shipper*", key="shipper")
        with col3:
            consignee = st.text_input("Consignee*", key="consignee")
        
        col3, col4 = st.columns(2)
        with col3:
            pol_aol = st.text_input("POL/AOD*", key="pol_aol")
        with col4:
            pod_aod = st.text_input("POD/AOD*", key="pod_aod")

        reference = st.text_area("Referencia*", key="reference")

        col5, col6, col7 = st.columns(3)

        with col5:
            cargo_type = st.selectbox('Seleccione el tipo de carga', ['Contenedor', 'Carga suelta'], key='cargo_type')

        if cargo_type == "Contenedor":
            with col6:
                container_op = [
                    "20' Dry Standard", "40' Dry Standard", "40' Dry High Cube", "Reefer 20'",
                    "Reefer 40'", "Open Top 20'", "Open Top 40'", "Flat Rack 20'", "Flat Rack 40'"
                ]

                selected_types = st.multiselect(
                    "Tipos de contenedor*", container_op, key="container_type"
                )

            container_data = {}                      # {c_type: {"qty": int, "names": [str, ...]}}

            if selected_types:
                rows = (len(selected_types) + 1) // 2
                for i in range(rows):
                    cols = st.columns(2)
                    for j in range(2):
                        idx = i * 2 + j
                        if idx < len(selected_types):
                            c_type = selected_types[idx]

                            qty_key   = f"qty_{c_type}"
                            base_name = f"name_{c_type}"     # base para claves únicas

                            with cols[j]:
                                # ---------- Cantidad ----------
                                qty = st.number_input(
                                    f"Cantidad para {c_type}*", min_value=0, step=1,
                                    key=qty_key
                                )
                                qty_int = int(qty)         

                                # ---------- Nombres ----------
                                names = []
                                for n in range(qty_int):    
                                    name_key = f"{base_name}_{n}"
                                    name = st.text_input(
                                        f"Nombre {n+1} para {c_type}",
                                        placeholder="Ej. Equipo médico",
                                        key=name_key
                                    )
                                    names.append(name)

                            container_data[c_type] = {
                                "qty": qty_int,
                                "names": names              
                            }

        else:
            with col6:
                unidad_medida = st.selectbox("Unidad de Medida*", ['KG', 'CBM', 'KV'], key='unidad_medida')

            with col7:
                cant_suelta = st.number_input('Cantidad*', min_value=0, step=1, key='cantidad_suelta')
        
        insurance = st.checkbox('Requiere Seguro', key='insurance')
        if insurance:
            col8, col9, col10 = st.columns(3)
            with col8:
                valor_carga = st.number_input('Valor de la Carga', min_value=0.0, step=0.1, key='valor_carga')
            with col9:
                porcentaje = st.number_input('Porcentaje (%)', min_value=0.0, step=0.1, key='porcentaje')
            with col10:
                valor_seguro = valor_carga * (porcentaje / 100)
                st.write("**Valor del seguro**")
                st.write(valor_seguro)

    with st.expander("**Ventas**", expanded=True):
        if "sales_surcharges" not in st.session_state or not isinstance(st.session_state["sales_surcharges"], list):
            st.session_state["sales_surcharges"] = []

        def remove_sales_surcharge(index):
            if 0 <= index < len(st.session_state["sales_surcharges"]):
                st.session_state["sales_surcharges"].pop(index)

        def add_sales_surcharge():
            st.session_state["sales_surcharges"].append({"concept": "", "quantity": 0, "rate": 0.0 , "total": 0.0, "currency": "USD"})

        for i, surcharge in enumerate(st.session_state["sales_surcharges"]):
            col1, col2, col3, col4, col5, col6 = st.columns([2.5, 0.5, 0.8, 0.8, 0.7, 0.5])

            with col1:
                surcharge["concept"] = st.text_input(f"Concept*", surcharge["concept"], key=f'sale_concept_{i}')
            
            with col2:
                surcharge["quantity"] = st.number_input(f"Quantity*", surcharge["quantity"], key=f'sale_quantity_{i}')
            
            with col3:
                surcharge["rate"] = st.number_input(f"Rate*", surcharge["rate"], key=f'sale_rate_{i}')
            
            with col4:
                computed_total = surcharge["rate"] * surcharge["quantity"]
                surcharge["total"] = st.number_input(f"Total*", computed_total, key=f'sale_total_{i}')

            with col5:
                surcharge["currency"] = st.selectbox(
                    f"Currency*", ['USD', 'COP', 'MXN'],
                    index=['USD', 'COP', 'MXN'].index(surcharge["currency"]),
                    key=f'sale_currency_{i}'
                )

            with col6:
                st.write(" ")
                st.write(" ")
                if st.button("❌", key=f'remove_sale_{i}'):
                    remove_sales_surcharge(i)
                    st.rerun()

        st.button("➕ Add Surcharge", key="add_sale_surcharge", on_click=add_sales_surcharge)

        sales_totals = {}
        for surcharge in st.session_state["sales_surcharges"]:
            currency = surcharge["currency"]
            value = surcharge.get("total", 0.0)
            sales_totals[currency] = sales_totals.get(currency, 0.0) + value

        for currency, amount in sales_totals.items():
            st.markdown(f"**Total {currency}**: {amount:,.2f} {currency}")

    with st.expander("**Costos**", expanded=True):
        if "cost_surcharges" not in st.session_state or not isinstance(st.session_state["cost_surcharges"], list):
            st.session_state["cost_surcharges"] = []

        def remove_cost_surcharge(index):
            if 0 <= index < len(st.session_state["cost_surcharges"]):
                st.session_state["cost_surcharges"].pop(index)

        def add_cost_surcharge():
            st.session_state["cost_surcharges"].append({"concept": "", "quantity": 0, "rate": 0.0 , "total": 0.0, "currency": "USD"})

        for i, surcharge in enumerate(st.session_state["cost_surcharges"]):

            col1, col2, col3, col4, col5, col6 = st.columns([2.5, 0.5, 0.8, 0.8, 0.7, 0.5])

            with col1:
                surcharge["concept"] = st.text_input(f"Concept*", surcharge["concept"], key=f'cost_concept_{i}')

            with col2:
                surcharge["quantity"] = st.number_input(f"Quantity*", surcharge["quantity"], key=f'cost_quantity_{i}')

            with col3:
                surcharge["rate"] = st.number_input(f"Rate*", surcharge["rate"], key=f'cost_rate_{i}')

            with col4:
                computed_total = surcharge["rate"] * surcharge["quantity"]
                surcharge["total"] = st.number_input(f"Total*", computed_total, key=f'cost_total_{i}')

            with col5:
                surcharge["currency"] = st.selectbox(
                    f"Currency*", ['USD', 'COP', 'MXN'],
                    index=['USD', 'COP', 'MXN'].index(surcharge["currency"]),
                    key=f'cost_currency_{i}'
                )

            with col6:
                st.write(" ")
                st.write(" ")
                if st.button("❌", key=f'remove_cost_{i}'):
                    remove_cost_surcharge(i)
                    st.rerun()

        st.button("➕ Add Surcharge", key="add_cost_surcharge", on_click=add_cost_surcharge)

        cost_totals = {}
        for surcharge in st.session_state["cost_surcharges"]:
            currency = surcharge["currency"]
            value = surcharge.get("total", 0.0)
            cost_totals[currency] = cost_totals.get(currency, 0.0) + value

        for currency, amount in cost_totals.items():
            st.markdown(f"**Total {currency}**: {amount:,.2f} {currency}")
    
    with st.expander("**Comentarios**", expanded=True):
        final_comments = st.text_area('Comentarios Finales', key="final_comments")

    profit_totals = {}
    all_currencies = set(sales_totals) | set(cost_totals)   # une todas las monedas presentes
    for currency in all_currencies:
        sales_amount = sales_totals.get(currency, 0.0)
        cost_amount  = cost_totals.get(currency, 0.0)
        profit_totals[currency] = sales_amount - cost_amount

    for currency, amount in profit_totals.items():
        st.markdown(f"**Profit {currency}**: {amount:,.2f} {currency}")

    order_info = {
        "commercial": commercial,
        "no_solicitud": no_solicitud,
        "client": st.session_state.get("client", ""),
        "customer_phone": st.session_state.get("customer_phone", ""),
        "customer_address": st.session_state.get("customer_address", ""),
        "customer_account": st.session_state.get("customer_account", ""),
        "customer_nit": st.session_state.get("customer_nit", ""),
        "customer_contact": st.session_state.get("customer_contact", ""),
        "customer_email": st.session_state.get("customer_email", ""),
        "bl_awb": bl_awb,
        "shipper": shipper,
        "consignee": consignee,
        "pol_aol": pol_aol,
        "pod_aod": pod_aod,
        "reference": reference,
        "cargo_type": cargo_type,
        "container_details": container_data if cargo_type == "Contenedor" else None,
        "unidad_medida": unidad_medida if cargo_type != "Contenedor" else None,
        "cantidad_suelta": cant_suelta if cargo_type != "Contenedor" else None,
        "insurance_required": insurance,
        "valor_carga": valor_carga if insurance else None,
        "porcentaje_seguro": porcentaje if insurance else None,
        "sales_surcharges": st.session_state.get("sales_surcharges", []),
        "cost_surcharges": st.session_state.get("cost_surcharges", []),
        "final_comments": final_comments,
    }

    #st.write(order_info)

    return order_info