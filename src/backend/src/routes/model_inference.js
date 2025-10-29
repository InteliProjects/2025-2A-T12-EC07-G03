import { Router } from 'express';
import { z } from 'zod';
import { requireAuth } from '../middleware/auth.js';

const router = Router();

/**
 * @swagger
 * /model-inference/machine/xgboost/predict:
 *   post:
 *     summary: Fazer predição com modelo XGBoost para detecção de anomalias
 *     tags: [Model Inference]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - machine_name
 *             properties:
 *               machine_name:
 *                 type: string
 *                 maxLength: 30
 *                 description: Nome da máquina para predição
 *                 example: "ITU-693"
 *     responses:
 *       200:
 *         description: Predição realizada com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   description: Indica se a operação foi bem-sucedida
 *                   example: true
 *                 result:
 *                   type: object
 *                   properties:
 *                     success:
 *                       type: boolean
 *                       example: true
 *                     total_samples:
 *                       type: integer
 *                       description: Número total de amostras analisadas
 *                       example: 1
 *                     alerts_detected:
 *                       type: integer
 *                       description: Número de alertas detectados
 *                       example: 0
 *                     results:
 *                       type: array
 *                       items:
 *                         type: object
 *                         properties:
 *                           sample:
 *                             type: integer
 *                             description: Número da amostra
 *                             example: 1
 *                           prediction:
 *                             type: integer
 *                             description: Predição (0=Normal, 1=Anomalia)
 *                             example: 0
 *                           status:
 *                             type: string
 *                             description: Status da operação da máquina
 *                             example: "NORMAL OPERATION"
 *                           probability_normal:
 *                             type: number
 *                             description: Probabilidade de operação normal
 *                             example: 0.8544999957084656
 *                           probability_pre_failure:
 *                             type: number
 *                             description: Probabilidade de pré-falha
 *                             example: 0.14550000429153442
 *                           risk_level:
 *                             type: string
 *                             description: Nível de risco
 *                             example: "LOW"
 *                           threshold_used:
 *                             type: number
 *                             description: Threshold utilizado para classificação
 *                             example: 0.5
 *       400:
 *         description: Dados de entrada inválidos
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: array
 *                   description: Lista de erros de validação
 *       500:
 *         description: Erro interno do servidor ou falha na predição
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Failed to get prediction"
 *                 details:
 *                   type: string
 *                   description: Detalhes do erro
 */
router.post('/machine/xgboost/predict', /*requireAuth*/ async (req, res) => { 
    const predictSchema = z.object({
        machine_name: z.string().max(30),
        bucket_address: z.string().optional()
    });

    try {
        const validatedData = predictSchema.parse(req.body);

        await fetch('http://localhost:3000/machine/xgboost/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
            body: JSON.stringify(validatedData)
        })
        .then(response => response.json())
        .then(data => {
            res.status(200).json(data);
        })
        .catch(error => {
            res.status(500).json({ error: 'Failed to get prediction', details: error.message });
        });
        
    } catch (err) {
        res.status(400).json({ error: err.errors });
    }

});

/**
 * @swagger
 * /model-inference/machine/gru/predict:
 *   post:
 *     summary: Fazer predição com modelo GRU para análise de índices de máquina
 *     tags: [Model Inference]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - machine_name
 *             properties:
 *               machine_name:
 *                 type: string
 *                 maxLength: 30
 *                 description: Nome da máquina para predição
 *                 example: "ITU-693"
 *               time_steps:
 *                 type: integer
 *                 minimum: 1
 *                 default: 60
 *                 description: Número de passos temporais para a predição
 *                 example: 60
 *     responses:
 *       200:
 *         description: Predição realizada com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   description: Indica se a operação foi bem-sucedida
 *                   example: true
 *                 indices:
 *                   type: object
 *                   description: Índices calculados para diferentes sistemas
 *                   properties:
 *                     lubrificacao:
 *                       type: number
 *                       description: Índice do sistema de lubrificação
 *                       example: 46.4
 *                     hidraulico:
 *                       type: number
 *                       description: Índice do sistema hidráulico
 *                       example: 23.84
 *                 status:
 *                   type: object
 *                   description: Status dos diferentes sistemas da máquina
 *                   properties:
 *                     lubrificacao:
 *                       type: string
 *                       description: Status do sistema de lubrificação
 *                       example: "ATENÇÃO"
 *                     hidraulico:
 *                       type: string
 *                       description: Status do sistema hidráulico
 *                       example: "ALERTA"
 *                 meta:
 *                   type: object
 *                   description: Metadados da predição
 *                   properties:
 *                     timesteps:
 *                       type: integer
 *                       description: Número de timesteps utilizados
 *                       example: 60
 *                     n_features:
 *                       type: integer
 *                       description: Número de features utilizadas
 *                       example: 8
 *                     feature_order:
 *                       type: array
 *                       items:
 *                         type: string
 *                       description: Ordem das features utilizadas
 *                       example: ["Eng_RPM","Cool_T","Oil_P","Oil_L","Recalque","Succao","Bat_V","Char_V"]
 *                     machine:
 *                       type: string
 *                       description: Nome da máquina analisada
 *                       example: "ITU-693"
 *                     fetched_rows:
 *                       type: integer
 *                       description: Número de linhas obtidas do banco de dados
 *                       example: 60
 *                     requested_time_steps:
 *                       type: integer
 *                       description: Número de timesteps solicitados
 *                       example: 60
 *       400:
 *         description: Dados de entrada inválidos
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: array
 *                   description: Lista de erros de validação
 *       500:
 *         description: Erro interno do servidor ou falha na predição
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Failed to get prediction"
 *                 details:
 *                   type: string
 *                   description: Detalhes do erro
 */
router.post('/machine/gru/predict', /*requireAuth*/ async (req, res) => { 
    const predictSchema = z.object({
        machine_name: z.string().max(30),
        time_steps: z.number().int().min(1).default(60),
        model_bucket_address: z.string()
    });

    try {
        const validatedData = predictSchema.parse(req.body);

        await fetch('http://localhost:3000/machine/gru/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'accept': 'application/json' },
            body: JSON.stringify(validatedData)
        })
        .then(response => response.json())
        .then(data => {
            res.status(200).json(data);
        })
        .catch(error => {
            res.status(500).json({ error: 'Failed to get prediction', details: error.message });
        });
        
    } catch (err) {
        res.status(400).json({ error: err.errors });
    }
});

export default router;
