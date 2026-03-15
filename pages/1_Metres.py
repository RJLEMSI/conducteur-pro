import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from lib.auth import check_feature
from utils import (GLOBAL_CSS, render_sidebar, check_api_key,
                   extract_text_from_pdf, pdf_first_page_to_image,
                   encode_image_bytes_to_base64, image_file_to_base64,
                   analyze_plan_image, get_client)


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Fonction utilitaire : parser le rÃ©sultat IA en lignes de mÃ©trÃ©
# (DOIT Ãªtre dÃ©finie AVANT son appel dans le flux Streamlit)
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def _parse_metres_from_result(result_text):
    """Parse le résultat IA en lignes structurées.
    Gère deux formats de tableau markdown :
    - 4 colonnes : | Désignation | Unité | Quantité | Prix unitaire |
    - 6 colonnes : | N° | Ouvrage | Description | Unité | Quantité | Observations |
    """
    lines = []
    col_count = 0

    for line in result_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 2:
            continue
        if all(c in "-| :" for c in line):
            continue

        lower_parts = [p.lower() for p in parts]
        is_header = any(h in " ".join(lower_parts) for h in [
            "désignation", "ouvrage", "description", "unité", "unite",
            "quantité", "quantite", "prix", "n°"
        ])
        if is_header:
            col_count = len(parts)
            continue

        designation = ""
        unite = ""
        quantite = 0.0
        prix_u = 0.0

        if col_count >= 6:
            designation = parts[1] if len(parts) > 1 else ""
            desc = parts[2] if len(parts) > 2 else ""
            if desc and desc != designation:
                designation += " - " + desc
            unite = parts[3] if len(parts) > 3 else ""
            try:
                quantite = float(parts[4].replace(",", ".").replace(" ", "")) if len(parts) > 4 else 0.0
            except (ValueError, IndexError):
                quantite = 0.0
            prix_u = 0.0
        elif col_count == 5:
            designation = parts[1] if len(parts) > 1 else ""
            unite = parts[2] if len(parts) > 2 else ""
            try:
                quantite = float(parts[3].replace(",", ".").replace(" ", "")) if len(parts) > 3 else 0.0
            except (ValueError, IndexError):
                quantite = 0.0
            try:
                prix_u = float(parts[4].replace(",", ".").replace("€", "").replace(" ", "")) if len(parts) > 4 else 0.0
            except (ValueError, IndexError):
                prix_u = 0.0
        else:
            designation = parts[0] if len(parts) > 0 else ""
            unite = parts[1] if len(parts) > 1 else ""
            try:
                quantite = float(parts[2].replace(",", ".").replace(" ", "")) if len(parts) > 2 else 0.0
            except (ValueError, IndexError):
                quantite = 0.0
            try:
                prix_u = float(parts[3].replace(",", ".").replace("€", "").replace(" ", "")) if len(parts) > 3 else 0.0
            except (ValueError, IndexError):
                prix_u = 0.0

        skip_words = ["désignation", "ouvrage", "description", "poste",
                      "n°", "numéro", "unité", "unite", "quantité", "prix"]
        if designation and designation.lower() not in skip_words:
            lines.append({
                "designation": designation,
                "unite": unite,
                "quantite": quantite,
                "prix_unitaire": prix_u,
            })
    return lines

# âââ Setup ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
user_id = page_setup(title="MÃ©trÃ©s", icon="\U0001f4d0")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## \U0001f4d0 MÃ©trÃ©s automatiques")
st.caption("Uploadez un plan (PDF ou image), l'IA extrait les ouvrages mesurables.")

# VÃ©rifier la clÃ© API
if not check_api_key():
    st.warning("\u2699\ufe0f Configurez votre clÃ© API Anthropic depuis la page ParamÃ¨tres.")
    st.stop()

chantier = chantier_selector(key="metres_chantier")
if not chantier:
    st.stop()

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Upload et analyse
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
uploaded = st.file_uploader("Plan (PDF ou image)", type=["pdf", "png", "jpg", "jpeg"],
                            key="metres_upload")
extra_info = st.text_area("Informations complÃ©mentaires (optionnel)",
                          placeholder="Ex: BÃ¢timent R+2, Ã©chelle 1/100...",
                          key="metres_extra")

if uploaded:
    # Preview
    if uploaded.type == "application/pdf":
        preview_bytes = pdf_first_page_to_image(uploaded)
        if preview_bytes:
            st.image(preview_bytes, caption="PremiÃ¨re page du plan", width=600)
            image_b64, media_type = encode_image_bytes_to_base64(preview_bytes)
        else:
            st.warning("Impossible de convertir le PDF en image.")
            st.stop()
    else:
        st.image(uploaded, caption="Plan chargÃ©", use_container_width=True)
        image_b64, media_type = image_file_to_base64(uploaded)

    if st.button("\U0001f680 Analyser le plan et extraire les mÃ©trÃ©s", width="stretch"):
        with st.spinner("\U0001f50d Analyse en cours par l'IA Claude..."):
            client = get_client()
            result = analyze_plan_image(image_b64, media_type, client, extra_info)

            if result:
                st.session_state["metres_result"] = result
                st.session_state["metres_filename"] = uploaded.name

                # ââ Parser le resultat IA en lignes editables ââ
                try:
                    parsed_lines = _parse_metres_from_result(result)
                    st.session_state["metres_lines"] = parsed_lines
                except Exception:
                    st.session_state["metres_lines"] = []

                # Sauvegarder dans Supabase avec les ouvrages parsÃ©s
                if chantier:
                    # Sauvegarder les ouvrages parsÃ©s directement (pas une liste vide)
                    ouvrages_json = json.dumps(
                        st.session_state.get("metres_lines", []), default=str
                    )
                    metre_data = {
                        "titre": f"MÃ©trÃ©s â {uploaded.name}",
                        "ouvrages": ouvrages_json,
                        "synthese": result,
                    }
                    saved = db.save_metre(user_id, chantier["id"], metre_data)
                    if saved:
                        st.session_state["metres_saved_id"] = saved.get("id", "")
                        try:
                            db.log_activity("create_metre", "metre", saved.get("id", ""),
                                            {"titre": uploaded.name})
                        except Exception:
                            pass

                    # Upload du fichier source dans le cloud
                    uploaded.seek(0)
                    try:
                        storage.upload_file(
                            file_bytes=uploaded.read(),
                            filename=uploaded.name,
                            chantier_id=chantier["id"],
                            famille="metres")
                    except Exception:
                        pass

                st.rerun()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Affichage des rÃ©sultats + tableau Ã©ditable
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
if st.session_state.get("metres_result"):
    st.markdown("---")
    st.markdown("### \U0001f4ca RÃ©sultats des mÃ©trÃ©s")

    # Afficher le brut IA dans un expander
    with st.expander("\U0001f4dd RÃ©sultat brut de l'IA", expanded=False):
        st.markdown(st.session_state["metres_result"])

    # ââ Tableau Ã©ditable ââ
    metres_lines = st.session_state.get("metres_lines", [])

    st.markdown("### \u270f\ufe0f MÃ©trÃ©s Ã©ditables")
    st.caption("Modifiez les quantitÃ©s et prix unitaires ci-dessous avant de valider ou gÃ©nÃ©rer un devis.")

    if not metres_lines:
        st.info("L'IA n'a pas renvoyÃ© de tableau structurÃ©. Ajoutez des lignes manuellement.")
        metres_lines = []

    nb_lignes = st.number_input("Nombre de lignes", min_value=1, max_value=100,
                                 value=max(len(metres_lines), 3), key="metres_nb_lines")

    # S'assurer qu'on a assez de lignes
    while len(metres_lines) < int(nb_lignes):
        metres_lines.append({"designation": "", "unite": "mÂ²", "quantite": 0.0, "prix_unitaire": 0.0})

    edited_lines = []
    total_ht = 0.0

    for i in range(int(nb_lignes)):
        default = metres_lines[i] if i < len(metres_lines) else {}
        cols = st.columns([4, 1, 1, 1, 1])
        with cols[0]:
            des = st.text_input(f"DÃ©signation", value=default.get("designation", ""),
                                key=f"met_des_{i}", label_visibility="collapsed",
                                placeholder="DÃ©signation de l'ouvrage")
        with cols[1]:
            unite = st.selectbox("UnitÃ©", ["mÂ²", "ml", "mÂ³", "u", "kg", "forfait"],
                                  index=["mÂ²", "ml", "mÂ³", "u", "kg", "forfait"].index(
                                      default.get("unite", "mÂ²")) if default.get("unite", "mÂ²") in ["mÂ²", "ml", "mÂ³", "u", "kg", "forfait"] else 0,
                                  key=f"met_unit_{i}", label_visibility="collapsed")
        with cols[2]:
            qte = st.number_input("QtÃ©", value=float(default.get("quantite", 0)),
                                   key=f"met_qte_{i}", label_visibility="collapsed",
                                   min_value=0.0, step=0.1, format="%.2f")
        with cols[3]:
            pu = st.number_input("PU HT", value=float(default.get("prix_unitaire", 0)),
                                  key=f"met_pu_{i}", label_visibility="collapsed",
                                  min_value=0.0, step=0.5, format="%.2f")
        with cols[4]:
            line_total = qte * pu
            st.text_input("Total", value=f"{line_total:.2f}", key=f"met_tot_{i}",
                          disabled=True, label_visibility="collapsed")

        if des:
            edited_lines.append({
                "designation": des, "unite": unite,
                "quantite": qte, "prix_unitaire": pu, "total_ht": line_total
            })
            total_ht += line_total

    if int(nb_lignes) > 0:
        st.markdown(f"**Total HT : {total_ht:,.2f} \u20ac**")

    # Sauvegarder les modifications dans session_state
    st.session_state["metres_lines"] = edited_lines

    st.markdown("---")

    # ââ Actions ââ
    col_save, col_devis, col_csv = st.columns(3)

    with col_save:
        if st.button("\U0001f4be Sauvegarder les modifications", width="stretch"):
            if chantier and st.session_state.get("metres_saved_id"):
                try:
                    update_data = {
                        "ouvrages": json.dumps(edited_lines, default=str),
                    }
                    from lib.supabase_client import get_supabase_client
                    sup_client = get_supabase_client()
                    if sup_client:
                        sup_client.table("metres").update(update_data).eq(
                            "id", st.session_state["metres_saved_id"]).execute()
                        st.success("\u2705 MÃ©trÃ©s mis Ã  jour !")
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")
            else:
                st.warning("Aucun mÃ©trÃ© enregistrÃ© Ã  mettre Ã  jour.")

    with col_devis:
        if st.button("\U0001f4cb GÃ©nÃ©rer le devis associÃ©", type="primary", width="stretch"):
            if edited_lines and chantier:
                lots = [{
                    "nom": "Lot 1 â MÃ©trÃ©s du plan",
                    "postes": edited_lines
                }]
                contenu = json.dumps({"lots": lots}, default=str)
                montant_ht = total_ht

                try:
                    existing_devis = db.get_devis(chantier_id=chantier['id'])
                    devis_numero = f"DEV-{datetime.now().strftime('%Y%m')}-{len(existing_devis)+1:03d}"
                except Exception:
                    devis_numero = f"DEV-{datetime.now().strftime('%Y%m')}-001"

                devis_data = {
                    "numero": devis_numero,
                    "objet": f"Devis mÃ©trÃ©s â {st.session_state.get('metres_filename', 'Plan')}",
                    "client_nom": chantier.get("client_nom", ""),
                    "montant_ht": montant_ht,
                    "statut": "brouillon",
                    "contenu": contenu,
                }

                try:
                    result_devis = db.save_devis(user_id, chantier["id"], devis_data)
                    if result_devis:
                        st.success(f"\u2705 Devis {devis_numero} crÃ©Ã© ! Montant HT : {montant_ht:,.2f} \u20ac")
                        st.info("\U0001f449 Retrouvez-le dans la page **Devis** pour le finaliser et gÃ©nÃ©rer le PDF.")
                    else:
                        st.error("Erreur lors de la crÃ©ation du devis.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Ajoutez des lignes au mÃ©trÃ© avant de gÃ©nÃ©rer un devis.")

    with col_csv:
        if edited_lines:
            df = pd.DataFrame(edited_lines)
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False, sep=";")
            st.download_button("\U0001f4e5 Exporter CSV", csv_buf.getvalue(),
                               file_name=f"metres_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", width="stretch")


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Historique des mÃ©trÃ©s
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown("---")
st.subheader("\U0001f4cb Historique des mÃ©trÃ©s")

try:
    from lib.supabase_client import get_supabase_client
    sup = get_supabase_client()
    if sup:
        metres_list = sup.table("metres").select("*").eq(
            "chantier_id", chantier["id"]
        ).order("created_at", desc=True).execute()
        if metres_list.data:
            for m in metres_list.data:
                titre = m.get('titre', 'Sans titre')
                date_str = m.get('created_at', '')[:10] if m.get('created_at') else ''
                with st.expander(f"\U0001f4d0 {titre} â {date_str}"):
                    # Afficher la synthÃ¨se IA
                    synthese = m.get("synthese", "")
                    if synthese:
                        st.markdown(synthese[:800] + ("..." if len(synthese) > 800 else ""))

                    # Afficher les ouvrages en tableau
                    ouvrages = m.get("ouvrages")
                    if ouvrages:
                        try:
                            ouv_list = json.loads(ouvrages) if isinstance(ouvrages, str) else ouvrages
                            if ouv_list and isinstance(ouv_list, list) and len(ouv_list) > 0:
                                df = pd.DataFrame(ouv_list)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.caption("Aucun ouvrage enregistrÃ© pour ce mÃ©trÃ©.")
                        except Exception:
                            st.caption("DonnÃ©es ouvrages non lisibles.")
                    else:
                        st.caption("Aucun ouvrage enregistrÃ© pour ce mÃ©trÃ©.")

                    # Bouton pour recharger ce mÃ©trÃ© dans l'Ã©diteur
                    if st.button(f"\U0001f504 Charger dans l'Ã©diteur", key=f"load_metre_{m.get('id', '')}"):
                        st.session_state["metres_result"] = synthese
                        ouv_data = []
                        if ouvrages:
                            try:
                                ouv_data = json.loads(ouvrages) if isinstance(ouvrages, str) else ouvrages
                            except Exception:
                                ouv_data = []
                        st.session_state["metres_lines"] = ouv_data if isinstance(ouv_data, list) else []
                        st.session_state["metres_saved_id"] = m.get("id", "")
                        st.session_state["metres_filename"] = titre
                        st.rerun()
        else:
            st.info("Aucun mÃ©trÃ© pour ce chantier.")
except Exception as e:
    st.info(f"Aucun mÃ©trÃ© pour ce chantier.")
