"""
OPCOPILOT v4.0 - Application Streamlit Complète
Gestion d'opérations immobilières pour ACO SPIC Guadeloupe
Utilise les données JSON des référentiels métier
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime, timedelta
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Configuration page
st.set_page_config(
    page_title="OPCOPILOT v4.0 - SPIC Guadeloupe",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour interface moderne
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0066cc, #004499);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .operation-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .timeline-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .module-tab {
        background: #e3f2fd;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem;
        border-left: 4px solid #0066cc;
    }
    .alert-critical { 
        background: #ffebee; 
        border-left: 4px solid #f44336; 
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .alert-warning { 
        background: #fff3e0; 
        border-left: 4px solid #ff9800; 
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .alert-info { 
        background: #e3f2fd; 
        border-left: 4px solid #2196f3; 
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. CONFIGURATION & CHARGEMENT DONNÉES
# ==============================================================================

@st.cache_data
def load_demo_data():
    """Charge demo_data.json avec gestion d'erreur"""
    try:
        with open('data/demo_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Fichier data/demo_data.json non trouvé")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Erreur format JSON dans demo_data.json")
        return {}

@st.cache_data
def load_templates_phases():
    """Charge templates_phases.json avec gestion d'erreur"""
    try:
        with open('data/templates_phases.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Fichier data/templates_phases.json non trouvé")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Erreur format JSON dans templates_phases.json")
        return {}

def get_couleur_statut(statut):
    """Retourne la couleur selon le statut de phase"""
    couleurs = {
        "VALIDEE": "#4CAF50",         # Vert
        "EN_COURS": "#2196F3",        # Bleu
        "EN_ATTENTE": "#FFC107",      # Jaune
        "RETARD": "#F44336",          # Rouge
        "CRITIQUE": "#E91E63",        # Rose
        "NON_DEMARREE": "#9E9E9E",    # Gris
        "VALIDATION_REQUISE": "#FF9800",  # Orange
        "EN_REVISION": "#673AB7"      # Violet
    }
    return couleurs.get(statut, "#0066cc")

# ==============================================================================
# 2. TIMELINE HORIZONTALE OBLIGATOIRE
# ==============================================================================

def create_timeline_horizontal(operation_data, phases_data):
    """
    Timeline Plotly Gantt HORIZONTALE style infographie
    - Barres horizontales colorées par statut
    - Jalons critiques visibles
    - Interactif : zoom, hover, clic
    - Freins intégrés visuellement
    """
    
    if not phases_data:
        st.warning("Aucune phase définie pour cette opération")
        return None
    
    # Préparation des données pour timeline horizontale
    fig = go.Figure()
    
    # Ajout des barres horizontales pour chaque phase
    for i, phase in enumerate(phases_data):
        debut = pd.to_datetime(phase.get('date_debut_prevue', datetime.now()))
        fin = pd.to_datetime(phase.get('date_fin_prevue', datetime.now() + timedelta(days=30)))
        
        # Couleur selon statut
        couleur = get_couleur_statut(phase.get('statut', 'NON_DEMARREE'))
        
        # Barre principale de la phase
        fig.add_trace(go.Scatter(
            x=[debut, fin, fin, debut, debut],
            y=[i-0.4, i-0.4, i+0.4, i+0.4, i-0.4],
            fill="toself",
            fillcolor=couleur,
            line=dict(color=couleur, width=2),
            mode="lines",
            name=phase['nom'],
            text=f"<b>{phase['nom']}</b><br>" +
                 f"Statut: {phase.get('statut', 'NON_DEMARREE')}<br>" +
                 f"Début: {debut.strftime('%d/%m/%Y')}<br>" +
                 f"Fin: {fin.strftime('%d/%m/%Y')}<br>" +
                 f"Responsable: {phase.get('responsable', 'Non assigné')}",
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        
        # Jalon de début (cercle)
        fig.add_trace(go.Scatter(
            x=[debut],
            y=[i],
            mode='markers',
            marker=dict(
                size=12,
                color=couleur,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            name=f"Début {phase['nom']}",
            showlegend=False,
            hovertemplate=f"<b>Début:</b> {debut.strftime('%d/%m/%Y')}<extra></extra>"
        ))
        
        # Jalon de fin (carré si critique, cercle sinon)
        symbol = 'square' if phase.get('est_critique', False) else 'circle'
        fig.add_trace(go.Scatter(
            x=[fin],
            y=[i],
            mode='markers',
            marker=dict(
                size=14 if phase.get('est_critique', False) else 10,
                color=couleur,
                symbol=symbol,
                line=dict(width=2, color='white')
            ),
            name=f"Fin {phase['nom']}",
            showlegend=False,
            hovertemplate=f"<b>Fin:</b> {fin.strftime('%d/%m/%Y')}<extra></extra>"
        ))
        
        # Indicateur frein si présent
        if phase.get('statut') == 'RETARD':
            fig.add_trace(go.Scatter(
                x=[fin + timedelta(days=1)],
                y=[i],
                mode='markers+text',
                marker=dict(size=16, color='red', symbol='x'),
                text=['⚠️'],
                textposition='middle right',
                name=f"Frein {phase['nom']}",
                showlegend=False,
                hovertemplate="<b>FREIN DÉTECTÉ</b><extra></extra>"
            ))
    
    # Configuration du layout pour timeline horizontale
    fig.update_layout(
        title={
            'text': f"📅 Timeline Horizontale - {operation_data.get('nom', 'Opération')}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#0066cc', 'family': 'Arial Black'}
        },
        xaxis=dict(
            title="📆 Chronologie",
            type='date',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            tickformat='%d/%m/%Y'
        ),
        yaxis=dict(
            title="🔄 Phases",
            tickmode='array',
            tickvals=list(range(len(phases_data))),
            ticktext=[f"{i+1}. {phase['nom'][:25]}{'...' if len(phase['nom']) > 25 else ''}" 
                     for i, phase in enumerate(phases_data)],
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            autorange='reversed'  # Pour que la première phase soit en haut
        ),
        height=max(500, len(phases_data) * 50),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=250, r=100, t=100, b=80),
        hovermode='closest',
        # Interactivité
        dragmode='zoom'
    )
    
    # Configuration des outils interactifs
    config = {
        'displayModeBar': True,
        'modeBarButtonsToAdd': ['pan2d', 'zoomin2d', 'zoomout2d', 'resetScale2d'],
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    }
    
    return fig, config

# ==============================================================================
# 3. MODULES INTÉGRÉS PAR OPÉRATION
# ==============================================================================

def module_rem(operation_id):
    """Module REM intégré dans l'opération"""
    st.markdown("### 💰 Module REM - Suivi Trimestriel")
    
    # Chargement données REM
    demo_data = load_demo_data()
    rem_data = demo_data.get('rem_demo', {}).get(f'operation_{operation_id}', [])
    
    if not rem_data:
        st.warning("Aucune donnée REM disponible pour cette opération")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Suivi REM")
        
        # Tableau REM
        df_rem = pd.DataFrame(rem_data)
        df_rem_display = df_rem[['trimestre', 'rem_projetee', 'rem_realisee', 'ecart_rem', 'avancement_rem']].copy()
        df_rem_display.columns = ['Trimestre', 'REM Projetée (€)', 'REM Réalisée (€)', 'Écart (€)', '% Avancement']
        
        st.dataframe(df_rem_display, use_container_width=True)
        
        # Graphique REM
        fig_rem = go.Figure()
        fig_rem.add_trace(go.Bar(
            x=df_rem['trimestre'],
            y=df_rem['rem_projetee'],
            name='REM Projetée',
            marker_color='#0066cc'
        ))
        fig_rem.add_trace(go.Bar(
            x=df_rem['trimestre'],
            y=df_rem['rem_realisee'],
            name='REM Réalisée',
            marker_color='#ff6b35'
        ))
        fig_rem.update_layout(
            title="Évolution REM par Trimestre",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_rem, use_container_width=True)
    
    with col2:
        st.markdown("#### 🏗️ Suivi Dépenses Travaux")
        
        # Tableau Travaux
        df_travaux_display = df_rem[['trimestre', 'depenses_projetees', 'depenses_facturees', 'ecart_depenses', 'avancement_travaux']].copy()
        df_travaux_display.columns = ['Trimestre', 'Dépenses Projetées (€)', 'Dépenses Facturées (€)', 'Écart (€)', '% Avancement']
        
        st.dataframe(df_travaux_display, use_container_width=True)
        
        # Graphique Travaux
        fig_travaux = go.Figure()
        fig_travaux.add_trace(go.Bar(
            x=df_rem['trimestre'],
            y=df_rem['depenses_projetees'],
            name='Dépenses Projetées',
            marker_color='#4CAF50'
        ))
        fig_travaux.add_trace(go.Bar(
            x=df_rem['trimestre'],
            y=df_rem['depenses_facturees'],
            name='Dépenses Facturées',
            marker_color='#FFC107'
        ))
        fig_travaux.update_layout(
            title="Évolution Dépenses par Trimestre",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_travaux, use_container_width=True)
    
    # Alertes et analyses
    st.markdown("#### 🚨 Alertes et Analyses")
    
    col_alert1, col_alert2, col_alert3 = st.columns(3)
    
    # Calcul des alertes
    ecarts_rem = [abs(x['ecart_rem']) for x in rem_data if x['ecart_rem'] != 0]
    ecart_moyen = sum(ecarts_rem) / len(ecarts_rem) if ecarts_rem else 0
    
    with col_alert1:
        if ecart_moyen < 2000:
            st.markdown("""
            <div class="alert-info">
            ✅ <strong>Corrélation REM/Travaux</strong><br>
            Cohérence globale respectée<br>
            Écart moyen: {:.0f}€
            </div>
            """.format(ecart_moyen), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-warning">
            ⚠️ <strong>Écart détecté</strong><br>
            Surveillance requise<br>
            Écart moyen: {:.0f}€
            </div>
            """.format(ecart_moyen), unsafe_allow_html=True)
    
    with col_alert2:
        derniere_donnee = rem_data[-2] if len(rem_data) > 1 else rem_data[0]
        if derniere_donnee['avancement_rem'] < 95:
            st.markdown("""
            <div class="alert-warning">
            ⚠️ <strong>Retard REM</strong><br>
            {}% réalisé seulement
            </div>
            """.format(derniere_donnee['avancement_rem']), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-info">
            ✅ <strong>REM dans les temps</strong><br>
            {}% réalisé
            </div>
            """.format(derniere_donnee['avancement_rem']), unsafe_allow_html=True)
    
    with col_alert3:
        st.markdown("""
        <div class="alert-info">
        📈 <strong>Prévision T4</strong><br>
        Objectif: 95% avancement<br>
        Action: Validation finale
        </div>
        """, unsafe_allow_html=True)

def module_avenants(operation_id):
    """Module Avenants intégré dans l'opération"""
    st.markdown("### 📝 Module Avenants")
    
    # Chargement données avenants
    demo_data = load_demo_data()
    avenants_data = demo_data.get('avenants_demo', {}).get(f'operation_{operation_id}', [])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Liste des Avenants")
        
        if avenants_data:
            df_avenants = pd.DataFrame(avenants_data)
            df_avenants_display = df_avenants[['numero', 'date', 'motif', 'impact_budget', 'impact_delai', 'statut']].copy()
            df_avenants_display.columns = ['N°', 'Date', 'Motif', 'Impact Budget (€)', 'Impact Délai (j)', 'Statut']
            
            st.dataframe(df_avenants_display, use_container_width=True)
            
            # Synthèse impacts
            impact_budget_total = sum([x['impact_budget'] for x in avenants_data])
            impact_delai_total = sum([x['impact_delai'] for x in avenants_data])
            
            col_synth1, col_synth2, col_synth3 = st.columns(3)
            
            with col_synth1:
                delta_budget = f"+{impact_budget_total:,}€" if impact_budget_total > 0 else f"{impact_budget_total:,}€"
                st.metric("Impact Budget Total", delta_budget, delta=f"{impact_budget_total/25000*100:.1f}%")
            
            with col_synth2:
                delta_delai = f"+{impact_delai_total} jours" if impact_delai_total > 0 else f"{impact_delai_total} jours"
                st.metric("Impact Délai Total", delta_delai, delta=f"{impact_delai_total/550*100:.1f}%")
            
            with col_synth3:
                st.metric("Nombre Avenants", len(avenants_data), delta="+1")
        else:
            st.info("Aucun avenant pour cette opération")
    
    with col2:
        st.markdown("#### Nouvel Avenant")
        
        with st.form("nouvel_avenant"):
            motif = st.selectbox("Motif", [
                "Modification programme",
                "Délai supplémentaire", 
                "Plus-value travaux",
                "Moins-value travaux",
                "Changement MOE",
                "Adaptation réglementaire",
                "Autre"
            ])
            
            impact_budget = st.number_input("Impact Budget (€)", value=0, step=1000)
            impact_delai = st.number_input("Impact Délai (jours)", value=0)
            description = st.text_area("Description détaillée", placeholder="Détaillez les modifications...")
            
            submitted = st.form_submit_button("📝 Créer Avenant")
            if submitted:
                st.success("✅ Avenant créé en brouillon")
                st.info("📧 Notification envoyée pour validation hiérarchique")

def module_med(operation_id):
    """Module MED Automatisé intégré dans l'opération"""
    st.markdown("### ⚖️ Module MED Automatisé")
    
    # Chargement données MED
    demo_data = load_demo_data()
    med_data = demo_data.get('med_demo', {}).get(f'operation_{operation_id}', [])
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Générer MED")
        
        with st.form("generation_med"):
            type_med = st.selectbox("Type MED", [
                "MED_MOE (Maîtrise d'Œuvre)",
                "MED_SPS (Sécurité Protection Santé)",
                "MED_OPC (Ordonnancement Pilotage)",
                "MED_ENTREPRISE (par lot)",
                "MED_CT (Contrôleur Technique)"
            ])
            
            destinataire = st.text_input("Destinataire", placeholder="Nom de l'entreprise/bureau d'études")
            
            motifs = st.multiselect("Motifs", [
                "Retard dans les études",
                "Non-respect du planning",
                "Défaut de coordination",
                "Non-conformité technique",
                "Absence sur chantier",
                "Documents manquants",
                "Malfaçons constatées",
                "Non-respect des règles de sécurité"
            ])
            
            delai_conformite = st.number_input("Délai mise en conformité (jours)", min_value=1, value=15, max_value=60)
            
            details = st.text_area("Détails spécifiques", placeholder="Précisez les éléments de non-conformité...")
            
            submitted = st.form_submit_button("📄 Générer MED Automatique")
            if submitted and motifs and destinataire:
                st.success("✅ MED généré automatiquement")
                st.info("📧 Document Word créé et envoyé par email")
                st.info("📅 Relances programmées automatiquement")
    
    with col2:
        st.markdown("#### Suivi MED Actives")
        
        if med_data:
            df_med = pd.DataFrame(med_data)
            df_med_display = df_med[['reference', 'destinataire', 'date_envoi', 'delai_conformite', 'statut']].copy()
            df_med_display.columns = ['Référence', 'Destinataire', 'Date Envoi', 'Délai (j)', 'Statut']
            
            st.dataframe(df_med_display, use_container_width=True)
            
            # Actions rapides
            st.markdown("#### Actions Rapides")
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if st.button("🔄 Relancer MED en attente"):
                    st.success("📧 Relance automatique envoyée")
            
            with col_action2:
                if st.button("📊 Rapport MED mensuel"):
                    st.info("📋 Génération rapport en cours...")
        else:
            st.info("Aucune MED active pour cette opération")
            
            # Suggestions
            st.markdown("#### 💡 Suggestions")
            st.markdown("""
            - Vérifiez les retards de planning
            - Contrôlez la qualité des livrables
            - Surveillez le respect des délais
            """)

def module_concessionnaires(operation_id):
    """Module Concessionnaires intégré dans l'opération"""
    st.markdown("### 🔌 Module Concessionnaires")
    
    # Chargement données concessionnaires
    demo_data = load_demo_data()
    concess_data = demo_data.get('concessionnaires_demo', {}).get(f'operation_{operation_id}', {})
    
    if not concess_data:
        st.warning("Aucune donnée concessionnaire pour cette opération")
        return
    
    # Onglets par concessionnaire
    tab_edf, tab_eau, tab_fibre = st.tabs(["⚡ EDF", "💧 EAU", "🌐 FIBRE"])
    
    with tab_edf:
        st.markdown("#### Processus EDF - Raccordement Électrique")
        
        edf_data = concess_data.get('EDF', {})
        edf_etapes = edf_data.get('etapes', [])
        
        for etape in edf_etapes:
            col_etape, col_statut, col_date = st.columns([3, 1, 1])
            
            with col_etape:
                st.write(f"🔸 {etape['nom']}")
            
            with col_statut:
                if etape['statut'] == 'VALIDEE':
                    st.success("✅ Validé")
                elif etape['statut'] == 'EN_COURS':
                    st.info("🔄 En cours")
                elif etape['statut'] == 'PLANIFIE':
                    st.warning("📅 Planifié")
                else:
                    st.info("⏳ En attente")
            
            with col_date:
                st.write(etape.get('date', 'À programmer'))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📞 Relancer EDF", key="relance_edf"):
                st.success("📧 Relance EDF programmée")
        with col_btn2:
            if st.button("📋 Rapport EDF", key="rapport_edf"):
                st.info("📊 Génération rapport EDF...")
    
    with tab_eau:
        st.markdown("#### Processus EAU - Branchement")
        
        eau_data = concess_data.get('EAU', {})
        eau_etapes = eau_data.get('etapes', [])
        
        for etape in eau_etapes:
            col_etape, col_statut, col_date = st.columns([3, 1, 1])
            
            with col_etape:
                st.write(f"🔸 {etape['nom']}")
            
            with col_statut:
                if etape['statut'] == 'VALIDEE':
                    st.success("✅ Validé")
                elif etape['statut'] == 'EN_COURS':
                    st.info("🔄 En cours")
                elif etape['statut'] == 'PLANIFIE':
                    st.warning("📅 Planifié")
                else:
                    st.info("⏳ En attente")
            
            with col_date:
                st.write(etape.get('date', 'À programmer'))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📞 Relancer Compagnie Eau", key="relance_eau"):
                st.success("📧 Relance programmée")
        with col_btn2:
            if st.button("📋 Rapport Eau", key="rapport_eau"):
                st.info("📊 Génération rapport...")
    
    with tab_fibre:
        st.markdown("#### Processus FIBRE - Installation")
        
        fibre_data = concess_data.get('FIBRE', {})
        fibre_etapes = fibre_data.get('etapes', [])
        
        for etape in fibre_etapes:
            col_etape, col_statut, col_date = st.columns([3, 1, 1])
            
            with col_etape:
                st.write(f"🔸 {etape['nom']}")
            
            with col_statut:
                if etape['statut'] == 'VALIDEE':
                    st.success("✅ Validé")
                elif etape['statut'] == 'EN_COURS':
                    st.info("🔄 En cours")
                elif etape['statut'] == 'PLANIFIE':
                    st.warning("📅 Planifié")
                else:
                    st.info("⏳ En attente")
            
            with col_date:
                st.write(etape.get('date', 'À programmer'))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📞 Relancer Opérateur", key="relance_fibre"):
                st.success("📧 Relance programmée")
        with col_btn2:
            if st.button("📋 Rapport Fibre", key="rapport_fibre"):
                st.info("📊 Génération rapport...")

def module_dgd(operation_id):
    """Module DGD intégré dans l'opération"""
    st.markdown("### 📊 Module DGD - Décompte Général Définitif")
    
    # Chargement données DGD
    demo_data = load_demo_data()
    dgd_data = demo_data.get('dgd_demo', {}).get(f'operation_{operation_id}', {})
    
    if not dgd_data:
        st.info("Module DGD non applicable pour cette opération (phase travaux non atteinte)")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Décompte par Lot")
        
        lots_data = dgd_data.get('lots', [])
        if lots_data:
            df_dgd = pd.DataFrame(lots_data)
            df_dgd_display = df_dgd[['nom', 'marche_initial', 'quantites_reelles', 'plus_moins_value', 'penalites', 'montant_final']].copy()
            df_dgd_display.columns = ['Lot', 'Marché Initial (€)', 'Qtés Réelles (%)', 'Plus/Moins-Value (€)', 'Pénalités (€)', 'Montant Final (€)']
            
            st.dataframe(df_dgd_display, use_container_width=True)
    
    with col2:
        st.markdown("#### Workflow Validation")
        
        workflow_steps = [
            {"nom": "Saisie quantités", "responsable": "ACO", "statut": "✅"},
            {"nom": "Validation entreprise", "responsable": "Entreprise", "statut": "✅"},
            {"nom": "Vérification MOE", "responsable": "MOE", "statut": "🔄"},
            {"nom": "Validation SPIC", "responsable": "SPIC", "statut": "⏳"},
            {"nom": "Génération décompte", "responsable": "Système", "statut": "⏳"}
        ]
        
        for step in workflow_steps:
            st.write(f"{step['statut']} **{step['nom']}** - {step['responsable']}")
    
    # Synthèse financière
    st.markdown("#### 💰 Synthèse Financière")
    
    synthese = dgd_data.get('synthese', {})
    if synthese:
        col_synth1, col_synth2, col_synth3, col_synth4 = st.columns(4)
        
        with col_synth1:
            st.metric("Montant Initial", f"{synthese['montant_initial']:,} €")
        
        with col_synth2:
            delta_pv = synthese['plus_moins_values']
            st.metric("Plus/Moins-Values", f"{delta_pv:,} €", delta=f"{delta_pv/synthese['montant_initial']*100:.1f}%")
        
        with col_synth3:
            st.metric("Pénalités", f"{synthese['penalites']:,} €")
        
        with col_synth4:
            montant_final = synthese['montant_final']
            ecart_pct = synthese['ecart_pourcentage']
            st.metric("Montant Final", f"{montant_final:,} €", delta=f"{ecart_pct:.1f}%")

def module_gpa(operation_id):
    """Module GPA intégré dans l'opération"""
    st.markdown("### 🛡️ Module GPA - Garantie Parfait Achèvement")
    
    # Chargement données GPA
    demo_data = load_demo_data()
    gpa_data = demo_data.get('gpa_demo', {}).get(f'operation_{operation_id}', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Réclamations Locataires")
        
        if gpa_data:
            df_gpa = pd.DataFrame(gpa_data)
            df_gpa_display = df_gpa[['date', 'logement', 'type', 'description', 'statut', 'delai_intervention']].copy()
            df_gpa_display.columns = ['Date', 'Logement', 'Type', 'Description', 'Statut', 'Délai (j)']
            
            st.dataframe(df_gpa_display, use_container_width=True)
        else:
            st.info("Aucune réclamation GPA pour cette opération")
    
    with col2:
        st.markdown("#### Statistiques")
        
        if gpa_data:
            # Répartition par type
            types_count = {}
            for reclamation in gpa_data:
                type_pb = reclamation['type']
                types_count[type_pb] = types_count.get(type_pb, 0) + 1
            
            if types_count:
                fig_gpa = px.pie(
                    values=list(types_count.values()), 
                    names=list(types_count.keys()),
                    title="Répartition Réclamations par Type"
                )
                st.plotly_chart(fig_gpa, use_container_width=True)
        else:
            st.success("🎉 Aucune réclamation GPA - Excellente qualité!")
    
    # Nouvelle réclamation
    st.markdown("#### 📝 Nouvelle Réclamation GPA")
    
    with st.form("nouvelle_reclamation_gpa"):
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        
        with col_rec1:
            logement = st.text_input("N° Logement", placeholder="Ex: A101")
            type_pb = st.selectbox("Type Problème", [
                "Plomberie", 
                "Électricité", 
                "Peinture", 
                "Menuiserie",
                "Carrelage",
                "Ventilation",
                "Autre"
            ])
        
        with col_rec2:
            locataire = st.text_input("Locataire", placeholder="Nom du locataire")
            urgence = st.selectbox("Niveau Urgence", [
                "Normale", 
                "Prioritaire", 
                "Urgente"
            ])
        
        with col_rec3:
            description = st.text_area("Description Problème", placeholder="Décrivez le problème...")
        
        submitted = st.form_submit_button("📨 Enregistrer Réclamation")
        if submitted and logement and locataire and description:
            st.success("✅ Réclamation enregistrée")
            st.info("📧 Transmission automatique à l'ACO")
            st.info("🔄 Entreprise notifiée selon le type de problème")

def module_cloture(operation_id):
    """Module Clôture intégré dans l'opération"""
    st.markdown("### ✅ Module Clôture - Finalisation Opération")
    
    # Checklist de clôture
    st.markdown("#### 📋 Checklist de Clôture")
    
    checklist_items = [
        {"item": "Toutes phases validées", "statut": True, "responsable": "ACO"},
        {"item": "Documents archivés", "statut": True, "responsable": "ACO"},
        {"item": "Soldes financiers validés", "statut": False, "responsable": "Financier"},
        {"item": "Retenue de garantie levée", "statut": False, "responsable": "Financier"},
        {"item": "Bilan opération rédigé", "statut": False, "responsable": "ACO"},
        {"item": "Lessons learned documentées", "statut": False, "responsable": "ACO"}
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        for item in checklist_items[:3]:
            status_icon = "✅" if item["statut"] else "⏳"
            st.write(f"{status_icon} **{item['item']}** - {item['responsable']}")
    
    with col2:
        for item in checklist_items[3:]:
            status_icon = "✅" if item["statut"] else "⏳"
            st.write(f"{status_icon} **{item['item']}** - {item['responsable']}")
    
    # Bilan opération
    st.markdown("#### 📊 Bilan Opération")
    
    col_bilan1, col_bilan2, col_bilan3 = st.columns(3)
    
    with col_bilan1:
        st.markdown("##### 💰 Bilan Financier")
        st.metric("Budget Initial", "2 450 000 €")
        st.metric("Budget Final", "2 398 000 €", delta="-52 000 €")
        st.metric("Écart Budget", "-2.1%", delta_color="inverse")
    
    with col_bilan2:
        st.markdown("##### ⏱️ Bilan Planning")
        st.metric("Durée Prévue", "24 mois")
        st.metric("Durée Réelle", "26 mois", delta="+2 mois")
        st.metric("Écart Planning", "+8.3%", delta_color="inverse")
    
    with col_bilan3:
        st.markdown("##### 🎯 Bilan Qualité")
        st.metric("Phases en Retard", "3")
        st.metric("Avenants Total", "3")
        st.metric("Réclamations GPA", "12")
    
    # Actions finales
    st.markdown("#### 🔚 Actions de Clôture")
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("📋 Générer Bilan Final", key="bilan_final"):
            st.success("📄 Bilan final généré en Word")
    
    with col_action2:
        if st.button("💾 Archiver Définitivement", key="archiver"):
            st.warning("⚠️ Confirmer archivage définitif")
    
    with col_action3:
        # Vérification que tous les items sont validés
        tous_valides = all(item["statut"] for item in checklist_items)
        if tous_valides:
            if st.button("✅ CLÔTURER OPÉRATION", key="cloturer", type="primary"):
                st.success("🎉 Opération clôturée avec succès!")
                st.balloons()
        else:
            st.button("⏳ Clôture en attente", key="cloturer_attente", disabled=True)
            st.info("Complétez tous les éléments de la checklist")

# ==============================================================================
# 4. NAVIGATION ACO-CENTRIQUE
# ==============================================================================

def page_dashboard():
    """Dashboard principal avec KPIs ACO"""
    st.markdown("""
    <div class="main-header">
        <h1>🏗️ OPCOPILOT v4.0 - Dashboard SPIC Guadeloupe</h1>
        <p>Interface de Gestion d'Opérations pour Agent de Conduite d'Opérations (ACO)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chargement données
    demo_data = load_demo_data()
    kpis_data = demo_data.get('kpis_aco_demo', {})
    activite_data = demo_data.get('activite_mensuelle_demo', {})
    alertes_data = demo_data.get('alertes_demo', [])
    
    # KPIs personnels ACO
    st.markdown("### 📊 Mes KPIs ACO - Marie-Claire ADMIN")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h2>{kpis_data.get('operations_actives', 23)}</h2>
            <p>Opérations Actives</p>
            <small>{kpis_data.get('operations_cloturees', 5)} clôturées</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rem_realise = kpis_data.get('rem_realisee_2024', 485000)
        rem_prevu = kpis_data.get('rem_prevue_2024', 620000)
        taux_real = kpis_data.get('taux_realisation_rem', 78)
        st.markdown(f"""
        <div class="kpi-card">
            <h2>{rem_realise/1000:.0f}k€</h2>
            <p>REM Réalisée 2024</p>
            <small>{taux_real}% / {rem_prevu/1000:.0f}k€ prévue</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        freins_actifs = kpis_data.get('freins_actifs', 3)
        freins_critiques = kpis_data.get('freins_critiques', 2)
        st.markdown(f"""
        <div class="kpi-card">
            <h2>{freins_actifs}</h2>
            <p>Freins Actifs</p>
            <small>{freins_critiques} critiques</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        echeances = kpis_data.get('echeances_semaine', 5)
        validations = kpis_data.get('validations_requises', 12)
        st.markdown(f"""
        <div class="kpi-card">
            <h2>{echeances}</h2>
            <p>Échéances Semaine</p>
            <small>{validations} validations requises</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Alertes et actions
    st.markdown("### 🚨 Alertes et Actions Prioritaires")
    
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        st.markdown("#### Alertes Critiques")
        
        for alerte in alertes_data:
            alert_class = f"alert-{alerte['type'].lower()}"
            if alerte['type'] == 'CRITIQUE':
                alert_class = "alert-critical"
            elif alerte['type'] == 'WARNING':
                alert_class = "alert-warning"
            else:
                alert_class = "alert-info"
                
            st.markdown(f"""
            <div class="{alert_class}">
                <strong>{alerte['operation']}</strong><br>
                {alerte['message']}<br>
                <em>Action: {alerte['action_requise']}</em>
            </div>
            """, unsafe_allow_html=True)
    
    with col_alert2:
        st.markdown("#### Actions Réalisées Aujourd'hui")
        
        actions_jour = [
            "✅ DGD validé - RÉSIDENCE SOLEIL",
            "✅ Phase ESQ terminée - COUR CHARNEAU", 
            "✅ MED envoyé - MANDAT ÉCOLE",
            "✅ REM T3 saisi - 3 opérations",
            "✅ Timeline mise à jour - VEFA BELCOURT"
        ]
        
        for action in actions_jour:
            st.write(action)
    
    # Graphique d'activité
    st.markdown("### 📈 Activité Mensuelle")
    
    if activite_data:
        fig_dashboard = go.Figure()
        
        # REM mensuelle
        fig_dashboard.add_trace(go.Scatter(
            x=activite_data['mois'],
            y=activite_data['rem_mensuelle'],
            mode='lines+markers',
            name='REM Mensuelle (€)',
            yaxis='y',
            line=dict(color='#0066cc', width=3),
            marker=dict(size=8)
        ))
        
        # Opérations actives
        fig_dashboard.add_trace(go.Scatter(
            x=activite_data['mois'],
            y=activite_data['operations_actives'],
            mode='lines+markers',
            name='Opérations Actives',
            yaxis='y2',
            line=dict(color='#ff6b35', width=3),
            marker=dict(size=8)
        ))
        
        fig_dashboard.update_layout(
            title="Évolution Activité ACO 2024",
            xaxis=dict(title="Mois"),
            yaxis=dict(title="REM (€)", side="left"),
            yaxis2=dict(title="Nb Opérations", side="right", overlaying="y"),
            height=450,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_dashboard, use_container_width=True)

def page_portefeuille_aco():
    """Portefeuille ACO avec liste des opérations"""
    st.markdown("### 📂 Mon Portefeuille - Marie-Claire ADMIN")
    
    # Chargement données
    demo_data = load_demo_data()
    operations_data = demo_data.get('operations_demo', [])
    
    # Filtres
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        filtre_type = st.selectbox("Type Opération", ["Tous", "OPP", "VEFA", "MANDAT_ETUDES", "MANDAT_REALISATION", "AMO"])
    
    with col_filter2:
        filtre_statut = st.selectbox("Statut", ["Tous", "EN_MONTAGE", "EN_COURS", "EN_RECEPTION", "CLOTUREE"])
    
    with col_filter3:
        filtre_commune = st.selectbox("Commune", ["Toutes", "Les Abymes", "Pointe-à-Pitre", "Basse-Terre", "Sainte-Anne"])
    
    with col_filter4:
        if st.button("➕ Nouvelle Opération", type="primary"):
            st.session_state.page = "creation_operation"
            st.rerun()
    
    # Application des filtres
    operations_filtrees = operations_data
    if filtre_type != "Tous":
        operations_filtrees = [op for op in operations_filtrees if op['type_operation'] == filtre_type]
    if filtre_statut != "Tous":
        operations_filtrees = [op for op in operations_filtrees if op['statut'] == filtre_statut]
    if filtre_commune != "Toutes":
        operations_filtrees = [op for op in operations_filtrees if op['commune'] == filtre_commune]
    
    # Liste des opérations
    st.markdown(f"#### 📋 Mes Opérations ({len(operations_filtrees)} affichées)")
    
    for op in operations_filtrees:
        with st.container():
            st.markdown(f"""
            <div class="operation-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>🏗️ {op['nom']} - {op['type_operation']}</h4>
                        <p><strong>📍 {op['commune']}</strong> • {op.get('nb_logements_total', 0)} logements • {op.get('budget_total', 0):,} €</p>
                        <p><em>Créé le {op['date_creation']} • Fin prévue {op['date_fin_prevue']}</em></p>
                    </div>
                    <div style="text-align: right;">
                        <p><strong>Avancement: {op['avancement']}%</strong></p>
                        <p>Statut: <span style="color: {'green' if op['statut'] == 'EN_COURS' else 'orange'}">{op['statut']}</span></p>
                        {f"<p style='color: red;'>⚠️ {op.get('freins_actifs', 0)} frein(s)</p>" if op.get('freins_actifs', 0) > 0 else ""}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                if st.button(f"📂 Ouvrir", key=f"open_{op['id']}"):
                    st.session_state.selected_operation_id = op['id']
                    st.session_state.selected_operation = op
                    st.session_state.page = "operation_details"
                    st.rerun()
            
            with col_btn2:
                if st.button(f"📊 Timeline", key=f"timeline_{op['id']}"):
                    st.session_state.selected_operation_id = op['id']
                    st.session_state.selected_operation = op
                    st.session_state.page = "operation_details"
                    st.session_state.active_tab = "timeline"
                    st.rerun()

def page_operation_details(operation_id=None):
    """Page détail opération avec timeline et modules intégrés"""
    
    # Récupération de l'opération
    if operation_id is None and 'selected_operation_id' in st.session_state:
        operation_id = st.session_state.selected_operation_id
    
    if 'selected_operation' in st.session_state:
        operation = st.session_state.selected_operation
    else:
        # Fallback avec données de démo
        demo_data = load_demo_data()
        operations_data = demo_data.get('operations_demo', [])
        operation = operations_data[0] if operations_data else {}
        operation_id = operation.get('id', 1)
    
    # En-tête opération
    st.markdown(f"""
    <div class="main-header">
        <h1>🏗️ {operation.get('nom', 'Opération')} - {operation.get('type_operation', 'OPP')}</h1>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p><strong>📍 {operation.get('commune', 'Commune')}</strong> • {operation.get('nb_logements_total', 0)} logements • ACO {operation.get('aco_responsable', 'Marie-Claire ADMIN')}</p>
            </div>
            <div>
                <p><strong>Budget:</strong> {operation.get('budget_total', 0):,} € • <strong>Avancement:</strong> {operation.get('avancement', 0)}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton retour
    if st.button("← Retour au Portefeuille"):
        st.session_state.page = "portefeuille"
        st.rerun()
    
    # Onglets modules intégrés
    tab_timeline, tab_rem, tab_avenants, tab_med, tab_concess, tab_dgd, tab_gpa, tab_cloture = st.tabs([
        "📅 Timeline", "💰 REM", "📝 Avenants", "⚖️ MED", 
        "🔌 Concess.", "📊 DGD", "🛡️ GPA", "✅ Clôture"
    ])
    
    with tab_timeline:
        st.markdown("### 📅 Timeline Horizontale - Gestion des Phases")
        
        # Chargement des phases
        demo_data = load_demo_data()
        phases_data = demo_data.get('phases_demo', {}).get(f'operation_{operation_id}', [])
        
        # Si pas de phases spécifiques, on charge un template selon le type
        if not phases_data:
            templates = load_templates_phases()
            type_op = operation.get('type_operation', 'OPP')
            template_phases = templates.get(type_op, {}).get('phases', [])
            
            # Conversion template en phases avec dates
            phases_data = []
            date_courante = datetime.now()
            
            for i, phase_template in enumerate(template_phases[:8]):  # Limite pour démo
                debut = date_courante + timedelta(days=i*20)
                fin = debut + timedelta(days=phase_template.get('duree_jours', 30))
                
                statuts_demo = ["VALIDEE", "EN_COURS", "EN_ATTENTE", "NON_DEMARREE"]
                statut = statuts_demo[i % len(statuts_demo)]
                
                phases_data.append({
                    "nom": phase_template['nom'],
                    "date_debut_prevue": debut.isoformat(),
                    "date_fin_prevue": fin.isoformat(),
                    "statut": statut,
                    "responsable": phase_template.get('responsable_type', 'ACO'),
                    "est_critique": phase_template.get('est_critique', False)
                })
        
        # Affichage timeline horizontale
        if phases_data:
            timeline_fig, config = create_timeline_horizontal(operation, phases_data)
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True, config=config)
                
                # Gestion des phases
                st.markdown("#### 🔧 Gestion des Phases")
                
                col_phase1, col_phase2, col_phase3, col_phase4 = st.columns(4)
                
                with col_phase1:
                    if st.button("➕ Ajouter Phase"):
                        st.success("✅ Interface d'ajout de phase")
                
                with col_phase2:
                    if st.button("✏️ Modifier Phase"):
                        st.info("🔄 Mode modification activé")
                
                with col_phase3:
                    if st.button("⚠️ Signaler Frein"):
                        st.warning("🚨 Frein signalé sur phase sélectionnée")
                
                with col_phase4:
                    if st.button("📊 Exporter Planning"):
                        st.info("📁 Export Excel en cours...")
        else:
            st.warning("⚠️ Aucune phase définie pour cette opération")
    
    with tab_rem:
        module_rem(operation_id)
    
    with tab_avenants:
        module_avenants(operation_id)
    
    with tab_med:
        module_med(operation_id)
    
    with tab_concess:
        module_concessionnaires(operation_id)
    
    with tab_dgd:
        module_dgd(operation_id)
    
    with tab_gpa:
        module_gpa(operation_id)
    
    with tab_cloture:
        module_cloture(operation_id)

def page_creation_operation():
    """Page de création nouvelle opération"""
    st.markdown("### ➕ Nouvelle Opération")
    
    # Chargement des templates
    templates = load_templates_phases()
    
    with st.form("creation_operation"):
        st.markdown("#### 📝 Informations Générales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nom_operation = st.text_input("Nom Opération *", placeholder="Ex: RÉSIDENCE LES JARDINS")
            type_operation = st.selectbox("Type Opération *", list(templates.keys()))
            commune = st.selectbox("Commune *", [
                "Les Abymes", "Pointe-à-Pitre", "Basse-Terre", 
                "Sainte-Anne", "Le Gosier", "Petit-Bourg",
                "Baie-Mahault", "Lamentin"
            ])
        
        with col2:
            aco_responsable = st.text_input("ACO Responsable", value="Marie-Claire ADMIN")
            adresse = st.text_area("Adresse")
            parcelle = st.text_input("Parcelle Cadastrale")
        
        # Formulaire adaptatif selon le type
        template_info = templates.get(type_operation, {})
        st.markdown(f"#### 🏠 Spécifique {type_operation}")
        st.info(f"📋 {template_info.get('description', '')} - {template_info.get('nb_phases', 0)} phases")
        
        if type_operation == "OPP":
            col_opp1, col_opp2 = st.columns(2)
            
            with col_opp1:
                nb_logements_total = st.number_input("Nombre Total Logements *", min_value=1, value=40)
                nb_lls = st.number_input("LLS (Logements Locatifs Sociaux)", min_value=0, value=25)
                nb_lts = st.number_input("LTS (Logements Très Sociaux)", min_value=0, value=10)
                nb_pls = st.number_input("PLS (Prêt Locatif Social)", min_value=0, value=5)
                type_logement = st.selectbox("Type", ["Collectif", "Individuel", "Mixte"])
            
            with col_opp2:
                budget_total = st.number_input("Budget Total (€)", min_value=0, value=2000000)
                rem_totale = st.number_input("REM Totale Prévue (€)", min_value=0, value=120000)
                financement = st.multiselect("Financement", ["CDC", "Région", "DEAL", "Fonds Propres"])
        
        elif type_operation == "VEFA":
            col_vefa1, col_vefa2 = st.columns(2)
            
            with col_vefa1:
                promoteur_nom = st.text_input("Nom Promoteur *")
                contact_promoteur = st.text_input("Contact Promoteur")
                nom_programme = st.text_input("Nom Programme")
            
            with col_vefa2:
                nb_logements_reserves = st.number_input("Logements Réservés *", min_value=1, value=20)
                prix_total_reservation = st.number_input("Prix Total Réservation (€)", min_value=0, value=1500000)
                garantie_financiere = st.number_input("Garantie Financière (€)", min_value=0, value=150000)
        
        # Dates prévisionnelles
        st.markdown("#### 📅 Planning Prévisionnel")
        
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            date_debut = st.date_input("Date Début Prévue", value=datetime.now())
        
        with col_date2:
            date_fin = st.date_input("Date Fin Prévue", value=datetime.now() + timedelta(days=730))
        
        # Validation
        submitted = st.form_submit_button("🎯 Créer Opération & Générer Timeline", type="primary")
        
        if submitted:
            if nom_operation and type_operation and commune:
                # Génération automatique des phases selon le type
                phases_template = template_info.get('phases', [])
                
                st.success(f"✅ Opération '{nom_operation}' créée avec succès!")
                st.info(f"📋 {len(phases_template)} phases générées automatiquement selon le référentiel {type_operation}")
                
                # Simulation de sauvegarde
                nouvelle_operation = {
                    "id": 999,  # ID temporaire pour la démo
                    "nom": nom_operation,
                    "type_operation": type_operation,
                    "commune": commune,
                    "aco_responsable": aco_responsable,
                    "budget_total": locals().get('budget_total', 0),
                    "avancement": 0,
                    "statut": "EN_MONTAGE",
                    "date_creation": datetime.now().strftime("%Y-%m-%d"),
                    "date_debut_prevue": date_debut.strftime("%Y-%m-%d"),
                    "date_fin_prevue": date_fin.strftime("%Y-%m-%d")
                }
                
                st.session_state.selected_operation = nouvelle_operation
                st.session_state.selected_operation_id = 999
                st.session_state.page = "operation_details"
                
                if st.button("📂 Ouvrir l'opération créée"):
                    st.rerun()
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires (*)")

# ==============================================================================
# 5. APPLICATION PRINCIPALE
# ==============================================================================

def main():
    """Point d'entrée avec navigation st.session_state"""
    
    # Initialisation session state
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    if 'selected_operation' not in st.session_state:
        st.session_state.selected_operation = None
    
    if 'selected_operation_id' not in st.session_state:
        st.session_state.selected_operation_id = None
    
    # Sidebar navigation ACO-centrique
    with st.sidebar:
        st.markdown("### 🎯 Navigation ACO")
        st.markdown("*Interface centrée Agent de Conduite d'Opérations*")
        
        if st.button("🏠 Dashboard", use_container_width=True, type="primary" if st.session_state.page == "dashboard" else "secondary"):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("📂 Mon Portefeuille", use_container_width=True, type="primary" if st.session_state.page == "portefeuille" else "secondary"):
            st.session_state.page = "portefeuille"
            st.rerun()
        
        if st.button("➕ Nouvelle Opération", use_container_width=True, type="primary" if st.session_state.page == "creation_operation" else "secondary"):
            st.session_state.page = "creation_operation"
            st.rerun()
        
        st.markdown("---")
        
        # Opérations courantes (raccourcis)
        st.markdown("#### 📋 Accès Rapide")
        
        demo_data = load_demo_data()
        operations_demo = demo_data.get('operations_demo', [])
        
        for op in operations_demo[:4]:  # Limite à 4 pour la sidebar
            progress_color = "🟢" if op['avancement'] > 80 else "🟡" if op['avancement'] > 50 else "🔴"
            button_text = f"{progress_color} {op['nom']} ({op['avancement']}%)"
            
            if st.button(button_text, use_container_width=True, key=f"sidebar_{op['id']}"):
                st.session_state.selected_operation = op
                st.session_state.selected_operation_id = op['id']
                st.session_state.page = "operation_details"
                st.rerun()
        
        st.markdown("---")
        
        # Informations système
        st.markdown("**OPCOPILOT v4.0**")
        st.markdown("*SPIC Guadeloupe*")
        st.markdown("*Architecture ACO-centrique*")
        
        # Statut données
        if demo_data:
            st.success("✅ Données chargées")
        else:
            st.error("❌ Erreur données")
    
    # Routage des pages
    if st.session_state.page == "dashboard":
        page_dashboard()
    elif st.session_state.page == "portefeuille":
        page_portefeuille_aco()
    elif st.session_state.page == "creation_operation":
        page_creation_operation()
    elif st.session_state.page == "operation_details":
        page_operation_details()
    else:
        # Page par défaut
        page_dashboard()

if __name__ == "__main__":
    main()
