import feedparser
import requests
import trafilatura
import logging
from datetime import datetime, timedelta
from app import db
from models import Article
from config import RSS_FEEDS, USER_AGENT
from bs4 import BeautifulSoup

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

        # Save new articles to database
        from sqlalchemy.exc import IntegrityError

        if new_articles:
            saved_count = 0
            for article in new_articles:
                try:
                    db.session.add(article)
                    db.session.commit()
                    saved_count += 1
                except IntegrityError:
                    db.session.rollback()
                    logger.warning(f"Artigo duplicado ignorado: {article.original_url}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Erro ao salvar artigo: {article.original_url} - {str(e)}")

            logger.info(f"Salvos {saved_count} artigos novos no banco")


        return len(new_articles)

    def _article_exists(self, url):
        """Check if article already exists in database"""
        return Article.query.filter_by(original_url=url).first() is not None

    def _extract_content(self, url):
        """Extract content from article URL"""
        try:
            headers = {
                'User-Agent': USER_AGENT
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove scripts and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Try to find main content
            content_selectors = [
                'article',
                '.entry-content',
                '.post-content',
                '.content',
                'main'
            ]

            content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break

            if not content:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)

            return content[:5000] if content else None  # Limit content length

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def _extract_featured_image(self, entry):
        """Extract featured image from RSS entry"""
        try:
            # Try different methods to find featured image
            image_url = None

            # Method 1: Look for media:content or enclosure in RSS
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if 'image' in media.get('type', ''):
                        image_url = media.get('url')
                        break

            # Method 2: Look for enclosures (common in RSS feeds)
            if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
                for enclosure in entry.enclosures:
                    if 'image' in enclosure.get('type', ''):
                        image_url = enclosure.get('href')
                        break

            # Method 3: Look in summary/description for img tags
            if not image_url and hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag.get('src')

            # Method 4: Look in content for img tags
            if not image_url and hasattr(entry, 'content') and entry.content:
                for content in entry.content:
                    soup = BeautifulSoup(content.value, 'html.parser')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        image_url = img_tag.get('src')
                        break

            # Clean and validate URL
            if image_url:
                # Make absolute URL if relative
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    # Extract domain from entry link
                    from urllib.parse import urlparse
                    parsed = urlparse(entry.link)
                    image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

                # Validate image extensions
                valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                if any(ext in image_url.lower() for ext in valid_extensions):
                    logger.info(f"Found featured image: {image_url}")
                    return image_url

            logger.debug(f"No featured image found for: {entry.title}")
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

    def _save_article(self, entry, feed_type):
        """Save article to database with duplicate checking"""
        try:
            # Check if article already exists by URL
            existing = Article.query.filter_by(original_url=entry.link).first()
            if existing:
                logger.debug(f"Article already exists in database: {entry.link}")
                return False

            # Check if similar article exists by title
            similar_title = Article.query.filter(
                Article.original_title.like(f"%{entry.title[:50]}%")
            ).first()
            if similar_title:
                logger.debug(f"Similar article found by title: {entry.title}")
                return False

            # Additional check using WordPress publisher
            from services.wordpress_publisher import WordPressPublisher
            wp_publisher = WordPressPublisher()
            if wp_publisher.check_if_post_exists(entry.title):
                logger.info(f"Article already exists in WordPress: {entry.title}")
                return False

            # Extract content and create article
            article_content = self._extract_content(entry.link)
            if article_content:
                article = Article(
                    original_url=entry.link,
                    original_title=entry.title,
                    original_content=article_content,
                    feed_type=feed_type,
                    status='pending'
                )
                db.session.add(article)
                db.session.commit()
                logger.info(f"New article saved: {entry.title}")
                return True
            else:
                logger.warning(f"Failed to extract content for: {entry.title}")
                return False

        except Exception as e:
            logger.error(f"Error checking for duplicate articles: {str(e)}")
            return False