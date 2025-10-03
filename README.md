# BigQuery ChatGPT Connector (HTTP Middleware)

> **Based on**: [LucasHild/mcp-server-bigquery](https://github.com/LucasHild/mcp-server-bigquery)
> This fork adds a ChatGPT-compatible HTTP/REST middleware layer on top of the original MCP server implementation.

A FastAPI-based HTTP server that exposes BigQuery functionality through REST endpoints compatible with ChatGPT custom actions and other web clients.

## What This Adds

This repository extends the original MCP server with:

- ✅ **HTTP/REST API** - FastAPI server with OpenAPI documentation
- ✅ **ChatGPT Integration** - Ready for ChatGPT custom actions
- ✅ **API Key Authentication** - Secure Bearer token authentication
- ✅ **CORS Support** - Pre-configured for ChatGPT origins
- ✅ **Docker Deployment** - Production-ready containerization
- ✅ **Auto-generated Docs** - Interactive Swagger UI at `/docs`

## Quick Start

### 1. Setup Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration...
```

Required variables:
- `BIGQUERY_PROJECT` - Your GCP project ID
- `BIGQUERY_LOCATION` - BigQuery location (e.g., `US`, `us-central1`)
- `MY_API_KEY` - Secret key for API authentication

Optional variables:
- `BIGQUERY_DATASETS` - Comma-separated list of datasets to expose
- `BIGQUERY_KEY_FILE` - Path to service account JSON key

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the HTTP Server

```bash
# Quick start
./quickstart.sh

# Or manually with uv
uv run mcp-server-bigquery-http

# With custom port
uv run mcp-server-bigquery-http --port 9000

# Development mode with auto-reload
uv run mcp-server-bigquery-http --reload
```

The server will start on `http://localhost:8000`

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# List tables (requires authentication)
curl -H "Authorization: Bearer your-secret-api-key" \
  http://localhost:8000/tables

# Execute query
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM dataset.table LIMIT 5"}'
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## ChatGPT Integration

### Prerequisites

- ChatGPT Plus or Enterprise account
- Google Cloud Platform account with BigQuery access
- HTTPS endpoint, required by ChatGPT (you may use Cloudflare or ngrok to tunnel to your local server)

### Step-by-Step Setup

#### 1. Deploy Your API with HTTPS

ChatGPT **requires HTTPS**. Choose one of these deployment options:

**Option A: Cloudflare Tunnel (Easiest)**
```bash
# Install cloudflared
# Start the server locally
uv run mcp-server-bigquery-http

# In another terminal, create tunnel
cloudflared tunnel create bigquery-api
cloudflared tunnel run bigquery-api
```

**Option B: Cloud Run (Production)**
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/bigquery-chatgpt

# Deploy to Cloud Run
gcloud run deploy bigquery-chatgpt \
  --image gcr.io/PROJECT_ID/bigquery-chatgpt \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BIGQUERY_PROJECT=PROJECT_ID,BIGQUERY_LOCATION=US,MY_API_KEY=SECRET
```

**Option C: Other Options**
- ngrok for quick testing
- AWS ALB/ELB with ACM certificate
- nginx reverse proxy with Let's Encrypt
- Any PaaS with automatic HTTPS (Heroku, Render, etc.)

#### 2. Get OpenAPI Specification

Once deployed with HTTPS, visit:
- **OpenAPI JSON**: `https://your-domain.com/openapi.json`
- **Swagger UI**: `https://your-domain.com/docs` (interactive testing)

The server auto-generates the OpenAPI spec from your running API.

#### 3. Configure ChatGPT Custom Action

1. **Open ChatGPT** and click your profile icon
2. Go to **Settings** → **Beta Features** → Enable **"Actions"**
3. **Create a new GPT** or edit an existing one
4. Click **Configure** → **Actions** → **"Create new action"**
5. **In the Schema section**, paste the OpenAPI specification from `/openapi.json`
6. **In the Authentication section**:
   - Select **"API Key"**
   - Choose **"Bearer"**
   - Enter your `MY_API_KEY` value
7. Click **"Save"**

#### 4. Test Your Integration

Try these prompts in ChatGPT:

- "List all available BigQuery tables"
- "Describe the schema of dataset.table_name"
- "Query the first 10 rows from dataset.users"
- "Show me the total count of records in analytics.events"

### Security for ChatGPT Integration

**Critical Security Considerations:**

1. **API Key Management**
   - Generate strong keys: `openssl rand -hex 32`
   - Never commit keys to version control
   - Use different keys for dev/prod
   - Rotate keys regularly

2. **Network Security**
   - **Always use HTTPS** in production (ChatGPT requirement)
   - Implement rate limiting to prevent abuse
   - Use VPC/firewall rules to restrict access
   - Consider IP allowlisting for additional security

3. **BigQuery Access Control**
   - Use service accounts with **minimum required permissions**
   - Enable BigQuery audit logs for query monitoring
   - Set up query cost limits to prevent runaway costs
   - Review executed queries regularly

4. **Query Safety**
   - Queries are executed directly - ensure proper BigQuery IAM
   - Consider implementing query validation/sanitization
   - Set reasonable query timeouts
   - Monitor for suspicious patterns

### CORS Configuration

The server is pre-configured with CORS for ChatGPT origins:
- `https://chat.openai.com`
- `https://chatgpt.com`

If you need to add additional origins, modify the `http_server.py` configuration.

### Troubleshooting ChatGPT Connection

**"ChatGPT can't connect to my API"**
- ✅ Verify API is accessible via HTTPS (not HTTP)
- ✅ Test endpoints directly with curl first
- ✅ Check CORS allows ChatGPT origins
- ✅ Review server logs for authentication errors
- ✅ Ensure API key matches exactly (no extra spaces)

**"Invalid API key" errors**
- ✅ Check `Authorization` header format: `Bearer YOUR_KEY`
- ✅ Verify `MY_API_KEY` environment variable is set correctly
- ✅ Ensure the key in ChatGPT matches your server configuration

**"Database not initialized" errors**
- ✅ Ensure `BIGQUERY_PROJECT` and `BIGQUERY_LOCATION` are set
- ✅ Check BigQuery credentials are valid
- ✅ Verify service account has proper permissions

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Create .env file with your configuration
cp .env.example .env
nano .env

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using Docker directly

```bash
docker build -t bigquery-chatgpt .

docker run -d \
  -p 8000:8000 \
  -e BIGQUERY_PROJECT="your-project" \
  -e BIGQUERY_LOCATION="us-central1" \
  -e MY_API_KEY="your-secret-key" \
  --name bigquery-api \
  bigquery-chatgpt
```

## API Endpoints

### Core BigQuery Operations

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` or `/health` | GET | Health check | No |
| `/tables` | GET | List all available tables | Yes |
| `/table/describe` | POST | Get table schema | Yes |
| `/query` | POST | Execute SQL query | Yes |

## Architecture

```
┌─────────────┐
│   ChatGPT   │
│   (Client)  │
└──────┬──────┘
       │ HTTPS
       │ Bearer Auth
┌──────▼──────────────┐
│  FastAPI HTTP       │
│  Middleware         │
│  (http_server.py)   │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  BigQueryDatabase   │
│  (Original MCP)     │
│  (server.py)        │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  Google BigQuery    │
│  API                │
└─────────────────────┘
```

The HTTP middleware wraps the original MCP server's `BigQueryDatabase` class, exposing its functionality through REST endpoints.

## Original MCP Server

For the original Model Context Protocol (MCP) server implementation designed for Claude Desktop and other MCP clients, see:

**[LucasHild/mcp-server-bigquery](https://github.com/LucasHild/mcp-server-bigquery)**

The original MCP server provides:
- stdio/SSE-based MCP protocol
- Direct integration with Claude Desktop
- MCP tools schema (`execute-query`, `list-tables`, `describe-table`)

This fork shares the same core BigQuery functionality but adds HTTP/REST access for broader client compatibility.

## Configuration

Both MCP and HTTP modes support the same configuration:

| Argument | Environment Variable | Required | Description |
|----------|---------------------|----------|-------------|
| `--project` | `BIGQUERY_PROJECT` | Yes | The GCP project ID |
| `--location` | `BIGQUERY_LOCATION` | Yes | The GCP location (e.g. `europe-west9`, `US`) |
| `--dataset` | `BIGQUERY_DATASETS` | No | Specific datasets (comma-separated). If not provided, all datasets are accessible |
| `--key-file` | `BIGQUERY_KEY_FILE` | No | Path to service account key file. If not provided, uses default credentials |
| N/A | `MY_API_KEY` | Yes (HTTP only) | API key for Bearer token authentication |

## Security Best Practices

1. **API Key Management**
   - Use strong, randomly generated keys: `openssl rand -hex 32`
   - Never commit keys to version control
   - Rotate keys regularly
   - Use different keys for dev/prod

2. **Network Security**
   - Always use HTTPS in production (required for ChatGPT)
   - Implement rate limiting
   - Use VPC/firewall rules to restrict access
   - Consider IP allowlisting

3. **BigQuery Access Control**
   - Use service accounts with minimum required permissions
   - Enable BigQuery audit logs
   - Set up query cost limits
   - Review queries regularly

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests (when available)
uv run pytest
```

### Code Formatting

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

This project builds upon [LucasHild/mcp-server-bigquery](https://github.com/LucasHild/mcp-server-bigquery). Thanks to the original author for the excellent MCP server implementation.
