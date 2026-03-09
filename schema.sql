-- ═══════════════════════════════════════════════════════════════════════════════
-- ConducteurPro — Schéma de base de données Supabase (PostgreSQL)
-- À exécuter dans le SQL Editor de Supabase Dashboard
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. USER PROFILES
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    company_name VARCHAR(255),
    siret VARCHAR(14),
    phone VARCHAR(20),
    address TEXT,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    max_concurrent_users INT DEFAULT 1,
    storage_limit_gb INT DEFAULT 1,
    subscription_active BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMPTZ,
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CHANTIERS
CREATE TABLE IF NOT EXISTS public.chantiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    client_nom VARCHAR(255),
    client_email VARCHAR(255),
    client_tel VARCHAR(20),
    adresse VARCHAR(500),
    code_postal VARCHAR(10),
    ville VARCHAR(255),
    localisation VARCHAR(255),
    statut VARCHAR(50) DEFAULT 'Planifié',
    budget_ht DECIMAL(12, 2) DEFAULT 0,
    facture_ht DECIMAL(12, 2) DEFAULT 0,
    encaisse_ht DECIMAL(12, 2) DEFAULT 0,
    date_debut DATE,
    date_fin DATE,
    avancement_pct INT DEFAULT 0,
    metier VARCHAR(255),
    lot VARCHAR(255),
    responsable VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. DOCUMENTS
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    famille VARCHAR(50),
    statut VARCHAR(50) DEFAULT 'Brouillon',
    storage_path VARCHAR(500),
    file_size_bytes BIGINT DEFAULT 0,
    file_hash VARCHAR(64),
    is_encrypted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. FACTURES
CREATE TABLE IF NOT EXISTS public.factures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    numero VARCHAR(50) NOT NULL,
    client_nom VARCHAR(255),
    type_facture VARCHAR(50) DEFAULT 'Situation',
    objet TEXT,
    date_facture DATE,
    date_echeance DATE,
    montant_ht DECIMAL(12, 2) DEFAULT 0,
    tva_pct DECIMAL(5, 2) DEFAULT 20.0,
    tva_montant DECIMAL(12, 2) DEFAULT 0,
    montant_ttc DECIMAL(12, 2) DEFAULT 0,
    statut VARCHAR(50) DEFAULT 'Brouillon',
    document_id UUID REFERENCES public.documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. DEVIS
CREATE TABLE IF NOT EXISTS public.devis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    numero VARCHAR(50) NOT NULL,
    client_nom VARCHAR(255),
    date_devis DATE,
    objet TEXT,
    montant_ht DECIMAL(12, 2) DEFAULT 0,
    tva_pct DECIMAL(5, 2) DEFAULT 20.0,
    montant_ttc DECIMAL(12, 2) DEFAULT 0,
    statut VARCHAR(50) DEFAULT 'Brouillon',
    lignes JSONB DEFAULT '[]',
    document_id UUID REFERENCES public.documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. PLANNINGS
CREATE TABLE IF NOT EXISTS public.plannings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    nom VARCHAR(255),
    description TEXT,
    phases JSONB DEFAULT '[]',
    tasks JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. ÉTAPES
CREATE TABLE IF NOT EXISTS public.etapes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    nom VARCHAR(255) NOT NULL,
    responsable VARCHAR(255),
    date_echeance DATE,
    statut VARCHAR(50) DEFAULT 'À faire',
    priorite VARCHAR(50) DEFAULT 'Normale',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. ÉTUDES
CREATE TABLE IF NOT EXISTS public.etudes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    titre VARCHAR(255),
    type_etude VARCHAR(100),
    synthese TEXT,
    document_id UUID REFERENCES public.documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. MÉTRÉS
CREATE TABLE IF NOT EXISTS public.metres (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    titre VARCHAR(255),
    ouvrages JSONB DEFAULT '[]',
    synthese TEXT,
    document_id UUID REFERENCES public.documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. DCE ANALYSES
CREATE TABLE IF NOT EXISTS public.dces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    chantier_id UUID REFERENCES public.chantiers(id) ON DELETE CASCADE,
    titre VARCHAR(255),
    synthese TEXT,
    document_id UUID REFERENCES public.documents(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. ACTIVITY LOG
CREATE TABLE IF NOT EXISTS public.activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEX pour performance
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_chantiers_user ON public.chantiers(user_id);
CREATE INDEX IF NOT EXISTS idx_chantiers_statut ON public.chantiers(user_id, statut);
CREATE INDEX IF NOT EXISTS idx_documents_user ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_chantier ON public.documents(chantier_id);
CREATE INDEX IF NOT EXISTS idx_documents_famille ON public.documents(user_id, famille);
CREATE INDEX IF NOT EXISTS idx_factures_user ON public.factures(user_id);
CREATE INDEX IF NOT EXISTS idx_factures_chantier ON public.factures(chantier_id);
CREATE INDEX IF NOT EXISTS idx_devis_user ON public.devis(user_id);
CREATE INDEX IF NOT EXISTS idx_etapes_user ON public.etapes(user_id);
CREATE INDEX IF NOT EXISTS idx_etapes_chantier ON public.etapes(chantier_id);
CREATE INDEX IF NOT EXISTS idx_activity_user ON public.activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_created ON public.activity_log(created_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY — Chaque utilisateur ne voit QUE ses données
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chantiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.factures ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plannings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.etapes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.etudes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metres ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_log ENABLE ROW LEVEL SECURITY;

-- Policies pour user_profiles
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policies pour chantiers
CREATE POLICY "Users own chantiers" ON public.chantiers
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour documents
CREATE POLICY "Users own documents" ON public.documents
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour factures
CREATE POLICY "Users own factures" ON public.factures
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour devis
CREATE POLICY "Users own devis" ON public.devis
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour plannings
CREATE POLICY "Users own plannings" ON public.plannings
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour etapes
CREATE POLICY "Users own etapes" ON public.etapes
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour etudes
CREATE POLICY "Users own etudes" ON public.etudes
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour metres
CREATE POLICY "Users own metres" ON public.metres
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour dces
CREATE POLICY "Users own dces" ON public.dces
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies pour activity_log
CREATE POLICY "Users own activity_log" ON public.activity_log
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STORAGE — Bucket privé pour les fichiers
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note: Créer le bucket via le Dashboard Supabase > Storage > New Bucket
-- Nom: conducteurpro-files
-- Type: Private
-- Puis ajouter ces policies dans Storage > Policies :

-- Policy: Authenticated users can upload to their folder
-- CREATE POLICY "Users upload own files" ON storage.objects
--     FOR INSERT WITH CHECK (
--         bucket_id = 'conducteurpro-files'
--         AND auth.uid()::text = (storage.foldername(name))[1]
--     );

-- Policy: Authenticated users can read their files
-- CREATE POLICY "Users read own files" ON storage.objects
--     FOR SELECT USING (
--         bucket_id = 'conducteurpro-files'
--         AND auth.uid()::text = (storage.foldername(name))[1]
--     );

-- Policy: Authenticated users can delete their files
-- CREATE POLICY "Users delete own files" ON storage.objects
--     FOR DELETE USING (
--         bucket_id = 'conducteurpro-files'
--         AND auth.uid()::text = (storage.foldername(name))[1]
--     );
