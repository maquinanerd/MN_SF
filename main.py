from app import app, db
from models import Article, ProcessingLog

# ⚠️ LIMPEZA DO BANCO DE DADOS (APAGAR ARTIGOS E LOGS)
with app.app_context():
    db.session.query(ProcessingLog).delete()
    db.session.query(Article).delete()
    db.session.commit()
    print(">>> Banco de dados resetado com sucesso.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
