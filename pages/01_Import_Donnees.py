"""
Page 01  Import de données client
Wizard d'import : CSV, Excel, JSON pour chantiers, factures, étapes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import json
from utils import GLOBAL_CSS, render_sidebar
from lib.auth import require_auth, check_feature, show_upgrade_message
from lib.import_manager import (
    get_template_csv, parse_file, import_chantiers,
    import_factures, import_étapes, build_chantier_map,
    import_json_full,
)

# st.set_page_config géré par app.py
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()
require_auth()

# Vrifier l'accs
if not check_feature("import_data"):
    show_upgrade_message("L'import de données")
    st.stop()

#  En-tte 
st.markdown("""
<div class="page-header">
    <h2> Import de données</h2>
    <p>Importez la base de données complète de votre client : chantiers, factures, étapes, documents</p>
</div>
""", unsafe_allow_html=True)

#  Onglets d'import 
tab_chantiers, tab_factures, tab_étapes, tab_json, tab_templates = st.tabs([
    " Chantiers",
    " Factures",
    "Étapes / Planning",
    " Import complet (JSON)",
    " Modèles CSV"
])

#  IMPORT CHANTIERS 
with tab_chantiers:
    st.markdown("### Importer des chantiers")
    st.markdown("Uploadez un fichier CSV ou Excel contenant vos chantiers.")

    file = st.file_uploader(
        "Fichier CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        key="import_chantiers_file"
    )

    if file:
        ext = file.name.rsplit(".", 1)[-1].lower()
        df = parse_file(file, "csv" if ext == "csv" else "excel")

        if not df.empty:
            st.markdown(f"**{len(df)} lignes dtectes.** Aperçu :")
            st.dataframe(df.head(10), use_container_width=True)

            # Mapping des colonnes
            st.markdown("#### Vrification des colonnes")
            required_cols = ["nom"]
            optional_cols = ["client_nom", "statut", "budget_ht", "date_debut", "date_fin", "avancement_pct", "metier"]
            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                st.error(f"Colonnes obligatoires manquantes : {', '.join(missing)}")
                st.info("Consultez l'onglet 'Modèles CSV' pour voir le format attendu.")
            else:
                present = [c for c in optional_cols if c in df.columns]
                st.success(f"Colonnes dtectes : nom + {', '.join(present)}")

                if st.button(" Importer les chantiers", type="primary", key="btn_import_ch"):
                    with st.spinner("Import en cours..."):
                        results = import_chantiers(df)

                    st.markdown(f"**Rsultat : {results['success']} imports, {results['errors']} erreurs**")
                    with st.expander("Dtails de l'import"):
                        for detail in results["details"]:
                            st.markdown(detail)

                    if results["success"] > 0:
                        st.balloons()

#  IMPORT FACTURES 
with tab_factures:
    st.markdown("### Importer des factures")
    st.markdown("Les factures seront rattaches aux chantiers existants par leur nom.")

    file_f = st.file_uploader(
        "Fichier CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        key="import_factures_file"
    )

    if file_f:
        ext = file_f.name.rsplit(".", 1)[-1].lower()
        df_f = parse_file(file_f, "csv" if ext == "csv" else "excel")

        if not df_f.empty:
            st.dataframe(df_f.head(10), use_container_width=True)

            chantier_map = build_chantier_map()
            if not chantier_map:
                st.warning(" Aucun chantier trouv. Importez d'abord vos chantiers.")
            else:
                st.info(f" {len(chantier_map)} chantiers disponibles pour le rattachement.")

                if st.button(" Importer les factures", type="primary", key="btn_import_f"):
                    with st.spinner("Import en cours..."):
                        results = import_factures(df_f, chantier_map)

                    st.markdown(f"**Rsultat : {results['success']} importes, {results['errors']} erreurs**")
                    with st.expander("Dtails"):
                        for d in results["details"]:
                            st.markdown(d)

#  IMPORT TAPES 
with tab_étapes:
    st.markdown("### Importer des étapes de planning")

    file_e = st.file_uploader(
        "Fichier CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        key="import_étapes_file"
    )

    if file_e:
        ext = file_e.name.rsplit(".", 1)[-1].lower()
        df_e = parse_file(file_e, "csv" if ext == "csv" else "excel")

        if not df_e.empty:
            st.dataframe(df_e.head(10), use_container_width=True)

            chantier_map = build_chantier_map()
            if not chantier_map:
                st.warning(" Aucun chantier trouv.")
            else:
                if st.button(" Importer les étapes", type="primary", key="btn_import_e"):
                    with st.spinner("Import en cours..."):
                        results = import_étapes(df_e, chantier_map)
                    st.markdown(f"**Rsultat : {results['success']} importes, {results['errors']} erreurs**")

#  IMPORT JSON COMPLET 
with tab_json:
    st.markdown("### Import complet depuis un export ConducteurPro")
    st.markdown("""
    Importez un fichier JSON export depuis ConducteurPro (ou au format compatible).
    Le fichier peut contenir : `chantiers`, `étapes`, `factures`.
    """)

    file_j = st.file_uploader(
        "Fichier JSON",
        type=["json"],
        key="import_json_file"
    )

    if file_j:
        try:
            data = json.loads(file_j.read().decode("utf-8"))
            sections = [k for k in ["chantiers", "étapes", "factures"] if k in data]
            st.success(f"Sections dtectes : {', '.join(sections)}")

            for section in sections:
                items = data[section]
                st.markdown(f"**{section.capitalize()}** : {len(items)} éléments")

            if st.button(" Tout importer", type="primary", key="btn_import_json"):
                with st.spinner("Import complet en cours..."):
                    results = import_json_full(data)

                for section, res in results.items():
                    if res:
                        st.markdown(f"**{section.capitalize()}** : {res['success']} imports, {res['errors']} erreurs")
                st.balloons()

        except json.JSONDecodeError:
            st.error("Fichier JSON invalide.")

#  MODLES CSV 
with tab_templates:
    st.markdown("### Modèles CSV  télécharger")
    st.markdown("Utilisez ces modles pour prparer vos fichiers d'import.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("####  Chantiers")
        st.download_button(
            " Modle chantiers.csv",
            data=get_template_csv("chantiers").encode("utf-8"),
            file_name="modele_chantiers.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        st.markdown("####  Factures")
        st.download_button(
            " Modle factures.csv",
            data=get_template_csv("factures").encode("utf-8"),
            file_name="modele_factures.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        st.markdown("####  tapes")
        st.download_button(
            " Modle étapes.csv",
            data=get_template_csv("étapes").encode("utf-8"),
            file_name="modele_étapes.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <strong> Conseils d'import :</strong>
        <ul style="margin:0.5rem 0;">
            <li>Importez d'abord les <strong>chantiers</strong>, puis les factures et tapes</li>
            <li>Les dates doivent tre au format <strong>AAAA-MM-JJ</strong> (ex: 2025-03-15)</li>
            <li>Les montants sont en euros, sans symbole (ex: 285000)</li>
            <li>Les statuts valides pour les chantiers : En cours, Planifi, Termin, En attente, En retard</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
