import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configuração do log
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Definição da classe Base para mapeamento de modelos
class Base(DeclarativeBase):
    pass

# Inicialização do banco de dados
db = SQLAlchemy(model_class=Base)

# Criação da aplicação Flask
app = Flask(__name__)

# Definindo a chave secreta para a sessão (em produção, altere para um valor seguro)
app.secret_key = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")

# Aplicando middleware para lidar com proxies reversos (para servidores em produção)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuração do banco de dados (substituindo com as credenciais fornecidas)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://mn_filme_serie_db_user:3N5o6A3gNnDSEojgOBHP61q9BDvd8xFk@dpg-d1mk3sumcj7s7399t1dg-a/mn_filme_serie_db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Tempo para reciclar conexões inativas
    "pool_pre_ping": True,  # Verifica a conexão antes de usar
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Desabilita notificações de modificações de objetos

# Inicializa a extensão do banco de dados com a aplicação Flask
db.init_app(app)

# Importando os blueprints das rotas
from routes.dashboard import dashboard_bp
from routes.api import api_bp

# Registrando os blueprints na aplicação Flask
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Contexto de aplicação para criar as tabelas no banco
with app.app_context():
    # Importando os modelos para criação das tabelas
    import models
    db.create_all()  # Cria todas as tabelas definidas nos modelos

    # Inicializando o agendador de tarefas (como o Celery ou similar)
    from services.scheduler import init_scheduler
    init_scheduler()

    # Log de sucesso na inicialização
    logger.info("Content Automation System initialized successfully")
