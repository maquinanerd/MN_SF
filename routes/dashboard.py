from flask import Blueprint, render_template
from models import Article
from services.scheduler import get_scheduler
from services.ai_processor import AIProcessor
from services.wordpress_publisher import WordPressPublisher
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    """Main dashboard view"""
    # Get basic statistics
    total_articles = Article.query.count()
    pending_articles = Article.query.filter_by(status='pending').count()
    processing_articles = Article.query.filter_by(status='processing').count()
    processed_articles = Article.query.filter_by(status='processed').count()
    published_articles = Article.query.filter_by(status='published').count()
    failed_articles = Article.query.filter_by(status='failed').count()

    # Today's statistics
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    today_published = Article.query.filter(
        Article.published_at >= today_start
    ).count()

    # Recent articles
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(10).all()

    # Scheduler status
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_status() if scheduler else {'running': False}

    # AI status
    try:
        ai_processor = AIProcessor()
        ai_status = ai_processor.get_ai_status()
    except Exception:
        ai_status = {}

    # WordPress status
    try:
        wp_publisher = WordPressPublisher()
        wordpress_connected = wp_publisher.test_connection()
    except Exception:
        wordpress_connected = False

    return render_template('dashboard.html',
                         total_articles=total_articles,
                         pending_articles=pending_articles,
                         processing_articles=processing_articles,
                         processed_articles=processed_articles,
                         published_articles=published_articles,
                         failed_articles=failed_articles,
                         today_published=today_published,
                         recent_articles=recent_articles,
                         scheduler_status=scheduler_status,
                         ai_status=ai_status,
                         wordpress_connected=wordpress_connected)
