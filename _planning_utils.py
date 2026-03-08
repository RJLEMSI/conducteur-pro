"""
Utilitaires partagés pour le module Planning.
"""


def extract_phases_from_markdown(text: str) -> list:
    """Tente d'extraire les phases depuis le markdown du planning généré par l'IA."""
    phases = []
    lines = text.split('\n')
    in_table = False
    header_found = False
    header_line_passed = False

    for line in lines:
        line_stripped = line.strip()
        if '|' not in line_stripped:
            if in_table and len(phases) > 0:
                break  # fin du tableau
            in_table = False
            header_found = False
            header_line_passed = False
            continue

        cols = [c.strip() for c in line_stripped.split('|') if c.strip()]
        if not cols:
            continue

        # Détection de l'entête du tableau de phases
        if not header_found:
            line_lower = line_stripped.lower()
            if any(kw in line_lower for kw in ['phase', 'phasage', 'durée', 'description']):
                in_table = True
                header_found = True
                header_line_passed = False
                continue

        if header_found and not header_line_passed:
            # Ligne séparatrice (ex: |---|---|---|)
            if all(set(c.replace('-', '').replace(' ', '').replace(':', '')) == set() or c.replace('-', '').replace(' ', '').replace(':', '') == '' for c in cols):
                header_line_passed = True
                continue
            else:
                header_line_passed = True

        if in_table and header_line_passed and len(cols) >= 2:
            # Ignorer les lignes vides ou séparatrices
            if all(c == '' or c.replace('-','').replace(':','').replace(' ','') == '' for c in cols):
                continue

            phase = {
                "phase": cols[0] if len(cols) > 0 else "",
                "description": cols[1] if len(cols) > 1 else "",
                "duree": cols[2] if len(cols) > 2 else "",
                "debut": "",
                "fin": "",
                "conditions": cols[3] if len(cols) > 3 else "",
                "responsable": "",
            }

            # Ne pas ajouter les lignes header résiduelles
            if phase["phase"].lower() in ['phase', 'n°', '#', 'lot'] and len(phases) == 0:
                continue

            if phase["phase"]:
                phases.append(phase)

    return phases
