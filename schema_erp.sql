-- BTP (Construction) ERP System - PostgreSQL Schema
-- Additions to existing Supabase database
-- These tables extend the core schema: user_profiles, chantiers, documents, factures, devis, plannings, etapes, etudes, metres, dces, activity_log

-- ============================================================================
-- TABLE: fournisseurs (Suppliers/Vendors Directory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.fournisseurs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  nom VARCHAR(255) NOT NULL,
  contact_nom VARCHAR(255),
  email VARCHAR(255),
  telephone VARCHAR(20),
  adresse TEXT,
  siret VARCHAR(14),
  categorie VARCHAR(50) NOT NULL CHECK (categorie IN ('materiaux', 'location', 'sous-traitance', 'services')),
  notes TEXT,
  actif BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fournisseurs IS 'Suppliers and vendors directory for all categories (materials, rentals, subcontracting, services)';
COMMENT ON COLUMN fournisseurs.siret IS 'SIRET number for French suppliers (System for Business Registration)';
COMMENT ON COLUMN fournisseurs.categorie IS 'Supplier category: materiaux (materials), location (rental), sous-traitance (subcontracting), services';

ALTER TABLE fournisseurs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own suppliers" ON fournisseurs
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_fournisseurs_user_id ON fournisseurs(user_id);
CREATE INDEX idx_fournisseurs_actif ON fournisseurs(actif);
CREATE INDEX idx_fournisseurs_categorie ON fournisseurs(categorie);


-- ============================================================================
-- TABLE: achats (Purchase Orders)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.achats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  chantier_id UUID NOT NULL REFERENCES public.chantiers(id) ON DELETE CASCADE,
  fournisseur_id UUID NOT NULL REFERENCES public.fournisseurs(id) ON DELETE RESTRICT,
  numero VARCHAR(50) NOT NULL,
  objet TEXT NOT NULL,
  date_commande DATE NOT NULL,
  date_livraison_prevue DATE,
  statut VARCHAR(50) NOT NULL DEFAULT 'brouillon' CHECK (statut IN ('brouillon', 'commandé', 'livré_partiel', 'livré', 'annulé')),
  montant_ht DECIMAL(12, 2) NOT NULL DEFAULT 0,
  tva_pct DECIMAL(5, 2) DEFAULT 20,
  montant_ttc DECIMAL(12, 2) NOT NULL DEFAULT 0,
  lignes JSONB DEFAULT '[]',
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE achats IS 'Purchase orders from suppliers for project materials and services';
COMMENT ON COLUMN achats.statut IS 'Order status: brouillon (draft), commandé (ordered), livré_partiel (partially delivered), livré (delivered), annulé (cancelled)';
COMMENT ON COLUMN achats.lignes IS 'JSON array of order lines: [{description, quantite, prix_unitaire, montant}]';

ALTER TABLE achats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own purchase orders" ON achats
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_achats_user_id ON achats(user_id);
CREATE INDEX idx_achats_chantier_id ON achats(chantier_id);
CREATE INDEX idx_achats_fournisseur_id ON achats(fournisseur_id);
CREATE INDEX idx_achats_statut ON achats(statut);


-- ============================================================================
-- TABLE: sous_traitants (Subcontractors)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.sous_traitants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  fournisseur_id UUID NOT NULL REFERENCES public.fournisseurs(id) ON DELETE CASCADE,
  chantier_id UUID NOT NULL REFERENCES public.chantiers(id) ON DELETE CASCADE,
  lot_concerne VARCHAR(255),
  montant_marche DECIMAL(12, 2) NOT NULL DEFAULT 0,
  retenue_garantie_pct DECIMAL(5, 2) DEFAULT 5,
  avancement_pct DECIMAL(5, 2) DEFAULT 0 CHECK (avancement_pct >= 0 AND avancement_pct <= 100),
  montant_facture DECIMAL(12, 2) DEFAULT 0,
  montant_paye DECIMAL(12, 2) DEFAULT 0,
  dc4_reference VARCHAR(100),
  contrat_signe BOOLEAN DEFAULT false,
  statut VARCHAR(50) NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'termine', 'suspendu')),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sous_traitants IS 'Subcontractors assigned to specific projects, tracking contract value, progress, and payments';
COMMENT ON COLUMN sous_traitants.retenue_garantie_pct IS 'Warranty/performance retention percentage (typically 5%)';
COMMENT ON COLUMN sous_traitants.avancement_pct IS 'Work progress percentage (0-100)';
COMMENT ON COLUMN sous_traitants.dc4_reference IS 'Reference to URSSAF declaration (DC4) for compliance tracking';

ALTER TABLE sous_traitants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own subcontractors" ON sous_traitants
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_sous_traitants_user_id ON sous_traitants(user_id);
CREATE INDEX idx_sous_traitants_chantier_id ON sous_traitants(chantier_id);
CREATE INDEX idx_sous_traitants_fournisseur_id ON sous_traitants(fournisseur_id);
CREATE INDEX idx_sous_traitants_statut ON sous_traitants(statut);


-- ============================================================================
-- TABLE: factures_sous_traitants (Subcontractor Invoices)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.factures_sous_traitants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  sous_traitant_id UUID NOT NULL REFERENCES public.sous_traitants(id) ON DELETE CASCADE,
  numero_facture VARCHAR(100) NOT NULL,
  date_facture DATE NOT NULL,
  montant_ht DECIMAL(12, 2) NOT NULL,
  montant_ttc DECIMAL(12, 2) NOT NULL,
  avancement_cumule_pct DECIMAL(5, 2) NOT NULL DEFAULT 0,
  statut VARCHAR(50) NOT NULL DEFAULT 'recue' CHECK (statut IN ('recue', 'validee', 'payee', 'contestee')),
  date_paiement DATE,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE factures_sous_traitants IS 'Invoices from subcontractors, tracked for payment and progress reconciliation';
COMMENT ON COLUMN factures_sous_traitants.avancement_cumule_pct IS 'Cumulative work progress as declared in invoice';
COMMENT ON COLUMN factures_sous_traitants.statut IS 'Invoice status: recue (received), validee (validated), payee (paid), contestee (disputed)';

ALTER TABLE factures_sous_traitants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own subcontractor invoices" ON factures_sous_traitants
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_factures_sous_traitants_user_id ON factures_sous_traitants(user_id);
CREATE INDEX idx_factures_sous_traitants_sous_traitant_id ON factures_sous_traitants(sous_traitant_id);
CREATE INDEX idx_factures_sous_traitants_statut ON factures_sous_traitants(statut);


-- ============================================================================
-- TABLE: pointages (Time Tracking / Employee Time Sheets)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.pointages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  chantier_id UUID NOT NULL REFERENCES public.chantiers(id) ON DELETE CASCADE,
  employe_nom VARCHAR(255) NOT NULL,
  date_pointage DATE NOT NULL,
  heures DECIMAL(5, 2) NOT NULL CHECK (heures >= 0),
  type_heure VARCHAR(50) NOT NULL DEFAULT 'normal' CHECK (type_heure IN ('normal', 'supplementaire', 'nuit', 'weekend')),
  description TEXT,
  valide BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pointages IS 'Time tracking and employee attendance on project sites';
COMMENT ON COLUMN pointages.type_heure IS 'Hour type for payroll: normal (regular), supplementaire (overtime), nuit (night shift), weekend';

ALTER TABLE pointages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own time tracking" ON pointages
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_pointages_user_id ON pointages(user_id);
CREATE INDEX idx_pointages_chantier_id ON pointages(chantier_id);
CREATE INDEX idx_pointages_date_pointage ON pointages(date_pointage);


-- ============================================================================
-- TABLE: employes (Employee Directory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.employes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  nom VARCHAR(255) NOT NULL,
  prenom VARCHAR(255) NOT NULL,
  poste VARCHAR(255),
  taux_horaire DECIMAL(8, 2),
  telephone VARCHAR(20),
  email VARCHAR(255),
  actif BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE employes IS 'Company employee directory with roles and contact information';
COMMENT ON COLUMN employes.taux_horaire IS 'Hourly rate in euros for payroll calculations';

ALTER TABLE employes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own employees" ON employes
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_employes_user_id ON employes(user_id);
CREATE INDEX idx_employes_actif ON employes(actif);


-- ============================================================================
-- TABLE: stocks (Inventory Management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.stocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  designation VARCHAR(255) NOT NULL,
  reference VARCHAR(100),
  categorie VARCHAR(100),
  unite VARCHAR(50),
  quantite_stock DECIMAL(12, 3) DEFAULT 0 CHECK (quantite_stock >= 0),
  stock_minimum DECIMAL(12, 3) DEFAULT 0,
  prix_unitaire DECIMAL(10, 2) DEFAULT 0,
  emplacement VARCHAR(255),
  fournisseur_id UUID REFERENCES public.fournisseurs(id) ON DELETE SET NULL,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stocks IS 'Inventory of materials and supplies with stock levels and pricing';
COMMENT ON COLUMN stocks.quantite_stock IS 'Current inventory quantity in specified unit';
COMMENT ON COLUMN stocks.stock_minimum IS 'Minimum stock level for reordering alerts';

ALTER TABLE stocks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own inventory" ON stocks
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_stocks_user_id ON stocks(user_id);
CREATE INDEX idx_stocks_fournisseur_id ON stocks(fournisseur_id);
CREATE INDEX idx_stocks_categorie ON stocks(categorie);


-- ============================================================================
-- TABLE: mouvements_stock (Stock Movements / Transactions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.mouvements_stock (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  stock_id UUID NOT NULL REFERENCES public.stocks(id) ON DELETE CASCADE,
  chantier_id UUID REFERENCES public.chantiers(id) ON DELETE SET NULL,
  type_mouvement VARCHAR(50) NOT NULL CHECK (type_mouvement IN ('entree', 'sortie', 'inventaire', 'transfert')),
  quantite DECIMAL(12, 3) NOT NULL,
  motif TEXT,
  date_mouvement DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mouvements_stock IS 'Audit trail of all inventory movements (inbound, outbound, adjustments, transfers)';
COMMENT ON COLUMN mouvements_stock.type_mouvement IS 'Movement type: entree (receipt), sortie (usage/delivery), inventaire (inventory adjustment), transfert (transfer between locations)';

ALTER TABLE mouvements_stock ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own stock movements" ON mouvements_stock
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_mouvements_stock_user_id ON mouvements_stock(user_id);
CREATE INDEX idx_mouvements_stock_stock_id ON mouvements_stock(stock_id);
CREATE INDEX idx_mouvements_stock_chantier_id ON mouvements_stock(chantier_id);
CREATE INDEX idx_mouvements_stock_date ON mouvements_stock(date_mouvement);


-- ============================================================================
-- TABLE: prospects (CRM Prospects / Sales Pipeline)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.prospects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  nom VARCHAR(255) NOT NULL,
  contact_nom VARCHAR(255),
  email VARCHAR(255),
  telephone VARCHAR(20),
  adresse TEXT,
  source VARCHAR(50) CHECK (source IN ('site_web', 'bouche_a_oreille', 'recommandation', 'pub', 'salon', 'autre')),
  type_projet TEXT,
  budget_estime DECIMAL(12, 2),
  statut VARCHAR(50) NOT NULL DEFAULT 'nouveau' CHECK (statut IN ('nouveau', 'contacte', 'devis_envoye', 'relance', 'gagne', 'perdu')),
  date_premier_contact DATE,
  date_relance DATE,
  notes TEXT,
  chantier_id UUID REFERENCES public.chantiers(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE prospects IS 'CRM prospects and sales pipeline management';
COMMENT ON COLUMN prospects.source IS 'Lead source: site_web (website), bouche_a_oreille (word of mouth), recommandation (referral), pub (advertising), salon (trade show), autre (other)';
COMMENT ON COLUMN prospects.statut IS 'Prospect status in sales pipeline: nouveau (new), contacte (contacted), devis_envoye (quote sent), relance (follow-up), gagne (won), perdu (lost)';
COMMENT ON COLUMN prospects.chantier_id IS 'Link to chantier when prospect converts to a project';

ALTER TABLE prospects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own prospects" ON prospects
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_prospects_user_id ON prospects(user_id);
CREATE INDEX idx_prospects_statut ON prospects(statut);
CREATE INDEX idx_prospects_date_premier_contact ON prospects(date_premier_contact);
CREATE INDEX idx_prospects_chantier_id ON prospects(chantier_id);


-- ============================================================================
-- TABLE: situations (Progress Billing / Factures de Situation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.situations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  chantier_id UUID NOT NULL REFERENCES public.chantiers(id) ON DELETE CASCADE,
  facture_id UUID REFERENCES public.factures(id) ON DELETE SET NULL,
  numero_situation INT NOT NULL,
  date_situation DATE NOT NULL,
  lots JSONB NOT NULL DEFAULT '[]',
  montant_ht_mois DECIMAL(12, 2) NOT NULL DEFAULT 0,
  retenue_garantie_pct DECIMAL(5, 2) DEFAULT 5,
  retenue_garantie_montant DECIMAL(12, 2) DEFAULT 0,
  montant_net_ht DECIMAL(12, 2) NOT NULL DEFAULT 0,
  tva_pct DECIMAL(5, 2) DEFAULT 20,
  montant_ttc DECIMAL(12, 2) NOT NULL DEFAULT 0,
  statut VARCHAR(50) NOT NULL DEFAULT 'brouillon' CHECK (statut IN ('brouillon', 'envoyee', 'validee', 'payee')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE situations IS 'Progress billing statements (factures de situation) tracking monthly project advancement and invoicing';
COMMENT ON COLUMN situations.numero_situation IS 'Sequential progress billing statement number';
COMMENT ON COLUMN situations.lots IS 'JSON array of work packages: [{nom, montant_marche, avancement_precedent_pct, avancement_cumule_pct, montant_cumule, montant_mois}]';
COMMENT ON COLUMN situations.retenue_garantie_montant IS 'Calculated warranty retention amount (montant_ht_mois * retenue_garantie_pct / 100)';
COMMENT ON COLUMN situations.statut IS 'Status: brouillon (draft), envoyee (sent), validee (validated), payee (paid)';

ALTER TABLE situations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own progress billings" ON situations
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_situations_user_id ON situations(user_id);
CREATE INDEX idx_situations_chantier_id ON situations(chantier_id);
CREATE INDEX idx_situations_facture_id ON situations(facture_id);
CREATE INDEX idx_situations_statut ON situations(statut);
CREATE INDEX idx_situations_date_situation ON situations(date_situation);


-- ============================================================================
-- TABLE: budgets_chantier (Project Budgets)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.budgets_chantier (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
  chantier_id UUID NOT NULL UNIQUE REFERENCES public.chantiers(id) ON DELETE CASCADE,
  budget_global DECIMAL(12, 2) NOT NULL DEFAULT 0,
  lignes_budget JSONB DEFAULT '[]',
  marge_prevue_pct DECIMAL(5, 2),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE budgets_chantier IS 'Project-level budget planning and tracking with margin analysis';
COMMENT ON COLUMN budgets_chantier.budget_global IS 'Total project budget';
COMMENT ON COLUMN budgets_chantier.lignes_budget IS 'JSON array of budget lines: [{lot, prevu_ht, engage_ht, facture_ht}]';
COMMENT ON COLUMN budgets_chantier.marge_prevue_pct IS 'Expected profit margin percentage';

ALTER TABLE budgets_chantier ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own project budgets" ON budgets_chantier
  FOR ALL USING (user_id = auth.uid());

CREATE INDEX idx_budgets_chantier_user_id ON budgets_chantier(user_id);
CREATE INDEX idx_budgets_chantier_chantier_id ON budgets_chantier(chantier_id);


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Summary: 11 new tables created for comprehensive BTP ERP functionality
-- All tables include RLS policies for multi-tenant data isolation
-- JSONB columns used for flexible nested data (order lines, budget lines, lot details)
-- Foreign key constraints enforce referential integrity
-- Indexes optimized for common query patterns
