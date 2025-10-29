from flask import Flask
from flask_cors import CORS
from routes.inference_route import inference_bp
from routes.xgb_route import xgb_bp
from flasgger import Swagger
import os


def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', True)
    app.config['SWAGGER'] = {
        'title': 'Modelo de Predição - API',
        'uiversion': 3,
        'openapi': '3.0.2'
    }
    
    ## Allow CORS for all domains on all routes
    CORS(app, origins=["*"])
    Swagger(app)
    
    app.register_blueprint(inference_bp, url_prefix='/api')
    app.register_blueprint(xgb_bp, url_prefix='/api')
    
    # Rota de health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'API is running'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )
