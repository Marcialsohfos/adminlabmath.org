from app import create_app
import os

# Forcer l'environnement de production pour Render
os.environ.setdefault('FLASK_CONFIG', 'production')

app = create_app(os.getenv('FLASK_CONFIG', 'production'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)