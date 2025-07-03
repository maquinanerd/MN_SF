#!/usr/bin/env python3
import sys
sys.path.append('.')

from app import app, db
from models import Article
import requests
import json

def quick_publish_test():
    with app.app_context():
        # Buscar artigo específico
        article = Article.query.get(25)
        if not article:
            print("Artigo não encontrado!")
            return
            
        print(f"Artigo: {article.titulo_final}")
        print(f"Status atual: {article.status}")
        
        # Testar publicação simples
        wp_url = "https://maquinanerd.com.br/wp-json/wp/v2/"
        auth = ("Eduardo", "QhDY Ch9y kTsX fyhU 9iR2 CAVp")
        
        # Dados mínimos para teste
        post_data = {
            'title': article.titulo_final,
            'content': article.conteudo_final or "Conteúdo de teste",
            'status': 'publish',
            'categories': [24]  # Filmes
        }
        
        try:
            print("Tentando publicar...")
            response = requests.post(
                f"{wp_url}posts",
                json=post_data,
                auth=auth,
                timeout=30
            )
            
            print(f"Status da resposta: {response.status_code}")
            
            if response.status_code == 201:
                post_info = response.json()
                print(f"✓ Artigo publicado com sucesso!")
                print(f"URL: {post_info['link']}")
                
                # Atualizar banco de dados
                article.status = 'published'
                article.wordpress_url = post_info['link']
                article.wordpress_id = post_info['id']
                db.session.commit()
                
            else:
                print(f"✗ Erro na publicação: {response.text}")
                
        except Exception as e:
            print(f"✗ Erro: {e}")

if __name__ == "__main__":
    quick_publish_test()