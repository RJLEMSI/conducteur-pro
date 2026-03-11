"""
Module CSS responsive pour ConducteurPro.
Injecte des styles adaptatifs pour tablettes et mobiles (usage chantier).
"""
import streamlit as st


def inject_responsive_css():
    """Injecte le CSS responsive dans l'application Streamlit."""
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════
       ConducteurPro - Styles Responsive
       Optimisé pour tablettes sur chantier
       ═══════════════════════════════════════ */
    
    /* ── Base : meilleure lisibilité ── */
    .stApp {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ── Boutons plus grands (tactile) ── */
    .stButton > button {
        min-height: 44px;  /* Minimum tactile recommandé */
        font-size: 15px;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* ── Inputs plus accessibles ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        min-height: 44px;
        font-size: 15px;
    }
    
    /* ── Sidebar compacte ── */
    [data-testid="stSidebar"] {
        min-width: 240px;
    }
    
    [data-testid="stSidebarNav"] a {
        padding: 8px 16px;
        font-size: 14px;
    }
    
    /* ── Tables scrollables ── */
    .stDataFrame {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    /* ── Métriques KPI ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #2E75B6;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700;
        color: #1B3A5C;
    }
    
    /* ── Cards d'abonnement ── */
    .stMarkdown h3 {
        color: #1B3A5C;
    }
    
    /* ══════════════════════════════════════
       TABLETTE (768px - 1024px)
       ══════════════════════════════════════ */
    @media (max-width: 1024px) {
        /* Sidebar auto-collapse */
        [data-testid="stSidebar"] {
            min-width: 200px;
        }
        
        /* Colonnes stack sur tablette portrait */
        .stColumns {
            flex-wrap: wrap;
        }
        
        /* Tables plus compactes */
        .stDataFrame td, .stDataFrame th {
            padding: 6px 8px;
            font-size: 13px;
        }
        
        /* Graphiques pleine largeur */
        .js-plotly-plot {
            width: 100% !important;
        }
    }
    
    /* ══════════════════════════════════════
       MOBILE (< 768px)
       ══════════════════════════════════════ */
    @media (max-width: 768px) {
        /* Texte plus grand pour lisibilité */
        .stMarkdown p {
            font-size: 15px;
            line-height: 1.6;
        }
        
        /* Boutons pleine largeur */
        .stButton > button {
            width: 100%;
            min-height: 48px;
            font-size: 16px;
        }
        
        /* KPIs empilés */
        [data-testid="stMetricValue"] {
            font-size: 24px !important;
        }
        
        /* Masquer le header Streamlit sur mobile */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Plus d'espace pour le contenu */
        .block-container {
            padding: 1rem 0.5rem;
        }
    }
    
    /* ══════════════════════════════════════
       IMPRESSION
       ══════════════════════════════════════ */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        header { display: none; }
        .stButton { display: none; }
        .block-container { padding: 0; max-width: 100%; }
    }
    
    /* ══════════════════════════════════════
       ANIMATIONS
       ══════════════════════════════════════ */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stAlert, [data-testid="stMetric"] {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* ══════════════════════════════════════
       SCROLLBAR PERSONNALISÉE
       ══════════════════════════════════════ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: #2E75B6;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #1B3A5C;
    }
    </style>
    """, unsafe_allow_html=True)


def inject_professional_theme():
    """Injecte un thème professionnel cohérent pour ConducteurPro."""
    st.markdown("""
    <style>
    /* Thème professionnel ConducteurPro */
    .stApp > header {
        background-color: #1B3A5C;
    }
    
    /* Success/Error/Warning messages stylés */
    .stAlert > div[data-baseweb="notification"] {
        border-radius: 8px;
        border-left-width: 4px;
    }
    
    /* Tabs stylés */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1B3A5C;
    }
    </style>
    """, unsafe_allow_html=True)
