FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir -c constraints.txt .
USER 65532:65532
ENV PORT=8000
EXPOSE 8000
CMD ["prim-foundation-mcp", "--transport", "http", "--host", "0.0.0.0"]
