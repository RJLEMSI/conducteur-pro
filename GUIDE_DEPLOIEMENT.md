# 🚀 Guide de déploiement — ConducteurPro
### Pour démarrer en moins de 30 minutes, sans savoir coder

---

## Ce dont vous avez besoin

1. **Un compte GitHub** (gratuit) → [github.com](https://github.com)
2. **Un compte Streamlit Cloud** (gratuit) → [share.streamlit.io](https://share.streamlit.io)
3. **Une clé API Anthropic Claude** (payant à l'usage) → [console.anthropic.com](https://console.anthropic.com)

> 💡 **Coût API :** Environ 0,015 $ par analyse. Pour 100 analyses/mois = ~1,50 $. Très rentable pour du SaaS.

---

## ÉTAPE 1 — Créer votre dépôt GitHub

1. Allez sur **github.com** et créez un compte gratuit
2. Cliquez sur le **bouton vert "New"** pour créer un nouveau dépôt
3. Donnez-lui un nom (ex : `conducteurpro`)
4. Cochez **"Private"** (votre code restera privé)
5. Cliquez **"Create repository"**

---

## ÉTAPE 2 — Uploader les fichiers

Une fois le dépôt créé, cliquez sur **"uploading an existing file"** et uploadez tous les fichiers du dossier `conducteur-pro/` :

```
conducteur-pro/
├── app.py                    ← Page d'accueil
├── utils.py                  ← Fonctions partagées
├── requirements.txt          ← Dépendances Python
├── .streamlit/
│   └── config.toml           ← Théme de l'app
└── pages/
    ├── 1_Metres.py           ← Module métrés
    ├── 2_DCE.py              ← Module DCE
    ├── 3_Etudes.py           ← Module études techniques
    └── 4_Planning.py         ← Module planning
```

> ⚠️ Important : Respectez exactement la structure des dossiers.

---

## ÉTAPE 3 — Déployer sur Streamlit Cloud

1. Allez sur **[share.streamlit.io](https://share.streamlit.io)**
2. Connectez-vous avec votre compte GitHub
3. Cliquez **"New app"**
4. Sélectionnez votre dépôt `conducteurpro`
5. Laissez le fichier principal sur **`app.py`**
6. Cliquez **"Deploy !"**

→ Votre application sera en ligne en 2-3 minutes à une URL du type :
`https://conducteurpro.streamlit.app`

---

## ÉTAPE 4 — Configurer votre clé API (OBLIGATOIRE)

**Ne jamais mettre la clé API directement dans le code.** Voici comment la configurer proprement :

1. Sur Streamlit Cloud, allez dans les **Settings** de votre app (roue dentée ⚙️)
2. Cliquez sur **"Secrets"**
3. Ajoutez ceci :

```toml
ANTHROPIC_API_KEY = "sk-ant-votre-cle-ici"
```

4. Cliquez **"Save"** — votre app redémarre automatiquement

> ✅ Votre clé est maintenant sécurisée et jamais visible dans le code.

---

## ÉTAPE 5 — Obtenir votre clé API Anthropic

1. Allez sur **[console.anthropic.com](https://console.anthropic.com)**
2. Créez un compte (vous avez droit à des crédits gratuits au départ)
3. Dans le menu, cliquez **"API Keys"** → **"Create Key"**
4. Copiez la clé (elle commence par `sk-ant-...`)
5. Collez-la dans les Secrets Streamlit (étape 4)

> 💳 Prévoyez un budget de 10-20$/mois pour démarrer. Rechargez au fur et à mesure.

---

## ÉTAPE 6 — Tester votre application

1. Ouvrez l'URL de votre app (ex : `https://conducteurpro.streamlit.app`)
2. Vérifiez que "✅ Claude AI connecté" apparaît dans la sidebar
3. Testez chaque module avec un fichier test

---

## Personnaliser le nom de votre logiciel

Pour changer "ConducteurPro" en votre propre nom de marque :

1. Ouvrez `app.py` dans GitHub (cliquez sur le fichier → icône crayon ✏️)
2. Cherchez tous les `ConducteurPro` et remplacez par votre nom
3. Faites pareil dans `utils.py` et les fichiers `pages/`
4. Cliquez **"Commit changes"** — l'app se met à jour automatiquement

---

## Modèle commercial suggéré

| Offre | Prix | Contenu |
|-------|------|---------|
| **Découverte** | 29 €/mois | 50 analyses, 1 utilisateur |
| **Pro** | 79 €/mois | Analyses illimitées, 3 utilisateurs |
| **Entreprise** | Sur devis | Instance dédiée, API clé pro, formation |

**Outils de paiement recommandés :**
- **Stripe** (stripe.com) pour les paiements récurrents
- **Gumroad** ou **Paddle** pour démarrer sans développement

---

## Questions fréquentes

**L'app est lente ?**
→ Normal au démarrage ("cold start"). Une fois lancée, les analyses prennent 30-60 secondes.

**Le PDF ne lit pas le texte ?**
→ Certains PDFs sont des scans (images). Il faut les passer en OCR d'abord (Adobe, ilovepdf.com).

**Comment avoir plusieurs clients ?**
→ Pour une vraie gestion multi-utilisateurs, il faudra ajouter un système d'auth (Streamlit propose `st.secrets` + authentification simple). Pour débuter, donnez l'accès via l'URL directement.

**Puis-je utiliser GPT-4 d'OpenAI à la place ?**
→ Oui, modifiez dans `utils.py` les appels `anthropic` par `openai`. La logique reste la même.

---

## Support technique

Pour toute question technique sur ce code, vous pouvez :
- Utiliser Claude Code ou ChatGPT pour vous aider à modifier le code
- Poster sur [community.streamlit.io](https://community.streamlit.io)  (en anglais)
- Embaucher un développeur Streamlit sur Malt ou Upwork (250-500€ pour modifications mineures)

---

*ConducteurPro — Généré avec Claude AI*
