#!/bin/bash
cd /opt/conducteurpro
curl -sL https://raw.githubusercontent.com/RJLEMSI/conducteur-pro/main/lib/helpers.py -o lib/helpers.py
curl -sL https://raw.githubusercontent.com/RJLEMSI/conducteur-pro/main/app.py -o app.py
curl -sL https://raw.githubusercontent.com/RJLEMSI/conducteur-pro/main/pages/0_Tableau_de_bord.py -o pages/0_Tableau_de_bord.py
sudo systemctl restart conducteurpro
echo "Deploy done"