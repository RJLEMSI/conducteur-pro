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

# ─── Setup ──────────────────────────────────────────────────────────────────
user_id = page_setup(title="Métrés", icon="\U0001f4d0")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## \U0001f4d0 Métrés automatiques")
st.caption("Uploadez un plan (PDF ou image), l'IA extrait les ouvrages mesurables.")

# Vérifier la clé API
if not check_api_key():
    st.warning("\u2699\ufe0f Configurez votre clé API Anthropic depuis la page Paramètres.")
    st.stop()

chantier = chantier_selector(key="metres_chantier")
if not chantier:
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# Upload et analyse
# ═══════════════════════════════════════════════════════════════════════════
uploaded = st.file_uploader("Plan (PDF ou image)", type=["pdf", "png", "jpg", "jpeg"],
                            key="metres_upload")
extra_info = st.text_area("Informations complémentaires (optionnel)",
                          placeholder="Ex: Bâtiment R+2, échelle 1/100...",
                          key="metres_extra")

if uploaded:
    # Preview
    if uploaded.type == "application/pdf":
        preview_bytes = pdf_first_page_to_image(uploaded)
        if preview_bytes:
            st.image(preview_bytes, caption="Première page du plan", width=600)
            image_b64, media_type = encode_image_bytes_to_base64(preview_bytes)
        else:
            st.warning("Impossible de convertir le PDF en image.")
            st.stop()
    else:
        st.image(uploaded, caption="Plan chargé", use_container_width=True)
        image_b64, media_type = image_file_to_base64(uploaded)

    if st.button("\U0001f680 Analyser le plan et extraire les métrés", width="stretch"):
        with st.spinner("\U0001f50d Analyse en cours par l'IA Claude..."):
            client = get_client()
            result = analyze_plan_image(image_b64, media_type, client, extra_info)

            if result:
                st.session_state["metres_result"] = result
                st.session_state["metres_filename"] = uploaded.name

                # ── Parser le resultat IA en lignes editables ──
                try:
                    parsed_lines = _parse_metres_from_result(result)
                    st.session_state["metres_lines"] = parsed_lines
                except Exception:
                    st.session_state["metres_lines"] = []

                # Sauvegarder dans Supabase
                if chantier:
                    metre_data = {
                        "titre": f"Métrés — {uploaded.name}",
                        "ouvrages": [],
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

                    # Upload du fichier source
                    uploaded.seek(0)
                    try:
                        storage.upload_file(
                            file_bytes=uploaded.read(),
                            filename=uploaded.name,
                            chantier_id=chantier["id"],
                            famille="metres")
                    except Exception:
                        pass


# ═══════════════════════════════════════════════════════════════════════════
# Fonction utilitaire : parser le résultat IA en lignes de métré
# ═══════════════════════════════════════════════════════════════════════════
def _parse_metres_from_result(result_text):
    """Essaie de parser le résultat IA en lignes structurées."""
    lines = []
    for line in result_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        # Essayer de détecter des lignes type tableau markdown
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and not all(c in "-| " for c in line):
                designation = parts[0] if len(parts) > 0 else ""
                unite = parts[1] if len(parts) > 1 else ""
                try:
                    quantite = float(parts[2].replace(",", ".")) if len(parts) > 2 else 0.0
                except (ValueError, IndexError):
                    quantite = 0.0
                try:
                    prix_u = float(parts[3].replace(",", ".").replace("\u20ac", "").strip()) if len(parts) > 3 else 0.0
                except (ValueError, IndexError):
                    prix_u = 0.0
                if designation and designation.lower() not in ("désignation", "ouvrage", "description", "poste"):
                    lines.append({
                        "designation": designation,
                        "unite": unite,
                        "quantite": quantite,
                        "prix_unitaire": prix_u,
                    })
    return lines


# ═══════════════════════════════════════════════════════════════════════════
# Affichage des résultats + tableau éditable
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.get("metres_result"):
    st.markdown("---")
    st.markdown("### \U0001f4ca Résultats des métrés")

    # Afficher le brut IA dans un expander
    with st.expander("\U0001f4dd Résultat brut de l'IA", expanded=False):
        st.markdown(st.session_state["metres_result"])

    # ── Tableau éditable ──
    metres_lines = st.session_state.get("metres_lines", [])

    st.markdown("### \u270f\ufe0f Métrés éditables")
    st.caption("Modifiez les quantités et prix unitaires ci-dessous avant de valider ou générer un devis.")

    if not metres_lines:
        # Permettre l'ajout manuel si le parsing n'a rien donné
        st.info("L'IA n'a pas renvoyé de tableau structuré. Ajoutez des lignes manuellement.")
        metres_lines = []

    nb_lignes = st.number_input("Nombre de lignes", min_value=1, max_value=100,
                                 value=max(len(metres_lines), 3), key="metres_nb_lines")

    # S'assurer qu'on a assez de lignes
    while len(metres_lines) < int(nb_lignes):
        metres_lines.append({"designation": "", "unite": "m²", "quantite": 0.0, "prix_unitaire": 0.0})

    edited_lines = []
    total_ht = 0.0

    for i in range(int(nb_lignes)):
        default = metres_lines[i] if i < len(metres_lines) else {}
        cols = st.columns([4, 1, 1, 1, 1])
        with cols[0]:
            des = st.text_input(f"Désignation", value=default.get("designation", ""),
                                key=f"met_des_{i}", label_visibility="collapsed",
                                placeholder="Désignation de l'ouvrage")
        with cols[1]:
            unite = st.selectbox("Unité", ["m²", "ml", "m³", "u", "kg", "forfait"],
                                  index=["m²", "ml", "m³", "u", "kg", "forfait"].index(
                                      default.get("unite", "m²")) if default.get("unite", "m²") in ["m²", "ml", "m³", "u", "kg", "forfait"] else 0,
                                  key=f"met_unit_{i}", label_visibility="collapsed")
        with cols[2]:
            qte = st.number_input("Qté", value=float(default.get("quantite", 0)),
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

    # En-tête colonnes
    if int(nb_lignes) > 0:
        st.markdown(f"**Total HT : {total_ht:,.2f} \u20ac**")

    # Sauvegarder les modifications dans session_state
    st.session_state["metres_lines"] = edited_lines

    st.markdown("---")

    # ── Actions ──
    col_save, col_devis, col_csv = st.columns(3)

    with col_save:
        if st.button("\U0001f4be Sauvegarder les modifications", width="stretch"):
            if chantier and st.session_state.get("metres_saved_id"):
                try:
                    update_data = {
                        "ouvrages": json.dumps(edited_lines, default=str),
                    }
                    # Mettre a jour le metre existant
                    from lib.supabase_client import get_supabase_client
                    client = get_supabase_client()
                    if client:
                        client.table("metres").update(update_data).eq(
                            "id", st.session_state["metres_saved_id"]).execute()
                        st.success("\u2705 Métrés mis à jour !")
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")
            else:
                st.warning("Aucun métré enregistré à mettre à jour.")

    with col_devis:
        if st.button("\U0001f4cb Générer le devis associé", type="primary", width="stretch"):
            if edited_lines and chantier:
                # Construire le devis a partir des lignes du metre
                lots = [{
                    "nom": "Lot 1 — Métrés du plan",
                    "postes": edited_lines
                }]
                contenu = json.dumps({"lots": lots}, default=str)
                montant_ht = total_ht

                devis_numero = f"DEV-{datetime.now().strftime('%Y%m')}-{len(db.get_devis(chantier_id=chantier['id']))+1:03d}"

                devis_data = {
                    "numero": devis_numero,
                    "objet": f"Devis métrés — {st.session_state.get('metres_filename', 'Plan')}",
                    "client_nom": chantier.get("client_nom", ""),
                    "montant_ht": montant_ht,
                    "statut": "brouillon",
                    "contenu": contenu,
                }

                try:
                    result_devis = db.save_devis(user_id, chantier["id"], devis_data)
                    if result_devis:
                        st.success(f"\u2705 Devis {devis_numero} créé ! Montant HT : {montant_ht:,.2f} \u20ac")
                        st.info("\U0001f449 Retrouvez-le dans la page **Devis** pour le finaliser et générer le PDF.")
                    else:
                        st.error("Erreur lors de la création du devis.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Ajoutez des lignes au métré avant de générer un devis.")

    with col_csv:
        if edited_lines:
            df = pd.DataFrame(edited_lines)
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False, sep=";")
            st.download_button("\U0001f4e5 Exporter CSV", csv_buf.getvalue(),
                               file_name=f"metres_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", width="stretch")


# ═══════════════════════════════════════════════════════════════════════════
# Historique des métrés
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("\U0001f4cb Historique des métrés")

try:
    from lib.supabase_client import get_supabase_client
    sup = get_supabase_client()
    if sup:
        metres_list = sup.table("metres").select("*").eq("chantier_id", chantier["id"]).order("created_at", desc=True).execute()
        if metres_list.data:
            for m in metres_list.data:
                with st.expander(f"\U0001f4d0 {m.get('titre', 'Sans titre')} — {m.get('created_at', '')[:10]}"):
                    synthese = m.get("synthese", "")
                    if synthese:
                        st.markdown(synthese[:500] + ("..." if len(synthese) > 500 else ""))
                    ouvrages = m.get("ouvrages")
                    if ouvrages:
                        try:
                            ouv_list = json.loads(ouvrages) if isinstance(ouvrages, str) else ouvrages
                            if ouv_list and isinstance(ouv_list, list):
                                df = pd.DataFrame(ouv_list)
                                st.dataframe(df, use_container_width=True)
                        except Exception:
                            pass
        else:
            st.info("Aucun métré pour ce chantier.")
except Exception:
    st.info("Aucun métré pour ce chantier.")
