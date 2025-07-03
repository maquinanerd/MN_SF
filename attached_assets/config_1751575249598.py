import os

# RSS Feeds Configuration
RSS_FEEDS = {
    'movies': 'https://comicbook.com/category/movies/feed/',
    'tv-shows': 'https://comicbook.com/category/tv-shows/feed/'
}

# AI Configuration - Sistema v2 Simplificado
AI_CONFIG = {
    'cinema': {
        'primary': os.environ.get('GEMINI_CINEMA') or 'AIzaSyBCSxUj2ydpaQPNBcl0QPiApNW2Xlh2wXk',
        'backup': os.environ.get('GEMINI_CINEMA_BACKUP') or 'AIzaSyAgDoanev71yGQOXvjesHLKfEqazJOv87w'
    },
    'series': {
        'primary': os.environ.get('GEMINI_SERIES') or 'AIzaSyDlvzqi5kmoC9IRgrqywX52YYMPCIplWhs', 
        'backup': os.environ.get('GEMINI_SERIES_BACKUP') or 'AIzaSyBCSxUj2ydpaQPNBcl0QPiApNW2Xlh2wXk'
    }
}

# WordPress Configuration
WORDPRESS_CONFIG = {
    'url': os.environ.get('WORDPRESS_URL') or 'https://maquinanerd.com.br/wp-json/wp/v2/',
    'user': os.environ.get('WORDPRESS_USER') or 'Eduardo',
    'password': os.environ.get('WORDPRESS_PASSWORD') or 'QhDY Ch9y kTsX fyhU 9iR2 CAVp'
}

# Category mapping for WordPress
WORDPRESS_CATEGORIES = {
    'Filmes': 24,
    'Séries': 21,
    'Notícias': 20
}

# Universal prompt for both AIs
UNIVERSAL_PROMPT = """Você é um redator especialista em cultura pop. Reescreva o seguinte artigo em português com SEO, parágrafos bem separados e otimize para o Google.

REGRAS:
1. Traduza o artigo original para o português, mantendo todos os detalhes e a estrutura.
2. Reescreva com pelo menos 5-7 parágrafos separados (com quebras duplas).
3. Crie um título otimizado para SEO.
4. Crie uma meta description de até 150 caracteres.
5. Destaque a palavra-chave principal.
6. Categorize o artigo como 'Filmes', 'Séries' ou 'Notícias'.
7. Identifique o nome do filme ou série principal abordado no artigo.
8. Se houver embeds de vídeos do YouTube ou publicações do Twitter, incorpore diretamente no local apropriado do conteúdo com o código embed real.
9. Use <strong></strong> em vez de ** para destacar texto.
10. Mantenha a coerência e a naturalidade do texto, como em uma publicação profissional de jornalismo de entretenimento.

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
}}"""

# Scheduling Configuration
SCHEDULE_CONFIG = {
    'check_interval': 15,  # minutes - aumentado para evitar sobrecarga
    'max_articles_per_run': 2,  # reduzido para processamento mais suave
    'cleanup_after_hours': 12  # limpeza mais frequente
}

# User Agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"