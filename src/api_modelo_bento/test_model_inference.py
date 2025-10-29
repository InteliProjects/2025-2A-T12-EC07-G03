import logging
import json
from model_inference_xgboost import ModelInference, create_sample_data

# Configuração básica de logging para exibir informações durante o teste
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_inference_test():
    """
    Executa um teste de ponta a ponta na classe ModelInference.

    Este teste demonstra como:
    1. Importar as classes necessárias do script principal.
    2. Instanciar a classe ModelInference para carregar o modelo.
    3. Obter os dados de amostra para o teste.
    4. Chamar o método de predição.
    5. Exibir os resultados da predição de forma legível.
    """
    logger.info("--- Iniciando Teste de Inferência do Modelo XGBoost ---")
    
    try:
        # 1. Instancia a classe ModelInference. O modelo será carregado no construtor.
        logger.info("Carregando o modelo e inicializando ModelInference...")
        model_inference = ModelInference()
        
        # Opcional: Exibe informações sobre o modelo carregado
        model_info = model_inference.get_model_info()
        logger.info(f"Modelo '{model_info.get('model_type')}' carregado com sucesso.")
        logger.info(f"Número de features esperadas pelo modelo: {model_info.get('num_features')}")
        
        # 2. Obtém os dados de teste da função importada
        logger.info("Gerando dados de amostra para o teste...")
        sample_data = create_sample_data()
        
        # 3. Executa a predição usando os dados de amostra
        logger.info("Executando predição de falha com os dados de amostra...")
        prediction_result = model_inference.predict_failure(sample_data)
        
        # 4. Verifica e exibe os resultados
        if prediction_result and prediction_result['success']:
            logger.info("Predição concluída com sucesso!")
            print("\n" + "="*50)
            print("            RESULTADO DA PREDIÇÃO DE TESTE")
            print("="*50)
            # Usamos json.dumps para uma impressão mais bonita do dicionário
            print(json.dumps(prediction_result, indent=2, ensure_ascii=False))
            print("="*50 + "\n")
        else:
            logger.error(f"O teste de predição falhou: {prediction_result.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado durante o teste: {e}", exc_info=True)

    logger.info("--- Teste de Inferência do Modelo XGBoost Concluído ---")

if __name__ == "__main__":
    run_inference_test()
