"""
Page 9 — Abonnement & Mon Compte
Gestion des abonnements via Stripe (CB + SEPA/Virement). Offres Free / Pro / Équipe.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import GLOBAL_CSS, render_sidebar, check_subscription_status

st.set_page_config(
    page_title="Abonnement · ConducteurPro",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# CSS spécifique
st.markdown("""
<style>
.plan-card {
    background: white;
    border: 2px solid #E2EBF5;
    border-radius: 20px;
    padding: 2rem 1.5rem;
    text-align: center;
    height: 100%;
    transition: all 0.25s;
    position: relative;
}
.plan-card:hover { border-color: #1B6CA8; box-shadow: 0 8px 30px rgba(13,59,110,0.12); }
.plan-card.popular { border-color: #0D3B6E; border-width: 3px; }
.plan-badge { position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
    background: #0D3B6E; color: white; padding: 0.25rem 1rem; border-radius: 20px;
    font-size: 0.78rem; font-weight: 700; white-space: nowrap; }
.plan-price { font-size: 2.8rem; font-weight: 800; color: #0D3B6E; }
.plan-price span { font-size: 1rem; font-weight: 400; color: #6B7280; }
.plan-name { font-size: 1.2rem; font-weight: 700; color: #0D3B6E; margin-bottom: 0.5rem; }
.plan-feature { font-size: 0.88rem; color: #4B5563; padding: 0.3rem 0; text-align: left; }
.plan-feature::before { content: "✅ "; }
.plan-feature.no::before { content: "❌ "; }
.subscription-active {
    background: linear-gradient(135deg, #0D3B6E, #1B6CA8);
    color: white;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
}
.rib-box {
    background: #F0F7FF;
    border: 2px solid #1B6CA8;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
}
.sepa-badge {
    background: #0D3B6E;
    color: white;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    margin-left: 0.4rem;
}
.payout-info {
    background: linear-gradient(135deg, #E8F5E9, #F1F8E9);
    border: 2px solid #4CAF50;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── En-tête ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>⭐ Abonnement & Mon Compte</h2>
    <p>Débloquez toutes les fonctionnalités — Paiement par carte ou virement SEPA</p>
</div>
""", unsafe_allow_html=True)

# ─── Onglets principaux ──────────────────────────────────────────────────────────
tab_offres, tab_sepa, tab_virements = st.tabs([
    "📦 Nos offres",
    "🏦 Payer par virement SEPA",
    "💳 Recevoir mes paiements (Admin)"
])

# ─── Vérification abonnement ─────────────────────────────────────────────────────
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_plan" not in st.session_state:
    st.session_state.user_plan = "free"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ─── Formulaire connexion / vérification ────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("**👤 Mon compte**")
    if st.session_state.user_email:
        plan_labels = {"free": "🆓 Gratuit", "pro": "🚀 Pro", "team": "🏢 Équipe"}
        st.success(f"✅ {st.session_state.user_email}")
        st.info(f"Plan : **{plan_labels.get(st.session_state.user_plan, '🆓 Gratuit')}**")
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.user_email = ""
            st.session_state.user_plan = "free"
            st.session_state.user_name = ""
            st.rerun()
    else:
        with st.form("login_form"):
            email_input = st.text_input("Votre email", placeholder="pro@entreprise.fr")
            submitted = st.form_submit_button("Vérifier mon abonnement", use_container_width=True)
            if submitted and email_input:
                with st.spinner("Vérification..."):
                    plan = check_subscription_status(email_input)
                    st.session_state.user_email = email_input
                    st.session_state.user_plan = plan
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 : Nos offres
# ═══════════════════════════════════════════════════════════════════════════════
with tab_offres:
    # ─── Statut abonnement actif ─────────────────────────────────────────────────
    if st.session_state.user_email and st.session_state.user_plan != "free":
        plan_labels = {"pro": "🚀 Pro", "team": "🏢 Équipe"}
        st.markdown(f"""
        <div class="subscription-active">
            <h3 style="margin:0;color:white;">✅ Abonnement actif : {plan_labels.get(st.session_state.user_plan, '')}</h3>
            <p style="margin:0.5rem 0 0 0;opacity:0.85;">Compte : {st.session_state.user_email} · Toutes les fonctionnalités sont débloquées.</p>
        </div>
        """, unsafe_allow_html=True)

        stripe_portal = st.secrets.get("STRIPE_PORTAL_URL", "")
        if stripe_portal:
            st.markdown(f'<a href="{stripe_portal}" target="_blank"><button style="background:#0D3B6E;color:white;border:none;padding:0.6rem 1.5rem;border-radius:8px;cursor:pointer;font-weight:600;">⚙️ Gérer mon abonnement (Stripe)</button></a>', unsafe_allow_html=True)

    st.markdown("### 💼 Choisissez votre offre")
    st.markdown("Paiement sécurisé par **carte bancaire** ou **virement SEPA** (prélèvement automatique mensuel)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">🆓 Découverte</div>
            <div class="plan-price">0 €<span>/mois</span></div>
            <hr style="border-color:#E2EBF5;margin:1rem 0;">
            <div class="plan-feature">3 analyses par mois</div>
            <div class="plan-feature">Toutes les fonctionnalités</div>
            <div class="plan-feature">Export TXT et Markdown</div>
            <div class="plan-feature no">Historique sauvegardé</div>
            <div class="plan-feature no">Générateur de devis PDF</div>
            <div class="plan-feature no">Support prioritaire</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;color:#6B7280;padding:0.6rem;border-radius:8px;background:#F9FAFB;font-weight:600;">Plan actuel (gratuit)</div>""", unsafe_allow_html=True)

    with col2:
        stripe_pro_url = st.secrets.get("STRIPE_LINK_PRO", "#")
        st.markdown(f"""
        <div class="plan-card popular">
            <div class="plan-badge">⭐ LE PLUS POPULAIRE</div>
            <div class="plan-name">🚀 Pro</div>
            <div class="plan-price">19 €<span>/mois</span></div>
            <hr style="border-color:#E2EBF5;margin:1rem 0;">
            <div class="plan-feature">Analyses <strong>illimitées</strong></div>
            <div class="plan-feature">Toutes les fonctionnalités</div>
            <div class="plan-feature">Export TXT et Markdown</div>
            <div class="plan-feature">Historique des plannings</div>
            <div class="plan-feature">Générateur de devis PDF</div>
            <div class="plan-feature">Support email</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.user_plan == "pro":
            st.success("✅ Votre plan actuel")
        else:
            st.markdown(f"""
            <a href="{stripe_pro_url}" target="_blank" style="text-decoration:none;">
                <div style="background:linear-gradient(135deg,#0D3B6E,#1B6CA8);color:white;text-align:center;
                        padding:0.7rem;border-radius:10px;font-weight:700;cursor:pointer;font-size:1.05rem;">
                    💳 S'abonner à 19 €/mois
                </div>
            </a>
            """, unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:0.78rem;color:#6B7280;margin-top:0.4rem;'>Carte bancaire ou virement SEPA</div>", unsafe_allow_html=True)

    with col3:
        stripe_team_url = st.secrets.get("STRIPE_LINK_TEAM", "#")
        st.markdown(f"""
        <div class="plan-card">
            <div class="plan-name">🏢 Équipe</div>
            <div class="plan-price">49 €<span>/mois</span></div>
            <hr style="border-color:#E2EBF5;margin:1rem 0;">
            <div class="plan-feature">Tout le plan Pro</div>
            <div class="plan-feature">Jusqu'à <strong>5 utilisateurs</strong></div>
            <div class="plan-feature">Historique illimité</div>
            <div class="plan-feature">Export PDF avancé</div>
            <div class="plan-feature">Support prioritaire</div>
            <div class="plan-feature">Formation dédiée (1h)</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.user_plan == "team":
            st.success("✅ Votre plan actuel")
        else:
            st.markdown(f"""
            <a href="{stripe_team_url}" target="_blank" style="text-decoration:none;">
                <div style="background:#1B6CA8;color:white;text-align:center;
                        padding:0.7rem;border-radius:10px;font-weight:700;cursor:pointer;font-size:1.05rem;">
                    💳 S'abonner à 49 €/mois
                </div>
            </a>
            """, unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:0.78rem;color:#6B7280;margin-top:0.4rem;'>Carte bancaire ou virement SEPA</div>", unsafe_allow_html=True)

    # ─── Après paiement ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✅ Vous venez de vous abonner ?")
    st.markdown("""
    <div class="info-box">
    Après votre paiement Stripe, entrez votre adresse email dans le champ <strong>"Mon compte"</strong>
    (barre latérale gauche) pour activer votre abonnement. Votre accès sera vérifié automatiquement.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("❓ Foire aux questions"):
        st.markdown("""
**Comment fonctionne le paiement ?**
Le paiement est sécurisé via Stripe. Vous êtes débité chaque mois. Résiliation possible à tout moment.

**Puis-je payer par virement bancaire (SEPA) ?**
Oui ! Cliquez sur l'onglet **"🏦 Payer par virement SEPA"** ci-dessus. Vous recevrez un mandat de prélèvement automatique mensuel.

**Puis-je essayer avant de payer ?**
Oui ! Le plan Découverte est gratuit et donne accès à 3 analyses par mois, sans carte bancaire.

**Mes données sont-elles sécurisées ?**
Les documents que vous uploadez sont traités en mémoire et ne sont jamais stockés durablement sur nos serveurs.

**Comment résilier ?**
Via le portail Stripe accessible depuis cette page, ou en nous écrivant à l'adresse email de support.

**L'IA peut-elle se tromper ?**
L'IA est un assistant, pas un substitut à votre expertise. Elle fournit une base de travail que vous validez.
        """)

    st.markdown("---")
    st.markdown("**Besoin d'aide ?** Écrivez-nous à " + st.secrets.get("SUPPORT_EMAIL", "support@conducteurpro.fr"))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 : Payer par virement SEPA (côté client)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_sepa:
    st.markdown("### 🏦 Abonnement par prélèvement SEPA")
    st.markdown("""
    <div class="rib-box">
        <h4 style="margin:0 0 0.5rem 0;color:#0D3B6E;">💡 Comment fonctionne le prélèvement SEPA ?</h4>
        <p style="margin:0;color:#374151;">
            Le prélèvement SEPA (Single Euro Payments Area) permet de payer votre abonnement <strong>directement depuis votre compte bancaire</strong>,
            sans carte bancaire. Vous signez une fois un mandat de prélèvement, et le renouvellement est <strong>automatique chaque mois</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Étapes pour s'abonner par virement SEPA")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("""
        **1️⃣ Choisissez votre offre**

        Sélectionnez votre plan ci-dessous et cliquez sur le lien de paiement SEPA.
        Vous serez redirigé vers notre page de paiement sécurisée Stripe.

        **2️⃣ Entrez votre IBAN**

        Sur la page Stripe, sélectionnez "Prélèvement SEPA" comme méthode de paiement
        et entrez votre IBAN (ex: FR76 3000 6000 0112 3456 7890 189).

        **3️⃣ Signez le mandat électronique**

        Vous recevrez par email un mandat de prélèvement SEPA à confirmer.
        Ce mandat autorise le débit mensuel automatique de votre compte.

        **4️⃣ Activation de votre compte**

        Une fois le premier prélèvement validé (1-2 jours ouvrés), entrez votre
        email dans "Mon compte" pour activer votre accès Pro ou Équipe.
        """)

    with col_s2:
        # Coordonnées bancaires affichées si configurées dans secrets
        iban_owner = st.secrets.get("OWNER_IBAN", "")
        bic_owner = st.secrets.get("OWNER_BIC", "")
        owner_name = st.secrets.get("OWNER_NAME", "ConducteurPro")

        if iban_owner:
            st.markdown(f"""
            <div class="rib-box">
                <h4 style="color:#0D3B6E;margin:0 0 1rem 0;">🏦 Virement bancaire direct</h4>
                <p style="font-size:0.85rem;color:#6B7280;margin:0 0 0.8rem 0;">
                    Vous pouvez aussi effectuer un virement manuel mensuel sur le compte ci-dessous.
                    Indiquez votre email en référence du virement.
                </p>
                <table style="width:100%;font-size:0.9rem;">
                    <tr><td style="color:#6B7280;padding:0.3rem 0;">Bénéficiaire</td>
                        <td style="font-weight:700;color:#0D3B6E;">{owner_name}</td></tr>
                    <tr><td style="color:#6B7280;padding:0.3rem 0;">IBAN</td>
                        <td style="font-weight:700;font-family:monospace;color:#0D3B6E;">{iban_owner}</td></tr>
                    {'<tr><td style="color:#6B7280;padding:0.3rem 0;">BIC/SWIFT</td><td style="font-weight:700;color:#0D3B6E;">' + bic_owner + '</td></tr>' if bic_owner else ''}
                    <tr><td style="color:#6B7280;padding:0.3rem 0;">Référence</td>
                        <td style="font-weight:700;color:#0D3B6E;">Votre adresse email</td></tr>
                    <tr><td style="color:#6B7280;padding:0.3rem 0;">Montant</td>
                        <td style="font-weight:700;color:#0D3B6E;">19 € (Pro) ou 49 € (Équipe)</td></tr>
                    <tr><td style="color:#6B7280;padding:0.3rem 0;">Fréquence</td>
                        <td style="font-weight:700;color:#0D3B6E;">Mensuelle (même date chaque mois)</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="rib-box">
                <h4 style="color:#0D3B6E;margin:0 0 0.5rem 0;">🏦 Coordonnées bancaires</h4>
                <p style="color:#6B7280;font-size:0.9rem;">
                    Les coordonnées bancaires pour le virement direct seront affichées ici une fois configurées.
                    Utilisez en attendant le paiement par carte ou SEPA via Stripe ci-dessous.
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 💳 Liens de paiement SEPA via Stripe")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        stripe_pro_sepa = st.secrets.get("STRIPE_LINK_PRO_SEPA", st.secrets.get("STRIPE_LINK_PRO", "#"))
        st.markdown(f"""
        <div style="border:2px solid #0D3B6E;border-radius:16px;padding:1.5rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;color:#0D3B6E;">🚀 Plan Pro</div>
            <div style="font-size:2rem;font-weight:800;color:#0D3B6E;margin:0.5rem 0;">19 €<span style="font-size:1rem;font-weight:400;color:#6B7280;">/mois</span></div>
            <a href="{stripe_pro_sepa}" target="_blank" style="text-decoration:none;">
                <div style="background:#0D3B6E;color:white;padding:0.7rem;border-radius:10px;font-weight:700;margin-top:1rem;">
                    🏦 S'abonner par SEPA — 19 €/mois
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

    with col_p2:
        stripe_team_sepa = st.secrets.get("STRIPE_LINK_TEAM_SEPA", st.secrets.get("STRIPE_LINK_TEAM", "#"))
        st.markdown(f"""
        <div style="border:2px solid #1B6CA8;border-radius:16px;padding:1.5rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;color:#1B6CA8;">🏢 Plan Équipe</div>
            <div style="font-size:2rem;font-weight:800;color:#1B6CA8;margin:0.5rem 0;">49 €<span style="font-size:1rem;font-weight:400;color:#6B7280;">/mois</span></div>
            <a href="{stripe_team_sepa}" target="_blank" style="text-decoration:none;">
                <div style="background:#1B6CA8;color:white;padding:0.7rem;border-radius:10px;font-weight:700;margin-top:1rem;">
                    🏦 S'abonner par SEPA — 49 €/mois
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box" style="margin-top:1.5rem;">
        <strong>🔒 Sécurité :</strong> Le prélèvement SEPA est régi par la réglementation bancaire européenne (mandat SEPA).
        Vous pouvez contester tout prélèvement non autorisé auprès de votre banque dans un délai de 8 semaines.
        Vos coordonnées bancaires ne sont <strong>jamais</strong> stockées sur nos serveurs — elles sont gérées par Stripe (certifié PCI DSS niveau 1).
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 : Configurer les virements entrants (Admin / propriétaire de l'app)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_virements:
    st.markdown("### 💳 Configuration des virements — Espace propriétaire")
    st.markdown("""
    <div class="info-box">
        <strong>📌 Cet espace est destiné au propriétaire de l'application.</strong>
        Configurez ici votre RIB/IBAN pour recevoir les paiements de vos abonnés chaque mois.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🏦 Comment recevoir les paiements sur votre compte bancaire ?")

    with st.expander("📖 Méthode 1 (Recommandée) — Via Stripe Payouts", expanded=True):
        st.markdown("""
        Stripe collecte les paiements de vos abonnés et les vire automatiquement sur votre compte bancaire.
        C'est la méthode la plus simple et la plus sécurisée.

        **Étapes à suivre :**

        1. **Créez un compte Stripe** sur [stripe.com](https://stripe.com) si ce n'est pas déjà fait
        2. **Complétez votre profil Stripe** : Dashboard → Paramètres → Informations entreprise
        3. **Ajoutez votre RIB** : Dashboard → Paramètres → Virements → Ajouter un compte bancaire
           - Entrez votre IBAN (ex: FR76 3000 6000 0112 3456 7890 189)
           - Choisissez la devise EUR
        4. **Définissez le calendrier** : Virements automatiques quotidiens ou hebdomadaires selon vos préférences
        5. **Copiez votre clé API Stripe** (Dashboard → Développeurs → Clés API) et ajoutez-la dans les secrets Streamlit

        Stripe prélève **1,5% + 0,25€** par transaction pour les cartes européennes et **0,35%** pour SEPA.
        """)

    with st.expander("📖 Méthode 2 — Virement bancaire manuel (via RIB affiché aux clients)"):
        st.markdown("""
        Vous affichez vos coordonnées bancaires (IBAN/RIB) directement dans l'onglet "Payer par virement SEPA",
        et vos clients font un virement manuel chaque mois.

        **Avantages :** Aucun frais bancaire, simplicité
        **Inconvénients :** Pas de prélèvement automatique, suivi manuel des paiements

        Pour activer cela, ajoutez dans vos **secrets Streamlit** :
        ```toml
        OWNER_IBAN = "FR76 3000 6000 0112 3456 7890 189"
        OWNER_BIC = "BNPAFRPPXXX"
        OWNER_NAME = "Votre Nom ou Raison Sociale"
        ```
        """)

    st.markdown("---")
    st.markdown("#### ⚙️ Configuration rapide des secrets Streamlit")
    st.markdown("""
    <div class="payout-info">
        <h4 style="margin:0 0 0.8rem 0;color:#2E7D32;">📝 Secrets à configurer dans Streamlit Cloud</h4>
        <p style="color:#374151;margin-bottom:0.8rem;">
            Rendez-vous sur <a href="https://share.streamlit.io" target="_blank">share.streamlit.io</a> →
            Votre app → Settings → Secrets, et ajoutez les lignes suivantes :
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.code("""# Clé API Stripe (Dashboard Stripe → Développeurs → Clés API)
STRIPE_SECRET_KEY = "sk_live_VOTRE_CLE_STRIPE"

# Liens de paiement Stripe (Dashboard → Payment Links)
STRIPE_LINK_PRO = "https://buy.stripe.com/XXXXXX"
STRIPE_LINK_TEAM = "https://buy.stripe.com/YYYYYY"

# Liens de paiement SEPA spécifiques (optionnel, sinon utilise les liens ci-dessus)
STRIPE_LINK_PRO_SEPA = "https://buy.stripe.com/SEPA_PRO"
STRIPE_LINK_TEAM_SEPA = "https://buy.stripe.com/SEPA_TEAM"

# IDs des prix Stripe (Dashboard → Produits → Votre produit → ID du prix)
STRIPE_PRICE_PRO = "price_XXXXXX"
STRIPE_PRICE_TEAM = "price_YYYYYY"

# Portail client Stripe (Dashboard → Paramètres → Portail client → Copier le lien)
STRIPE_PORTAL_URL = "https://billing.stripe.com/p/login/XXXXXX"

# Vos coordonnées bancaires (pour virement manuel par les clients)
OWNER_IBAN = "FR76 XXXX XXXX XXXX XXXX XXXX XXX"
OWNER_BIC = "XXXXXXXX"
OWNER_NAME = "Votre Nom"

# Email de support
SUPPORT_EMAIL = "votre@email.fr"
""", language="toml")

    st.markdown("---")
    st.markdown("#### 🧮 Simulateur de revenus")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        nb_pro = st.number_input("Abonnés Pro (19 €/mois)", min_value=0, value=10, step=1)
    with col_r2:
        nb_team = st.number_input("Abonnés Équipe (49 €/mois)", min_value=0, value=3, step=1)
    with col_r3:
        st.markdown("<br>", unsafe_allow_html=True)
        ca_brut = nb_pro * 19 + nb_team * 49
        frais_stripe = ca_brut * 0.015 + (nb_pro + nb_team) * 0.25
        ca_net = ca_brut - frais_stripe
        st.markdown(f"""
        <div style="background:#0D3B6E;color:white;border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:0.85rem;opacity:0.8;">Revenu mensuel net estimé</div>
            <div style="font-size:2rem;font-weight:800;">{ca_net:.0f} €</div>
            <div style="font-size:0.75rem;opacity:0.7;">CA brut {ca_brut} € — Frais Stripe ~{frais_stripe:.0f} €</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box" style="margin-top:1rem;">
        <strong>💡 Pour aller plus loin :</strong> Une fois Stripe configuré, vous recevrez un virement automatique
        sur votre IBAN chaque semaine (ou chaque jour en mode avancé). Le tableau de bord Stripe vous permet de
        suivre vos encaissements, gérer les remboursements et exporter vos factures pour la comptabilité.
    </div>
    """, unsafe_allow_html=True)
