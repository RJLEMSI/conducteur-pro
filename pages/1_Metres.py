import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import json
import io
import unicodedata
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from lib.auth import check_feature
from utils import (GLOBAL_CSS, render_sidebar, check_api_key,
                   extract_text_from_pdf, pdf_first_page_to_image,
                   encode_image_bytes_to_base64, image_file_to_base64,
                   analyze_plan_image, get_client)


# ===================================================================
# Helpers
# ===================================================================
def _strip_accents(s):
    """Supprime les accents d'une chaine pour comparaison robuste."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


VALID_UNITS = {"m2", "ml", "m3", "u", "kg", "forfait", "ens", "l", "t", "pm", "m\u00b2", "m\u00b3"}

def _parse_metres_from_result(result_text):
    """Parse le resultat IA en lignes structurees.
    Detecte le header du tableau markdown puis parse les lignes de donnees.
    Utilise la normalisation des accents pour un matching robuste.
    """
    lines = []
    in_table = False
    col_indices = {}

    for raw_line in result_text.split("\n"):
        raw_line = raw_line.strip()
        if not raw_line:
            if in_table:
                in_table = False
            continue

        if "|" not in raw_line:
            if in_table and not raw_line.startswith("#"):
                continue
            in_table = False
            continue

        parts = [p.strip() for p in raw_line.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]

        if len(parts) < 3:
            continue

        # Ignorer les lignes de separation (---|---|---)
        if all(c in "-: " for c in "".join(parts)):
            continue

        # Version sans accents pour le matching
        lower_joined = " ".join(_strip_accents(p.lower()) for p in parts)
        header_keywords = ["ouvrage", "designation", "description", "unite",
                           "quantite", "prix", "n\u00b0", "numero"]
        is_header = sum(1 for kw in header_keywords if kw in lower_joined) >= 2

        if is_header:
            in_table = True
            col_indices = {}
            for i, p in enumerate(parts):
                pl = _strip_accents(p.lower().strip())
                if any(w in pl for w in ["ouvrage", "designation", "poste"]):
                    col_indices["ouvrage"] = i
                elif "description" in pl:
                    col_indices["description"] = i
                elif any(w in pl for w in ["unite", "unit"]):
                    col_indices["unite"] = i
                elif any(w in pl for w in ["quantite", "qte", "qty"]):
                    col_indices["quantite"] = i
                elif any(w in pl for w in ["prix", "pu", "cout"]):
                    col_indices["prix"] = i
                elif "observation" in pl or "remarque" in pl or "note" in pl:
                    col_indices["observations"] = i
                elif pl in ["n\u00b0", "no", "num", "numero", "n"]:
                    col_indices["numero"] = i
            continue

        if not in_table:
            continue

        # Parser la ligne de donnees
        designation = ""
        unite = ""
        quantite = 0.0
        prix_u = 0.0

        if "ouvrage" in col_indices and col_indices["ouvrage"] < len(parts):
            designation = parts[col_indices["ouvrage"]].strip()
        if "description" in col_indices and col_indices["description"] < len(parts):
            desc = parts[col_indices["description"]].strip()
            if desc:
                if designation:
                    designation += " - " + desc
                else:
                    designation = desc

        if not designation:
            for i, p in enumerate(parts):
                if i != col_indices.get("numero", -1) and p.strip() and not p.strip().replace(".", "").isdigit():
                    designation = p.strip()
                    break

        if "unite" in col_indices and col_indices["unite"] < len(parts):
            unite = parts[col_indices["unite"]].strip()
        if unite and _strip_accents(unite.lower()) not in {_strip_accents(u) for u in VALID_UNITS}:
            unite = "u"

        if "quantite" in col_indices and col_indices["quantite"] < len(parts):
            raw_q = parts[col_indices["quantite"]].replace(",", ".").replace(" ", "").strip()
            clean_q = "".join(c for c in raw_q if c.isdigit() or c == ".")
            try:
                quantite = float(clean_q) if clean_q else 0.0
            except ValueError:
                quantite = 0.0

        if "prix" in col_indices and col_indices["prix"] < len(parts):
            raw_p = parts[col_indices["prix"]].replace(",", ".").replace(" ", "").replace("\u20ac", "").strip()
            clean_p = "".join(c for c in raw_p if c.isdigit() or c == ".")
            try:
                prix_u = float(clean_p) if clean_p else 0.0
            except ValueError:
                prix_u = 0.0

        if designation and len(designation) > 1:
            lines.append({
                "designation": designation,
                "unite": unite if unite else "u",
                "quantite": quantite,
                "prix_unitaire": prix_u,
            })

    return lines


# --- Setup ---
user_id = page_setup(title="M\u00e9tr\u00e9s", icon="\U0001f4d0")
if not user_id:
    st.stop()
render_saas_sidebar(user_id)

st.title("\U0001f4d0 M\u00e9tr\u00e9s automatiques")
st.caption("T\u00e9l\u00e9chargez un plan (PDF ou image), l'IA extrait les ouvrages mesurables.")

if not check_api_key():
    st.warning("\u2699\ufe0f Configurez votre cl\u00e9 API Anthropic depuis la page Param\u00e8tres.")
    st.stop()

chantier = chantier_selector(key="metres_chantier")
if not chantier:
    st.stop()

# ===================================================================
# Upload et analyse
# ===================================================================
uploaded = st.file_uploader("Plan (PDF ou image)", type=["pdf", "png", "jpg", "jpeg"],
                            key="metres_upload")
extra_info = st.text_area("Informations compl\u00e9mentaires (optionnel)",
                          placeholder="Ex: B\u00e2timent R+2, \u00e9chelle 1/100...",
                          key="metres_extra")

if uploaded:
    if uploaded.type == "application/pdf":
        preview_bytes = pdf_first_page_to_image(uploaded)
        if preview_bytes:
            st.image(preview_bytes, caption="Premi\u00e8re page du plan", width=600)
            image_b64, media_type = encode_image_bytes_to_base64(preview_bytes)
        else:
            st.warning("Impossible de convertir le PDF en image.")
            st.stop()
    else:
        st.image(uploaded, caption="Plan charg\u00e9", use_container_width=True)
        image_b64, media_type = image_file_to_base64(uploaded)

    if st.button("\U0001f680 Analyser le plan et extraire les m\u00e9tr\u00e9s", use_container_width=True):
        with st.spinner("\U0001f50d Analyse en cours par l'IA Claude..."):
            client = get_client()
            result = analyze_plan_image(image_b64, media_type, client, extra_info)

            if result:
                st.session_state["metres_result"] = result
                st.session_state["metres_filename"] = uploaded.name

                try:
                    parsed_lines = _parse_metres_from_result(result)
                    st.session_state["metres_lines"] = parsed_lines
                except Exception:
                    st.session_state["metres_lines"] = []

                if chantier:
                    ouvrages_json = json.dumps(
                        st.session_state.get("metres_lines", []), default=str)
                    metre_data = {
                        "titre": f"M\u00e9tr\u00e9s \u2014 {uploaded.name}",
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


# ===================================================================
# Affichage des resultats + tableau editable
# ===================================================================
if st.session_state.get("metres_result"):
    st.markdown("---")
    st.markdown("### \U0001f4ca R\u00e9sultats des m\u00e9tr\u00e9s")

    with st.expander("\U0001f4dd R\u00e9sultat brut de l'IA", expanded=False):
        st.markdown(st.session_state["metres_result"])

    metres_lines = st.session_state.get("metres_lines", [])

    st.markdown("### \u270f\ufe0f M\u00e9tr\u00e9s \u00e9ditables")
    st.caption("Modifiez les quantit\u00e9s et prix unitaires ci-dessous avant de valider ou g\u00e9n\u00e9rer un devis.")

    if not metres_lines:
        st.info("L'IA n'a pas renvoy\u00e9 de tableau structur\u00e9. Ajoutez des lignes manuellement.")
        metres_lines = []

    # Nombre de lignes (avec bouton pour ajouter)
    if "metres_nb_extra" not in st.session_state:
        st.session_state["metres_nb_extra"] = 0

    nb_base = max(len(metres_lines), 3)
    nb_lignes = nb_base + st.session_state["metres_nb_extra"]

    while len(metres_lines) < int(nb_lignes):
        metres_lines.append({"designation": "", "unite": "m\u00b2", "quantite": 0.0, "prix_unitaire": 0.0})

    edited_lines = []
    total_ht = 0.0

    unite_options = ["m\u00b2", "ml", "m\u00b3", "u", "kg", "forfait"]

    for i in range(int(nb_lignes)):
        default = metres_lines[i] if i < len(metres_lines) else {}
        cols = st.columns([4, 1, 1, 1, 1])
        with cols[0]:
            des = st.text_input("D\u00e9signation", value=default.get("designation", ""),
                                key=f"met_des_{i}", label_visibility="collapsed",
                                placeholder="D\u00e9signation de l'ouvrage")
        with cols[1]:
            stored_unite = default.get("unite", "m\u00b2")
            if stored_unite in unite_options:
                unite_idx = unite_options.index(stored_unite)
            else:
                unite_idx = 0
            unite = st.selectbox("Unit\u00e9", unite_options,
                                  index=unite_idx,
                                  key=f"met_unit_{i}", label_visibility="collapsed")
        with cols[2]:
            qte = st.number_input("Qt\u00e9", value=float(default.get("quantite", 0)),
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

    st.session_state["metres_lines"] = edited_lines

    if st.button("\u2795 Ajouter une ligne au m\u00e9tr\u00e9", key="add_metre_line"):
        st.session_state["metres_nb_extra"] = st.session_state.get("metres_nb_extra", 0) + 1
        st.rerun()

    st.markdown("---")

    col_save, col_devis, col_csv = st.columns(3)

    with col_save:
        if st.button("\U0001f4be Sauvegarder les modifications", use_container_width=True):
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
                        st.success("\u2705 M\u00e9tr\u00e9s mis \u00e0 jour !")
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")
            else:
                st.warning("Aucun m\u00e9tr\u00e9 enregistr\u00e9 \u00e0 mettre \u00e0 jour.")

    with col_devis:
        if st.button("\U0001f4cb G\u00e9n\u00e9rer le devis associ\u00e9", type="primary", use_container_width=True):
            if edited_lines and chantier:
                lots = [{
                    "nom": "Lot 1 \u2014 M\u00e9tr\u00e9s du plan",
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
                    "objet": f"Devis m\u00e9tr\u00e9s \u2014 {st.session_state.get('metres_filename', 'Plan')}",
                    "client_nom": chantier.get("client_nom", ""),
                    "montant_ht": montant_ht,
                    "statut": "brouillon",
                    "contenu": contenu,
                }

                try:
                    result_devis = db.save_devis(user_id, chantier["id"], devis_data)
                    if result_devis:
                        st.success(f"\u2705 Devis {devis_numero} cr\u00e9\u00e9 ! Montant HT : {montant_ht:,.2f} \u20ac")
                        st.info("\U0001f449 Retrouvez-le dans la page **Devis** pour le finaliser et g\u00e9n\u00e9rer le PDF.")
                    else:
                        st.error("Erreur lors de la cr\u00e9ation du devis.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Ajoutez des lignes au m\u00e9tr\u00e9 avant de g\u00e9n\u00e9rer un devis.")

    with col_csv:
        if edited_lines:
            df = pd.DataFrame(edited_lines)
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False, sep=";")
            st.download_button("\U0001f4e5 Exporter CSV", csv_buf.getvalue(),
                               file_name=f"metres_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", use_container_width=True)


# ===================================================================
# Historique des metres avec suppression
# ===================================================================
st.markdown("---")
st.subheader("\U0001f4cb Historique des m\u00e9tr\u00e9s")

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
                metre_id = m.get('id', '')
                with st.expander(f"\U0001f4d0 {titre} \u2014 {date_str}"):
                    synthese = m.get("synthese", "")
                    if synthese:
                        st.markdown(synthese[:800] + ("..." if len(synthese) > 800 else ""))

                    ouvrages = m.get("ouvrages")
                    if ouvrages:
                        try:
                            ouv_list = json.loads(ouvrages) if isinstance(ouvrages, str) else ouvrages
                            if ouv_list and isinstance(ouv_list, list) and len(ouv_list) > 0:
                                df = pd.DataFrame(ouv_list)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.caption("Aucun ouvrage enregistr\u00e9 pour ce m\u00e9tr\u00e9.")
                        except Exception:
                            st.caption("Donn\u00e9es ouvrages non lisibles.")
                    else:
                        st.caption("Aucun ouvrage enregistr\u00e9 pour ce m\u00e9tr\u00e9.")

                    col_load, col_del = st.columns(2)
                    with col_load:
                        if st.button(f"\U0001f504 Charger dans l'\u00e9diteur", key=f"load_metre_{metre_id}"):
                            st.session_state["metres_result"] = synthese
                            ouv_data = []
                            if ouvrages:
                                try:
                                    ouv_data = json.loads(ouvrages) if isinstance(ouvrages, str) else ouvrages
                                except Exception:
                                    ouv_data = []
                            st.session_state["metres_lines"] = ouv_data if isinstance(ouv_data, list) else []
                            st.session_state["metres_saved_id"] = metre_id
                            st.session_state["metres_filename"] = titre
                            st.rerun()
                    with col_del:
                        if st.button(f"\U0001f5d1\ufe0f Supprimer", key=f"del_metre_{metre_id}",
                                     type="secondary"):
                            try:
                                sup.table("metres").delete().eq("id", metre_id).execute()
                                st.success("M\u00e9tr\u00e9 supprim\u00e9 !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur suppression : {e}")
        else:
            st.info("Aucun m\u00e9tr\u00e9 pour ce chantier.")
except Exception as e:
    st.info("Aucun m\u00e9tr\u00e9 pour ce chantier.")
