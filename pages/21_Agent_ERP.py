import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import json
from datetime import datetime
import pandas as pd
from lib.helpers import page_setup, render_saas_sidebar, require_feature
from lib.supabase_client import get_supabase_client
from utils import GLOBAL_CSS

user_id = page_setup('Agent ERP', icon='🎤')
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, 'agent_erp')

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

st.title('🎤 Agent ERP — ConducteurPro')
st.markdown('**Votre assistant IA pour piloter tout votre ERP en langage naturel.**')

if 'agent_history' not in st.session_state:
    st.session_state.agent_history = []

# Chargement du contexte live
try:
    chantiers = sb.table('chantiers').select('id,nom,statut,budget_ht,facture_ht,avancement_pct').eq('user_id', user_id).execute().data or []
except Exception:
    chantiers = []
try:
    fournisseurs = sb.table('fournisseurs').select('id,nom,categorie').eq('user_id', user_id).execute().data or []
except Exception:
    fournisseurs = []
try:
    prospects = sb.table('prospects').select('id,nom,statut,budget_estime').eq('user_id', user_id).execute().data or []
except Exception:
    prospects = []
try:
    stocks_list = sb.table('stocks').select('designation,quantite_stock,stock_minimum').eq('user_id', user_id).execute().data or []
    stocks_alerts = [s for s in stocks_list if float(s.get('quantite_stock') or 0) <= float(s.get('stock_minimum') or 0)]
except Exception:
    stocks_alerts = []
try:
    achats_recents = sb.table('achats').select('numero,objet,montant_ttc,statut').eq('user_id', user_id).order('created_at', desc=True).limit(5).execute().data or []
except Exception:
    achats_recents = []

def build_system_context():
    chantiers_data = json.dumps([dict(nom=c['nom'], statut=c.get('statut'), budget=c.get('budget_ht', 0), avancement=c.get('avancement_pct', 0)) for c in chantiers[:8]], ensure_ascii=False)
    fournis_data = json.dumps([dict(nom=f['nom'], cat=f.get('categorie')) for f in fournisseurs[:8]], ensure_ascii=False)
    prospects_data = json.dumps([dict(nom=p['nom'], statut=p.get('statut'), budget=p.get('budget_estime', 0)) for p in prospects[:8]], ensure_ascii=False)
    stocks_data = json.dumps([dict(art=s['designation'], qte=s.get('quantite_stock', 0)) for s in stocks_alerts[:5]], ensure_ascii=False)
    achats_data = json.dumps([dict(num=a.get('numero'), objet=a.get('objet', '')[:30], ttc=a.get('montant_ttc', 0), statut=a.get('statut')) for a in achats_recents], ensure_ascii=False)
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return (f"Tu es l'Agent ERP de ConducteurPro, expert BTP. Date: {now}\n\n"
            f"CHANTIERS ({len(chantiers)}): {chantiers_data}\n"
            f"FOURNISSEURS ({len(fournisseurs)}): {fournis_data}\n"
            f"PIPELINE CRM ({len(prospects)} prospects): {prospects_data}\n"
            f"ALERTES STOCK ({len(stocks_alerts)} sous seuil): {stocks_data}\n"
            f"DERNIERS ACHATS: {achats_data}\n\n"
            "ROLE: Analyse les donnees, detecte anomalies, conseille. Reponds en francais avec emojis. "
            "Propose toujours une action concrete. Signale les urgences clairement.")

def call_claude(user_message, history):
    try:
        import anthropic
        api_key = st.secrets.get('ANTHROPIC_API_KEY', '')
        if not api_key or 'METS' in api_key:
            return 'Cle API Anthropic manquante. Ajoutez ANTHROPIC_API_KEY dans .streamlit/secrets.toml'
        client = anthropic.Anthropic(api_key=api_key)
        messages = []
        for h in history[-8:]:
            messages.append({'role': h['role'], 'content': h['content']})
        messages.append({'role': 'user', 'content': user_message})
        response = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=2048,
            system=build_system_context(),
            messages=messages
        )
        return response.content[0].text
    except ImportError:
        return 'Module anthropic non installe. Lancez: pip install anthropic'
    except Exception as e:
        return f'Erreur agent: {str(e)}'

# Actions rapides
st.markdown('### ⚡ Actions Rapides')
col1, col2, col3, col4 = st.columns(4)
quick = {
    'U0001f4ca Bilan du jour': 'Donne-moi un bilan complet: chantiers, finances, alertes, priorites.',
    'U0001f6a8 Alertes': 'Quelles sont toutes les alertes urgentes? Retards, budgets, stocks critiques, relances CRM.',
    'U0001f4b0 Rentabilite': 'Analyse la rentabilite de chaque chantier actif.',
    'U0001f4cb Pipeline CRM': 'Resume mon pipeline commercial et les relances prioritaires.',
}
for i, (label, prompt) in enumerate(quick.items()):
    with [col1, col2, col3, col4][i]:
        if st.button(label, use_container_width=True):
            st.session_state['pending_prompt'] = prompt

st.markdown('---')
st.markdown('### U0001f4dd Commande texte')

user_input = st.text_area(
    'Tapez votre commande en langage naturel',
    placeholder='Ex: Etat de mes chantiers? Quels fournisseurs relancer? Rentabilite du chantier Dupont?',
    height=100,
    key='agent_input'
)

col_send, col_clear, col_voice_soon = st.columns([2, 1, 2])
with col_send:
    send = st.button('U0001f680 Envoyer', type='primary', use_container_width=True)
with col_clear:
    if st.button('U0001f5d1 Effacer', use_container_width=True):
        st.session_state.agent_history = []
        st.rerun()
with col_voice_soon:
    st.markdown('<div style="background:#1e3a5f;border-radius:8px;padding:10px;text-align:center;color:#90caf9;font-size:13px;">U0001f3a4 Commande vocale<br><b>Bientôt disponible</b></div>', unsafe_allow_html=True)

# Traitement
if 'pending_prompt' in st.session_state:
    pending = st.session_state.pop('pending_prompt')
    with st.spinner('U0001f916 Agent en réflexion...'):
        resp = call_claude(pending, st.session_state.agent_history)
    st.session_state.agent_history.append({'role': 'user', 'content': pending})
    st.session_state.agent_history.append({'role': 'assistant', 'content': resp})
    st.rerun()

if send and user_input.strip():
    with st.spinner('U0001f916 Agent en réflexion...'):
        resp = call_claude(user_input.strip(), st.session_state.agent_history)
    st.session_state.agent_history.append({'role': 'user', 'content': user_input.strip()})
    st.session_state.agent_history.append({'role': 'assistant', 'content': resp})
    st.rerun()

# Historique
st.markdown('---')
st.markdown('### U0001f4ac Conversation')
if not st.session_state.agent_history:
    st.info('U0001f44b Bonjour ! Tapez une commande ou cliquez sur une action rapide ci-dessus.\n\n**Exemples :** Etat de mes chantiers • Fournisseurs à relancer • Rentabilité chantier X • Ruptures de stock • Pipeline CRM')
else:
    for msg in reversed(st.session_state.agent_history):
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-msg">U0001f464 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-response">U0001f916 {msg["content"]}</div>', unsafe_allow_html=True)

# Dashboard bas de page
st.markdown('---')
st.markdown('### U0001f4ca Vue d\'ensemble en temps réel')
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric('U0001f3d7 Chantiers', len(chantiers))
with c2:
    st.metric('U0001f3ed Fournisseurs', len(fournisseurs))
with c3:
    st.metric('U0001f465 Prospects', len(prospects))
with c4:
    label = ('U0001f534' if stocks_alerts else 'U0001f7e2') + ' Alertes Stock'
    st.metric(label, len(stocks_alerts))

if chantiers:
    df_c = pd.DataFrame([{
        'Chantier': c.get('nom', ''),
        'Statut': c.get('statut', ''),
        'Budget HT': f"{float(c.get('budget_ht') or 0):,.0f} EUR",
        'Avancement': f"{c.get('avancement_pct', 0)}%",
    } for c in chantiers])
    st.dataframe(df_c, use_container_width=True, hide_index=True)
