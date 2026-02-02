from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from database.models import db, Post, User, Media, Activity, Offer
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    # Statistiques
    stats = {
        'total_posts': Post.query.count(),
        'published_posts': Post.query.filter_by(status='published').count(),
        'total_users': User.query.count(),
        'total_media': Media.query.count(),
        'total_activities': Activity.query.count(),
        'total_offers': Offer.query.count()
    }
    
    # Posts récents
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # Activités à venir
    upcoming_activities = Activity.query.filter(
        Activity.start_date >= datetime.utcnow()
    ).order_by(Activity.start_date).limit(5).all()
    
    # Offres ouvertes
    open_offers = Offer.query.filter_by(status='open').order_by(
        Offer.application_deadline
    ).limit(5).all()
    
    return render_template('dashboard/index.html',
                         stats=stats,
                         recent_posts=recent_posts,
                         upcoming_activities=upcoming_activities,
                         open_offers=open_offers)

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API pour les statistiques du dashboard"""
    # Statistiques de base
    total_posts = Post.query.count()
    published_posts = Post.query.filter_by(status='published').count()
    draft_posts = Post.query.filter_by(status='draft').count()
    
    # Par type de post
    posts_by_type = db.session.query(
        Post.post_type,
        func.count(Post.id).label('count')
    ).group_by(Post.post_type).all()
    
    # Activités par statut
    activities_by_status = db.session.query(
        Activity.status,
        func.count(Activity.id).label('count')
    ).group_by(Activity.status).all()
    
    # Posts des 30 derniers jours
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_posts = Post.query.filter(
        Post.created_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'posts_by_type': {ptype: count for ptype, count in posts_by_type},
        'activities_by_status': {status: count for status, count in activities_by_status},
        'recent_posts': recent_posts
    })