from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from config import config
from uploads import save_uploaded_file, allowed_file

app = Flask(__name__)
app.config.from_object(config['default'])

# Ignore favicon requests
@app.route('/favicon.ico')
def favicon():
    return '', 204

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    """User model for farmers."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    farm_type = db.Column(db.String(50))  # crop, livestock, mixed
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(200), default='default-avatar.png')
    social_provider = db.Column(db.String(20))  # google, facebook, twitter, local
    language = db.Column(db.String(10), default='en')  # en, es, fr, de, zh, hi
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)
    offers_sent = db.relationship('Offer', foreign_keys='Offer.buyer_id', backref='buyer', lazy=True)
    offers_received = db.relationship('Offer', foreign_keys='Offer.seller_id', backref='seller', lazy=True)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    """Product model for seeds and animals."""
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # seeds, animals
    subcategory = db.Column(db.String(50))  # vegetables, fruits, livestock, poultry
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit = db.Column(db.String(20))  # kg, piece, liter
    image_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='available')  # available, sold, reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    offers = db.relationship('Offer', backref='product', lazy=True)

class Question(db.Model):
    """Question model for community forum."""
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # crop_farming, animal_husbandry, equipment, weather, market
    tags = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    solved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')

class Answer(db.Model):
    """Answer model for forum replies."""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    is_solution = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    """Offer model for bargaining."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    offer_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, counter
    message = db.Column(db.Text)
    counter_offer = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    """Message model for direct messaging."""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FriendRequest(db.Model):
    """Friend request model."""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')
    
    __table_args__ = (db.UniqueConstraint('sender_id', 'receiver_id', name='unique_friend_request'),)

# ==================== TIKTOK-STYLE MODELS ====================

class Post(db.Model):
    """Post model for TikTok-style stories/videos."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    media_url = db.Column(db.String(200))  # Video or image URL
    media_type = db.Column(db.String(20), default='video')  # video, image
    thumbnail_url = db.Column(db.String(200))
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    gifts_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='posts')
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    gifts = db.relationship('PostGift', backref='post', lazy=True, cascade='all, delete-orphan')

class PostLike(db.Model):
    """Like model for posts."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)

class PostComment(db.Model):
    """Comment model for posts."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='post_comments')
    likes = db.relationship('CommentLike', backref='comment', lazy=True, cascade='all, delete-orphan')

class CommentLike(db.Model):
    """Like model for comments."""
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('post_comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_like'),)

class Follow(db.Model):
    """Follow model for user following."""
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),)
    
    # Relationships
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    following = db.relationship('User', foreign_keys=[following_id], backref='followers')

class Gift(db.Model):
    """Gift model for virtual gifts."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)  # Real money value in USD
    coin_value = db.Column(db.Integer, nullable=False)  # Virtual coin value
    is_active = db.Column(db.Boolean, default=True)

class PostGift(db.Model):
    """Gift sent to a post."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gift_id = db.Column(db.Integer, db.ForeignKey('gift.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_value = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='sent_gifts')
    gift = db.relationship('Gift')

class UserWallet(db.Model):
    """User wallet for virtual coins."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    coins = db.Column(db.Integer, default=100)  # Start with 100 free coins
    total_spent = db.Column(db.Float, default=0)  # Total real money spent
    total_earned = db.Column(db.Float, default=0)  # Total real money earned from gifts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='wallet')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== LANGUAGE CONFIG ====================

# Language translations dictionary
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文',
    'hi': 'हिन्दी',
    'ar': 'العربية',
    'pt': 'Português'
}

# Common translations - comprehensive
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome back',
        'welcome_message': 'Welcome back, {name}!',
        'dashboard': 'Dashboard',
        'dashboard_subtitle': 'Manage your farm activities from one place',
        'marketplace': 'Marketplace',
        'forum': 'Forum',
        'messages': 'Messages',
        'profile': 'Profile',
        'logout': 'Logout',
        'login': 'Login',
        'signup': 'Sign Up',
        'products': 'Products',
        'questions': 'Questions',
        'settings': 'Settings',
        'language': 'Language',
        'quick_actions': 'Quick Actions',
        'recent_products': 'Recent Products',
        'your_recent_questions': 'Your Recent Questions',
        'add_product': 'List Product',
        'post_question': 'Ask Question',
        'browse_marketplace': 'Browse Marketplace',
        'products_listed': 'Products Listed',
        'questions_asked': 'Questions Asked',
        'pending_offers': 'Pending Offers',
        'no_products': 'No products listed yet.',
        'no_questions': 'No questions asked yet.',
        'solved': 'Solved',
        'pending': 'Pending',
        'seeds': 'Seeds',
        'animals': 'Animals',
        'all': 'All',
        'search': 'Search',
        'make_offer': 'Make Offer',
        'send_message': 'Send Message',
        'answers': 'Answers',
        'no_answers': 'No answers yet',
        'post_answer': 'Post Answer',
        'upvote': 'Upvote',
        'mark_solution': 'Mark as Solution',
        'edit_profile': 'Edit Profile',
        'my_products': 'My Products',
        'my_questions': 'My Questions',
        'accept': 'Accept',
        'reject': 'Reject',
        'counter_offer': 'Counter Offer',
        'inbox': 'Inbox',
        'sent': 'Sent',
        'no_messages': 'No messages',
        'compose_message': 'Compose Message',
        'reply': 'Reply',
        'available': 'Available',
        'sold': 'Sold',
        'view_all': 'View All',
        'read_more': 'Read More'
    },
    'es': {
        'welcome': 'Bienvenido de nuevo',
        'welcome_message': '¡Bienvenido, {name}!',
        'dashboard': 'Panel',
        'dashboard_subtitle': 'Gestiona las actividades de tu granja',
        'marketplace': 'Mercado',
        'forum': 'Foro',
        'messages': 'Mensajes',
        'profile': 'Perfil',
        'logout': 'Cerrar sesión',
        'login': 'Iniciar sesión',
        'signup': 'Registrarse',
        'products': 'Productos',
        'questions': 'Preguntas',
        'settings': 'Configuración',
        'language': 'Idioma',
        'quick_actions': 'Acciones rápidas',
        'recent_products': 'Productos recientes',
        'your_recent_questions': 'Tus preguntas recientes',
        'add_product': 'Agregar producto',
        'post_question': 'Hacer pregunta',
        'browse_marketplace': 'Explorar mercado',
        'products_listed': 'Productos listados',
        'questions_asked': 'Preguntas realizadas',
        'pending_offers': 'Ofertas pendientes',
        'no_products': 'Aún no hay productos.',
        'no_questions': 'Aún no hay preguntas.',
        'solved': 'Resuelto',
        'pending': 'Pendiente',
        'seeds': 'Semillas',
        'animals': 'Animales',
        'all': 'Todos',
        'search': 'Buscar',
        'make_offer': 'Hacer oferta',
        'send_message': 'Enviar mensaje',
        'answers': 'Respuestas',
        'no_answers': 'Sin respuestas aún',
        'post_answer': 'Publicar respuesta',
        'upvote': 'Votar',
        'mark_solution': 'Marcar como solución',
        'edit_profile': 'Editar perfil',
        'my_products': 'Mis productos',
        'my_questions': 'Mis preguntas',
        'accept': 'Aceptar',
        'reject': 'Rechazar',
        'counter_offer': 'Contraoferta',
        'inbox': 'Bandeja de entrada',
        'sent': 'Enviados',
        'no_messages': 'Sin mensajes',
        'compose_message': 'Redactar mensaje',
        'reply': 'Responder',
        'available': 'Disponible',
        'sold': 'Vendido',
        'view_all': 'Ver todo',
        'read_more': 'Leer más'
    },
    'fr': {
        'welcome': 'Bon retour',
        'welcome_message': 'Bienvenue, {name}!',
        'dashboard': 'Tableau de bord',
        'dashboard_subtitle': 'Gérez vos activités agricoles',
        'marketplace': 'Marché',
        'forum': 'Forum',
        'messages': 'Messages',
        'profile': 'Profil',
        'logout': 'Déconnexion',
        'login': 'Connexion',
        'signup': "S'inscrire",
        'products': 'Produits',
        'questions': 'Questions',
        'settings': 'Paramètres',
        'language': 'Langue',
        'quick_actions': 'Actions rapides',
        'recent_products': 'Produits récents',
        'your_recent_questions': 'Vos questions récentes',
        'add_product': 'Ajouter un produit',
        'post_question': 'Poser une question',
        'browse_marketplace': 'Parcourir le marché',
        'products_listed': 'Produits listés',
        'questions_asked': 'Questions posées',
        'pending_offers': 'Offres en attente',
        'no_products': 'Pas encore de produits.',
        'no_questions': 'Pas encore de questions.',
        'solved': 'Résolu',
        'pending': 'En attente',
        'seeds': 'Graines',
        'animals': 'Animaux',
        'all': 'Tous',
        'search': 'Rechercher',
        'make_offer': 'Faire une offre',
        'send_message': 'Envoyer un message',
        'answers': 'Réponses',
        'no_answers': 'Pas encore de réponses',
        'post_answer': 'Publier une réponse',
        'upvote': 'Voter',
        'mark_solution': 'Marquer comme solution',
        'edit_profile': 'Modifier le profil',
        'my_products': 'Mes produits',
        'my_questions': 'Mes questions',
        'accept': 'Accepter',
        'reject': 'Rejeter',
        'counter_offer': 'Contre-offre',
        'inbox': 'Boîte de réception',
        'sent': 'Envoyés',
        'no_messages': 'Pas de messages',
        'compose_message': 'Rédiger un message',
        'reply': 'Répondre',
        'available': 'Disponible',
        'sold': 'Vendu',
        'view_all': 'Voir tout',
        'read_more': 'Lire plus'
    },
    'de': {
        'welcome': 'Willkommen zurück',
        'welcome_message': 'Willkommen, {name}!',
        'dashboard': 'Dashboard',
        'dashboard_subtitle': 'Verwalten Sie Ihre Farmaktivitäten',
        'marketplace': 'Marktplatz',
        'forum': 'Forum',
        'messages': 'Nachrichten',
        'profile': 'Profil',
        'logout': 'Abmelden',
        'login': 'Anmelden',
        'signup': 'Registrieren',
        'products': 'Produkte',
        'questions': 'Fragen',
        'settings': 'Einstellungen',
        'language': 'Sprache',
        'quick_actions': 'Schnellaktionen',
        'recent_products': 'Aktuelle Produkte',
        'your_recent_questions': 'Ihre aktuellen Fragen',
        'add_product': 'Produkt hinzufügen',
        'post_question': 'Frage stellen',
        'browse_marketplace': 'Marktplatz durchsuchen',
        'products_listed': 'Gelistete Produkte',
        'questions_asked': 'Gestellte Fragen',
        'pending_offers': 'Ausstehende Angebote',
        'no_products': 'Noch keine Produkte.',
        'no_questions': 'Noch keine Fragen.',
        'solved': 'Gelöst',
        'pending': 'Ausstehend',
        'seeds': 'Samen',
        'animals': 'Tiere',
        'all': 'Alle',
        'search': 'Suchen',
        'make_offer': 'Angebot machen',
        'send_message': 'Nachricht senden',
        'answers': 'Antworten',
        'no_answers': 'Noch keine Antworten',
        'post_answer': 'Antwort posten',
        'upvote': 'Aufwerten',
        'mark_solution': 'Als Lösung markieren',
        'edit_profile': 'Profil bearbeiten',
        'my_products': 'Meine Produkte',
        'my_questions': 'Meine Fragen',
        'accept': 'Akzeptieren',
        'reject': 'Ablehnen',
        'counter_offer': 'Gegenangebot',
        'inbox': 'Posteingang',
        'sent': 'Gesendet',
        'no_messages': 'Keine Nachrichten',
        'compose_message': 'Nachricht verfassen',
        'reply': 'Antworten',
        'available': 'Verfügbar',
        'sold': 'Verkauft',
        'view_all': 'Alle anzeigen',
        'read_more': 'Mehr lesen'
    },
    'zh': {
        'welcome': '欢迎回来',
        'welcome_message': '欢迎，{name}！',
        'dashboard': '仪表板',
        'dashboard_subtitle': '管理您的农场活动',
        'marketplace': '市场',
        'forum': '论坛',
        'messages': '消息',
        'profile': '个人资料',
        'logout': '退出',
        'login': '登录',
        'signup': '注册',
        'products': '产品',
        'questions': '问题',
        'settings': '设置',
        'language': '语言',
        'quick_actions': '快速操作',
        'recent_products': '最近产品',
        'your_recent_questions': '您最近的问题',
        'add_product': '添加产品',
        'post_question': '提问',
        'browse_marketplace': '浏览市场',
        'products_listed': '已列出产品',
        'questions_asked': '已提问',
        'pending_offers': '待处理报价',
        'no_products': '还没有产品。',
        'no_questions': '还没有问题。',
        'solved': '已解决',
        'pending': '待处理',
        'seeds': '种子',
        'animals': '动物',
        'all': '全部',
        'search': '搜索',
        'make_offer': '报价',
        'send_message': '发送消息',
        'answers': '答案',
        'no_answers': '还没有答案',
        'post_answer': '发布答案',
        'upvote': '点赞',
        'mark_solution': '标记为解决方案',
        'edit_profile': '编辑资料',
        'my_products': '我的产品',
        'my_questions': '我的问题',
        'accept': '接受',
        'reject': '拒绝',
        'counter_offer': '还价',
        'inbox': '收件箱',
        'sent': '已发送',
        'no_messages': '无消息',
        'compose_message': '撰写消息',
        'reply': '回复',
        'available': '可用',
        'sold': '已售',
        'view_all': '查看全部',
        'read_more': '阅读更多'
    },
    'hi': {
        'welcome': 'वापसी पर स्वागत है',
        'welcome_message': 'स्वागत है, {name}!',
        'dashboard': 'डैशबोर्ड',
        'dashboard_subtitle': 'अपनी खेती गतिविधियों का प्रबंधन करें',
        'marketplace': 'बाज़ार',
        'forum': 'फ़ोरम',
        'messages': 'संदेश',
        'profile': 'प्रोफ़ाइल',
        'logout': 'लॉग आउट',
        'login': 'लॉग इन',
        'signup': 'साइन अप',
        'products': 'उत्पाद',
        'questions': 'प्रश्न',
        'settings': 'सेटिंग्स',
        'language': 'भाषा',
        'quick_actions': 'त्वरित कार्य',
        'recent_products': 'हाल के उत्पाद',
        'your_recent_questions': 'आपके हाल के प्रश्न',
        'add_product': 'उत्पाद जोड़ें',
        'post_question': 'प्रश्न पूछें',
        'browse_marketplace': 'बाज़ार ब्राउज़ करें',
        'products_listed': 'सूचीबद्ध उत्पाद',
        'questions_asked': 'पूछे गए प्रश्न',
        'pending_offers': 'लंबित प्रस्ताव',
        'no_products': 'अभी तक कोई उत्पाद नहीं।',
        'no_questions': 'अभी तक कोई प्रश्न नहीं।',
        'solved': 'हल किया',
        'pending': 'लंबित',
        'seeds': 'बीज',
        'animals': 'जानवर',
        'all': 'सभी',
        'search': 'खोजें',
        'make_offer': 'प्रस्ताव दें',
        'send_message': 'संदेश भेजें',
        'answers': 'उत्तर',
        'no_answers': 'अभी तक कोई उत्तर नहीं',
        'post_answer': 'उत्तर पोस्ट करें',
        'upvote': 'अपवोट',
        'mark_solution': 'समाधान के रूप में चिह्नित करें',
        'edit_profile': 'प्रोफ़ाइल संपादित करें',
        'my_products': 'मेरे उत्पाद',
        'my_questions': 'मेरे प्रश्न',
        'accept': 'स्वीकार करें',
        'reject': 'अस्वीकार करें',
        'counter_offer': 'प्रति-प्रस्ताव',
        'inbox': 'इनबॉक्स',
        'sent': 'भेजा गया',
        'no_messages': 'कोई संदेश नहीं',
        'compose_message': 'संदेश लिखें',
        'reply': 'जवाब दें',
        'available': 'उपलब्ध',
        'sold': 'बिक गया',
        'view_all': 'सभी देखें',
        'read_more': 'और पढ़ें'
    },
    'ar': {
        'welcome': 'مرحباً بعودتك',
        'welcome_message': 'مرحباً، {name}!',
        'dashboard': 'لوحة القيادة',
        'dashboard_subtitle': 'إدارة أنشطة مزرعتك',
        'marketplace': 'السوق',
        'forum': 'المنتدى',
        'messages': 'الرسائل',
        'profile': 'الملف الشخصي',
        'logout': 'تسجيل الخروج',
        'login': 'تسجيل الدخول',
        'signup': 'سجل',
        'products': 'المنتجات',
        'questions': 'الأسئلة',
        'settings': 'الإعدادات',
        'language': 'اللغة',
        'quick_actions': 'إجراءات سريعة',
        'recent_products': 'المنتجات الأخيرة',
        'your_recent_questions': 'أسئلتك الأخيرة',
        'add_product': 'إضافة منتج',
        'post_question': 'طرح سؤال',
        'browse_marketplace': 'تصفح السوق',
        'products_listed': 'المنتجات المدرجة',
        'questions_asked': 'الأسئلة المطروحة',
        'pending_offers': 'العروض المعلقة',
        'no_products': 'لا توجد منتجات بعد.',
        'no_questions': 'لا توجد أسئلة بعد.',
        'solved': 'تم الحل',
        'pending': 'معلق',
        'seeds': 'البذور',
        'animals': 'الحيوانات',
        'all': 'الكل',
        'search': 'بحث',
        'make_offer': 'تقديم عرض',
        'send_message': 'إرسال رسالة',
        'answers': 'الإجابات',
        'no_answers': 'لا توجد إجابات بعد',
        'post_answer': 'نشر إجابة',
        'upvote': 'تصويت',
        'mark_solution': 'وضع علامة كحل',
        'edit_profile': 'تعديل الملف الشخصي',
        'my_products': 'منتجاتي',
        'my_questions': 'أسئلتي',
        'accept': 'قبول',
        'reject': 'رفض',
        'counter_offer': 'عرض مضاد',
        'inbox': 'صندوق الوارد',
        'sent': 'المرسلة',
        'no_messages': 'لا توجد رسائل',
        'compose_message': 'رسالة جديدة',
        'reply': 'رد',
        'available': 'متاح',
        'sold': 'مباع',
        'view_all': 'عرض الكل',
        'read_more': 'اقرأ المزيد'
    },
    'pt': {
        'welcome': 'Bem-vindo de volta',
        'welcome_message': 'Bem-vindo, {name}!',
        'dashboard': 'Painel',
        'dashboard_subtitle': 'Gerencie suas atividades agrícolas',
        'marketplace': 'Mercado',
        'forum': 'Fórum',
        'messages': 'Mensagens',
        'profile': 'Perfil',
        'logout': 'Sair',
        'login': 'Entrar',
        'signup': 'Cadastrar',
        'products': 'Produtos',
        'questions': 'Perguntas',
        'settings': 'Configurações',
        'language': 'Idioma',
        'quick_actions': 'Ações rápidas',
        'recent_products': 'Produtos recentes',
        'your_recent_questions': 'Suas perguntas recentes',
        'add_product': 'Adicionar produto',
        'post_question': 'Fazer pergunta',
        'browse_marketplace': 'Explorar mercado',
        'products_listed': 'Produtos listados',
        'questions_asked': 'Perguntas feitas',
        'pending_offers': 'Ofertas pendentes',
        'no_products': 'Nenhum produto ainda.',
        'no_questions': 'Nenhuma pergunta ainda.',
        'solved': 'Resolvido',
        'pending': 'Pendente',
        'seeds': 'Sementes',
        'animals': 'Animais',
        'all': 'Todos',
        'search': 'Pesquisar',
        'make_offer': 'Fazer oferta',
        'send_message': 'Enviar mensagem',
        'answers': 'Respostas',
        'no_answers': 'Nenhuma resposta ainda',
        'post_answer': 'Postar resposta',
        'upvote': 'Votar',
        'mark_solution': 'Marcar como solução',
        'edit_profile': 'Editar perfil',
        'my_products': 'Meus produtos',
        'my_questions': 'Minhas perguntas',
        'accept': 'Aceitar',
        'reject': 'Rejeitar',
        'counter_offer': 'Contra-oferta',
        'inbox': 'Caixa de entrada',
        'sent': 'Enviadas',
        'no_messages': 'Nenhuma mensagem',
        'compose_message': 'Escrever mensagem',
        'reply': 'Responder',
        'available': 'Disponível',
        'sold': 'Vendido',
        'view_all': 'Ver tudo',
        'read_more': 'Ler mais'
    }
}

@app.context_processor
def inject_translations():
    """Inject translations and language info into all templates."""
    lang = 'en'
    if current_user.is_authenticated and current_user.language:
        lang = current_user.language
    elif session.get('language'):
        lang = session['language']
    
    return dict(
        languages=LANGUAGES,
        current_language=lang,
        t=TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    )

@app.route('/change-language/<lang>')
def change_language(lang):
    """Change user language preference."""
    if lang in LANGUAGES:
        if current_user.is_authenticated:
            current_user.language = lang
            db.session.commit()
        else:
            session['language'] = lang
    
    # Redirect back to the previous page
    return redirect(request.referrer or url_for('dashboard'))

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Redirect to splash screen."""
    return redirect(url_for('splash'))

@app.route('/splash')
def splash():
    """Splash screen with animation."""
    return render_template('splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Login attempt - Email: {email}")  # Debug
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            print(f"User found: {user.email}, hash: {user.password_hash[:20]}...")  # Debug
            password_check = user.check_password(password)
            print(f"Password check result: {password_check}")  # Debug
        else:
            print("No user found with that email")  # Debug
        
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page with social options."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        location = request.form.get('location')
        farm_type = request.form.get('farm_type')
        
        # Handle avatar upload
        avatar_file = request.files.get('avatar')
        avatar_path = None
        if avatar_file and allowed_file(avatar_file.filename):
            avatar_path = save_uploaded_file(app, avatar_file, 'avatars')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('signup.html')
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            location=location,
            farm_type=farm_type,
            avatar=avatar_path if avatar_path else 'default-avatar.png',
            social_provider='local'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/social-signup/<provider>')
def social_signup(provider):
    """Social signup simulation."""
    if provider == 'google':
        flash('Google sign-up simulation - In production, OAuth would be implemented', 'info')
    elif provider == 'facebook':
        flash('Facebook sign-up simulation - In production, OAuth would be implemented', 'info')
    elif provider == 'twitter':
        flash('Twitter sign-up simulation - In production, OAuth would be implemented', 'info')
    
    return redirect(url_for('signup'))

@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    user_products = Product.query.filter_by(seller_id=current_user.id).all()
    user_questions = Question.query.filter_by(author_id=current_user.id).all()
    pending_offers = Offer.query.filter_by(seller_id=current_user.id, status='pending').all()
    
    stats = {
        'products_listed': len(user_products),
        'questions_asked': len(user_questions),
        'pending_offers': len(pending_offers)
    }
    
    return render_template('dashboard.html', stats=stats, products=user_products, questions=user_questions)

@app.route('/marketplace')
@login_required
def marketplace():
    """Marketplace page for browsing products."""
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    search = request.args.get('search')
    
    query = Product.query.filter_by(status='available')
    
    if category:
        query = query.filter_by(category=category)
    if subcategory:
        query = query.filter_by(subcategory=subcategory)
    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))
    
    products = query.order_by(Product.created_at.desc()).all()
    
    return render_template('marketplace.html', products=products)

@app.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    """Product detail page."""
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/create-product', methods=['GET', 'POST'])
@login_required
def create_product():
    """Create new product listing."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        unit = request.form.get('unit')
        
        # Handle product image upload
        product_image = request.files.get('product_image')
        image_url = None
        if product_image and allowed_file(product_image.filename):
            image_url = save_uploaded_file(app, product_image, 'products')
        
        product = Product(
            seller_id=current_user.id,
            title=title,
            description=description,
            category=category,
            subcategory=subcategory,
            price=price,
            quantity=quantity,
            unit=unit,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product listed successfully!', 'success')
        return redirect(url_for('marketplace'))
    
    return render_template('create_product.html')

@app.route('/make-offer/<int:product_id>', methods=['POST'])
@login_required
def make_offer(product_id):
    """Make an offer on a product."""
    product = Product.query.get_or_404(product_id)
    
    if product.seller_id == current_user.id:
        flash('You cannot make an offer on your own product', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    offer_price = float(request.form.get('offer_price'))
    message = request.form.get('message')
    
    offer = Offer(
        product_id=product_id,
        buyer_id=current_user.id,
        seller_id=product.seller_id,
        offer_price=offer_price,
        message=message
    )
    
    db.session.add(offer)
    db.session.commit()
    
    flash('Offer sent successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/respond-offer/<int:offer_id>', methods=['POST'])
@login_required
def respond_offer(offer_id):
    """Respond to an offer (accept/reject/counter)."""
    offer = Offer.query.get_or_404(offer_id)
    
    if offer.seller_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard'))
    
    action = request.form.get('action')
    
    if action == 'accept':
        offer.status = 'accepted'
        flash('Offer accepted!', 'success')
    elif action == 'reject':
        offer.status = 'rejected'
        flash('Offer rejected', 'info')
    elif action == 'counter':
        offer.counter_offer = float(request.form.get('counter_price'))
        offer.status = 'counter'
        flash('Counter offer sent!', 'success')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/forum')
@login_required
def forum():
    """Community forum page."""
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Question.query
    
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Question.title.ilike(f'%{search}%'))
    
    questions = query.order_by(Question.created_at.desc()).all()
    
    return render_template('forum.html', questions=questions)

@app.route('/question/<int:question_id>')
@login_required
def question_detail(question_id):
    """Question detail page with answers."""
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.upvotes.desc()).all()
    
    return render_template('question.html', question=question, answers=answers)

@app.route('/create-question', methods=['GET', 'POST'])
@login_required
def create_question():
    """Create new question."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        tags = request.form.get('tags')
        
        question = Question(
            author_id=current_user.id,
            title=title,
            description=description,
            category=category,
            tags=tags
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Question posted successfully!', 'success')
        return redirect(url_for('forum'))
    
    return render_template('create_question.html')

@app.route('/answer/<int:question_id>', methods=['POST'])
@login_required
def post_answer(question_id):
    """Post an answer to a question."""
    question = Question.query.get_or_404(question_id)
    content = request.form.get('content')
    
    answer = Answer(
        question_id=question_id,
        author_id=current_user.id,
        content=content
    )
    
    db.session.add(answer)
    db.session.commit()
    
    flash('Answer posted successfully!', 'success')
    return redirect(url_for('question_detail', question_id=question_id))

@app.route('/upvote-answer/<int:answer_id>')
@login_required
def upvote_answer(answer_id):
    """Upvote an answer."""
    answer = Answer.query.get_or_404(answer_id)
    answer.upvotes += 1
    
    db.session.commit()
    
    return redirect(url_for('question_detail', question_id=answer.question_id))

@app.route('/mark-solution/<int:answer_id>')
@login_required
def mark_solution(answer_id):
    """Mark an answer as the solution."""
    answer = Answer.query.get_or_404(answer_id)
    question = Question.query.get_or_404(answer.question_id)
    
    if question.author_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('question_detail', question_id=question.id))
    
    # Remove previous solution if any
    Answer.query.filter_by(question_id=question.id, is_solution=True).update({'is_solution': False})
    
    answer.is_solution = True
    question.solved = True
    
    db.session.commit()
    
    flash('Answer marked as solution!', 'success')
    return redirect(url_for('question_detail', question_id=question.id))

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    products = Product.query.filter_by(seller_id=current_user.id).all()
    questions = Question.query.filter_by(author_id=current_user.id).all()
    
    return render_template('profile.html', user=current_user, products=products, questions=questions)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.location = request.form.get('location')
        current_user.farm_type = request.form.get('farm_type')
        current_user.bio = request.form.get('bio')
        
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/messages')
@login_required
def messages():
    """Messages inbox."""
    received = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    return render_template('messages.html', received=received, sent=sent)

@app.route('/send-message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    """Send a message to another user."""
    content = request.form.get('content')
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    flash('Message sent!', 'success')
    return redirect(url_for('chat', friend_id=user_id))

@app.route('/search_users')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    users = []
    if q:
        users = User.query.filter(
            User.username.ilike(f'%{q}%'),
            User.id != current_user.id
        ).limit(20).all()
    return render_template('search_users.html', users=users, q=q)

@app.route('/chats')
@login_required
def chats():
    # Friends (accepted requests both ways)
    friends = db.session.query(User).join(FriendRequest, 
        (FriendRequest.sender_id == current_user.id) | (FriendRequest.receiver_id == current_user.id)
    ).filter(FriendRequest.status == 'accepted').distinct().filter(User.id != current_user.id).all()
    
    # Pending requests received
    requests = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    
    return render_template('chats.html', friends=friends, requests=requests)

@app.route('/chat/<int:friend_id>')
@login_required
def chat(friend_id):
    friend = User.query.get_or_404(friend_id)
    # Messages between current_user and friend
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == friend_id),
            db.and_(Message.sender_id == friend_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark as read
    Message.query.filter_by(receiver_id=current_user.id, sender_id=friend_id).update({'read': True})
    db.session.commit()
    
    return render_template('chat.html', friend=friend, messages=messages)

@app.route('/add_friend/<int:user_id>', methods=['POST'])
@login_required
def add_friend(user_id):
    if user_id == current_user.id:
        flash('Cannot add yourself', 'error')
        return redirect(request.referrer)
    
    existing = FriendRequest.query.filter(
        db.or_(
            db.and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == user_id),
            db.and_(FriendRequest.sender_id == user_id, FriendRequest.receiver_id == current_user.id)
        )
    ).first()
    
    if existing:
        flash('Friend request already exists', 'info')
    else:
        req = FriendRequest(sender_id=current_user.id, receiver_id=user_id)
        db.session.add(req)
        db.session.commit()
        flash('Friend request sent!', 'success')
    
    return redirect(request.referrer)

@app.route('/accept_request/<int:request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    req = FriendRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('chats'))
    
    req.status = 'accepted'
    db.session.commit()
    flash('Friend request accepted!', 'success')
    return redirect(url_for('chats'))

# ==================== TIKTOK-STYLE FEATURES ====================

@app.route('/feed')
@login_required
def feed():
    """TikTok-style video feed."""
    followed_ids = [f.following_id for f in Follow.query.filter_by(follower_id=current_user.id).all()]
    followed_ids.append(current_user.id)
    
    posts = Post.query.filter(
        Post.is_active == True,
        Post.user_id.in_(followed_ids)
    ).order_by(Post.created_at.desc()).limit(20).all()
    
    if not posts:
        posts = Post.query.filter_by(is_active=True).order_by(Post.created_at.desc()).limit(20).all()
    
    return render_template('feed.html', posts=posts)

@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post/story."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        media_file = request.files.get('media')
        media_url = None
        media_type = 'image'
        
        if media_file and allowed_file(media_file.filename):
            media_url = save_uploaded_file(app, media_file, 'posts')
            if media_file.filename.lower().endswith(('.mp4', '.webm', '.mov')):
                media_type = 'video'
        
        post = Post(
            user_id=current_user.id,
            title=title,
            description=description,
            media_url=media_url,
            media_type=media_type
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('feed'))
    
    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    """View single post with comments."""
    post = Post.query.get_or_404(post_id)
    post.views_count += 1
    db.session.commit()
    
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.desc()).all()
    user_liked = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first() is not None
    gifts = PostGift.query.filter_by(post_id=post_id).order_by(PostGift.created_at.desc()).all()
    available_gifts = Gift.query.filter_by(is_active=True).all()
    
    return render_template('post_detail.html', post=post, comments=comments, user_liked=user_liked, gifts=gifts, available_gifts=available_gifts)

@app.route('/like-post/<int:post_id>')
@login_required
def like_post(post_id):
    """Like or unlike a post."""
    post = Post.query.get_or_404(post_id)
    
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        flash('Post unliked', 'info')
    else:
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        post.likes_count += 1
        flash('Post liked!', 'success')
    
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/like-comment/<int:comment_id>')
@login_required
def like_comment(comment_id):
    """Like or unlike a comment."""
    comment = PostComment.query.get_or_404(comment_id)
    post_id = comment.post_id
    
    existing_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=current_user.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        comment.likes_count = max(0, comment.likes_count - 1)
        flash('Comment unliked', 'info')
    else:
        like = CommentLike(comment_id=comment_id, user_id=current_user.id)
        db.session.add(like)
        comment.likes_count += 1
        flash('Comment liked!', 'success')
    
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/comment-post/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    """Post a comment on a post."""
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if content.strip():
        comment = PostComment(post_id=post_id, user_id=current_user.id, content=content)
        db.session.add(comment)
        post.comments_count += 1
        db.session.commit()
        flash('Comment posted!', 'success')
    
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/follow/<int:user_id>')
@login_required
def follow_user(user_id):
    """Follow or unfollow a user."""
    if user_id == current_user.id:
        flash('You cannot follow yourself', 'error')
        return redirect(request.referrer or url_for('dashboard'))
    
    existing_follow = Follow.query.filter_by(follower_id=current_user.id, following_id=user_id).first()
    
    if existing_follow:
        db.session.delete(existing_follow)
        flash('User unfollowed', 'info')
    else:
        follow = Follow(follower_id=current_user.id, following_id=user_id)
        db.session.add(follow)
        flash('You are now following this user!', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/user/<int:user_id>/profile')
@login_required
def user_profile(user_id):
    """View another user's profile."""
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id, is_active=True).order_by(Post.created_at.desc()).all()
    is_following = Follow.query.filter_by(follower_id=current_user.id, following_id=user_id).first() is not None
    followers_count = Follow.query.filter_by(following_id=user_id).count()
    following_count = Follow.query.filter_by(follower_id=user_id).count()
    
    return render_template('user_profile.html', user=user, posts=posts, is_following=is_following, followers_count=followers_count, following_count=following_count)

@app.route('/gift-post/<int:post_id>', methods=['POST'])
@login_required
def gift_post(post_id):
    """Send a gift to a post."""
    post = Post.query.get_or_404(post_id)
    gift_id = request.form.get('gift_id')
    quantity = int(request.form.get('quantity', 1))
    
    gift = Gift.query.get_or_404(gift_id)
    
    wallet = UserWallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = UserWallet(user_id=current_user.id, coins=100)
        db.session.add(wallet)
        db.session.commit()
    
    total_coins = gift.coin_value * quantity
    
    if wallet.coins < total_coins:
        flash('Not enough coins! Purchase more coins.', 'error')
        return redirect(url_for('post_detail', post_id=post_id))
    
    wallet.coins -= total_coins
    wallet.total_spent += gift.price * quantity
    
    post_gift = PostGift(post_id=post_id, sender_id=current_user.id, gift_id=gift_id, quantity=quantity, total_value=gift.price * quantity)
    db.session.add(post_gift)
    
    post.gifts_count += quantity
    
    post_owner_wallet = UserWallet.query.filter_by(user_id=post.user_id).first()
    if not post_owner_wallet:
        post_owner_wallet = UserWallet(user_id=post.user_id, coins=0)
        db.session.add(post_owner_wallet)
    
    post_owner_wallet.total_earned += gift.price * quantity
    
    db.session.commit()
    
    flash(f'You sent {quantity}x {gift.icon} to this post!', 'success')
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/wallet')
@login_required
def wallet():
    """View user wallet."""
    wallet = UserWallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = UserWallet(user_id=current_user.id, coins=100)
        db.session.add(wallet)
        db.session.commit()
    
    sent_gifts = PostGift.query.filter_by(sender_id=current_user.id).order_by(PostGift.created_at.desc()).limit(10).all()
    
    return render_template('wallet.html', wallet=wallet, sent_gifts=sent_gifts)

@app.route('/buy-coins', methods=['GET', 'POST'])
@login_required
def buy_coins():
    """Purchase more coins."""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 9.99))
        coins = int(amount * 10)
        
        wallet = UserWallet.query.filter_by(user_id=current_user.id).first()
        if not wallet:
            wallet = UserWallet(user_id=current_user.id, coins=0)
            db.session.add(wallet)
        
        wallet.coins += coins
        db.session.commit()
        
        flash(f'You purchased {coins} coins!', 'success')
        return redirect(url_for('wallet'))
    
    return render_template('buy_coins.html')

@app.route('/my-posts')
@login_required
def my_posts():
    """View user's own posts."""
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('my_posts.html', posts=posts)

@app.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a post."""
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard'))
    
    post.is_active = False
    db.session.commit()
    
    flash('Post deleted', 'success')
    return redirect(url_for('my_posts'))

# ==================== API ROUTES ====================

@app.route('/api/products')
@login_required
def api_products():
    """API endpoint for products."""
    products = Product.query.filter_by(status='available').all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'price': p.price,
        'category': p.category,
        'seller': p.seller.username
    } for p in products])

@app.route('/api/questions')
@login_required
def api_questions():
    """API endpoint for questions."""
    questions = Question.query.all()
    return jsonify([{
        'id': q.id,
        'title': q.title,
        'author': q.author.username,
        'solved': q.solved,
        'answers_count': len(q.answers)
    } for q in questions])

# ==================== ADMIN FEATURES ====================

def admin_required(f):
    """Decorator to require admin privileges."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('You do not have admin privileges.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with system overview."""
    total_users = User.query.count()
    total_products = Product.query.count()
    total_questions = Question.query.count()
    total_answers = Answer.query.count()
    total_offers = Offer.query.count()
    total_messages = Message.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(10).all()
    recent_questions = Question.query.order_by(Question.created_at.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_products': total_products,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'total_offers': total_offers,
        'total_messages': total_messages,
        'active_users': User.query.filter_by(is_active=True).count(),
        'inactive_users': User.query.filter_by(is_active=False).count(),
        'available_products': Product.query.filter_by(status='available').count(),
        'sold_products': Product.query.filter_by(status='sold').count(),
        'solved_questions': Question.query.filter_by(solved=True).count(),
        'pending_offers': Offer.query.filter_by(status='pending').count()
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_users=recent_users,
                         recent_products=recent_products,
                         recent_questions=recent_questions)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """View all users."""
    search = request.args.get('search')
    status = request.args.get('status')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    """View user details."""
    user = User.query.get_or_404(user_id)
    user_products = Product.query.filter_by(seller_id=user_id).all()
    user_questions = Question.query.filter_by(author_id=user_id).all()
    user_answers = Answer.query.filter_by(author_id=user_id).all()
    
    return render_template('admin/user_detail.html', 
                         user=user, 
                         products=user_products,
                         questions=user_questions,
                         answers=user_answers)

@app.route('/admin/user/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin_user_detail', user_id=user_id))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User account {status} successfully.', 'success')
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Reset user password (admin function)."""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin_user_detail', user_id=user_id))
    
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password for {user.username} has been reset.', 'success')
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete user account."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    Product.query.filter_by(seller_id=user_id).delete()
    Question.query.filter_by(author_id=user_id).delete()
    Answer.query.filter_by(author_id=user_id).delete()
    Offer.query.filter((Offer.buyer_id == user_id) | (Offer.seller_id == user_id)).delete()
    Message.query.filter((Message.sender_id == user_id) | (Message.receiver_id == user_id)).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """View all products."""
    search = request.args.get('search')
    category = request.args.get('category')
    status = request.args.get('status')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    
    products = query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    """Delete a product."""
    product = Product.query.get_or_404(product_id)
    
    Offer.query.filter_by(product_id=product_id).delete()
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/questions')
@login_required
@admin_required
def admin_questions():
    """View all questions."""
    search = request.args.get('search')
    category = request.args.get('category')
    solved = request.args.get('solved')
    
    query = Question.query
    
    if search:
        query = query.filter(Question.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if solved == 'yes':
        query = query.filter_by(solved=True)
    elif solved == 'no':
        query = query.filter_by(solved=False)
    
    questions = query.order_by(Question.created_at.desc()).all()
    return render_template('admin/questions.html', questions=questions)

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_question(question_id):
    """Delete a question and its answers."""
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin/offers')
@login_required
@admin_required
def admin_offers():
    """View all offers."""
    status = request.args.get('status')
    
    query = Offer.query
    
    if status:
        query = query.filter_by(status=status)
    
    offers = query.order_by(Offer.created_at.desc()).all()
    return render_template('admin/offers.html', offers=offers)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset."""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Password reset instructions have been sent to your email.', 'success')
        else:
            flash('No account found with that email address.', 'error')
    
    return render_template('forgot_password.html')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error=error), 500

# ==================== ADMIN CREATION ====================

@app.route('/create-admin')
def create_admin():
    """Create an admin user (for testing purposes)."""
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@farmerhub.com').first()
    if admin:
        admin.is_admin = True
        admin.is_active = True
        db.session.commit()
        return 'Admin already exists and has been updated!'
    
    # Create new admin user
    admin = User(
        username='admin',
        email='admin@farmerhub.com',
        full_name='System Admin',
        location='Headquarters',
        farm_type='admin',
        is_admin=True,
        is_active=True,
        social_provider='local'
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    return 'Admin created! Login with: admin@farmerhub.com / admin123'

# ==================== MAIN ====================

# Seed default gifts
def seed_gifts():
    gifts = [
        Gift(name='Rose', icon='🌹', price=0.99, coin_value=10),
        Gift(name='Tractor', icon='🚜', price=4.99, coin_value=50),
        Gift(name='Trophy', icon='🏆', price=9.99, coin_value=100),
        Gift(name='Crown', icon='👑', price=19.99, coin_value=200),
        Gift(name='Rocket', icon='🚀', price=49.99, coin_value=500),
    ]
    for gift in gifts:
        if not Gift.query.filter_by(name=gift.name).first():
            db.session.add(gift)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_gifts()
        print("Database ready with gifts!")
    app.run(debug=True)
