# Wikipedia Chatbot - Microservicio

ChatBot de Wikipedia usando ChatGPT. 

## Requisitos

- Docker 
- OpenAI API Key

## Instrucciones 

### Clonar el Repositorio

```bash
git clone https://github.com/NBK3E/wikipedia-chatbot.git
cd wikipedia-chatbot
```

### Configurar Variables de Entorno

```
OPENAI_API_KEY=sk-tu-clave-aqui
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
DEBUG=False
```

### Docker Compose

```bash
docker compose up --build -d
```

Esto levantará:
- FastAPI API (puerto 8000)
- RabbitMQ (puerto 5672, Management 15672)

### Acceder al microservicio

- **API Documentation**: http://localhost:8000/api/docs
- **RabbitMQ Management**: http://localhost:15672 (user: guest, pass: guest)

## API

### Endpoint Principal

```bash
POST /chat
```

**Request:**
```json
{
  "question": "¿Qué es Python?"
}
```

**Response:**
```json
{
  "message": "Python es un lenguaje de programación interpretado...\n\nFuentes: https://en.wikipedia.org/wiki/Python",

}
```

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET    | `/health` | Health check |
| POST   | `/chat` | Chatbot |
