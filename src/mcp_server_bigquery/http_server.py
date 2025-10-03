"""
HTTP middleware for BigQuery MCP server to support ChatGPT connectors.

This module provides a FastAPI-based HTTP server that exposes BigQuery
functionality through REST endpoints compatible with ChatGPT custom actions.
"""

import json
import logging
import os
from typing import Any, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .server import BigQueryDatabase

logger = logging.getLogger("mcp_bigquery_http")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

security = HTTPBearer()
API_KEY = os.environ.get("MY_API_KEY", "your-secret-api-key")

# Parse server URLs from environment variable
OPENAPI_SERVERS = []
if "OPENAPI_SERVERS" in os.environ:
    try:
        servers_json = os.environ.get("OPENAPI_SERVERS", "[]")
        OPENAPI_SERVERS = json.loads(servers_json)
        logger.info(f"Loaded {len(OPENAPI_SERVERS)} OpenAPI server(s) from environment")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OPENAPI_SERVERS environment variable: {e}")


class QueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute using BigQuery dialect")


class TableNameRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table (e.g., dataset.table)")


class HealthResponse(BaseModel):
    healthy: bool
    version: str = "1.0.0"
    service: str = "BigQuery API for ChatGPT Connector"


class QueryResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]
    row_count: int
    error: Optional[str] = None


class TablesResponse(BaseModel):
    success: bool
    tables: list[str]
    count: int
    error: Optional[str] = None


class TableSchemaResponse(BaseModel):
    success: bool
    ddl: list[dict[str, Any]]
    error: Optional[str] = None


app = FastAPI(
    title="BigQuery API for ChatGPT",
    description="REST API for executing BigQuery operations through ChatGPT custom actions",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com", "https://chatgpt.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = app.openapi()

    # Inject servers from environment variable
    if OPENAPI_SERVERS:
        openapi_schema["servers"] = OPENAPI_SERVERS
        logger.info(f"Injected {len(OPENAPI_SERVERS)} server(s) into OpenAPI schema")

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

db: Optional[BigQueryDatabase] = None


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Bearer token"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


@app.on_event("startup")
async def startup_event():
    """Initialize BigQuery database on startup"""
    global db

    project = os.environ.get("BIGQUERY_PROJECT")
    location = os.environ.get("BIGQUERY_LOCATION")
    key_file = os.environ.get("BIGQUERY_KEY_FILE")

    datasets_filter = []
    if "BIGQUERY_DATASETS" in os.environ:
        datasets_filter = os.environ.get("BIGQUERY_DATASETS", "").split(",")
        datasets_filter = [d.strip() for d in datasets_filter if d.strip()]

    if not project or not location:
        raise ValueError(
            "BIGQUERY_PROJECT and BIGQUERY_LOCATION environment variables are required"
        )

    db = BigQueryDatabase(project, location, key_file, datasets_filter)
    logger.info(f"BigQuery HTTP server initialized for project: {project}")


@app.get("/")
@app.get("/health")
async def health() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(healthy=True)


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_token)])
async def execute_query(request: QueryRequest):
    """
    Execute a SQL query on BigQuery.

    This endpoint allows you to run SELECT queries against your BigQuery datasets.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not initialized")

        logger.info(f"Executing query: {request.query[:100]}...")
        results = db.execute_query(request.query)

        return QueryResponse(
            success=True, data=results, row_count=len(results), error=None
        )
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return QueryResponse(success=False, data=[], row_count=0, error=str(e))


@app.get("/tables", response_model=TablesResponse, dependencies=[Depends(verify_token)])
async def list_tables():
    """
    List all tables in the BigQuery database.

    Returns a list of all available tables in the format: dataset.table
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not initialized")

        logger.info("Listing all tables")
        tables = db.list_tables()

        return TablesResponse(
            success=True, tables=tables, count=len(tables), error=None
        )
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return TablesResponse(success=False, tables=[], count=0, error=str(e))


@app.post(
    "/table/describe",
    response_model=TableSchemaResponse,
    dependencies=[Depends(verify_token)],
)
async def describe_table(request: TableNameRequest):
    """
    Get the schema information for a specific table.

    Provide the table name in the format: dataset.table
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not initialized")

        logger.info(f"Describing table: {request.table_name}")
        schema = db.describe_table(request.table_name)

        return TableSchemaResponse(success=True, ddl=schema, error=None)
    except Exception as e:
        logger.error(f"Error describing table: {str(e)}")
        return TableSchemaResponse(success=False, ddl=[], error=str(e))


def main():
    """Run the HTTP server - CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BigQuery HTTP Server for ChatGPT")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    logger.info(f"Starting BigQuery HTTP server on {args.host}:{args.port}")
    uvicorn.run(
        "mcp_server_bigquery.http_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
