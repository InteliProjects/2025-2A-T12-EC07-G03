from flask import Blueprint, request, jsonify
import logging
from model_utils import xgb_predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

xgb_bp = Blueprint('xgb', __name__)


@xgb_bp.route('/xgb/predict', methods=['POST'])
def xgb_predict():
    """
    XGBoost - Predict
    ---
    tags:
      - XGBoost
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            threshold:
              type: number
              default: 0.5
              description: limiar de decisão para converter probabilidade em classe
            data:
              description: Uma única amostra (objeto) ou múltiplas amostras (lista de objetos)
              oneOf:
                - type: object
                  additionalProperties:
                    type: number
                - type: array
                  items:
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

        if not xgb_predictor.is_loaded:
            logger.warning("XGBoost model not loaded, attempting to load...")
            if not xgb_predictor.load_model():
                return jsonify({
                    'error': 'Model not available',
                    'message': 'XGBoost model could not be loaded'
                }), 503

        data = request.json
        result = xgb_predictor.predict(data)

        logger.info("XGB prediction successful")
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
        logger.error(f"Unexpected error in XGB prediction: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing the XGB prediction'
        }), 500


@xgb_bp.route('/xgb/model/info', methods=['GET'])
def xgb_model_info():
    """
    XGBoost - Model Info
    ---
    tags:
      - XGBoost
    responses:
      200:
        description: Informações do modelo XGBoost
      503:
        description: Modelo indisponível
      500:
        description: Erro interno
    """
    try:
        if not xgb_predictor.is_loaded:
            if not xgb_predictor.load_model():
                return jsonify({
                    'error': 'Model not available',
                    'message': 'XGBoost model could not be loaded'
                }), 503

        info = xgb_predictor.get_model_info()
        return jsonify(info), 200

    except Exception as e:
        logger.error(f"Error getting XGB model info: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while retrieving XGB model information'
        }), 500


@xgb_bp.route('/xgb/status', methods=['GET'])
def xgb_status():
    """
    XGBoost - Status
    ---
    tags:
      - XGBoost
    responses:
      200:
        description: Status do serviço XGBoost
    """
    model_status = "loaded" if xgb_predictor.is_loaded else "not_loaded"

    return jsonify({
        'status': 'active',
        'service': 'xgboost',
        'model_status': model_status,
        'message': 'XGBoost inference service is running'
    }), 200


