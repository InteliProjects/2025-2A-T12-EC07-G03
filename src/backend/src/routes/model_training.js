import { Router } from 'express';
import { z } from 'zod';
import { requireAuth } from '../middleware/auth.js';

const router = Router();


/**
 * @swagger
 * /model-training/train:
 *   post:
 *     summary: Iniciar treinamento de modelo de machine learning
 *     tags: [Model Training]
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
 *               - indicator
 *             properties:
 *               machine_name:
 *                 type: string
 *                 maxLength: 30
 *                 description: Nome da máquina para treinamento
 *                 example: "ITU-693"
 *               indicator:
 *                 type: string
 *                 enum: [status, health]
 *                 description: Tipo de indicador para treinamento
 *                 example: "status"
 *               start_date:
 *                 type: string
 *                 format: date
 *                 description: Data de início para coleta de dados de treinamento
 *                 example: "2025-05-13"
 *               end_date:
 *                 type: string
 *                 format: date
 *                 description: Data de fim para coleta de dados de treinamento
 *                 example: "2025-05-14"
 *     responses:
 *       200:
 *         description: Treinamento iniciado com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 process_id:
 *                   type: string
 *                   format: uuid
 *                   description: ID único do processo de treinamento
 *                   example: "32b16a83-4685-40f4-ae98-25a9fae2f25a"
 *                 status:
 *                   type: string
 *                   description: Status inicial do processo
 *                   example: "pending"
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
 *         description: Erro interno do servidor ou falha ao iniciar treinamento
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Failed to start training"
 *                 details:
 *                   type: string
 *                   description: Detalhes do erro
 */
router.post('/train', /*requireAuth*/ async (req, res) => {
    const trainSchema = z.object({
        machine_name: z.string().max(30),
        indicator: z.enum(['status', 'health']),
        start_date: z.string().optional(),
        end_date: z.string().optional()
    });

    try {
        const validatedData = trainSchema.parse(req.body);

        const response = await fetch('http://localhost:8000/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(validatedData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return res.status(response.status).json({ 
                error: 'Failed to start training', 
                details: errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`,
                status_code: response.status
            });
        }

        const data = await response.json();
        res.status(200).json(data);

    } catch (err) {
        if (err.name === 'ZodError') {
            return res.status(400).json({ error: 'Validation error', details: err.errors });
        }
        res.status(500).json({ 
            error: 'Internal server error', 
            details: err.message,
            stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
        });
    }
});



/**
 * @swagger
 * /model-training/status/{process_id}:
 *   get:
 *     summary: Verificar status do processo de treinamento
 *     tags: [Model Training]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: process_id
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *         description: ID único do processo de treinamento
 *         example: "32b16a83-4685-40f4-ae98-25a9fae2f25a"
 *     responses:
 *       200:
 *         description: Status recuperado com sucesso
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 process_id:
 *                   type: string
 *                   format: uuid
 *                   description: ID único do processo de treinamento
 *                   example: "32b16a83-4685-40f4-ae98-25a9fae2f25a"
 *                 indicator:
 *                   type: string
 *                   description: Tipo de indicador sendo treinado
 *                   example: "status"
 *                 machine_name:
 *                   type: string
 *                   description: Nome da máquina sendo treinada
 *                   example: "ITU-693"
 *                 status:
 *                   type: string
 *                   enum: [pending, running, finished, failed]
 *                   description: Status atual do processo de treinamento
 *                   example: "finished"
 *                 error_message:
 *                   type: string
 *                   nullable: true
 *                   description: Mensagem de erro se houver falha
 *                   example: null
 *                 created_at:
 *                   type: string
 *                   format: date-time
 *                   description: Timestamp de criação do processo
 *                   example: "2025-10-01T22:15:07.494531"
 *                 updated_at:
 *                   type: string
 *                   format: date-time
 *                   description: Timestamp da última atualização
 *                   example: "2025-10-01T22:15:49"
 *                 finished_at:
 *                   type: string
 *                   format: date-time
 *                   nullable: true
 *                   description: Timestamp de finalização do processo
 *                   example: "2025-10-01T22:15:49"
 *                 bucket_address:
 *                   type: string
 *                   nullable: true
 *                   description: Endereço do modelo treinado no bucket de armazenamento
 *                   example: "model/xgb_model_ITU-693_2025_10_01_22_15_49.pkl"
 *       400:
 *         description: ID do processo inválido
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: array
 *                   description: Lista de erros de validação
 *       404:
 *         description: Processo de treinamento não encontrado
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Process not found"
 *       500:
 *         description: Erro interno do servidor ao buscar status
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 error:
 *                   type: string
 *                   example: "Failed to fetch status"
 *                 details:
 *                   type: string
 *                   description: Detalhes do erro
 */
router.get('/status/:process_id', /*requireAuth*/ async (req, res) => {
    const statusSchema = z.object({
        process_id: z.string().uuid()
    });

    try {
        const validatedParams = statusSchema.parse(req.params);
        const process_id = validatedParams.process_id;
        
        await fetch(`http://localhost:8000/status/${process_id}`)
        .then(response => response.json())
        .then(data => {
            res.status(200).json(data);
        })
        .catch(error => {
            res.status(500).json({ error: 'Failed to fetch status', details: error.message });
        });
        
    } catch (err) {
        res.status(400).json({ error: err.errors });
    }
});

export default router;
