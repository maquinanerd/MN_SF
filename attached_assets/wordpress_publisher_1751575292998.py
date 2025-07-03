import json
import logging
import requests
import base64
from datetime import datetime
from app import db
from models import Article, ProcessingLog
from config import WORDPRESS_CONFIG, WORDPRESS_CATEGORIES

logger = logging.getLogger(__name__)

class WordPressPublisher:
    def __init__(self):
        self.base_url = WORDPRESS_CONFIG['url']
        self.auth = (WORDPRESS_CONFIG['user'], WORDPRESS_CONFIG['password'])

    def publish_processed_articles(self, max_articles=5):
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
                    logger.info(f"📸 Processing featured image for article: {article.titulo_final}")
                    logger.info(f"📸 Featured image URL: {article.featured_image_url}")
                    featured_image_id = self._upload_featured_image(article.featured_image_url, article.titulo_final)
                    if featured_image_id:
                        logger.info(f"✅ Image uploaded successfully: ID {featured_image_id}")
                    else:
                        logger.warning(f"⚠️ Failed to upload featured image for: {article.titulo_final}")
                else:
                    logger.info(f"ℹ️ No featured image URL found for article: {article.titulo_final}")

                # Prepare post data
                post_data = {
                    'title': article.titulo_final,
                    'content': article.conteudo_final,
                    'status': 'publish',
                    'categories': self._get_categories_for_article(article)
                }

                # Add tags if available - WordPress expects tag names, not IDs
                tags = self._prepare_tags(article.tags, article.obra_principal)
                if tags:
                    # Convert tags to create new tags by name
                    post_data['tags'] = []
                    for tag_name in tags:
                        # Try to find existing tag first
                        tag_response = requests.get(
                            f"{self.base_url}tags?search={tag_name}",
                            auth=self.auth
                        )
                        if tag_response.status_code == 200 and tag_response.json():
                            # Use existing tag ID
                            post_data['tags'].append(tag_response.json()[0]['id'])
                        else:
                            # Create new tag
                            new_tag_response = requests.post(
                                f"{self.base_url}tags",
                                json={'name': tag_name},
                                auth=self.auth
                            )
                            if new_tag_response.status_code == 201:
                                post_data['tags'].append(new_tag_response.json()['id'])

                if featured_image_id:
                    post_data['featured_media'] = featured_image_id
                    logger.info(f"✅ Assigned featured_media: {featured_image_id} to post: {article.titulo_final}")
                else:
                    logger.info(f"ℹ️ No featured image to assign for post: {article.titulo_final}")

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

                    # Log with detailed info
                    if featured_image_id:
                        logger.info(f"✅ Post created successfully: ID {article.wordpress_id} with featured image {featured_image_id}")
                    else:
                        logger.info(f"✅ Post created successfully: ID {article.wordpress_id} (no featured image)")
                    
                    logger.info(f"✅ WordPress URL: {article.wordpress_url}")

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
        if not image_url:
            logger.debug("No featured image URL provided")
            return None
            
        try:
            logger.info(f"Attempting to upload featured image: {image_url}")
            
            # Download image with proper headers and follow redirects
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': image_url
            }
            
            response = requests.get(
                image_url, 
                timeout=30, 
                headers=headers,
                allow_redirects=True,
                stream=True
            )
            response.raise_for_status()
            
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not return an image (content-type: {content_type}): {image_url}")
                return None
            
            # Get file content
            image_content = response.content
            if len(image_content) == 0:
                logger.warning(f"Empty image content from: {image_url}")
                return None
            
            # Check minimum file size (avoid tiny placeholder images)
            if len(image_content) < 1024:  # Less than 1KB
                logger.warning(f"Image too small ({len(image_content)} bytes): {image_url}")
                return None

            # Determine file extension and mime type
            if 'png' in content_type:
                filename = 'featured_image.png'
                mime_type = 'image/png'
            elif 'webp' in content_type:
                filename = 'featured_image.webp'
                mime_type = 'image/webp'
            elif 'gif' in content_type:
                filename = 'featured_image.gif'
                mime_type = 'image/gif'
            else:
                filename = 'featured_image.jpg'
                mime_type = 'image/jpeg'

            # Prepare upload data
            files = {
                'file': (filename, image_content, mime_type)
            }
            data = {
                'title': f"Featured image for {title[:50]}",
                'alt_text': title[:100]
            }

            # Upload to WordPress
            upload_response = requests.post(
                f"{self.base_url}media",
                files=files,
                data=data,
                auth=self.auth,
                timeout=30
            )

            if upload_response.status_code == 201:
                media_data = upload_response.json()
                media_id = media_data['id']
                media_url = media_data.get('source_url', 'Unknown URL')
                logger.info(f"✅ Successfully uploaded featured image with ID: {media_id} - URL: {media_url}")
                return media_id
            else:
                logger.error(f"❌ Failed to upload featured image: {upload_response.status_code} - {upload_response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error downloading image from {image_url}: {str(e)}")
            logger.error(f"❌ Image download failed for article: {title}")
            return None
        except Exception as e:
            logger.error(f"❌ Error uploading featured image from {image_url}: {str(e)}")
            logger.error(f"❌ Image upload failed for article: {title}")
            return None

    def _get_category_id(self, categoria):
        """Get WordPress category ID"""
        return WORDPRESS_CATEGORIES.get(categoria, WORDPRESS_CATEGORIES['Notícias'])

    def _get_categories_for_article(self, article):
        """Get list of category IDs for article"""
        categories = []

        # Always include Notícias as default
        categories.append(WORDPRESS_CATEGORIES['Notícias'])

        # Add specific category based on feed type
        if article.feed_type == 'movies':
            if 'Cinema' in WORDPRESS_CATEGORIES:
                categories.append(WORDPRESS_CATEGORIES['Cinema'])
        elif article.feed_type == 'tv-shows':
            if 'Séries' in WORDPRESS_CATEGORIES:
                categories.append(WORDPRESS_CATEGORIES['Séries'])

        # Add article's specific category if different
        article_category_id = self._get_category_id(article.categoria)
        if article_category_id not in categories:
            categories.append(article_category_id)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(categories))

    def _prepare_tags(self, tags_json, obra_principal):
        """Prepare tags for WordPress"""
        try:
            tags = json.loads(tags_json) if tags_json else []
            if obra_principal and obra_principal not in tags:
                tags.append(obra_principal)
            return tags
        except Exception:
            return [obra_principal] if obra_principal else []

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

    def get_recent_posts_by_author(self, author_id=None, hours_back=24):
        """Get recent posts, optionally filtered by author"""
        from datetime import datetime, timedelta
        
        try:
            # Calculate date filter (last X hours)
            cutoff_date = datetime.utcnow() - timedelta(hours=hours_back)
            date_filter = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            params = {
                'per_page': 10,
                'after': date_filter,
                'orderby': 'date',
                'order': 'desc'
            }
            
            # Add author filter if specified
            if author_id:
                params['author'] = author_id
                
            response = requests.get(
                f"{self.base_url}posts",
                auth=self.auth,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                logger.info(f"Found {len(posts)} recent posts from WordPress")
                return posts
            else:
                logger.error(f"Error fetching WordPress posts: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching recent WordPress posts: {str(e)}")
            return []

    def check_if_post_exists(self, title_or_url):
        """Check if a post with similar title or URL already exists"""
        from app import db
        from models import Article
        
        try:
            # Check in our database first
            existing_article = Article.query.filter(
                (Article.titulo_final == title_or_url) | 
                (Article.original_url == title_or_url) |
                (Article.wordpress_url.like(f"%{title_or_url}%"))
            ).first()
            
            if existing_article:
                logger.info(f"Post already processed in our database: {title_or_url}")
                return True
                
            # Check WordPress directly with search
            response = requests.get(
                f"{self.base_url}posts",
                auth=self.auth,
                params={
                    'search': title_or_url[:50],  # WordPress search by title
                    'per_page': 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                if posts:
                    logger.info(f"Similar post found in WordPress: {title_or_url}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking if post exists: {str(e)}")
            return False

    def test_connection(self):
        """Test WordPress connection with improved logging"""
        try:
            response = requests.get(
                f"{self.base_url}posts",
                auth=self.auth,
                params={'per_page': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    logger.info(f"WordPress connection OK. Found {len(json_response)} posts")
                    return True
                except Exception as json_error:
                    logger.error(f"WordPress API JSON parsing error: {str(json_error)}")
                    return False
            else:
                logger.error(f"WordPress API returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"WordPress connection test failed: {str(e)}")
            return False