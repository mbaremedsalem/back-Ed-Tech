"""
analytics/models.py

Conformément à FATIN_Schema_Final_Complet.docx (Partie 7.3, "Points de
vigilance") : cette app ne définit AUCUNE table dédiée. Les tables
LearningAnalytics, TeacherDashboard, Notification et SystemLog sont
explicitement hors scope du MVP.

Toutes les statistiques (dashboard enseignant, analyse des erreurs, etc.)
sont calculées à la volée via des requêtes SQL agrégées sur les tables
existantes (User, StudentProgress, LogAnswer, Error, ...).
Voir analytics/views.py.
"""
