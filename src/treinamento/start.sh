#!/bin/bash

echo "Iniciando o serviço de treinamento"

if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado. Por favor, instale o Docker."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi

echo "Construindo as imagens..."
docker compose build

echo "Iniciando os serviços..."
docker compose up -d

echo "Aguardando os serviços ficarem prontos..."
sleep 3

echo "Status dos serviços:"
docker compose ps

echo "Serviços iniciados com sucesso!"
echo ""
echo "FastAPI disponível em: http://localhost:8000"
echo "Docs da API disponível em: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Para parar os serviços, execute: docker compose down"
echo "Para ver logs em tempo real: docker compose logs -f"
