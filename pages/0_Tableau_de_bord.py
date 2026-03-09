import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from lib.auth import check_feature
from utils import GLOBAL_CSS

# ─── Setup ──────────────────────────────────────────────────────────────────
user_id = page_setup(title="Tableau de bord", icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
