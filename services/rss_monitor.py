import feedparser
import requests
import trafilatura
import logging
from datetime import datetime, timedelta
from app import db
from models import Article
from config import RSS_FEEDS, USER_AGENT
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class RSSMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

    def fetch_new_articles(self):
        """Fetch new articles from RSS feeds"""
        new_articles = []

        for feed_type, feed_url in RSS_FEEDS.items():
            try:
                logger.info(f"Fetching {feed_type} feed from {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(f"Feed parsing warning for {feed_type}: {feed.bozo_exception}")

                for entry in feed.entries[:3]:  # Limit to 3 most recent per feed
                    if not self._article_exists(entry.link):
                        article_content = self._extract_content(entry.link)
                        featured_image_url = self._extract_featured_image(entry)
                        if article_content:
                            article = Article(
                                original_url=entry.link,
                                original_title=entry.title,
                                original_content=article_content,
                                feed_type=feed_type,
                                status='pending',
                                featured_image_url=featured_image_url
                            )
                            new_articles.append(article)
                            logger.info(f"New article found: {entry.title}")

            except Exception as e:
                logger.error(f"Error fetching {feed_type} feed: {str(e)}")

        # Save new articles individually to handle duplicates gracefully
        saved_count = 0
        for article in new_articles:
            try:
                db.session.add(article)
                db.session.commit()
                saved_count += 1
            except IntegrityError:
                db.session.rollback()
                logger.warning(f"Duplicate article skipped: {article.original_url}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving article: {article.original_url} - {str(e)}")

        logger.info(f"Saved {saved_count} new articles to database")
        return saved_count

    def _article_exists(self, url):
        """Check if article already exists in database"""
        return Article.query.filter_by(original_url=url).first() is not None

    def _extract_content(self, url):
        """Extract content from article URL"""
        try:
            downloaded = trafilatura.fetch_url(url)
            content = trafilatura.extract(downloaded)
            return content[:5000] if content else None  # Limit content length
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def _extract_featured_image(self, entry):
        """Extract featured image from RSS entry"""
        try:
            image_url = None

            # Method 1: Look for media:content or enclosure in RSS
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if 'image' in media.get('type', ''):
                        image_url = media.get('url')
                        break

            # Method 2: Look for enclosures
            if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
                for enclosure in entry.enclosures:
                    if 'image' in enclosure.get('type', ''):
                        image_url = enclosure.get('href')
                        break

            # Method 3: Look in summary for img tags
            if not image_url and hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag.get('src')

            # Clean and validate URL
            if image_url:
                # Make absolute URL if relative
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(entry.link)
                    image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

                # Validate image extensions
                valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                if any(ext in image_url.lower() for ext in valid_extensions):
                    logger.info(f"Found featured image: {image_url}")
                    return image_url

            return None

        except Exception as e:
            logger.error(f"Error extracting featured image: {str(e)}")
            return None

    def cleanup_old_articles(self):
        """Remove old processed articles to keep database clean"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            old_articles = Article.query.filter(
                Article.status.in_(['published', 'failed']),
                Article.created_at < cutoff_date
            ).all()

            for article in old_articles:
                db.session.delete(article)

            db.session.commit()
            logger.info(f"Cleaned up {len(old_articles)} old articles")

        except Exception as e:
            logger.error(f"Error cleaning up old articles: {str(e)}")
            db.session.rollback()
