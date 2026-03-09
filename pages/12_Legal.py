"""
Page 12 - Mentions Legales, CGV, Politique de Confidentialite
Pages legales obligatoires pour la vente en France.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import GLOBAL_CSS

st.set_page_config(
    page_title="Mentions Legales - ConducteurPro",
    page_icon="\u2696\ufe0f",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.title("\u2696\ufe0f Informations Legales")

tab1, tab2, tab3 = st.tabs(["Mentions Legales", "CGV", "Politique de Confidentialite"])

with tab1:
    st.header("Mentions Legales")
    st.markdown("""
**Editeur du site :**  
ConducteurPro  
Contact : contact@conducteurpro.fr

**Hebergement :**  
- Application : Streamlit Cloud (Snowflake Inc.)  
  Address: 450 Concar Dr, San Mateo, CA 94402, USA
- Base de donnees : Supabase Inc.  
  Address: 970 Toa Payoh North, Singapore

**Directeur de la publication :**  
Le responsable de la societe exploitante de ConducteurPro.

**Propriete intellectuelle :**  
L'ensemble du contenu du site ConducteurPro (textes, images, logos, logiciels) est protege par le droit d'auteur. 
Toute reproduction, meme partielle, est interdite sans autorisation prealable ecrite.

**Donnees personnelles :**  
Conformement au RGPD et a la loi Informatique et Libertes, vous disposez d'un droit d'acces, 
de rectification, de suppression et de portabilite de vos donnees. 
Pour exercer ces droits : contact@conducteurpro.fr
    """)

with tab2:
    st.header("Conditions Generales de Vente")
    st.markdown("""
**Article 1 - Objet**  
Les presentes CGV regissent les conditions d'utilisation et de souscription aux services 
ConducteurPro, plateforme SaaS destinee aux conducteurs de travaux.

**Article 2 - Services proposes**  
ConducteurPro propose trois formules d'abonnement :
- **Decouverte (Gratuit)** : 3 analyses/mois, 3 chantiers max, stockage 50 Mo
- **Pro (69,90\u20ac/mois)** : Chantiers et analyses illimites, stockage 5 Go, support prioritaire
- **Equipe (118,90\u20ac/mois)** : Tout Pro + jusqu'a 4 utilisateurs, partage de chantiers, stockage 20 Go

**Article 3 - Inscription**  
L'inscription est gratuite et ouverte a toute personne physique ou morale exercant 
une activite professionnelle dans le secteur du BTP.

**Article 4 - Tarifs et paiement**  
Les prix sont indiques en euros TTC. Le paiement est effectue par carte bancaire 
via la plateforme securisee Stripe. L'abonnement est mensuel et reconduit tacitement.

**Article 5 - Droit de retractation**  
Conformement a l'article L221-28 du Code de la consommation, le droit de retractation 
ne peut etre exerce pour les services pleinement executes avant la fin du delai de retractation 
et dont l'execution a commence avec l'accord prealable du consommateur.

**Article 6 - Resiliation**  
L'utilisateur peut resilier son abonnement a tout moment depuis son espace personnel. 
La resiliation prend effet a la fin de la periode d'abonnement en cours.

**Article 7 - Responsabilite**  
ConducteurPro s'engage a fournir un service conforme aux descriptions. 
Les analyses generees par l'intelligence artificielle sont fournies a titre indicatif 
et ne se substituent pas a l'expertise professionnelle du conducteur de travaux.

**Article 8 - Protection des donnees**  
Les donnees personnelles sont traitees conformement a notre Politique de Confidentialite 
et au Reglement General sur la Protection des Donnees (RGPD).

**Article 9 - Droit applicable**  
Les presentes CGV sont soumises au droit francais. En cas de litige, les tribunaux 
competents seront ceux du siege social de l'editeur.

**Article 10 - Modification des CGV**  
ConducteurPro se reserve le droit de modifier les presentes CGV. Les utilisateurs 
seront informes par email de toute modification substantielle.
    """)

with tab3:
    st.header("Politique de Confidentialite")
    st.markdown("""
**Date de derniere mise a jour :** Mars 2026

**1. Responsable du traitement**  
ConducteurPro est responsable du traitement des donnees personnelles collectees 
dans le cadre de l'utilisation de ses services.

**2. Donnees collectees**  
Nous collectons les donnees suivantes :
- **Donnees d'identification** : nom, prenom, adresse email, nom de societe
- **Donnees de connexion** : adresse IP, logs de connexion
- **Donnees d'utilisation** : chantiers, documents uploades, analyses effectuees
- **Donnees de paiement** : traitees exclusivement par Stripe (nous ne stockons pas vos coordonnees bancaires)

**3. Finalites du traitement**  
Vos donnees sont utilisees pour :
- Fournir et ameliorer nos services
- Gerer votre compte et votre abonnement
- Assurer le support technique
- Envoyer des communications relatives au service

**4. Base legale**  
- Execution du contrat (fourniture du service)
- Consentement (communications marketing)
- Interet legitime (amelioration du service, securite)

**5. Duree de conservation**  
- Donnees de compte : pendant la duree de l'abonnement + 3 ans
- Donnees de facturation : 10 ans (obligation legale)
- Logs de connexion : 12 mois

**6. Destinataires des donnees**  
Vos donnees peuvent etre transmises a :
- **Supabase** (hebergement et base de donnees)
- **Stripe** (traitement des paiements)
- **Anthropic** (traitement IA - donnees anonymisees)
- **Streamlit/Snowflake** (hebergement de l'application)

**7. Transferts hors UE**  
Certains sous-traitants sont situes aux Etats-Unis. Les transferts sont encadres 
par les clauses contractuelles types de la Commission europeenne.

**8. Vos droits**  
Conformement au RGPD, vous disposez des droits suivants :
- Droit d'acces a vos donnees
- Droit de rectification
- Droit a l'effacement (droit a l'oubli)
- Droit a la portabilite
- Droit d'opposition
- Droit a la limitation du traitement

Pour exercer vos droits : **contact@conducteurpro.fr**

**9. Securite**  
Nous mettons en oeuvre des mesures techniques et organisationnelles appropriees :
- Chiffrement des donnees en transit (HTTPS/TLS)
- Chiffrement des documents stockes (AES-256)
- Isolation des donnees par utilisateur (Row Level Security)
- Authentification securisee via Supabase Auth

**10. Cookies**  
ConducteurPro utilise uniquement des cookies techniques necessaires au fonctionnement 
du service. Aucun cookie publicitaire ou de tracking n'est utilise.

**11. Contact DPO**  
Pour toute question relative a la protection de vos donnees :  
**contact@conducteurpro.fr**
    """)

st.divider()
st.caption("ConducteurPro - Tous droits reserves - 2026")
