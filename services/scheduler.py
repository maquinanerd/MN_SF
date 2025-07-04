import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.rss_monitor import RSSMonitor
from services.ai_processor import AIProcessor
from services.wordpress_publisher import WordPressPublisher
from config import SCHEDULE_CONFIG

logger = logging.getLogger(__name__)

class ContentAutomationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.rss_monitor = RSSMonitor()
        self.ai_processor = AIProcessor()
        self.wordpress_publisher = WordPressPublisher()
        self.is_running = False

    def start(self):
        """Start the automation scheduler"""
        if not self.is_running:
            # Schedule main automation cycle
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
                trigger=IntervalTrigger(hours=SCHEDULE_CONFIG['cleanup_after_hours']),
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
        """Main automation cycle"""
        from app import app
        
        with app.app_context():
            try:
                logger.info("=== Starting automation cycle ===")

                # Step 1: Fetch new articles from RSS feeds
                logger.info("Step 1: Fetching new articles...")
                new_articles = self.rss_monitor.fetch_new_articles()
                logger.info(f"Found {new_articles} new articles")

                # Step 2: Process pending articles with AI
                logger.info("Step 2: Processing articles with AI...")
                processed = self.ai_processor.process_pending_articles(
                    max_articles=SCHEDULE_CONFIG['max_articles_per_run']
                )
                logger.info(f"Processed {processed} articles")

                # Step 3: Publish processed articles to WordPress
                logger.info("Step 3: Publishing to WordPress...")
                published = self.wordpress_publisher.publish_processed_articles(
                    max_articles=SCHEDULE_CONFIG['max_articles_per_run']
                )
                logger.info(f"Published {published} articles")

                logger.info(f"=== Cycle completed: {new_articles} new, {processed} processed, {published} published ===")

            except Exception as e:
                logger.error(f"Error in automation cycle: {str(e)}", exc_info=True)

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
