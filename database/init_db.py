import os
import sys
from app import create_app, db
from database.models import User, Category, Setting
from flask_bcrypt import Bcrypt

app = create_app('development')
bcrypt = Bcrypt(app)

def init_database():
    """Initialisation de la base de données avec données par défaut"""
    with app.app_context():
        # Créer les tables
        db.drop_all()
        db.create_all()
        
        # Créer l'administrateur par défaut
        admin_user = User(
            username='admin',
            email='admin@labmath.com',
            first_name='Admin',
            last_name='LabMath',
            role='admin'
        )
        admin_user.password = 'admin123'  # À changer après la première connexion
        db.session.add(admin_user)
        
        # Créer les catégories par défaut
        categories = [
            {'name': 'Actualités', 'slug': 'actualites', 'color': '#00bcd4', 'icon': 'newspaper'},
            {'name': 'Recherche', 'slug': 'recherche', 'color': '#00ffcc', 'icon': 'flask'},
            {'name': 'Publications', 'slug': 'publications', 'color': '#ffd700', 'icon': 'book'},
            {'name': 'Événements', 'slug': 'evenements', 'color': '#9c27b0', 'icon': 'calendar'},
            {'name': 'Annonces', 'slug': 'annonces', 'color': '#ff9800', 'icon': 'bullhorn'},
            {'name': 'Offres', 'slug': 'offres', 'color': '#4caf50', 'icon': 'briefcase'}
        ]
        
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)
        
        # Créer les paramètres par défaut
        settings = [
            {'key': 'site_name', 'value': 'Lab_Math', 'category': 'general'},
            {'key': 'site_description', 'value': 'Laboratoire de Mathématiques Appliquées', 'category': 'general'},
            {'key': 'main_site_url', 'value': 'https://labmath-scsmaubmar-org.onrender.com', 'category': 'integration'},
            {'key': 'api_enabled', 'value': 'true', 'value_type': 'boolean', 'category': 'api'},
            {'key': 'posts_per_page', 'value': '10', 'value_type': 'integer', 'category': 'display'},
            {'key': 'maintenance_mode', 'value': 'false', 'value_type': 'boolean', 'category': 'general'},
        ]
        
        for setting_data in settings:
            setting = Setting(**setting_data)
            db.session.add(setting)
        
        # Sauvegarder
        db.session.commit()
        
        print("✅ Base de données initialisée avec succès !")
        print("👤 Compte administrateur créé:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@labmath.com")
        print("\n⚠️  IMPORTANT: Changez le mot de passe après votre première connexion !")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        confirm = input("Êtes-vous sûr de vouloir réinitialiser la base de données ? (yes/no): ")
        if confirm.lower() == 'yes':
            init_database()
        else:
            print("Opération annulée.")
    else:
        print("Utilisation: python init_db.py reset")