#!/usr/bin/env python3
"""
Script d'initialisation simplifié pour Render
"""

import os
import sys
from app import create_app, db
from database.models import User
from flask_bcrypt import Bcrypt

# Configuration pour Render
os.environ['FLASK_CONFIG'] = 'production'

app = create_app('production')
bcrypt = Bcrypt(app)

def init_database():
    """Initialisation simplifiée de la base de données"""
    print("🔧 Initialisation de la base de données...")
    
    with app.app_context():
        # Créer toutes les tables
        db.create_all()
        
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
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
            db.session.commit()
            
            print("✅ Base de données initialisée avec succès !")
            print("👤 Compte administrateur créé:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@labmath.com")
            print("\n⚠️  IMPORTANT: Changez le mot de passe après votre première connexion !")
        else:
            print("✅ Base de données déjà initialisée.")
            print(f"👤 Admin existe déjà: {admin.email}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_database()
    else:
        print("Utilisation: python init_db_simple.py init")