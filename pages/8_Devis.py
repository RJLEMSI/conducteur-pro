import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import (GLOBAL_CSS, check_api_key, get_client, generate_devis_lots, generate_devis_pdf)