# Wikipedia Chatbot - Microservicio

ChatBot de Wikipedia usando ChatGPT. 

## Requisitos

- Docker 
- OpenAI API Key: https://platform.openai.com/api-keys

## Instrucciones 

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/NBK3E/wikipedia-chatbot.git
cd wikipedia-chatbot
```

### Paso 2: Configurar Variables de Entorno

```
OPENAI_API_KEY=sk-tu-clave-aqui
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
DEBUG=False
```

### Paso 3: Ejecutar Docker Compose

```bash
docker compose up --build -d
```

Esto levantará:
- FastAPI API (puerto 8000)
- RabbitMQ (puerto 5672, Management 15672)

### Paso 4: Acceder a la Aplicación

- **API Documentation**: http://localhost:8000/api/docs
- **RabbitMQ Management**: http://localhost:15672 (user: guest, pass: guest)

### Paso 5: Probar la API

#### Con cURL:

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la Inteligencia Artificial?",
    "session_id": "user-001"
  }'
```

#### Con Swagger UI:

1. Abre http://localhost:8000/api/docs
2. Click en **POST /api/chat**
3. Click en "Try it out"
4. Ingresa:
   ```json
   {
     "question": "¿Qué es Python?",
     "session_id": "user-123"
   }
   ```
5. Click en "Execute"

### Paso 6: Detener la Ejecución

```bash
# Detener los contenedores
docker compose down

# Detener y eliminar volúmenes
docker compose down -v

```

## API

### Endpoint Principal

```bash
POST /api/chat
```

**Request:**
```json
{
  "question": "¿Qué es Python?",
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "message": "Python es un lenguaje de programación interpretado...\n\nFuentes verificables:\n- Python (programming language): https://en.wikipedia.org/wiki/Python_(programming_language)",
  "session_id": "user-123",
  "request_id": "uuid"
}
```

## Arquitectura

```
┌─────────────┐
│   Usuario   │ Hace pregunta
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   FastAPI Application       │
│  ┌───────────────────────┐  │
│  │ 1. Extrae tema        │  │ ChatGPT
│  │ 2. Busca Wikipedia    │  │ (Extrae tema)
│  │ 3. Genera respuesta   │  │
│  └───────────────────────┘  │
└──────┬──────────────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
   Wikipedia    ChatGPT      RabbitMQ
   (Buscar)     (Explica)    (Eventos)
```

## Flujo de Solicitud

1. **Usuario hace pregunta** → "¿Qué es IA?"
2. **ChatGPT extrae tema** → "Inteligencia Artificial"
3. **Busca en Wikipedia** → Obtiene contenido
4. **ChatGPT genera explicación** → Basada solo en Wikipedia
5. **Publica eventos** → En RabbitMQ
6. **Retorna respuesta** → Con URLs verificables

## Componentes

### FastAPI (`app/main.py`)
- API REST con endpoints
- Manejo de excepciones
- Documentación automática

### ChatGPT (`services/chatgpt_service.py`)
- Extrae tema de pregunta
- Genera explicaciones
- Usa solo información de Wikipedia

### Wikipedia (`services/wikipedia_service.py`)
- Busca temas
- Extrae contenido y URLs
- Maneja errores

### RabbitMQ (`services/rabbitmq_service.py`)
- Publica eventos
- Consume eventos asincronos
- Reintentos automáticos

## Comandos Útiles

```bash
# Ver logs
docker compose logs -f api

# Detener servicios
docker compose down

# Reconstruir imagen
docker compose up -d --build


```

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Chat con pregunta |
| GET | `/api/status` | Estado API |
| GET | `/api/docs` | Swagger UI |

