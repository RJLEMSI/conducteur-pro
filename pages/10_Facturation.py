import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from lib.storage import get_signed_url
from utils import GLOBAL_CSS