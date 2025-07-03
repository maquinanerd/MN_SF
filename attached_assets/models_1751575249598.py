from datetime import datetime
from app import db
from sqlalchemy import Integer, String, Text, DateTime, Boolean

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(Integer, primary_key=True)
    original_url = db.Column(String(500), unique=True, nullable=False, index=True)
    original_title = db.Column(String(500), nullable=False, index=True)
    original_content = db.Column(Text, nullable=False)
    feed_type = db.Column(String(50), nullable=False, index=True)  # 'movies' or 'tv-shows'
    
    # Processed content
    titulo_final = db.Column(String(500))
    conteudo_final = db.Column(Text)
    meta_description = db.Column(String(300))
    focus_keyword = db.Column(String(100))
    categoria = db.Column(String(100))
    obra_principal = db.Column(String(200))
    tags = db.Column(Text)  # JSON string
    
    # WordPress data
    wordpress_id = db.Column(Integer, unique=True, index=True)
    wordpress_url = db.Column(String(500), index=True)
    featured_image_url = db.Column(String(500))
    
    # Status tracking
    status = db.Column(String(50), default='pending', index=True)  # pending, processing, published, failed
    ai_used = db.Column(String(50))  # cinema, cinema_backup, series, series_backup
    processing_time = db.Column(Integer)  # seconds
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    processed_at = db.Column(DateTime)
    published_at = db.Column(DateTime)
    
    # Error handling
    error_message = db.Column(Text)
    retry_count = db.Column(Integer, default=0)

class ProcessingLog(db.Model):
    __tablename__ = 'processing_logs'
    
    id = db.Column(Integer, primary_key=True)
    article_id = db.Column(Integer, db.ForeignKey('articles.id'), nullable=False)
    action = db.Column(String(100), nullable=False)
    message = db.Column(Text)
    ai_used = db.Column(String(50))
    success = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    article = db.relationship('Article', backref='logs')

class SystemStats(db.Model):
    __tablename__ = 'system_stats'
    
    id = db.Column(Integer, primary_key=True)
    date = db.Column(DateTime, default=datetime.utcnow)
    articles_processed = db.Column(Integer, default=0)
    articles_published = db.Column(Integer, default=0)
    articles_failed = db.Column(Integer, default=0)
    cinema_requests = db.Column(Integer, default=0)
    series_requests = db.Column(Integer, default=0)
    avg_processing_time = db.Column(Integer, default=0)
