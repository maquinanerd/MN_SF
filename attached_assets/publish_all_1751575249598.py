#!/usr/bin/env python3
import sys
sys.path.append('.')

from app import app, db
from models import Article
import requests
from datetime import datetime

def publish_all_processed():
    with app.app_context():
        # Buscar todos os artigos processados
        articles = Article.query.filter_by(status='processed').all()
        
        if not articles:
            print("Nenhum artigo processado encontrado!")
            return
            
        print(f"Encontrados {len(articles)} artigos para publicar")
        
        # Configuração WordPress
        wp_url = "https://maquinanerd.com.br/wp-json/wp/v2/"
        auth = ("Eduardo", "QhDY Ch9y kTsX fyhU 9iR2 CAVp")
        
        published_count = 0
        
        for article in articles:
            try:
                print(f"\nPublicando: {article.titulo_final}")
                
                # Dados para publicação
                post_data = {
                    'title': article.titulo_final,
                    'content': article.conteudo_final or "Conteúdo processado automaticamente",
                    'status': 'publish',
                    'categories': [24]  # Categoria Filmes
                }
                
                # Publicar
                response = requests.post(
                    f"{wp_url}posts",
                    json=post_data,
                    auth=auth,
                    timeout=30
                )
                
                if response.status_code == 201:
                    post_info = response.json()
                    print(f"✓ Publicado: {post_info['link']}")
                    
                    # Atualizar banco
                    article.status = 'published'
                    article.wordpress_url = post_info['link']
                    article.wordpress_id = post_info['id']
                    article.published_at = datetime.utcnow()
                    
                    published_count += 1
                    
                else:
                    print(f"✗ Erro {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"✗ Erro ao publicar artigo {article.id}: {e}")
        
        # Salvar todas as mudanças
        db.session.commit()
        print(f"\n🎉 Total publicado: {published_count} artigos")

if __name__ == "__main__":
    publish_all_processed()