import streamlit as st

# ─── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ConducteurPro · IA Chantier",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS Global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Masquer les éléments Streamlit par défaut */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}

    /* Header principal */
    .hero-header {
        background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 60%, #2196F3 100%);
        padding: 3rem 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2.5rem;
        box-shadow: 0 8px 32px rgba(13, 59, 110, 0.35);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    }
    .hero-header h1 {font-size: 2.8rem; font-weight: 800; margin: 0; letter-spacing: -1px;}
    .hero-header .subtitle {font-size: 1.15rem; opacity: 0.85; margin-top: 0.5rem; font-weight: 400;}
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
        letter-spacing: 0.5px;
    }

    /* Cartes features */
    .feat-card {
        background: white;
        border: 1px solid #E2EBF5;
        border-radius: 18px;
        padding: 2rem 1.5rem;
        text-align: center;
        box-shadow: 0 2px 16px rgba(27, 79, 138, 0.07);
        transition: all 0.25s ease;
        height: 100%;
        cursor: pointer;
    }
    .feat-card:hover {
        box-shadow: 0 8px 32px rgba(27, 79, 138, 0.18);
        border-color: #1B4F8A;
        transform: translateY(-4px);
    }
    .feat-icon {font-size: 2.8rem; margin-bottom: 1rem; display: block;}
    .feat-title {font-size: 1.15rem; font-weight: 700; color: #0D3B6E; margin-bottom: 0.6rem;}
    .feat-desc {color: #6B7280; font-size: 0.88rem; line-height: 1.6;}

    /* Sidebar logo */
    .sidebar-brand {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0D3B6E;
        padding: 0.5rem 0 1rem 0;
        border-bottom: 2px solid #E2EBF5;
        margin-bottom: 1.2rem;
    }

    /* Info box */
    .info-box {
        background: #EFF6FF;
        border-left: 4px solid #1B6CA8;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1.5rem 0;
        font-size: 0.92rem;
        line-height: 1.7;
    }
    .info-box strong {color: #0D3B6E;}

    /* Step indicator */
    .step-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .step-item {
        background: white;
        border: 1px solid #E2EBF5;
        border-radius: 12px;
        padding: 1rem;
        flex: 1;
        text-align: center;
        font-size: 0.85rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .step-num {
        background: #0D3B6E;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }

    /* API key section */
    .api-box {
        background: #FFF7ED;
        border: 1px solid #FCD34D;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.85rem;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.5rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 0.8rem !important;
        transition: all 0.2s !important;
        box-shadow: 0 2px 8px rgba(13, 59, 110, 0.25) !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(13, 59, 110, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🏗️ ConducteurPro</div>', unsafe_allow_html=True)

    # Gestion de la clé API
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    if not st.session_state.api_key:
        st.markdown('<div class="api-box">⚠️ Clé API requise</div>', unsafe_allow_html=True)
        key_input = st.text_input(
            "Clé API Anthropic",
            type="password",
            placeholder="sk-ant-...",
            key="api_input"
        )
        if key_input:
            st.session_state.api_key = key_input
            st.rerun()
        st.caption("🔑 [Créer une clé gratuite →](https://console.anthropic.com)")
    else:
        st.success("✅ Claude AI connecté")

    st.divider()
    st.markdown("**Navigation**")
    st.page_link("app.py", label="🏠 Accueil")
    st.page_link("pages/1_Metres.py", label="📐 Métrés automatiques")
    st.page_link("pages/2_DCE.py", label="📋 Synthèse DCE")
    st.page_link("pages/3_Etudes.py", label="🐬 Études techniques")
    st.page_link("pages/4_Planning.py", label="📅 Aide au planning")
    st.page_link("pages/5_PLU.py", label="🗺️ Analyse PLU")
    st.page_link("pages/6_Synthese.py", label="🧠 Synthèse Globale ★")

    st.divider()
    st.caption("ConducteurPro v1.1")
    st.caption("Propulsé par Claude AI")

# ─── Contenu principal ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">✦ Intelligence Artificielle · Chantier</div>
    <h1>🏗️ ConducteurPro</h1>
    <div class="subtitle">L'assistant IA des conducteurs de travaux · Métrés · DCE · PLU · Études · Planning · Synthèse Globale</div>
</div>
""", unsafe_allow_html=True)

# ─── Ligne 1 : 4 modules de base ───────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div class="feat-card">
        <span class="feat-icon">📐</span>
        <div class="feat-title">Métrés automatiques</div>
        <div class="feat-desc">Uploadez un plan PDF ou photo. L'IA extrait les surfaces, linéaires et volumes en quelques secondes.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Lancer les métrés", key="go_metre"):
        st.switch_page("pages/1_Metres.py")

with c2:
    st.markdown("""
    <div class="feat-card">
        <span class="feat-icon">📋</span>
        <div class="feat-title">Synthèse DCE</div>
        <div class="feat-desc">Uploadez votre DCE complet. Obtenez un résumé structuré, dates clés et points critiques instantanément.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Analyser le DCE", key="go_dce"):
        st.switch_page("pages/2_DCE.py")

with c3:
    st.markdown("""
    <div class="feat-card">
        <span class="feat-icon">🔬</span>
        <div class="feat-title">Études techniques</div>
        <div class="feat-desc">Béton, structure, thermique, acoustique — l'IA lit les études et vous dit l'essentiel pour le chantier.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Analyser une étude", key="go_etude"):
        st.switch_page("pages/3_Etudes.py")

with c4:
    st.markdown("""
    <div class="feat-card">
        <span class="feat-icon">📅</span>
        <div class="feat-title">Aide au planning</div>
        <div class="feat-desc">Décrivez votre projet ou importez vos analyses. L'IA génère un phasage, planning et checklist démarrage.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Générer un planning", key="go_planning"):
        st.switch_page("pages/4_Planning.py")

# ─── Ligne 2 : PLU + Synthèse Globale ────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
c5, c6, _ = st.columns([1, 1, 2])

with c5:
    st.markdown("""
    <div class="feat-card" style="border-color:#7C3AED;border-width:2px;">
        <span class="feat-icon">🗺️</span>
        <div class="feat-title" style="color:#5B21B6;">Analyse PLU / PLUi</div>
        <div class="feat-desc">Uploadez le règlement de votre zone. L'IA extrait toutes les règles applicables et vérifie la conformité de votre projet.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Analyser le PLU", key="go_plu"):
        st.switch_page("pages/5_PLU.py")

with c6:
    st.markdown("""
    <div class="feat-card" style="border-color:#0D3B6E;border-width:2px;background:linear-gradient(135deg,#f0f4ff,#fff);">
        <span class="feat-icon">🧠</span>
        <div class="feat-title" style="color:#0D3B6E;">Synthèse Globale ★</div>
        <div class="feat-desc">Donnez TOUS vos documents (PLU + DCE + études + plans). L'IA croise tout et produit <strong>90% du dossier projet</strong>. Vous vérifiez, vous signez.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🧠 Lancer la Synthèse Globale", key="go_synthese"):
        st.switch_page("pages/6_Synthese.py")

# ─── Comment démarrer ──────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
    <strong>🚀 Flux de travail recommandé</strong><br><br>
    <strong>1.</strong> Analysez vos documents un par un (PLU, DCE, études, plans) dans les modules dédiés<br>
    <strong>2.</strong> Cliquez "Envoyer à la Synthèse Globale" dans chaque module<br>
    <strong>3.</strong> Allez dans <strong>🧠 Synthèse Globale</strong> — l'IA croise tout et génère votre rapport complet de projet
</div>
""", unsafe_allow_html=True)

# ─── Fonctionnalités clés ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Pourquoi ConducteurPro ?")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("**⚡ Gain de temps massif**")
    st.write("Un métré qui prenait 2 heures se fait en 30 secondes. Une synthèse de DCE de 200 pages en 1 minute.")
with col_b:
    st.markdown("**🎯 Zéro oubli critique**")
    st.write("L'IA repère les clauses importantes, les dates limites et les contraintes techniques que l'œil humain peut rater.")
with col_c:
    st.markdown("**📱 Accessible partout**")
    st.write("Interface web accessible depuis n'importe quel appareil. Pas d'installation, pas de maintenance.")
