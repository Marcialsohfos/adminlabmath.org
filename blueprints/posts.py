from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import markdown
from bleach import clean
from slugify import slugify

from database.models import db, Post, Category, Tag, PostMedia, Activity, Offer, post_tags
from .media import allowed_file, save_media_file, generate_thumbnail

posts_bp = Blueprint('posts', __name__, template_folder='../templates')

@posts_bp.route('/posts')
@login_required
def posts_list():
    """Liste des posts"""
    page = request.args.get('page', 1, type=int)
    post_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = Post.query
    
    if post_type != 'all':
        query = query.filter_by(post_type=post_type)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(Post.title.ilike(f'%{search}%'))
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('posts/list.html',
                         posts=posts,
                         categories=categories,
                         post_type=post_type,
                         status=status,
                         search=search)

@posts_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Créer un nouveau post"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        post_type = request.form.get('post_type', 'article')
        category_id = request.form.get('category_id')
        status = request.form.get('status', 'draft')
        is_featured = request.form.get('is_featured') == 'on'
        allow_comments = request.form.get('allow_comments') == 'on'
        
        # Créer le post
        post = Post(
            title=title,
            content=content,
            excerpt=excerpt,
            post_type=post_type,
            status=status,
            is_featured=is_featured,
            allow_comments=allow_comments,
            user_id=current_user.id,
            category_id=category_id if category_id else None
        )
        
        # Générer le HTML sécurisé
        post.content_html = clean(markdown.markdown(content))
        
        if status == 'published' and not post.published_at:
            post.published_at = datetime.utcnow()
        
        # Gérer les tags
        tags_input = request.form.get('tags', '')
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)
        
        db.session.add(post)
        db.session.commit()
        
        # Gérer l'image principale
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{post.id}_{filename}"
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'images')
                
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                
                # Générer une miniature
                thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', unique_filename)
                generate_thumbnail(file_path, thumb_path)
                
                post.featured_image = unique_filename
                db.session.commit()
        
        flash('Post créé avec succès !', 'success')
        
        # Rediriger selon le type de post
        if post_type == 'activity':
            return redirect(url_for('posts.create_activity', post_id=post.id))
        elif post_type == 'offer':
            return redirect(url_for('posts.create_offer', post_id=post.id))
        else:
            return redirect(url_for('posts.edit_post', post_id=post.id))
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('posts/create.html', categories=categories)

@posts_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Éditer un post"""
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.excerpt = request.form.get('excerpt')
        post.post_type = request.form.get('post_type')
        post.category_id = request.form.get('category_id')
        post.status = request.form.get('status')
        post.is_featured = request.form.get('is_featured') == 'on'
        post.allow_comments = request.form.get('allow_comments') == 'on'
        
        # Mettre à jour le HTML
        post.content_html = clean(markdown.markdown(post.content))
        
        if post.status == 'published' and not post.published_at:
            post.published_at = datetime.utcnow()
        
        # Mettre à jour les tags
        tags_input = request.form.get('tags', '')
        post.tags.clear()
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)
        
        db.session.commit()
        flash('Post mis à jour avec succès !', 'success')
        return redirect(url_for('posts.edit_post', post_id=post.id))
    
    categories = Category.query.filter_by(is_active=True).all()
    tags_str = ', '.join([tag.name for tag in post.tags])
    
    return render_template('posts/edit.html',
                         post=post,
                         categories=categories,
                         tags_str=tags_str)

@posts_bp.route('/posts/<int:post_id>/activity', methods=['GET', 'POST'])
@login_required
def create_activity(post_id):
    """Créer/modifier une activité liée à un post"""
    post = Post.query.get_or_404(post_id)
    
    activity = Activity.query.filter_by(post_id=post_id).first()
    
    if request.method == 'POST':
        if not activity:
            activity = Activity(post_id=post_id)
        
        activity.title = request.form.get('title', post.title)
        activity.description = request.form.get('description')
        activity.activity_type = request.form.get('activity_type')
        activity.location = request.form.get('location')
        activity.is_online = request.form.get('is_online') == 'on'
        activity.registration_url = request.form.get('registration_url')
        activity.max_participants = request.form.get('max_participants', type=int)
        activity.status = request.form.get('status', 'upcoming')
        
        # Dates
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        if start_date_str:
            activity.start_date = datetime.fromisoformat(start_date_str.replace('T', ' '))
        if end_date_str:
            activity.end_date = datetime.fromisoformat(end_date_str.replace('T', ' '))
        
        if not activity.slug:
            activity.slug = slugify(activity.title)
        
        if activity not in db.session:
            db.session.add(activity)
        
        db.session.commit()
        flash('Activité enregistrée avec succès !', 'success')
        return redirect(url_for('posts.edit_post', post_id=post_id))
    
    return render_template('posts/activity.html', post=post, activity=activity)

@posts_bp.route('/posts/<int:post_id>/offer', methods=['GET', 'POST'])
@login_required
def create_offer(post_id):
    """Créer/modifier une offre liée à un post"""
    post = Post.query.get_or_404(post_id)
    
    offer = Offer.query.filter_by(post_id=post_id).first()
    
    if request.method == 'POST':
        if not offer:
            offer = Offer(post_id=post_id)
        
        offer.title = request.form.get('title', post.title)
        offer.description = request.form.get('description')
        offer.offer_type = request.form.get('offer_type')
        offer.contract_type = request.form.get('contract_type')
        offer.location = request.form.get('location')
        offer.salary_range = request.form.get('salary_range')
        offer.experience_required = request.form.get('experience_required')
        offer.is_remote = request.form.get('is_remote') == 'on'
        offer.status = request.form.get('status', 'open')
        
        # Dates
        deadline_str = request.form.get('application_deadline')
        start_date_str = request.form.get('start_date')
        
        if deadline_str:
            offer.application_deadline = datetime.fromisoformat(deadline_str.replace('T', ' '))
        if start_date_str:
            offer.start_date = datetime.fromisoformat(start_date_str.replace('T', ' '))
        
        if not offer.slug:
            offer.slug = slugify(offer.title)
        
        if offer not in db.session:
            db.session.add(offer)
        
        db.session.commit()
        flash('Offre enregistrée avec succès !', 'success')
        return redirect(url_for('posts.edit_post', post_id=post_id))
    
    return render_template('posts/offer.html', post=post, offer=offer)

@posts_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Supprimer un post"""
    post = Post.query.get_or_404(post_id)
    
    # Vérifier les permissions
    if current_user.role != 'admin' and post.user_id != current_user.id:
        flash('Vous n\'avez pas la permission de supprimer ce post.', 'danger')
        return redirect(url_for('posts.posts_list'))
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post supprimé avec succès !', 'success')
    return redirect(url_for('posts.posts_list'))

@posts_bp.route('/api/posts/preview', methods=['POST'])
@login_required
def preview_post():
    """Prévisualiser un post en markdown"""
    content = request.json.get('content', '')
    html = clean(markdown.markdown(content))
    return jsonify({'html': html})