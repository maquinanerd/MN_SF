import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app
from services.rss_monitor import RSSMonitor
from services.ai_processor import AIProcessor
from services.wordpress_publisher import WordPressPublisher
from config import SCHEDULE_CONFIG

logger = logging.getLogger(__name__)

class ContentAutomationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.rss_monitor = RSSMonitor()
        # Initialize AI processor once during scheduler creation
        self.ai_processor = AIProcessor()
        self.wordpress_publisher = WordPressPublisher()
        self.is_running = False

    def start(self):
        """Start the automation scheduler"""
        if not self.is_running:
            # Schedule RSS monitoring and processing
            self.scheduler.add_job(
                func=self.automation_cycle,
                trigger=IntervalTrigger(minutes=SCHEDULE_CONFIG['check_interval']),
                id='automation_cycle',
                name='Content Automation Cycle',
                replace_existing=True
            )

            # Schedule cleanup
            self.scheduler.add_job(
                func=self.cleanup_cycle,
                trigger=IntervalTrigger(hours=6),
                id='cleanup_cycle',
                name='Database Cleanup',
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("Content automation scheduler started")

    def stop(self):
        """Stop the automation scheduler"""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Content automation scheduler stopped")

    def automation_cycle(self):
        """Main automation cycle with improved duplicate control"""
        import time
        from app import app

        with app.app_context():
            try:
                logger.info("=== Starting automation cycle ===")

                # Check WordPress connection first
                if not self.wordpress_publisher.test_connection():
                    logger.error("WordPress connection failed - skipping cycle")
                    return

                # Step 1: Fetch new articles from RSS feeds
                logger.info("Step 1: Fetching new articles from RSS feeds...")
                try:
                    new_articles = self.rss_monitor.fetch_new_articles()
                    if new_articles > 0:
                        logger.info(f"✅ Found {new_articles} new articles")
                    else:
                        logger.info("ℹ️ No new articles found")
                except Exception as e:
                    logger.error(f"❌ Error fetching RSS articles: {str(e)}")
                    new_articles = 0

                # Add small delay between steps
                time.sleep(2)

                # Step 2: Process pending articles with AI
                logger.info("Step 2: Processing pending articles with AI...")
                try:
                    from models import Article
                    pending_articles = (
                        Article.query.filter_by(status='pending')
                        .order_by(Article.created_at.asc())
                        .limit(SCHEDULE_CONFIG['max_articles_per_run'])
                        .all()
                    )

                    processed = 0
                    for article in pending_articles:
                        try:
                            logger.info(f"🔍 Processando artigo: {article.title}")
                            result = self.ai_processor.process_article(article)

                            article.status = 'processed'
                            article.processed_content = result["content"]
                            article.processed_title = result["title"]
                            article.processed_meta = result.get("meta", "")
                            article.category = result.get("category", "")
                            article.tags = result.get("tags", [])
                            article.thumbnail_url = result.get("image_url", "")

                            from app import db
                            db.session.commit()
                            processed += 1
                            time.sleep(1)

                        except Exception as e:
                            logger.error(f"❌ Erro ao processar artigo '{article.title}': {str(e)}")

                    if processed > 0:
                        logger.info(f"✅ Processed {processed} articles with AI")
                    else:
                        logger.info("ℹ️ No articles to process")
                except Exception as e:
                    logger.error(f"❌ Error processing articles with AI: {str(e)}")
                    processed = 0

                # Add small delay between steps
                time.sleep(2)

                # Step 3: Publish processed articles to WordPress
                logger.info("Step 3: Publishing processed articles to WordPress...")
                try:
                    from models import Article
                    processed_count = Article.query.filter_by(status='processed').count()
                    logger.info(f"📄 Found {processed_count} processed articles ready for publishing")

                    published = self.wordpress_publisher.publish_processed_articles(
                        max_articles=SCHEDULE_CONFIG['max_articles_per_run']
                    )
                    if published > 0:
                        logger.info(f"✅ Published {published} articles to WordPress")
                    else:
                        logger.info("ℹ️ No articles to publish")
                except Exception as e:
                    logger.error(f"❌ Error publishing articles to WordPress: {str(e)}")
                    published = 0

                logger.info(f"=== Automation cycle completed: {new_articles} new, {processed} processed, {published} published ===")

                if new_articles == 0 and processed == 0 and published == 0:
                    logger.debug("No activity in this cycle - system is idle")

            except Exception as e:
                logger.error(f"❌ Error in automation cycle: {str(e)}", exc_info=True)

    def cleanup_cycle(self):
        """Database cleanup cycle"""
        from app import app

        with app.app_context():
            try:
                logger.info("Starting cleanup cycle")
                self.rss_monitor.cleanup_old_articles()
                logger.info("Cleanup cycle completed")
            except Exception as e:
                logger.error(f"Error in cleanup cycle: {str(e)}")

    def execute_now(self):
        """Execute automation cycle immediately"""
        from app import app

        logger.info("Manual execution triggered")
        with app.app_context():
            self.automation_cycle()

    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }

# Global scheduler instance
scheduler_instance = None

def init_scheduler():
    """Initialize global scheduler"""
    global scheduler_instance
    scheduler_instance = ContentAutomationScheduler()
    scheduler_instance.start()
    return scheduler_instance

def get_scheduler():
    """Get global scheduler instance"""
    return scheduler_instance
