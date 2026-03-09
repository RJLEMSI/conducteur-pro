#!/usr/bin/env python3
"""
ConducteurPro — Script de vérification de configuration
Exécutez ce script pour vérifier que tous les secrets sont correctement configurés.
Usage: python setup_guide.py
"""

import sys

def check_config():
    print("=" * 60)
    print("  ConducteurPro — Vérification de Configuration")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. Check Streamlit secrets
    try:
        import streamlit as st
        secrets = st.secrets
        print("\n✅ Streamlit secrets accessible")
    except Exception:
        # Running outside Streamlit, check .env or .streamlit/secrets.toml
        import os
        from pathlib import Path
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            print("\n✅ .streamlit/secrets.toml trouvé")
        else:
            errors.append("❌ .streamlit/secrets.toml introuvable")
    
    # 2. Check required packages
    required = [
        "streamlit", "anthropic", "supabase", "stripe",
        "cryptography", "pdfplumber", "pandas", "fpdf2", "plotly"
    ]
    print("\n📦 Vérification des packages:")
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            errors.append(f"  ❌ {pkg} manquant → pip install {pkg}")
    
    # 3. Check Supabase connection
    print("\n🔌 Vérification Supabase:")
    try:
        from supabase import create_client
        import os
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if url and key:
            client = create_client(url, key)
            # Test query
            result = client.table("profiles").select("count").limit(1).execute()
            print("  ✅ Connexion Supabase OK")
        else:
            warnings.append("  ⚠️ SUPABASE_URL ou SUPABASE_KEY non définis")
    except Exception as e:
        warnings.append(f"  ⚠️ Supabase: {e}")
    
    # 4. Check Stripe
    print("\n💳 Vérification Stripe:")
    try:
        import stripe
        import os
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if stripe.api_key:
            # Test API
            stripe.Price.list(limit=1)
            print("  ✅ Connexion Stripe OK")
        else:
            warnings.append("  ⚠️ STRIPE_SECRET_KEY non défini")
    except Exception as e:
        warnings.append(f"  ⚠️ Stripe: {e}")
    
    # 5. Check Encryption Key
    print("\n🔐 Vérification chiffrement:")
    try:
        from cryptography.fernet import Fernet
        import os
        key = os.environ.get("ENCRYPTION_KEY", "")
        if key:
            Fernet(key.encode())
            print("  ✅ Clé de chiffrement valide")
        else:
            warnings.append("  ⚠️ ENCRYPTION_KEY non définie")
    except Exception as e:
        errors.append(f"  ❌ Clé invalide: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("❌ ERREURS À CORRIGER:")
        for e in errors:
            print(f"  {e}")
    if warnings:
        print("⚠️  AVERTISSEMENTS:")
        for w in warnings:
            print(f"  {w}")
    if not errors and not warnings:
        print("🎉 Tout est configuré correctement !")
    print("=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
