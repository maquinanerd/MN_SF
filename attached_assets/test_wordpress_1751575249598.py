#!/usr/bin/env python3
"""
Teste direto da publicação WordPress
"""
import sys
import os
sys.path.append('.')

from app import app, db
from models import Article
from services.wordpress_publisher import WordPressPublisher

def test_wordpress_publishing():
    with app.app_context():
        # Buscar artigo processado para testar
        article = Article.query.filter_by(status='processed').first()
        
        if not article:
            print("Nenhum artigo processado encontrado!")
            return
        
        print(f"Testando publicação do artigo: {article.titulo_final}")
        
        # Criar publisher e testar
        publisher = WordPressPublisher()
        
        try:
            # Testar conexão primeiro
            result = publisher.test_connection()
            print(f"Teste de conexão WordPress: {result}")
            
            # Tentar publicar um artigo
            published = publisher.publish_processed_articles(max_articles=1)
            print(f"Artigos publicados: {published}")
            
            # Verificar se foi publicado
            db.session.refresh(article)
            print(f"Status do artigo após publicação: {article.status}")
            if article.wordpress_url:
                print(f"URL no WordPress: {article.wordpress_url}")
                
        except Exception as e:
            print(f"Erro ao testar publicação: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_wordpress_publishing()