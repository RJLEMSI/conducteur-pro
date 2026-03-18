import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
import re
from datetime import datetime, date
import pandas as pd
from lib.helpers import page_setup, render_saas_sidebar, require_feature
from lib.supabase_client import get_supabase_client, is_authenticated
from utils import GLOBAL_CSS

user_id = page_setup("Agent ERP", icon="🎤")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "suivi_financier")

sb = get_supabase_client()

st.markdown("""
<style>
.agent-response {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2838 100%);
    border-left: 4px solid #4fc3f7;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    color: #e0f7fa;
    font-size: 15px;
    line-height: 1.6;
}
.user-msg {
    background: #1e3a5f;
    border-radius: 8px;
    padding: 12px;
    margin: 4px 0;
    color: #fff;
}
</style>
""", unsafe_allow_html=True)

st.title("🎤 Agent ERP — ConducteurPro")
st.markdown("**Votre assistant IA pour piloter tout votre ERP en langage naturel.**")

# Init session
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

# Load context
try:
    chantiers = sb.table("chantiers").select("id,nom,statut,budget_ht,facture_ht,avancement_pct").eq("user_id", user_id).execute().data or []
except Exception:
    chantiers = []

try:
    fournisseurs = sb.table("fournisseurs").select("id,nom,categorie").eq("user_id", user_id).execute().data or []
except Exception:
    fournisseurs = []

try:
    prospects = sb.table("prospects").select("id,nom,statut,budget_estime").eq("user_id", user_id).execute().data or []
except Exception:
    prospects = []

try:
    stocks_list = sb.table("stocks").select("designation,quantite_stock,stock_minimum").eq("user_id", user_id).execute().data or []
    stocks_alerts = [s for s in stocks_list if float(s.get("quantite_stock") or 0) <= float(s.get("stock_minimum") or 0)]
except Exception:
    stocks_alerts = []

try:
    achats_recents = sb.table("achats").select("numero,objet,montant_ttc,statut").eq("user_id", user_id).order("created_at", desc=True).limit(5).execute().data or []
except Exception:
    achats_recents = []


def build_system_context():
    return f"""Tu es l'Agent ERP de ConducteurPro, expert BTP. Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

CHANTIERS ({len(chantiers)}): {json.dumps([dict(nom=c['nom'],statut=c.get('statut'),budget=c.get('budget_ht',0),avancement=c.get('avancement_pct',0)) for c in chantiers[:8]], ensure_ascii=False)}

FOURNISSEURS ({len(fournisseurs)}): {json.dumps([dict(nom=f['nom'],cat=f.get('categorie')) for f in fournisseurs[:8]], ensure_ascii=False)}

PIPELINE CRM ({len(prospects)} prospects): {json.dumps([dict(nom=p['nom'],statut=p.get('statut'),budget=p.get('budget_estime',0)) for p in prospects[:8]], ensure_ascii=False)}

ALERTES STOCK ({len(stocks_alerts)} sous seuil): {json.dumps([dict(art=s['designation'],qte=s.get('quantite_stock',0)) for s in stocks_alerts[:5]], ensure_ascii=False)}

DERNIERS ACHATS: {json.dumps([dict(num=a.get('numero'),objet=a.get('objet','')[:30],ttc=a.get('montant_ttc',0),statut=a.get('statut')) for a in achats_recents], ensure_ascii=False)}

ROLE: Analyse les donnees, detecte anomalies, conseille. Reponds en francais avec emojis.
Propose toujours une action concrete. Signale les urgences clairement."""


def call_claude(user_message, history):
    try:
        import anthropic
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key or "METS" in api_key:
            return "Cle API Anthropic manquante. Ajoutez-la dans .streamlit/secrets.toml sous ANTHROPIC_API_KEY."
        client = anthropic.Anthropic(api_key=api_key)
        messages = []
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=build_system_context(),
            messages=messages
        )
        return response.content[0].text
    except ImportError:
        return "Module anthropic non installe. Lancez: pip install anthropic"
    except Exception as e:
        return f"Erreur agent: {str(e)}"


# Quick actions
st.markdown("### ⚡ Actions Rapides")
col1, col2, col3, col4 = st.columns(4)
quick = {
    "📊 Bilan du jour": "Donne-moi un bilan complet: chantiers, finances, alertes, priorites.",
    "🚨 Alertes": "Quelles sont toutes les alertes urgentes? Retards, budgets, stocks critiques, relances CRM.",
    "💰 Rentabilite": "Analyse la rentabilite de chaque chantier actif.",
    "📋 Pipeline CRM": "Resume mon pipeline commercial et les relances prioritaires.",
}
for i, (label, prompt) in enumerate(quick.items()):
    with [col1, col2, col3, col4][i]:
        if st.button(label, use_container_width=True):
            st.session_state["pending_prompt"] = prompt

st.markdown("---")
st.markdown("### 📝 Commande")

col_txt, col_voice = st.columns([3, 1])
with col_txt:
    user_input = st.text_area(
        "Tapez votre commande",
        placeholder="Ex: Etat de mes chantiers? Quels fournisseurs relancer? Rentabilite du chantier X?",
        height=100, key="agent_input"
    )
    c1, c2 = st.columns([3,1])
    with c1:
        send = st.button("🚀 Envoyer", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑 Effacer", use_container_width=True):
            st.session_state.agent_history = []
            st.rerun()

with col_voice:
    st.markdown("**🎤 Voix:**")
    try:
        audio = st.audio_input("🎤 Enregistrer", key="audio_cmd")
        if audio is not None:
            with st.spinner("Transcription..."):
                try:
                    import anthropic, base64
                    client = anthropic.Anthropic(api_key=st.secrets.get("ANTHROPIC_API_KEY",""))
                    audio_bytes = audio.read()
                    # Note: direct audio transcription not yet in Claude API
                    # Use as text trigger for now
                    st.session_state["pending_prompt"] = "Bilan du jour"
                    st.info("Audio recu - utilise le bilan du jour par defaut.")
                except Exception as e:
                    st.warning(f"Transcription: {e}")
    except Exception:
        st.info("Voix N/A")

# Process
if "pending_prompt" in st.session_state:
    pending = st.session_state.pop("pending_prompt")
    with st.spinner("🤖 Agent en reflexion..."):
        resp = call_claude(pending, st.session_state.agent_history)
    st.session_state.agent_history.append({"role": "user", "content": pending})
    st.session_state.agent_history.append({"role": "assistant", "content": resp})
    st.rerun()

if send and user_input.strip():
    with st.spinner("🤖 Agent en reflexion..."):
        resp = call_claude(user_input.strip(), st.session_state.agent_history)
    st.session_state.agent_history.append({"role": "user", "content": user_input.strip()})
    st.session_state.agent_history.append({"role": "assistant", "content": resp})
    st.rerun()

# History
st.markdown("---")
st.markdown("### 💬 Conversation")

if not st.session_state.agent_history:
    st.markdown("""
    **Bienvenue! Je suis votre Agent ERP. Exemples de commandes:**
    - Quel est l'etat de mes chantiers?
    - Quels fournisseurs dois-je relancer?
    - Analyse la rentabilite du chantier X
    - Quels materiaux sont en rupture?
    - Prepare un bon de commande beton
    - Redige une relance pour le prospect Dupont
    """)
else:
    for msg in reversed(st.session_state.agent_history):
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-response">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# Dashboard
st.markdown("---")
st.markdown("### 📊 Vue d'ensemble")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("🏗 Chantiers", len(chantiers))
with c2: st.metric("🏭 Fournisseurs", len(fournisseurs))
with c3: st.metric("👥 Prospects", len(prospects))
with c4: st.metric(("🔴" if stocks_alerts else "🟢")+" Alertes Stock", len(stocks_alerts))

if chantiers:
    df_c = pd.DataFrame([{
        "Chantier": c.get("nom",""),
        "Statut": c.get("statut",""),
        "Budget HT": f"{float(c.get('budget_ht') or 0):,.0f} EUR",
        "Avancement": f"{c.get('avancement_pct',0)}%",
    } for c in chantiers])
    st.dataframe(df_c, use_container_width=True, hide_index=True)
