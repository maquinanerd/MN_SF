import json
from flask import Blueprint, request, jsonify
from services.scheduler import get_scheduler
from services.wordpress_publisher import WordPressPublisher
from services.ai_processor import AIProcessor
from models import Article, ProcessingLog
from app import db
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/stats')
def get_stats():
    """Get system statistics"""
    try:
        from models import Article
        from datetime import datetime, timedelta

        total_articles = Article.query.count()
        pending_articles = Article.query.filter_by(status='pending').count()
        processing_articles = Article.query.filter_by(status='processing').count()
        published_articles = Article.query.filter_by(status='published').count()

        # Today's stats
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_published = Article.query.filter(
            Article.published_at >= today_start
        ).count()

        return jsonify({
            'total_articles': total_articles,
            'pending_articles': pending_articles,
            'processing_articles': processing_articles,
            'published_articles': published_articles,
            'today_published': today_published
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/ai-status')
def get_ai_status():
    """Get AI systems status"""
    try:
        ai_processor = AIProcessor()
        status = ai_processor.get_ai_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/scheduler-status')
def get_scheduler_status():
    """Get scheduler status"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            return jsonify(scheduler.get_status())
        else:
            return jsonify({'running': False, 'jobs': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/recent-articles')
def get_recent_articles():
    """Get recent articles"""
    try:
        limit = request.args.get('limit', 10, type=int)
        articles = Article.query.order_by(Article.created_at.desc()).limit(limit).all()

        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.titulo_final or article.original_title,
                'status': article.status,
                'feed_type': article.feed_type,
                'created_at': article.created_at.isoformat(),
                'processed_at': article.processed_at.isoformat() if article.processed_at else None,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'wordpress_url': article.wordpress_url,
                'ai_used': article.ai_used,
                'processing_time': article.processing_time,
                'error_message': article.error_message
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/recent-logs')
def get_recent_logs():
    """Get recent processing logs"""
    try:
        limit = request.args.get('limit', 20, type=int)
        logs = ProcessingLog.query.order_by(ProcessingLog.created_at.desc()).limit(limit).all()

        result = []
        for log in logs:
            result.append({
                'id': log.id,
                'article_id': log.article_id,
                'action': log.action,
                'message': log.message,
                'ai_used': log.ai_used,
                'success': log.success,
                'created_at': log.created_at.isoformat()
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/execute-now', methods=['POST'])
def execute_now():
    """Execute automation cycle immediately"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            scheduler.execute_now()
            return jsonify({'message': 'Automation cycle executed successfully'})
        else:
            logger.error('Scheduler not available for manual execution')
            return jsonify({'error': 'Scheduler not available'}), 500
    except Exception as e:
        logger.error(f"Error executing automation cycle: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/pause-automation', methods=['POST'])
def pause_automation():
    """Pause automation"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            scheduler.stop()
            return jsonify({'message': 'Automation paused'})
        else:
            return jsonify({'error': 'Scheduler not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/resume-automation', methods=['POST'])
def resume_automation():
    """Resume automation"""
    try:
        scheduler = get_scheduler()
        if scheduler:
            scheduler.start()
            return jsonify({'message': 'Automation resumed'})
        else:
            return jsonify({'error': 'Scheduler not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/wordpress-test')
def test_wordpress():
    """Test WordPress connection"""
    try:
        wp_publisher = WordPressPublisher()
        connected = wp_publisher.test_connection()
        return jsonify({'connected': connected})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/wordpress-status')
def get_wordpress_status():
    """Get WordPress connection status"""
    try:
        from services.scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler and scheduler.wordpress_publisher:
            return jsonify({'connected': scheduler.wordpress_publisher.test_connection()})
        else:
            # Fallback if scheduler not available
            publisher = WordPressPublisher()
            return jsonify({'connected': publisher.test_connection()})
    except Exception as e:
        logger.error(f"Error getting WordPress status: {str(e)}")
        return jsonify({'error': str(e)}), 500