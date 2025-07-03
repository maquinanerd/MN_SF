from app import db
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(Integer, primary_key=True)
    original_url = db.Column(String(500), unique=True, nullable=False)
    original_title = db.Column(String(500), nullable=False)
    original_content = db.Column(Text, nullable=False)
    
    # AI processed content
    titulo_final = db.Column(String(500))
    conteudo_final = db.Column(Text)
    meta_description = db.Column(String(300))
    focus_keyword = db.Column(String(100))
    categoria = db.Column(String(100))
    obra_principal = db.Column(String(200))
    tags = db.Column(Text)  # JSON string
    
    # WordPress data
    wordpress_id = db.Column(Integer)
    wordpress_url = db.Column(String(500))
    
    # Featured image
    featured_image_url = db.Column(String(500))
    
    # Metadata
    feed_type = db.Column(String(50), nullable=False)
    status = db.Column(String(50), default='pending')  # pending, processing, processed, published, failed
    ai_used = db.Column(String(100))
    processing_time = db.Column(Integer)  # seconds
    error_message = db.Column(Text)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    processed_at = db.Column(DateTime)
    published_at = db.Column(DateTime)

    def __repr__(self):
        return f'<Article {self.id}: {self.original_title}>'

class ProcessingLog(db.Model):
    __tablename__ = 'processing_logs'
    
    id = db.Column(Integer, primary_key=True)
    article_id = db.Column(Integer, db.ForeignKey('articles.id'), nullable=True)
    action = db.Column(String(100), nullable=False)
    message = db.Column(Text)
    ai_used = db.Column(String(100))
    success = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProcessingLog {self.id}: {self.action}>'
