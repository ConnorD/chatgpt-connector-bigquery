# ChatGPT Integration Guide

This guide explains how to set up the BigQuery HTTP middleware for use with ChatGPT custom actions.

## Prerequisites

- Python 3.13 or higher
- Google Cloud Platform account with BigQuery access
- Service account key file (optional, if not using default credentials)
- ChatGPT Plus or Enterprise account

## Installation

1. Install dependencies:

```bash
uv sync
```

2. Set up environment variables:

```bash
export BIGQUERY_PROJECT="your-gcp-project-id"
export BIGQUERY_LOCATION="us-central1"
export MY_API_KEY="your-secret-api-key"  # Used for authentication
export BIGQUERY_KEY_FILE="/path/to/service-account-key.json"  # Optional
export BIGQUERY_DATASETS="dataset1,dataset2"  # Optional, comma-separated
export OPENAPI_SERVERS='[{"url": "https://your-api-domain.com", "description": "Production"}]'  # Optional
```

## Running the HTTP Server

### Development Mode

```bash
uv run mcp-server-bigquery-http
```

The server will start on `http://localhost:8000` by default.

### Production Mode

For production deployment, you'll want to:

1. Use a proper WSGI server
2. Set up HTTPS (required for ChatGPT)
3. Deploy behind a reverse proxy (nginx, Cloudflare, etc.)

Example with Uvicorn:

```bash
uv run uvicorn mcp_server_bigquery.http_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

A `Dockerfile` is provided for containerized deployment:

```bash
docker build -t bigquery-chatgpt-api .
docker run -p 8000:8000 \
  -e BIGQUERY_PROJECT="your-project" \
  -e BIGQUERY_LOCATION="us-central1" \
  -e MY_API_KEY="your-api-key" \
  bigquery-chatgpt-api
```

## API Endpoints

The HTTP server exposes the following endpoints:

### `GET /` or `GET /health`
Health check endpoint

### `GET /tables`
List all available tables in BigQuery

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`

**Response:**
```json
{
  "success": true,
  "tables": [
    "dataset1.table1",
    "dataset1.table2",
    "dataset2.table3"
  ],
  "count": 3
}
```

### `POST /table/describe`
Get schema information for a specific table

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`

**Body:**
```json
{
  "table_name": "dataset.table"
}
```

**Response:**
```json
{
  "success": true,
  "schema": [
    {
      "ddl": "CREATE TABLE ..."
    }
  ]
}
```

### `POST /query`
Execute a SQL query

**Headers:**
- `Authorization: Bearer YOUR_API_KEY`

**Body:**
```json
{
  "query": "SELECT * FROM dataset.table LIMIT 10"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
  ],
  "row_count": 2
}
```

## ChatGPT Configuration

### Step 1: Deploy Your API

Ensure your API is:
1. Accessible via HTTPS (ChatGPT requires HTTPS)
2. Has CORS configured for `https://chat.openai.com` and `https://chatgpt.com`
3. Protected with API key authentication

### Step 2: Get OpenAPI Specification

Visit `https://your-domain.com/openapi.json` to get the OpenAPI specification.

### Step 3: Configure ChatGPT Custom Action

1. Open ChatGPT and click your profile icon
2. Go to "Settings" → "Beta Features" → Enable "Actions"
3. Create a new GPT or edit an existing one
4. Click "Configure" → "Actions" → "Create new action"
5. In the "Authentication" section:
   - Select "API Key"
   - Choose "Bearer"
   - Enter your `MY_API_KEY`
6. In the "Schema" section, paste the OpenAPI specification from `/openapi.json`
7. Click "Save"

### Step 4: Test Your Integration

Try these prompts in ChatGPT:

1. "List all available BigQuery tables"
2. "Describe the schema of dataset.table_name"
3. "Query the first 10 rows from dataset.table_name"

## OpenAPI Specification

The server automatically generates an OpenAPI specification available at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Security Considerations

1. **API Key**: Always use a strong, randomly generated API key
2. **HTTPS**: Never expose the API over plain HTTP in production
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **Query Validation**: The server executes queries directly - ensure proper access controls in BigQuery
5. **Network Security**: Use firewalls/security groups to restrict access to your API
6. **Audit Logging**: BigQuery automatically logs queries; review them regularly

## Example ChatGPT Actions Schema

If you need to manually create the schema, here's an example:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "BigQuery API for ChatGPT",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://your-domain.com"
    }
  ],
  "paths": {
    "/tables": {
      "get": {
        "summary": "List all BigQuery tables",
        "operationId": "listTables",
        "responses": {
          "200": {
            "description": "Successful response"
          }
        }
      }
    },
    "/query": {
      "post": {
        "summary": "Execute SQL query",
        "operationId": "executeQuery",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                  }
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful response"
          }
        }
      }
    }
  }
}
```

## Troubleshooting

### Server won't start
- Check that all required environment variables are set
- Verify BigQuery credentials are valid
- Ensure the port 8000 is not already in use

### ChatGPT can't connect
- Verify the API is accessible via HTTPS
- Check CORS configuration
- Confirm API key authentication is working
- Review server logs for errors

### Queries fail
- Check BigQuery permissions for your service account
- Verify the query syntax is correct for BigQuery
- Review BigQuery quotas and limits
- Check network connectivity to Google Cloud

## Advanced Configuration

### Custom Port

```bash
uv run python -c "from mcp_server_bigquery.http_server import main; main(port=9000)"
```

### Multiple Workers

```bash
uv run uvicorn mcp_server_bigquery.http_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop
```

### Environment File

Create a `.env` file:

```env
BIGQUERY_PROJECT=my-project
BIGQUERY_LOCATION=us-central1
MY_API_KEY=your-secret-key
BIGQUERY_KEY_FILE=/path/to/key.json
BIGQUERY_DATASETS=dataset1,dataset2
```

Load it before starting:

```bash
source .env
uv run mcp-server-bigquery-http
```
