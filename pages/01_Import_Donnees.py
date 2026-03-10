"""
Page 01 â Import de donnÃ©es client
Wizard d'import : CSV, Excel, JSON pour chantiers, factures, Ã©tapes.
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
    import_factures, import_etapes, build_chantier_map,
    import_json_full,
)

# st.set_page_config gere par app.py
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()
require_auth()

# VÃ©rifier l'accÃ¨s
if not check_feature("import_data"):
    show_upgrade_message("L'import de donnÃ©es")
    st.stop()

# âââ En-tÃªte âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown("""
<div class="page-header">
    <h2>ð¥ Import de donnÃ©es</h2>
    <p>Importez la base de donnÃ©es complÃ¨te de votre client : chantiers, factures, Ã©tapes, documents</p>
</div>
""", unsafe_allow_html=True)

# âââ Onglets d'import ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
tab_chantiers, tab_factures, tab_etapes, tab_json, tab_templates = st.tabs([
    "ðï¸ Chantiers",
    "ð§¾ Factures",
    "ð Ãtapes / Planning",
    "ð¦ Import complet (JSON)",
    "ð ModÃ¨les CSV"
])

# âââ IMPORT CHANTIERS âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
            st.markdown(f"**{len(df)} lignes dÃ©tectÃ©es.** AperÃ§u :")
            st.dataframe(df.head(10), use_container_width=True)

            # Mapping des colonnes
            st.markdown("#### VÃ©rification des colonnes")
            required_cols = ["nom"]
            optional_cols = ["client_nom", "statut", "budget_ht", "date_debut", "date_fin", "avancement_pct", "metier"]
            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                st.error(f"Colonnes obligatoires manquantes : {', '.join(missing)}")
                st.info("Consultez l'onglet 'ModÃ¨les CSV' pour voir le format attendu.")
            else:
                present = [c for c in optional_cols if c in df.columns]
                st.success(f"Colonnes dÃ©tectÃ©es : nom + {', '.join(present)}")

                if st.button("ð Importer les chantiers", type="primary", key="btn_import_ch"):
                    with st.spinner("Import en cours..."):
                        results = import_chantiers(df)

                    st.markdown(f"**RÃ©sultat : {results['success']} importÃ©s, {results['errors']} erreurs**")
                    with st.expander("DÃ©tails de l'import"):
                        for detail in results["details"]:
                            st.markdown(detail)

                    if results["success"] > 0:
                        st.balloons()

# âââ IMPORT FACTURES âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_factures:
    st.markdown("### Importer des factures")
    st.markdown("Les factures seront rattachÃ©es aux chantiers existants par leur nom.")

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
                st.warning("â ï¸ Aucun chantier trouvÃ©. Importez d'abord vos chantiers.")
            else:
                st.info(f"ðï¸ {len(chantier_map)} chantiers disponibles pour le rattachement.")

                if st.button("ð Importer les factures", type="primary", key="btn_import_f"):
                    with st.spinner("Import en cours..."):
                        results = import_factures(df_f, chantier_map)

                    st.markdown(f"**RÃ©sultat : {results['success']} importÃ©es, {results['errors']} erreurs**")
                    with st.expander("DÃ©tails"):
                        for d in results["details"]:
                            st.markdown(d)

# âââ IMPORT ÃTAPES âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_etapes:
    st.markdown("### Importer des Ã©tapes de planning")

    file_e = st.file_uploader(
        "Fichier CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        key="import_etapes_file"
    )

    if file_e:
        ext = file_e.name.rsplit(".", 1)[-1].lower()
        df_e = parse_file(file_e, "csv" if ext == "csv" else "excel")

        if not df_e.empty:
            st.dataframe(df_e.head(10), use_container_width=True)

            chantier_map = build_chantier_map()
            if not chantier_map:
                st.warning("â ï¸ Aucun chantier trouvÃ©.")
            else:
                if st.button("ð Importer les Ã©tapes", type="primary", key="btn_import_e"):
                    with st.spinner("Import en cours..."):
                        results = import_etapes(df_e, chantier_map)
                    st.markdown(f"**RÃ©sultat : {results['success']} importÃ©es, {results['errors']} erreurs**")

# âââ IMPORT JSON COMPLET âââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_json:
    st.markdown("### Import complet depuis un export ConducteurPro")
    st.markdown("""
    Importez un fichier JSON exportÃ© depuis ConducteurPro (ou au format compatible).
    Le fichier peut contenir : `chantiers`, `etapes`, `factures`.
    """)

    file_j = st.file_uploader(
        "Fichier JSON",
        type=["json"],
        key="import_json_file"
    )

    if file_j:
        try:
            data = json.loads(file_j.read().decode("utf-8"))
            sections = [k for k in ["chantiers", "etapes", "factures"] if k in data]
            st.success(f"Sections dÃ©tectÃ©es : {', '.join(sections)}")

            for section in sections:
                items = data[section]
                st.markdown(f"**{section.capitalize()}** : {len(items)} Ã©lÃ©ments")

            if st.button("ð Tout importer", type="primary", key="btn_import_json"):
                with st.spinner("Import complet en cours..."):
                    results = import_json_full(data)

                for section, res in results.items():
                    if res:
                        st.markdown(f"**{section.capitalize()}** : {res['success']} importÃ©s, {res['errors']} erreurs")
                st.balloons()

        except json.JSONDecodeError:
            st.error("Fichier JSON invalide.")

# âââ MODÃLES CSV âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_templates:
    st.markdown("### ModÃ¨les CSV Ã  tÃ©lÃ©charger")
    st.markdown("Utilisez ces modÃ¨les pour prÃ©parer vos fichiers d'import.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### ðï¸ Chantiers")
        st.download_button(
            "ð¥ ModÃ¨le chantiers.csv",
            data=get_template_csv("chantiers").encode("utf-8"),
            file_name="modele_chantiers.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        st.markdown("#### ð§¾ Factures")
        st.download_button(
            "ð¥ ModÃ¨le factures.csv",
            data=get_template_csv("factures").encode("utf-8"),
            file_name="modele_factures.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        st.markdown("#### ð Ãtapes")
        st.download_button(
            "ð¥ ModÃ¨le etapes.csv",
            data=get_template_csv("etapes").encode("utf-8"),
            file_name="modele_etapes.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <strong>ð¡ Conseils d'import :</strong>
        <ul style="margin:0.5rem 0;">
            <li>Importez d'abord les <strong>chantiers</strong>, puis les factures et Ã©tapes</li>
            <li>Les dates doivent Ãªtre au format <strong>AAAA-MM-JJ</strong> (ex: 2025-03-15)</li>
            <li>Les montants sont en euros, sans symbole (ex: 285000)</li>
            <li>Les statuts valides pour les chantiers : En cours, PlanifiÃ©, TerminÃ©, En attente, En retard</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
