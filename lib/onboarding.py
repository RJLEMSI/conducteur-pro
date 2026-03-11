"""
Module d'onboarding pour les nouveaux utilisateurs ConducteurPro.
Tutoriel guidé en 4 étapes lors de la première connexion.
"""
import streamlit as st


ONBOARDING_STEPS = [
    {
        "title": "Bienvenue sur ConducteurPro !",
        "icon": "\U0001f3d7\ufe0f",
        "content": """
Félicitations pour votre inscription ! ConducteurPro est votre assistant tout-en-un 
pour piloter vos chantiers de construction.

**Ce que vous pouvez faire :**
- Gérer vos chantiers et suivre leur avancement
- Créer des devis et factures professionnels
- Analyser vos plans avec l'intelligence artificielle
- Planifier vos interventions avec le planning Gantt
- Stocker et organiser tous vos documents
""",
    },
    {
        "title": "Créez votre premier chantier",
        "icon": "\U0001f4cb",
        "content": """
Pour commencer, rendez-vous sur la page **Import Données** dans le menu à gauche.

**Vous pouvez :**
1. Importer un fichier Excel ou CSV avec vos données de chantier
2. Ou créer un chantier manuellement depuis le **Tableau de bord**

Une fois votre chantier créé, toutes les autres fonctionnalités 
(métrés, DCE, devis, facturation) seront liées à ce chantier.
""",
    },
    {
        "title": "L'IA à votre service",
        "icon": "\U0001f916",
        "content": """
ConducteurPro intègre une intelligence artificielle puissante pour vous aider :

- **Métrés** : Uploadez un plan et l'IA extrait les quantités
- **DCE** : Analyse automatique des documents de consultation
- **Études** : Analyse technique de vos documents
- **PLU** : Vérification de conformité urbanistique
- **Synthèse** : Rapport global généré automatiquement

Chaque analyse prend quelques secondes et vous fait gagner des heures de travail.
""",
    },
    {
        "title": "Devis, factures et suivi financier",
        "icon": "\U0001f4b0",
        "content": """
Gérez toute votre activité financière :

- **Devis** : Créez des devis professionnels en PDF, envoyez-les à vos clients
- **Facturation** : Transformez vos devis en factures en un clic
- **Tableau de bord** : Suivez votre CA, vos impayés et vos échéances
- **Documents** : Stockez et organisez tous vos fichiers de chantier

**Astuce** : Commencez par créer un chantier, puis un devis. 
Le reste suivra naturellement !
""",
    },
]


def should_show_onboarding():
    """Vérifie si l'onboarding doit être affiché."""
    return (
        st.session_state.get("authenticated", False)
        and not st.session_state.get("onboarding_completed", False)
        and st.session_state.get("is_first_login", False)
    )


def render_onboarding():
    """Affiche le tutoriel d'onboarding étape par étape."""
    if not should_show_onboarding():
        return False
    
    step = st.session_state.get("onboarding_step", 0)
    total = len(ONBOARDING_STEPS)
    current = ONBOARDING_STEPS[step]
    
    # Container principal
    with st.container():
        st.markdown("""
        <style>
        .onboarding-card {
            background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
            border: 2px solid #2E75B6;
            border-radius: 16px;
            padding: 30px;
            margin: 20px 0;
        }
        .onboarding-progress {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-bottom: 20px;
        }
        .onboarding-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #2E75B6, #1B3A5C);
            border-radius: 3px;
            transition: width 0.3s ease;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Barre de progression
        progress = (step + 1) / total
        st.progress(progress, text=f"Étape {step + 1} sur {total}")
        
        # Contenu
        st.markdown(f"## {current['icon']} {current['title']}")
        st.markdown(current["content"])
        
        # Navigation
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col1:
            if step > 0:
                if st.button("\u2b05\ufe0f Précédent", key="onboard_prev", use_container_width=True):
                    st.session_state["onboarding_step"] = step - 1
                    st.rerun()
        
        with col3:
            if step < total - 1:
                if st.button("Suivant \u27a1\ufe0f", key="onboard_next", type="primary", use_container_width=True):
                    st.session_state["onboarding_step"] = step + 1
                    st.rerun()
            else:
                if st.button("\U0001f680 Commencer !", key="onboard_finish", type="primary", use_container_width=True):
                    st.session_state["onboarding_completed"] = True
                    st.session_state["onboarding_step"] = 0
                    st.rerun()
        
        # Lien pour passer
        st.markdown("---")
        if st.button("Passer le tutoriel", key="onboard_skip"):
            st.session_state["onboarding_completed"] = True
            st.rerun()
    
    return True


def mark_first_login(supabase, user_id):
    """Marque que l'utilisateur a complété l'onboarding dans la base."""
    try:
        supabase.table("profiles").update({
            "onboarding_completed": True
        }).eq("id", user_id).execute()
    except Exception:
        pass  # Non bloquant
