from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from PIL import Image
import magic
from database.models import db, Media as MediaModel
from datetime import datetime

media_bp = Blueprint('media', __name__, template_folder='../templates')

def allowed_file(filename):
    """Vérifier les extensions autorisées"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_thumbnail(input_path, output_path, size=(300, 200)):
    """Générer une miniature pour une image"""
    try:
        with Image.open(input_path) as img:
            img.thumbnail(size)
            img.save(output_path)
        return True
    except Exception as e:
        print(f"Erreur génération thumbnail: {e}")
        return False

def save_media_file(file, folder='images'):
    """Sauvegarder un fichier média"""
    if not file or not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    
    # Créer le dossier s'il n'existe pas
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    # Détecter le type MIME
    mime_type = magic.from_file(file_path, mime=True)
    
    # Générer une miniature pour les images
    thumbnail_path = None
    if mime_type.startswith('image/'):
        thumb_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        thumbnail_path = os.path.join(thumb_dir, unique_filename)
        generate_thumbnail(file_path, thumbnail_path)
    
    return {
        'filename': unique_filename,
        'original_filename': filename,
        'file_path': file_path,
        'thumbnail_path': thumbnail_path,
        'file_size': os.path.getsize(file_path),
        'mime_type': mime_type
    }

@media_bp.route('/media')
@login_required
def media_library():
    """Bibliothèque des médias"""
    page = request.args.get('page', 1, type=int)
    file_type = request.args.get('type', 'all')
    search = request.args.get('search', '')
    
    query = MediaModel.query
    
    if file_type != 'all':
        query = query.filter(MediaModel.file_type == file_type)
    
    if search:
        query = query.filter(MediaModel.filename.ilike(f'%{search}%'))
    
    media_items = query.order_by(MediaModel.created_at.desc()).paginate(
        page=page, per_page=24, error_out=False
    )
    
    return media_items

@media_bp.route('/media/upload', methods=['POST'])
@login_required
def upload_media():
    """Uploader un fichier"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    file_info = save_media_file(file)
    if not file_info:
        return jsonify({'error': 'Type de fichier non autorisé'}), 400
    
    # Créer l'entrée en base de données
    media = MediaModel(
        filename=file_info['filename'],
        original_filename=file_info['original_filename'],
        file_path=file_info['file_path'].replace('\\', '/'),
        thumbnail_path=file_info['thumbnail_path'].replace('\\', '/') if file_info['thumbnail_path'] else None,
        file_size=file_info['file_size'],
        mime_type=file_info['mime_type'],
        file_type=file_info['mime_type'].split('/')[0],
        uploaded_by=current_user.id if current_user.is_authenticated else None
    )
    
    # Pour les images, récupérer les dimensions
    if media.file_type == 'image':
        try:
            with Image.open(file_info['file_path']) as img:
                media.width, media.height = img.size
        except:
            pass
    
    db.session.add(media)
    db.session.commit()
    
    return jsonify({
        'id': media.id,
        'filename': media.filename,
        'url': f"/media/{media.id}/file",
        'thumbnail_url': f"/media/{media.id}/thumbnail" if media.thumbnail_path else None,
        'mime_type': media.mime_type,
        'file_size': media.file_size,
        'created_at': media.created_at.isoformat()
    })

@media_bp.route('/media/<int:media_id>/file')
def get_media_file(media_id):
    """Récupérer un fichier média"""
    media = MediaModel.query.get_or_404(media_id)
    
    if not os.path.exists(media.file_path):
        return 'File not found', 404
    
    return send_file(media.file_path)

@media_bp.route('/media/<int:media_id>/thumbnail')
def get_media_thumbnail(media_id):
    """Récupérer la miniature d'un média"""
    media = MediaModel.query.get_or_404(media_id)
    
    if not media.thumbnail_path or not os.path.exists(media.thumbnail_path):
        # Retourner l'original si pas de miniature
        if os.path.exists(media.file_path):
            return send_file(media.file_path)
        return 'File not found', 404
    
    return send_file(media.thumbnail_path)

@media_bp.route('/media/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """Supprimer un média"""
    media = MediaModel.query.get_or_404(media_id)
    
    # Supprimer les fichiers physiques
    try:
        if os.path.exists(media.file_path):
            os.remove(media.file_path)
        if media.thumbnail_path and os.path.exists(media.thumbnail_path):
            os.remove(media.thumbnail_path)
    except Exception as e:
        current_app.logger.error(f"Erreur suppression fichier: {e}")
    
    # Supprimer de la base
    db.session.delete(media)
    db.session.commit()
    
    return jsonify({'success': True})

@media_bp.route('/api/media')
@login_required
def api_media_list():
    """API pour la liste des médias"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    file_type = request.args.get('type', 'image')
    
    query = MediaModel.query
    
    if file_type != 'all':
        query = query.filter(MediaModel.file_type == file_type)
    
    media_items = query.order_by(MediaModel.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [{
            'id': item.id,
            'filename': item.filename,
            'original_filename': item.original_filename,
            'url': f"/media/{item.id}/file",
            'thumbnail_url': f"/media/{item.id}/thumbnail" if item.thumbnail_path else None,
            'file_type': item.file_type,
            'mime_type': item.mime_type,
            'file_size': item.file_size,
            'created_at': item.created_at.isoformat(),
            'description': item.description,
            'alt_text': item.alt_text
        } for item in media_items.items],
        'total': media_items.total,
        'pages': media_items.pages,
        'current_page': media_items.page
    })