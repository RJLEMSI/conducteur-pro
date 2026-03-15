import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import (GLOBAL_CSS, check_api_key, get_client,
                   extract_text_from_pdf, generate_synthese_globale)

# ─── Setup ──────────────────────────────────────────────────────────────────
user_id = page_setup(title="Synthèse", icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## 📊 Synthèse globale du projet")
st.caption("Générez une synthèse complète en croisant toutes les analyses disponibles.")

if not check_api_key():
    st.warning("⚙️ Configurez votre clé API Anthropic depuis la page d'accueil.")
    st.stop()

require_feature(user_id, "ai_analysis")

chantier = chantier_selector(key="synthese_chantier")


def assemble_context(chantier_data: dict) -> str:
    """Assemble le contexte complet du chantier depuis la base de données."""
    parts = []

    if not chantier_data:
        return ""

    cid = chantier_data["id"]

    # Informations du chantier
    parts.append(f"# Chantier : {chantier_data.get('nom', 'Sans nom')}")
    parts.append(f"Client : {chantier_data.get('client_nom', '—')}")
    parts.append(f"Budget HT : {chantier_data.get('budget_ht', '—')} €")
    parts.append(f"Statut : {chantier_data.get('statut', '—')}")
    if chantier_data.get("description"):
        parts.append(f"Description : {chantier_data['description']}")
    parts.append("")

    # Études disponibles
    etudes = db.get_etudes(chantier_id=cid)
    if etudes:
        parts.append("## Études réalisées")
        for e in etudes:
            parts.append(f"### {e.get('type_etude', 'Étude')} — {e.get('titre', '')}")
            synthese = e.get("synthese", "")
            if synthese:
                parts.append(synthese[:2000])
            parts.append("")

    # PLU (from etudes of type PLU)
    plu_etudes = [e for e in etudes if e.get("type_etude") == "PLU"]
    if plu_etudes:
        parts.append("## Analyse PLU")
        for p in plu_etudes:
            parts.append(p.get("synthese", "")[:2000])
        parts.append("")

    # Métrés
    metres = db.get_metres(chantier_id=cid)
    if metres:
        parts.append("## Métrés")
        for m in metres:
            parts.append(f"### {m.get('titre', 'Métré')}")
            if m.get("ouvrages"):
                import json
                try:
                    ouvrages = json.loads(m["ouvrages"]) if isinstance(m["ouvrages"], str) else m["ouvrages"]
                    for o in ouvrages[:10]:
                        parts.append(f"- {o.get('designation', '')} : {o.get('quantité', '')} {o.get('unite', '')}")
                except Exception:
                    pass
            parts.append("")

    # Devis
    devis_list = db.get_devis(chantier_id=cid)
    if devis_list:
        parts.append("## Devis")
        for d in devis_list:
            parts.append(f"- Devis {d.get('numero', '—')} : {d.get('montant_ttc', 0):,.2f} € TTC — {d.get('statut', '')}")
        parts.append("")

    # Factures
    factures = db.get_factures(chantier_id=cid)
    if factures:
        parts.append("## Factures")
        for f in factures:
            parts.append(f"- Facture {f.get('numero', '—')} : {f.get('montant_ttc', 0):,.2f} € TTC — {f.get('statut', '')}")
        parts.append("")

    # Étapes / Planning
    étapes = db.get_etapes(chantier_id=cid)
    if étapes:
        parts.append("## Planning / Étapes")
        for et in étapes:
            parts.append(f"- {et.get('nom', '')} — {et.get('statut', '')} — Échéance : {et.get('date_échéance', '—')}")
        parts.append("")

    # Session state fallbacks (for data generated in current session but not yet saved)
    if st.session_state.get("planning_result") and not étapes:
        parts.append("## Planning (session en cours)")
        parts.append(str(st.session_state["planning_result"])[:2000])
        parts.append("")

    if st.session_state.get("plu_result") and not plu_etudes:
        parts.append("## Analyse PLU (session en cours)")
        parts.append(str(st.session_state["plu_result"])[:2000])
        parts.append("")

    return "\n".join(parts)


# ─── Contexte assemblé ───────────────────────────────────────────────────────
if chantier:
    with st.spinner("📦 Chargement des données du chantier..."):
        context = assemble_context(chantier)

    if context:
        with st.expander("📋 Données disponibles pour la synthèse", expanded=False):
            st.text(context[:5000])
            if len(context) > 5000:
                st.caption(f"... et {len(context) - 5000} caractères de plus")

        # Options de synthèse
        st.markdown("### ⚙️ Options")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            focus = st.multiselect("Points de focus",
                ["Budget & finances", "Planning & délais", "Conformité PLU",
                 "Risques & alertes", "Métrés & quantités", "Recommandations"],
                default=["Budget & finances", "Risques & alertes"],
                key="synth_focus")
        with col_opt2:
            detail_level = st.select_slider("Niveau de détail",
                options=["Résumé", "Standard", "Détaillé"],
                value="Standard", key="synth_detail")

        focus_text = ", ".join(focus) if focus else "Tous les aspects"

        # ─── Génération ───────────────────────────────────────────────────────
        if st.button("🚀 Générer la synthèse globale", width="stretch", type="primary"):
            with st.spinner("🤖 Génération de la synthèse globale... (30-60 secondes)"):
                client = get_client()
                enhanced_context = (
                    f"Niveau de détail demandé : {detail_level}\n"
                    f"Points de focus : {focus_text}\n\n"
                    f"{context}"
                )
                result = generate_synthese_globale(enhanced_context, client)

                if result:
                    st.session_state["synthese_result"] = result

                    # Sauvegarder en base
                    etude_data = {
                        "titre": f"Synthèse globale — {chantier.get('nom', '')}",
                        "type_etude": "Synthèse",
                        "synthese": result[:5000],
                        "chantier_id": chantier["id"],
                    }
                    saved = db.save_etude(etude_data)
                    if saved:
                        db.log_activity("create_synthese", "etude", saved.get("id", ""),
                                        {"chantier": chantier.get("nom")})


                    # Auto-classification: stocker dans les documents du chantier
                    try:
                        from datetime import datetime as _dt
                        _synth_filename = f"synthese_{chantier.get('nom', 'chantier').replace(' ', '_').lower()}_{_dt.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        _synth_bytes = result.encode("utf-8")
                        storage.upload_generated_document(
                            file_bytes=_synth_bytes,
                            filename=_synth_filename,
                            chantier_id=chantier["id"],
                            famille="Etude",
                            doc_type="Synthese",
                        )
                        # Document auto-classifie par storage.upload_generated_document()
                    except Exception:
                        pass

                    st.success("✅ Synthèse générée !")

        # ─── Résultat ─────────────────────────────────────────────────────────
        if st.session_state.get("synthese_result"):
            st.markdown("### 📊 Synthèse globale")
            st.markdown(st.session_state["synthese_result"])

            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.download_button("💾 Télécharger (TXT)",
                                   st.session_state["synthese_result"],
                                   file_name=f"synthese_{chantier.get('nom', 'projet')}.txt",
                                   mime="text/plain")
            with col_a2:
                st.download_button("💾 Télécharger (MD)",
                                   st.session_state["synthese_result"],
                                   file_name=f"synthese_{chantier.get('nom', 'projet')}.md",
                                   mime="text/markdown")
            with col_a3:
                if st.button("🗑️ Effacer", key="clear_synthese"):
                    st.session_state["synthese_result"] = None
                    st.rerun()

    else:
        st.info("Aucune donnée disponible pour ce chantier. Commencez par réaliser des analyses (Métrés, Études, PLU, Planning...).")

else:
    st.info("Sélectionnez un chantier pour générer une synthèse globale.")

# ─── Historique ──────────────────────────────────────────────────────────────
if chantier:
    st.markdown("---")
    st.markdown("### 📚 Historique des synthèses")
    etudes = db.get_etudes(chantier_id=chantier["id"])
    syntheses = [e for e in etudes if e.get("type_etude") == "Synthèse"]

    if syntheses:
        for s in syntheses:
            with st.expander(f"📊 {s.get('titre', 'Synthèse')} — {s.get('created_at', '')[:10]}"):
                st.markdown(s.get("synthese", ""))
    else:
        st.info("Aucune synthèse enregistrée pour ce chantier.")
