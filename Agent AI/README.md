# Agent AI

# agent_venv\Scripts\Activate.ps1

LLM Service untuk KSM Main dengan RAG Integration

## Deskripsi

Agent AI adalah service terpisah yang menyediakan LLM (Large Language Model) capabilities untuk KSM Main. Service ini menerima RAG context dari KSM Main dan menghasilkan response yang akurat berdasarkan knowledge base.

## Fitur

- 🤖 **OpenAI Integration** - Menggunakan OpenAI API untuk response generation
- 🔍 **RAG Context Processing** - Memproses RAG context dari KSM Main
- 📱 **Telegram Support** - Endpoint khusus untuk Telegram chatbot
- 🔄 **Multi-tier Fallback** - Fallback mechanism yang robust
- 📊 **Monitoring & Logging** - Comprehensive logging dan monitoring
- 🛡️ **Security** - Input validation dan rate limiting

## Arsitektur

```
KSM Main → Agent AI
1. RAG Search (Qdrant) → Build Context
2. Send Context + Message → Agent AI
3. Process Context → Generate Response
4. Return Response → KSM Main → Telegram
```

## Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - Detailed status
- `GET /ping` - Simple ping

### Chat Endpoints
- `POST /api/telegram/chat` - Simple Telegram chat
- `POST /api/rag/chat` - RAG-enhanced chat
- `GET /api/rag/status` - RAG service status

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `env.example` ke `.env` dan sesuaikan konfigurasi:

```bash
cp env.example .env
```

### 3. Database Setup

Agent AI menggunakan database yang sama dengan KSM Main. Pastikan:
- MySQL server running
- Database `KSM_main` tersedia
- Connection string sesuai di `.env`

### 4. OpenAI API Key

Dapatkan API key dari OpenAI dan set di `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run Application

```bash
python app.py
```

Service akan berjalan di `http://localhost:5000`

## Konfigurasi

### Model Settings
- `DEFAULT_MODEL` - Model OpenAI yang digunakan (default: gpt-4o-mini)
- `AI_TEMPERATURE` - Temperature untuk response generation (0.0-1.0)
- `AI_MAX_TOKENS` - Maximum tokens per response

### RAG Settings
- `RAG_MAX_CONTEXT_LENGTH` - Maximum context length
- `RAG_MIN_SIMILARITY` - Minimum similarity threshold
- `RAG_MAX_CHUNKS` - Maximum chunks to process

### Performance Settings
- `API_TIMEOUT` - Request timeout
- `CACHE_TTL` - Cache time-to-live
- `RATE_LIMIT_REQUESTS` - Rate limiting

## Testing

### Test Health
```bash
curl http://localhost:5000/health
```

### Test RAG Chat
```bash
curl -X POST http://localhost:5000/api/rag/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

### Test Telegram Chat
```bash
curl -X POST http://localhost:5000/api/telegram/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Monitoring

### Logs
- Application logs: `agent_ai.log`
- Log level: Configurable via `LOG_LEVEL`

### Metrics
- Response time tracking
- Token usage monitoring
- Error rate monitoring
- Context processing metrics

## Integration dengan KSM Main

### 1. RAG Context Format

```json
{
  "rag_results": [
    {
      "content": "Document content",
      "similarity": 0.85,
      "source_document": "document.pdf",
      "chunk_id": "chunk_1"
    }
  ],
  "total_chunks": 1,
  "avg_similarity": 0.85,
  "search_time_ms": 150.5,
  "context_available": true
}
```

### 2. Request Format

```json
{
  "user_id": 12345,
  "message": "User question",
  "context": { /* RAG context */ },
  "session_id": "session_123",
  "source": "KSM_main_telegram_rag"
}
```

### 3. Response Format

```json
{
  "success": true,
  "data": {
    "response": "AI response",
    "model_used": "gpt-4o-mini",
    "processing_time": 1.2,
    "tokens_used": 150,
    "rag_metadata": {
      "context_used": true,
      "chunks_processed": 3
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **OpenAI API Error**
   - Check API key validity
   - Verify API quota
   - Check network connectivity

2. **Database Connection Error**
   - Verify MySQL server status
   - Check connection string
   - Verify database exists

3. **RAG Context Error**
   - Validate context format
   - Check similarity thresholds
   - Verify context processing

### Debug Mode

Enable debug mode:

```env
AGENT_AI_DEBUG=true
LOG_LEVEL=DEBUG
```

## Development

### Project Structure

```
Agent AI/
├── app.py                 # Main application
├── config/               # Configuration
├── controllers/          # API endpoints
├── services/            # Business logic
├── models/              # Data models
├── utils/               # Utilities
├── requirements.txt     # Dependencies
└── env.example         # Environment template
```

### Adding New Features

1. Create service in `services/`
2. Add controller in `controllers/`
3. Update models if needed
4. Add tests
5. Update documentation

## License

Internal use only - KSM Group
