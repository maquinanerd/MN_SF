import json
import logging
import time
import re
from datetime import datetime
from google import genai
from google.genai import types
from app import db
from models import Article, ProcessingLog
from config import AI_CONFIG, UNIVERSAL_PROMPT

logger = logging.getLogger(__name__)

class AIProcessor:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.clients = {}
            self._init_clients()
            AIProcessor._initialized = True

    def _init_clients(self):
        for ai_type, config in AI_CONFIG.items():
            if config['primary']:
                try:
                    self.clients[f"{ai_type}_primary"] = genai.Client(api_key=config['primary'])
                    logger.info(f"Initialized {ai_type} primary AI")
                except Exception as e:
                    logger.error(f"Failed to initialize {ai_type} primary AI: {str(e)}")
            if config['backup']:
                try:
                    self.clients[f"{ai_type}_backup"] = genai.Client(api_key=config['backup'])
                    logger.info(f"Initialized {ai_type} backup AI")
                except Exception as e:
                    logger.error(f"Failed to initialize {ai_type} backup AI: {str(e)}")

    def process_pending_articles(self, max_articles=5):
        pending_articles = Article.query.filter_by(status='pending').limit(max_articles).all()
        processed_count = 0

        for article in pending_articles:
            try:
                start_time = time.time()
                article.status = 'processing'
                db.session.commit()

                ai_type = 'cinema' if article.feed_type == 'movies' else 'series'
                result = self._process_with_ai(article, ai_type)

                if result:
                    article.titulo_final = re.sub(r'</?strong>', '', result.get('titulo_final', ''))
                    article.conteudo_final = self._correct_paragraphs(result.get('conteudo_final'))
                    article.meta_description = result.get('meta_description')
                    article.focus_keyword = result.get('focus_keyword')
                    article.categoria = result.get('categoria')
                    article.obra_principal = result.get('obra_principal')
                    article.tags = json.dumps(result.get('tags', []))
                    article.status = 'processed'
                    article.processed_at = datetime.utcnow()
                    article.processing_time = int(time.time() - start_time)

                    self._log_processing(article.id, 'AI_PROCESSING', 'Successfully processed article', 
                                         article.ai_used, True)

                    db.session.commit()
                    processed_count += 1
                    logger.info(f"Successfully processed article: {article.original_title}")
                else:
                    article.status = 'failed'
                    article.error_message = 'AI processing failed'
                    db.session.commit()
                    self._log_processing(article.id, 'AI_PROCESSING', 'AI processing failed', 
                                         article.ai_used, False)

            except Exception as e:
                logger.error(f"Error processing article {article.id}: {str(e)}")
                article.status = 'failed'
                article.error_message = str(e)
                db.session.rollback()

        return processed_count

    def _process_with_ai(self, article, ai_type):
        client_key = f"{ai_type}_primary"
        if client_key in self.clients:
            result = self._call_ai(self.clients[client_key], article, f"{ai_type}_primary")
            if result:
                article.ai_used = f"{ai_type}_primary"
                return result

        client_key = f"{ai_type}_backup"
        if client_key in self.clients:
            logger.warning(f"Primary {ai_type} AI failed, trying backup")
            result = self._call_ai(self.clients[client_key], article, f"{ai_type}_backup")
            if result:
                article.ai_used = f"{ai_type}_backup"
                return result

        logger.error(f"Both primary and backup {ai_type} AIs failed")
        return None

    def _call_ai(self, client, article, ai_name):
        try:
            prompt = UNIVERSAL_PROMPT.format(
                titulo=article.original_title,
                conteudo=article.original_content
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
                request_options={"timeout": 30}
            )

            if response.text:
                try:
                    result = json.loads(response.text)
                    required_fields = ['titulo_final', 'conteudo_final', 'meta_description', 
                                       'focus_keyword', 'categoria', 'obra_principal', 'tags']
                    if all(field in result for field in required_fields):
                        return result
                    else:
                        logger.error(f"Missing required fields in AI response from {ai_name}")
                        return None
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from {ai_name}: {str(e)}")
                    return None
            else:
                logger.error(f"Empty response from {ai_name}")
                return None

        except Exception as e:
            logger.error(f"AI call failed for {ai_name}: {str(e)}")
            return None

    def _correct_paragraphs(self, content):
        if not content:
            return content

        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 5:
            return content

        paragraphs = []
        for i in range(0, len(sentences), 3):
            paragraph = '. '.join(sentences[i:i+3])
            if not paragraph.endswith('.'):
                paragraph += '.'
            paragraphs.append(paragraph)

        return '\n\n'.join(paragraphs)

    def _log_processing(self, article_id, action, message, ai_used, success):
        try:
            log = ProcessingLog(
                article_id=article_id,
                action=action,
                message=message,
                ai_used=ai_used,
                success=success
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging processing action: {str(e)}")

    def get_ai_status(self):
        status = {}
        for ai_type in ['cinema', 'series']:
            status[ai_type] = {
                'primary_available': f"{ai_type}_primary" in self.clients,
                'backup_available': f"{ai_type}_backup" in self.clients,
                'last_used': self._get_last_used_time(ai_type)
            }
        return status

    def _get_last_used_time(self, ai_type):
        last_log = ProcessingLog.query.filter(
            ProcessingLog.ai_used.like(f"{ai_type}%")
        ).order_by(ProcessingLog.created_at.desc()).first()

        return last_log.created_at.isoformat() if last_log else None
