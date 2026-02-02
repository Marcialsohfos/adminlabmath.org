from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from functools import wraps
import jwt
from datetime import datetime, timedelta
from database.models import Post, Activity, Offer, Category, Media, db, ApiToken, Setting

api_bp = Blueprint('api', __name__)

def token_required(f):
    """Décorateur pour vérifier les tokens API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Chercher le token dans les headers
        if 'X-API-Key' in request.headers:
            token = request.headers['X-API-Key']
        
        # Chercher le token dans les query params
        if not token and request.args.get('api_key'):
            token = request.args.get('api_key')
        
        if not token:
            return jsonify({'error': 'Token API manquant'}), 401
        
        # Vérifier le token dans la base de données
        api_token = ApiToken.query.filter_by(token=token, is_active=True).first()
        if not api_token:
            return jsonify({'error': 'Token API invalide'}), 401
        
        # Vérifier l'expiration
        if api_token.expires_at and api_token.expires_at < datetime.utcnow():
            return jsonify({'error': 'Token API expiré'}), 401
        
        # Mettre à jour la dernière utilisation
        api_token.last_used = datetime.utcnow()
        db.session.commit()
        
        return f(*args, **kwargs)
    
    return decorated

@api_bp.route('/posts')
@cross_origin()
def get_posts():
    """API pour récupérer les posts"""
    post_type = request.args.get('type', 'all')
    category = request.args.get('category')
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    featured = request.args.get('featured', False, type=bool)
    
    query = Post.query.filter_by(status='published')
    
    if post_type != 'all':
        query = query.filter_by(post_type=post_type)
    
    if category:
        query = query.join(Category).filter(Category.slug == category)
    
    if featured:
        query = query.filter_by(is_featured=True)
    
    total = query.count()
    posts = query.order_by(Post.published_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'excerpt': post.excerpt,
            'content': post.content_html,
            'post_type': post.post_type,
            'featured_image': f"/media/{post.featured_image}" if post.featured_image else None,
            'published_at': post.published_at.isoformat() if post.published_at else None,
            'author': post.author.username if post.author else None,
            'category': {
                'name': post.category_ref.name,
                'slug': post.category_ref.slug,
                'color': post.category_ref.color
            } if post.category_ref else None,
            'tags': [tag.name for tag in post.tags],
            'activity': {
                'activity_type': post.activity.activity_type,
                'start_date': post.activity.start_date.isoformat() if post.activity and post.activity.start_date else None,
                'end_date': post.activity.end_date.isoformat() if post.activity and post.activity.end_date else None,
                'location': post.activity.location,
                'is_online': post.activity.is_online,
                'status': post.activity.status
            } if post.activity else None,
            'offer': {
                'offer_type': post.offer.offer_type,
                'contract_type': post.offer.contract_type,
                'location': post.offer.location,
                'salary_range': post.offer.salary_range,
                'application_deadline': post.offer.application_deadline.isoformat() if post.offer and post.offer.application_deadline else None,
                'status': post.offer.status
            } if post.offer else None
        } for post in posts],
        'meta': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(posts) < total
        }
    })

@api_bp.route('/posts/<slug>')
@cross_origin()
def get_post(slug):
    """API pour récupérer un post spécifique"""
    post = Post.query.filter_by(slug=slug, status='published').first_or_404()
    
    # Incrémenter le compteur de vues
    post.views += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'excerpt': post.excerpt,
            'content': post.content_html,
            'post_type': post.post_type,
            'featured_image': f"/media/{post.featured_image}" if post.featured_image else None,
            'published_at': post.published_at.isoformat() if post.published_at else None,
            'author': {
                'username': post.author.username,
                'first_name': post.author.first_name,
                'last_name': post.author.last_name
            } if post.author else None,
            'category': {
                'name': post.category_ref.name,
                'slug': post.category_ref.slug,
                'color': post.category_ref.color
            } if post.category_ref else None,
            'tags': [tag.name for tag in post.tags],
            'activity': {
                'activity_type': post.activity.activity_type,
                'start_date': post.activity.start_date.isoformat() if post.activity and post.activity.start_date else None,
                'end_date': post.activity.end_date.isoformat() if post.activity and post.activity.end_date else None,
                'location': post.activity.location,
                'is_online': post.activity.is_online,
                'registration_url': post.activity.registration_url,
                'status': post.activity.status
            } if post.activity else None,
            'offer': {
                'offer_type': post.offer.offer_type,
                'contract_type': post.offer.contract_type,
                'location': post.offer.location,
                'salary_range': post.offer.salary_range,
                'experience_required': post.offer.experience_required,
                'application_deadline': post.offer.application_deadline.isoformat() if post.offer and post.offer.application_deadline else None,
                'start_date': post.offer.start_date.isoformat() if post.offer and post.offer.start_date else None,
                'is_remote': post.offer.is_remote,
                'status': post.offer.status
            } if post.offer else None,
            'views': post.views,
            'likes': post.likes
        }
    })

@api_bp.route('/activities')
@cross_origin()
def get_activities():
    """API pour récupérer les activités"""
    status = request.args.get('status', 'upcoming')
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Activity.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    # Filtrer pour les activités futures ou en cours
    if status == 'upcoming':
        query = query.filter(Activity.start_date >= datetime.utcnow())
    elif status == 'ongoing':
        query = query.filter(
            Activity.start_date <= datetime.utcnow(),
            Activity.end_date >= datetime.utcnow()
        )
    
    total = query.count()
    activities = query.order_by(Activity.start_date).offset(offset).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': activity.id,
            'title': activity.title,
            'slug': activity.slug,
            'description': activity.description,
            'activity_type': activity.activity_type,
            'start_date': activity.start_date.isoformat() if activity.start_date else None,
            'end_date': activity.end_date.isoformat() if activity.end_date else None,
            'location': activity.location,
            'is_online': activity.is_online,
            'registration_url': activity.registration_url,
            'max_participants': activity.max_participants,
            'current_participants': activity.current_participants,
            'status': activity.status,
            'featured_image': f"/media/{activity.post.featured_image}" if activity.post and activity.post.featured_image else None,
            'post_slug': activity.post.slug if activity.post else None
        } for activity in activities],
        'meta': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(activities) < total
        }
    })

@api_bp.route('/offers')
@cross_origin()
def get_offers():
    """API pour récupérer les offres"""
    offer_type = request.args.get('type', 'all')
    status = request.args.get('status', 'open')
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Offer.query
    
    if offer_type != 'all':
        query = query.filter_by(offer_type=offer_type)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    total = query.count()
    offers = query.order_by(Offer.created_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': offer.id,
            'title': offer.title,
            'slug': offer.slug,
            'description': offer.description,
            'offer_type': offer.offer_type,
            'contract_type': offer.contract_type,
            'location': offer.location,
            'salary_range': offer.salary_range,
            'experience_required': offer.experience_required,
            'application_deadline': offer.application_deadline.isoformat() if offer.application_deadline else None,
            'start_date': offer.start_date.isoformat() if offer.start_date else None,
            'is_remote': offer.is_remote,
            'status': offer.status,
            'views': offer.views,
            'applications_count': offer.applications_count,
            'featured_image': f"/media/{offer.post.featured_image}" if offer.post and offer.post.featured_image else None,
            'post_slug': offer.post.slug if offer.post else None
        } for offer in offers],
        'meta': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(offers) < total
        }
    })

@api_bp.route('/categories')
@cross_origin()
def get_categories():
    """API pour récupérer les catégories"""
    categories = Category.query.filter_by(is_active=True).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'description': cat.description,
            'color': cat.color,
            'icon': cat.icon,
            'post_count': cat.posts.filter_by(status='published').count()
        } for cat in categories]
    })

@api_bp.route('/sync', methods=['POST'])
@token_required
def sync_data():
    """Endpoint de synchronisation pour le site principal"""
    data = request.json
    
    # Ici, vous pouvez implémenter la logique de synchronisation
    # Par exemple, mettre à jour le cache ou générer des fichiers statiques
    
    return jsonify({
        'success': True,
        'message': 'Synchronisation réussie',
        'timestamp': datetime.utcnow().isoformat(),
        'synced_items': {
            'posts': Post.query.filter_by(status='published').count(),
            'activities': Activity.query.count(),
            'offers': Offer.query.count()
        }
    })

@api_bp.route('/health')
@cross_origin()
def api_health():
    """Health check pour l'API"""
    return jsonify({
        'status': 'healthy',
        'service': 'labmath-admin-api',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.session.query('1').from_statement(db.text('SELECT 1')).first() else 'disconnected'
    })