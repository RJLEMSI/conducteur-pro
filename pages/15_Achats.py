import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
import re
from datetime import datetime, date
import pandas as pd
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_supabase_client, is_authenticated
from utils import GLOBAL_CSS

user_id = page_setup("Achats", icon="🛒")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "achats")

sb = get_supabase_client()

def fmt(val):
    try:
        return f"{float(val or 0):,.2f} €".replace(",", " ")
    except:
        return "0,00 €"

# ─── Load fournisseurs ────────────────────────────────────────────
try:
    resp_f = sb.table("fournisseurs").select("*").eq("user_id", user_id).eq("actif", True).execute()
    fournisseurs = resp_f.data or []
except Exception as e:
    st.error(f"Erreur fournisseurs: {e}")
    fournisseurs = []

fourn_map = {f["nom"]: f["id"] for f in fournisseurs}
fourn_by_id = {f["id"]: f for f in fournisseurs}

st.title("🛒 Achats & Fournisseurs")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏭 Fournisseurs",
    "📋 Bons de Commande",
    "📄 Documents Fournisseurs",
    "📊 Suivi"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — FOURNISSEURS
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Répertoire Fournisseurs")

    col_list, col_form = st.columns([1, 1])

    with col_list:
        if fournisseurs:
            for f in fournisseurs:
                with st.expander(f"🏭 {f['nom']} — {f.get('categorie','').upper()}"):
                    st.write(f"📞 {f.get('telephone','')}")
                    st.write(f"📧 {f.get('email','')}")
                    st.write(f"📍 {f.get('adresse','')}")
                    if f.get('siret'):
                        st.write(f"🏢 SIRET: {f['siret']}")
                    if f.get('notes'):
                        st.write(f"📝 {f['notes']}")
        else:
            st.info("Aucun fournisseur. Ajoutez-en un ci-contre.")

    with col_form:
        st.markdown("### ➕ Nouveau Fournisseur")
        with st.form("form_fourn", clear_on_submit=True):
            nom = st.text_input("Nom *")
            categorie = st.selectbox("Catégorie *", ["materiaux", "location", "sous-traitance", "services"])
            contact = st.text_input("Contact")
            email_f = st.text_input("Email")
            tel_f = st.text_input("Téléphone")
            adresse_f = st.text_area("Adresse", height=60)
            siret_f = st.text_input("SIRET (14 chiffres)")
            notes_f = st.text_area("Notes", height=60)
            if st.form_submit_button("💾 Enregistrer"):
                if not nom:
                    st.error("Le nom est obligatoire.")
                else:
                    try:
                        sb.table("fournisseurs").insert({
                            "user_id": user_id,
                            "nom": nom,
                            "categorie": categorie,
                            "contact_nom": contact,
                            "email": email_f,
                            "telephone": tel_f,
                            "adresse": adresse_f,
                            "siret": siret_f or None,
                            "notes": notes_f,
                            "actif": True,
                        }).execute()
                        st.success(f"Fournisseur '{nom}' ajouté ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

# ══════════════════════════════════════════════════════════
# TAB 2 — BONS DE COMMANDE
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("Bons de Commande")

    # chantier_selector returns a DICT — extract id safely
    chantier_obj = chantier_selector(key="achats_chantier")
    chantier_id = chantier_obj["id"] if isinstance(chantier_obj, dict) else chantier_obj

    if not chantier_id:
        st.info("Sélectionnez un chantier pour voir les commandes.")
        st.stop()

    # Load commandes
    try:
        resp_c = sb.table("achats").select("*, fournisseurs(nom)").eq("user_id", user_id).eq("chantier_id", chantier_id).order("created_at", desc=True).execute()
        commandes = resp_c.data or []
    except Exception as e:
        st.error(f"Erreur chargement commandes: {e}")
        commandes = []

    col_cmds, col_new = st.columns([3, 2])

    with col_cmds:
        st.markdown(f"**{len(commandes)} commande(s)**")
        if commandes:
            statut_filtre = st.selectbox("Filtrer par statut", ["Tous", "brouillon", "commandé", "livré", "annulé"], key="filtre_cmd")
            filtered = commandes if statut_filtre == "Tous" else [c for c in commandes if c.get("statut") == statut_filtre]
            rows = []
            for c in filtered:
                fourn_nom = ""
                if isinstance(c.get("fournisseurs"), dict):
                    fourn_nom = c["fournisseurs"].get("nom", "")
                rows.append({
                    "N°": c.get("numero", ""),
                    "Fournisseur": fourn_nom,
                    "Objet": c.get("objet", "")[:40],
                    "Montant TTC": fmt(c.get("montant_ttc") or c.get("montant_ht") or 0),
                    "Statut": c.get("statut", ""),
                    "Date": str(c.get("date_commande", ""))[:10],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            total = sum(float(c.get("montant_ttc") or c.get("montant_ht") or 0) for c in filtered)
            st.metric("Total commandes", fmt(total))
        else:
            st.info("Aucune commande pour ce chantier.")

    with col_new:
        st.markdown("### ➕ Nouvelle Commande")
        if not fournisseurs:
            st.warning("Ajoutez d'abord un fournisseur dans l'onglet Fournisseurs.")
        else:
            with st.form("form_commande", clear_on_submit=True):
                fourn_sel = st.selectbox("Fournisseur *", list(fourn_map.keys()))
                numero = st.text_input("N° Commande *", value=f"BC-{datetime.now().strftime('%Y%m%d-%H%M')}")
                objet = st.text_area("Objet *", height=60)
                date_cmd = st.date_input("Date commande", value=date.today())
                date_liv = st.date_input("Date livraison prévue")
                montant_ht = st.number_input("Montant HT (€)", min_value=0.0, step=100.0)
                tva = st.number_input("TVA (%)", value=20.0, step=0.5)
                montant_ttc = montant_ht * (1 + tva / 100)
                st.info(f"Montant TTC: {fmt(montant_ttc)}")
                statut_cmd = st.selectbox("Statut", ["brouillon", "commandé", "livré_partiel", "livré", "annulé"])
                notes_cmd = st.text_area("Notes", height=50)

                if st.form_submit_button("💾 Enregistrer"):
                    if not objet or not fourn_sel:
                        st.error("Fournisseur et objet sont obligatoires.")
                    else:
                        try:
                            sb.table("achats").insert({
                                "user_id": user_id,
                                "chantier_id": chantier_id,
                                "fournisseur_id": fourn_map[fourn_sel],
                                "numero": numero,
                                "objet": objet,
                                "date_commande": str(date_cmd),
                                "date_livraison_prevue": str(date_liv),
                                "montant_ht": montant_ht,
                                "tva_pct": tva,
                                "montant_ttc": montant_ttc,
                                "statut": statut_cmd,
                                "notes": notes_cmd,
                                "lignes": [],
                            }).execute()
                            st.success("Commande enregistrée ✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {e}")

# ══════════════════════════════════════════════════════════
# TAB 3 — DOCUMENTS FOURNISSEURS + IA
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("📄 Documents Fournisseurs — Extraction IA des Prix")
    st.markdown("""
    Déposez un **devis PDF**, **tarif Excel** ou **catalogue** d'un fournisseur.
    L'IA analyse le document et extrait automatiquement les **prix unitaires** pour les intégrer
    dans vos calculs de rentabilité et métrés.
    """)

    if not fournisseurs:
        st.warning("Ajoutez d'abord un fournisseur dans l'onglet Fournisseurs.")
    else:
        col_upload, col_result = st.columns([1, 1])

        with col_upload:
            fourn_doc = st.selectbox("Fournisseur concerné", list(fourn_map.keys()), key="fourn_doc")
            doc_type = st.selectbox("Type de document", ["Devis / Offre de prix", "Tarif général", "Catalogue", "Facture", "Autre"])
            uploaded_file = st.file_uploader(
                "Déposer le document (PDF, Excel, CSV, image)",
                type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg", "txt"],
                key="doc_fourn"
            )

            if uploaded_file and st.button("🤖 Analyser avec l'IA", type="primary"):
                with st.spinner("Analyse IA en cours..."):
                    try:
                        import anthropic

                        # Read file content
                        file_bytes = uploaded_file.read()
                        file_name = uploaded_file.name
                        file_ext = file_name.rsplit(".", 1)[-1].lower()

                        # Prepare content for Claude
                        if file_ext == "csv":
                            text_content = file_bytes.decode("utf-8", errors="ignore")
                            prompt_content = f"Voici le contenu CSV du document fournisseur:\n\n{text_content[:8000]}"
                        elif file_ext in ["xlsx", "xls"]:
                            try:
                                import io
                                df_doc = pd.read_excel(io.BytesIO(file_bytes))
                                text_content = df_doc.to_string(index=False)
                                prompt_content = f"Voici les données Excel du document fournisseur:\n\n{text_content[:8000]}"
                            except Exception:
                                prompt_content = f"Document Excel: {file_name} (contenu non lisible directement)"
                        elif file_ext == "txt":
                            text_content = file_bytes.decode("utf-8", errors="ignore")
                            prompt_content = f"Voici le contenu texte du document:\n\n{text_content[:8000]}"
                        else:
                            # PDF or image — encode as base64
                            import base64
                            b64 = base64.standard_b64encode(file_bytes).decode()
                            if file_ext == "pdf":
                                prompt_content = None
                                media_type = "application/pdf"
                            else:
                                prompt_content = None
                                media_type = f"image/{file_ext}"

                        # Build Claude request
                        client = anthropic.Anthropic(
                            api_key=st.secrets.get("ANTHROPIC_API_KEY", "")
                        )

                        fourn_info = fourn_by_id.get(fourn_map[fourn_doc], {})

                        system_prompt = f"""Tu es un assistant ERP spécialisé BTP. Analyse ce document fournisseur et extrait TOUS les prix.

Fournisseur: {fourn_info.get('nom', fourn_doc)}
Type: {doc_type}

Retourne un JSON structuré avec:
{{
  "fournisseur": "nom",
  "date_document": "YYYY-MM-DD ou null",
  "devise": "EUR",
  "articles": [
    {{
      "designation": "description précise",
      "reference": "ref ou null",
      "unite": "m2/ml/m3/u/kg/t/h...",
      "prix_unitaire_ht": 0.00,
      "categorie": "materiaux/main_oeuvre/location/transport/autre"
    }}
  ],
  "resume": "résumé en 2 phrases de ce que propose ce fournisseur"
}}

Sois précis sur les unités et prix. Si une info manque, mets null."""

                        if prompt_content:
                            # Text-based document
                            response = client.messages.create(
                                model="claude-opus-4-6",
                                max_tokens=4096,
                                system=system_prompt,
                                messages=[{"role": "user", "content": prompt_content}]
                            )
                        else:
                            # PDF or image
                            response = client.messages.create(
                                model="claude-opus-4-6",
                                max_tokens=4096,
                                system=system_prompt,
                                messages=[{
                                    "role": "user",
                                    "content": [{
                                        "type": "document" if file_ext == "pdf" else "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": media_type,
                                            "data": b64,
                                        }
                                    }, {
                                        "type": "text",
                                        "text": "Analyse ce document et extrait tous les prix selon le format JSON demandé."
                                    }]
                                }]
                            )

                        raw = response.content[0].text
                        # Extract JSON from response
                        json_match = re.search(r'\{[\s\S]*\}', raw)
                        if json_match:
                            extracted = json.loads(json_match.group())
                            st.session_state["extracted_prices"] = extracted
                            st.session_state["extracted_fourn"] = fourn_doc
                            st.success("✅ Extraction réussie !")
                        else:
                            st.session_state["extracted_prices"] = {"resume": raw, "articles": []}
                            st.warning("Extraction partielle — voir résultat.")

                    except ImportError:
                        st.error("Module 'anthropic' non installé. Lancez: pip install anthropic")
                    except Exception as e:
                        st.error(f"Erreur IA: {e}")

        with col_result:
            extracted = st.session_state.get("extracted_prices")
            if extracted:
                st.markdown(f"### 📊 Résultat — {st.session_state.get('extracted_fourn','')}")
                if extracted.get("resume"):
                    st.info(extracted["resume"])

                articles = extracted.get("articles", [])
                if articles:
                    df_prix = pd.DataFrame(articles)
                    st.dataframe(df_prix, use_container_width=True)

                    # Export button
                    csv = df_prix.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Télécharger les prix (CSV)",
                        data=csv,
                        file_name=f"prix_{st.session_state.get('extracted_fourn','fourn')}.csv",
                        mime="text/csv"
                    )

                    # Save to session for reuse in other modules
                    if st.button("💾 Sauvegarder dans le catalogue de prix"):
                        st.session_state["catalogue_prix"] = articles
                        fourn_id = fourn_map.get(st.session_state.get("extracted_fourn", ""), "")
                        if fourn_id:
                            try:
                                # Update fournisseur notes with price summary
                                prix_note = f"[Catalogue IA - {datetime.now().strftime('%d/%m/%Y')}]\n"
                                for a in articles[:10]:
                                    prix_note += f"- {a.get('designation','')}: {a.get('prix_unitaire_ht',0)} €/{a.get('unite','')}\n"
                                existing = fourn_by_id.get(fourn_id, {})
                                new_notes = (existing.get("notes") or "") + "\n" + prix_note
                                sb.table("fournisseurs").update({"notes": new_notes}).eq("id", fourn_id).execute()
                                st.success("✅ Catalogue sauvegardé sur le fournisseur !")
                            except Exception as e:
                                st.error(f"Erreur sauvegarde: {e}")
                        else:
                            st.info("Catalogue disponible en session.")
            else:
                st.info("Déposez un document et cliquez sur 'Analyser' pour extraire les prix.")

# ══════════════════════════════════════════════════════════
# TAB 4 — SUIVI GLOBAL
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("📊 Suivi Global des Achats")

    try:
        resp_all = sb.table("achats").select("*, fournisseurs(nom), chantiers(nom)").eq("user_id", user_id).order("created_at", desc=True).execute()
        all_achats = resp_all.data or []
    except Exception as e:
        st.error(f"Erreur: {e}")
        all_achats = []

    if all_achats:
        total_ht = sum(float(a.get("montant_ht") or 0) for a in all_achats)
        total_ttc = sum(float(a.get("montant_ttc") or 0) for a in all_achats)
        nb_commandes = len(all_achats)
        nb_livres = sum(1 for a in all_achats if a.get("statut") == "livré")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("🛒 Commandes", nb_commandes)
        with col2: st.metric("✅ Livrées", nb_livres)
        with col3: st.metric("💰 Total HT", fmt(total_ht))
        with col4: st.metric("💶 Total TTC", fmt(total_ttc))

        rows_all = []
        for a in all_achats:
            fourn_nom = ""
            if isinstance(a.get("fournisseurs"), dict):
                fourn_nom = a["fournisseurs"].get("nom", "")
            chant_nom = ""
            if isinstance(a.get("chantiers"), dict):
                chant_nom = a["chantiers"].get("nom", "")
            rows_all.append({
                "N°": a.get("numero", ""),
                "Chantier": chant_nom,
                "Fournisseur": fourn_nom,
                "Objet": a.get("objet", "")[:35],
                "Montant TTC": fmt(a.get("montant_ttc") or a.get("montant_ht") or 0),
                "Statut": a.get("statut", ""),
                "Date": str(a.get("date_commande", ""))[:10],
            })
        st.dataframe(pd.DataFrame(rows_all), use_container_width=True)
    else:
        st.info("Aucune commande enregistrée.")
