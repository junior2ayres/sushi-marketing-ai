import os
import sys
# DON'T CHANGE THIS
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager
from src.models.auth import db, User
from src.routes.user import user_bp
from src.routes.campaign import campaign_bp
from src.routes.messaging import messaging_bp
from src.routes.social import social_bp
from src.routes.crm import crm_bp
from src.routes.auth import auth_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Habilitar CORS para todas as rotas
CORS(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configuração do banco de dados
if os.getenv('VERCEL'):
    # Para produção (Vercel) - usar PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    # Para desenvolvimento local (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(campaign_bp, url_prefix='/api')
app.register_blueprint(messaging_bp, url_prefix='/api')
app.register_blueprint(social_bp, url_prefix='/api')
app.register_blueprint(crm_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')

# Inicializar o banco de dados
db.init_app(app)

# Criar as tabelas
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
