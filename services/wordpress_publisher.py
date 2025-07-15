import json
import logging
import requests
from datetime import datetime
from app import db
from models import Article, ProcessingLog
from config import WORDPRESS_CONFIG, WORDPRESS_CATEGORIES

logger = logging.getLogger(__name__)

class WordPressPublisher:
    def __init__(self):
        base_url = WORDPRESS_CONFIG['url']
        # Ensure URL has proper WordPress API endpoint
        if not base_url.rstrip('/').endswith('wp-json/wp/v2'):
            base_url = base_url.rstrip('/') + '/wp-json/wp/v2'
        self.base_url = base_url.rstrip('/') + '/'
        self.auth = (WORDPRESS_CONFIG['user'], WORDPRESS_CONFIG['password'])

    def publish_processed_articles(self, max_articles=3):
        """Publish processed articles to WordPress"""
        processed_articles = Article.query.filter_by(status='processed').limit(max_articles).all()

        published_count = 0
        for article in processed_articles:
            try:
                article.status = 'publishing'
                db.session.commit()

                # Upload featured image if available
                featured_image_id = None
                if article.featured_image_url:
                    featured_image_id = self._upload_featured_image(
                        article.featured_image_url, 
                        article.titulo_final
                    )

                # Prepare post data
                post_data = {
                    'title': article.titulo_final,
                    'content': article.conteudo_final,
                    'status': 'publish',
                    'categories': self._get_categories_for_article(article),
                    'meta': {
                        'description': article.meta_description
                    }
                }

                # Add tags if available
                tags = self._prepare_tags(article.tags, article.obra_principal)
                if tags:
                    post_data['tags'] = self._create_or_get_tags(tags)

                if featured_image_id:
                    post_data['featured_media'] = featured_image_id

                # Publish post
                response = requests.post(
                    f"{self.base_url}posts",
                    json=post_data,
                    auth=self.auth,
                    timeout=30
                )

                if response.status_code == 201:
                    post_data_response = response.json()
                    article.wordpress_id = post_data_response['id']
                    article.wordpress_url = post_data_response['link']
                    article.status = 'published'
                    article.published_at = datetime.utcnow()

                    self._log_publishing(article.id, 'WORDPRESS_PUBLISH', 
                                       f'Successfully published to WordPress: {article.wordpress_url}', True)

                    published_count += 1
                    logger.info(f"Successfully published article: {article.titulo_final}")
                else:
                    raise Exception(f"WordPress API error: {response.status_code} - {response.text}")

                db.session.commit()

            except Exception as e:
                logger.error(f"Error publishing article {article.id}: {str(e)}")
                article.status = 'failed'
                article.error_message = str(e)
                self._log_publishing(article.id, 'WORDPRESS_PUBLISH', 
                                   f'Publishing failed: {str(e)}', False)
                db.session.commit()

        return published_count

    def _upload_featured_image(self, image_url, title):
        """Upload featured image to WordPress media library"""
        try:
            # Download image
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not return an image: {image_url}")
                return None
            
            # Determine file extension and mime type
            if 'png' in content_type:
                filename = 'featured_image.png'
                mime_type = 'image/png'
            elif 'webp' in content_type:
                filename = 'featured_image.webp'
                mime_type = 'image/webp'
            else:
                filename = 'featured_image.jpg'
                mime_type = 'image/jpeg'

            # Upload to WordPress
            files = {
                'file': (filename, response.content, mime_type)
            }
            data = {
                'title': f"Featured image for {title[:50]}",
                'alt_text': title[:100]
            }

            upload_response = requests.post(
                f"{self.base_url}media",
                files=files,
                data=data,
                auth=self.auth,
                timeout=30
            )

            if upload_response.status_code == 201:
                media_data = upload_response.json()
                logger.info(f"Successfully uploaded featured image with ID: {media_data['id']}")
                return media_data['id']
            else:
                logger.error(f"Failed to upload featured image: {upload_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error uploading featured image: {str(e)}")
            return None

    def _get_categories_for_article(self, article):
        """Get list of category IDs for article"""
        categories = [WORDPRESS_CATEGORIES['Notícias']]  # Default category

        # Add specific category based on feed type
        if article.feed_type == 'movies':
            categories.append(WORDPRESS_CATEGORIES['Filmes'])
        elif article.feed_type == 'tv-shows':
            categories.append(WORDPRESS_CATEGORIES['Séries'])

        # Add article's specific category if different
        if article.categoria in WORDPRESS_CATEGORIES:
            category_id = WORDPRESS_CATEGORIES[article.categoria]
            if category_id not in categories:
                categories.append(category_id)

        return list(set(categories))

    def _prepare_tags(self, tags_json, obra_principal):
        """Prepare tags for WordPress"""
        try:
            tags = json.loads(tags_json) if tags_json else []
            if obra_principal and obra_principal not in tags:
                tags.append(obra_principal)
            return tags
        except Exception:
            return [obra_principal] if obra_principal else []

    def _create_or_get_tags(self, tag_names):
        """Create or get tag IDs for given tag names"""
        tag_ids = []
        for tag_name in tag_names:
            try:
                # Check if tag exists
                response = requests.get(
                    f"{self.base_url}tags",
                    params={'search': tag_name},
                    auth=self.auth
                )
                
                if response.status_code == 200 and response.json():
                    tag_ids.append(response.json()[0]['id'])
                else:
                    # Create new tag
                    new_tag_response = requests.post(
                        f"{self.base_url}tags",
                        json={'name': tag_name},
                        auth=self.auth
                    )
                    if new_tag_response.status_code == 201:
                        tag_ids.append(new_tag_response.json()['id'])
            except Exception as e:
                logger.error(f"Error handling tag {tag_name}: {str(e)}")
        
        return tag_ids

    def _log_publishing(self, article_id, action, message, success):
        """Log publishing actions"""
        try:
            log = ProcessingLog(
                article_id=article_id,
                action=action,
                message=message,
                success=success
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging publishing action: {str(e)}")

    def test_connection(self):
        """Test WordPress connection"""
        try:
            # Test with a simple GET request to the posts endpoint
            response = requests.get(f"{self.base_url}posts", auth=self.auth, timeout=10)
            logger.info(f"WordPress connection test: {response.status_code} - {self.base_url}posts")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WordPress connection failed: {str(e)}")
            return False
