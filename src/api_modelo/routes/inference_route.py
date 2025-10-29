from flask import Blueprint, request, jsonify
import logging
from model_utils import fcm_predictor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar blueprint
inference_bp = Blueprint('inference', __name__)

@inference_bp.route('/predict', methods=['POST'])
def predict():
    """
    FCM - Predict
    ---
    tags:
      - FCM
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            data:
              type: object
              additionalProperties:
                type: number
          required:
            - data
    responses:
      200:
        description: Predição realizada com sucesso
      400:
        description: Erro de validação dos dados
      503:
        description: Modelo indisponível
      500:
        description: Erro interno
    """
    try:
        if not request.json:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request must contain JSON data'
            }), 400
        
        data = request.json
        logger.info("Received prediction request")
        
        if not fcm_predictor.is_loaded:
            logger.warning("Model not loaded, attempting to load...")
            if not fcm_predictor.load_model():
                return jsonify({
                    'error': 'Model not available',
                    'message': 'FCM model could not be loaded'
                }), 503
        
        # Fazer predição usando o modelo FCM
        result = fcm_predictor.predict(data)
        
        logger.info(f"Prediction successful: cluster {result['prediction']['cluster']} with confidence {result['prediction']['confidence']:.4f}")
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Invalid input data',
            'message': str(e)
        }), 400
        
    except RuntimeError as e:
        logger.error(f"Runtime error: {str(e)}")
        return jsonify({
            'error': 'Prediction error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in prediction: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing the prediction'
        }), 500


@inference_bp.route('/model/info', methods=['GET'])
def model_info():
    """
    FCM - Model Info
    ---
    tags:
      - FCM
    responses:
      200:
        description: Informações do modelo FCM
      503:
        description: Modelo indisponível
      500:
        description: Erro interno
    """
    try:
        if not fcm_predictor.is_loaded:
            if not fcm_predictor.load_model():
                return jsonify({
                    'error': 'Model not available',
                    'message': 'FCM model could not be loaded'
                }), 503
        
        model_info_data = fcm_predictor.get_model_info()
        
        info = {
            'model_name': 'Fuzzy C-Means Clustering Model',
            'description': 'Modelo Fuzzy C-Means para análise de regimes operacionais de motobombas',
            'algorithm': 'Fuzzy C-Means (FCM)',
            **model_info_data
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while retrieving model information'
        }), 500


@inference_bp.route('/status', methods=['GET'])
def status():
    """
    FCM - Status
    ---
    tags:
      - FCM
    responses:
      200:
        description: Status do serviço FCM
    """
    model_status = "loaded" if fcm_predictor.is_loaded else "not_loaded"
    
    return jsonify({
        'status': 'active',
        'service': 'inference',
        'model_status': model_status,
        'message': 'Inference service is running'
    }), 200
