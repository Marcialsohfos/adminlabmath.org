from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from config import config
import logging
from logging.handlers import RotatingFileHandler

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_name='default'):
    """Factory d'application Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Configuration du login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Setup logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/labmath_admin.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('LabMath Admin startup')
    
    # Création des dossiers nécessaires
    with app.app_context():
        os.makedirs('uploads/images', exist_ok=True)
        os.makedirs('uploads/documents', exist_ok=True)
        os.makedirs('uploads/thumbnails', exist_ok=True)
    
    # Import des blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.posts import posts_bp
    from blueprints.media import media_bp
    from blueprints.api import api_bp
    
    # Enregistrement des blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import des modèles après db pour éviter les imports circulaires
    from database.models import User, Post, Media, Category, Activity
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Filtres Jinja2 personnalisés
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%d/%m/%Y %H:%M'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('excerpt')
    def excerpt_filter(text, length=200):
        if len(text) > length:
            return text[:length] + '...'
        return text
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
    
    # Route principale de l'admin
    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('dashboard.dashboard'))
    
    # Route pour les assets
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return app.send_static_file(filename)
    
    # Synchronisation avec le site principal (webhook)
    @app.route('/webhook/sync', methods=['POST'])
    def sync_webhook():
        # Cette route sera appelée par le site principal pour synchroniser les données
        # Pour l'instant, c'est un placeholder
        return jsonify({'status': 'ok', 'message': 'Sync endpoint ready'})
    
    # Health check pour Render
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    return app

# Création de l'application
app = create_app(os.getenv('FLASK_CONFIG', 'default'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False') == 'True')