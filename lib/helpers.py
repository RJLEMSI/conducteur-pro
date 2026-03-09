"""
ConducteurPro — Helpers communs pour toutes les pages Streamlit.
Fournit l&#39;authentification, la configuration de page et la sidebar SaaS.
"""
import streamlit as st
from lib.supabase_client import init_supabase_session, get_user_id, is_authenticated
def page_setup(): pass