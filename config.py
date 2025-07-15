import os

# RSS Feeds Configuration
RSS_FEEDS = {
    'movies': 'https://comicbook.com/category/movies/feed/',
    'tv-shows': 'https://comicbook.com/category/tv-shows/feed/'
}

# User Agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# AI Configuration with multiple keys for fallback
AI_CONFIG = {
    'cinema': {
        'primary': os.getenv('GEMINI_API_KEY_MOVIE', ''),
        'backup': os.getenv('GEMINI_API_KEY_MOVIE_BACKUP', '')
    },
    'series': {
        'primary': os.getenv('GEMINI_API_KEY_TV', ''),
        'backup': os.getenv('GEMINI_API_KEY_TV_BACKUP', '')
    }
}

# WordPress Configuration
WORDPRESS_CONFIG = {
    'url': os.getenv('WORDPRESS_URL', 'https://www.maquinanerd.com.br/wp-json/wp/v2/'),
    'user': os.getenv('WORDPRESS_USER', 'Eduardo'),
    'password': os.getenv('WORDPRESS_PASSWORD', 'QhDY Ch9y kTsX fyhU 9iR2 CAVp')
}

# WordPress Categories
WORDPRESS_CATEGORIES = {
    'Notícias': 20,
    'Filmes': 24,
    'Séries': 21,
    'Cinema': 78,
    'DC Comics': 23,
    'Entretenimento': 74
}

# Schedule Configuration
SCHEDULE_CONFIG = {
    'check_interval': 15,  # minutes
    'max_articles_per_run': 5,  # aumentado para processar mais artigos
    'cleanup_after_hours': 12
}

# Universal Prompt for AI Processing
UNIVERSAL_PROMPT = """
Você é um redator especialista em cultura pop. Reescreva o seguinte artigo em português com SEO, parágrafos bem separados e otimize para o Google.

REGRAS:
1. Traduza o artigo original para o português, mantendo todos os detalhes e a estrutura.
2. Reescreva com pelo menos 5-7 parágrafos separados (com quebras duplas).
3. Crie um título otimizado para SEO.
4. Crie uma meta description de até 150 caracteres.
5. Destaque a palavra-chave principal.
6. Categorize o artigo como 'Filmes', 'Séries' ou 'Notícias'.
7. Identifique o nome do filme ou série principal abordado no artigo.
8. Se houver embeds de vídeos do YouTube ou publicações do Twitter, incorpore diretamente no local apropriado do conteúdo com o código embed real.
9. Mantenha a coerência e a naturalidade do texto, como em uma publicação profissional de jornalismo de entretenimento.

ARTIGO ORIGINAL:
Título: {titulo}
Conteúdo: {conteudo}

Responda APENAS em JSON:
{{
  "titulo_final": "...",
  "conteudo_final": "...",
  "meta_description": "...",
  "focus_keyword": "...",
  "categoria": "...",
  "obra_principal": "...",
  "tags": ["...", "...", "..."]
}}
"""
