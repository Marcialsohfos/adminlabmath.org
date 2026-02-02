from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from app import db, bcrypt
from slugify import slugify

class User(UserMixin, db.Model):
    """Modèle utilisateur pour l'administration"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    role = db.Column(db.String(20), default='editor')  # admin, editor, viewer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Catégories pour les posts"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#00bcd4')  # Code couleur hex
    icon = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    posts = db.relationship('Post', backref='category_ref', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    """Articles/Publications"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)  # HTML généré pour performance
    post_type = db.Column(db.String(20), nullable=False)  # article, activity, announcement, offer
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    featured_image = db.Column(db.String(300))
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    # Relations
    media = db.relationship('PostMedia', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='post_tags', backref='posts', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            self.published_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Tag(db.Model):
    """Tags pour les posts"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

# Table de liaison pour les tags
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class PostMedia(db.Model):
    """Médias associés aux posts"""
    __tablename__ = 'post_media'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300))
    file_type = db.Column(db.String(50))  # image, document, video
    file_size = db.Column(db.Integer)
    file_path = db.Column(db.String(500))
    thumbnail_path = db.Column(db.String(500))
    caption = db.Column(db.String(300))
    alt_text = db.Column(db.String(300))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    
    def __repr__(self):
        return f'<PostMedia {self.filename}>'

class Media(db.Model):
    """Médias de la bibliothèque"""
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300))
    file_type = db.Column(db.String(50))  # image, document, video, audio
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    file_path = db.Column(db.String(500))
    thumbnail_path = db.Column(db.String(500))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(300))
    is_public = db.Column(db.Boolean, default=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Media {self.filename}>'

class Activity(db.Model):
    """Activités du laboratoire (liées aux posts)"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.String(50))  # workshop, conference, research, project
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    is_online = db.Column(db.Boolean, default=False)
    registration_url = db.Column(db.String(500))
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed, cancelled
    featured_image = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clé étrangère
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), unique=True)
    
    # Relation
    post = db.relationship('Post', backref='activity', uselist=False)
    
    def __init__(self, **kwargs):
        super(Activity, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
    
    def __repr__(self):
        return f'<Activity {self.title}>'

class Offer(db.Model):
    """Offres (emplois, stages, appels d'offres)"""
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    offer_type = db.Column(db.String(50), nullable=False)  # job, internship, tender
    contract_type = db.Column(db.String(50))  # full-time, part-time, contract, freelance
    location = db.Column(db.String(200))
    salary_range = db.Column(db.String(100))
    experience_required = db.Column(db.String(100))
    application_deadline = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    is_remote = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='open')  # open, closed, filled
    views = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clé étrangère
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), unique=True)
    
    # Relation
    post = db.relationship('Post', backref='offer', uselist=False)
    
    def __init__(self, **kwargs):
        super(Offer, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
    
    def __repr__(self):
        return f'<Offer {self.title}>'

class Setting(db.Model):
    """Paramètres du site"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')  # string, integer, boolean, json
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.String(300))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}>'

class ApiToken(db.Model):
    """Tokens API pour la synchronisation"""
    __tablename__ = 'api_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.Text)  # JSON des permissions
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<ApiToken {self.name}>'