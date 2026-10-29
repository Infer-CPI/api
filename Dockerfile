# stdio MCP server (for MCP directories that build and inspect servers); hosted copy: https://infercpi.com/mcp
FROM python:3.13-slim
RUN pip install --no-cache-dir mcp
WORKDIR /app
COPY mcp_server.py .
CMD ["python", "mcp_server.py"]
