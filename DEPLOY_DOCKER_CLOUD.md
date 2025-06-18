# 🐳 Deploy OrdnungsHub with Docker

## Cloud Provider Options

### Option A: DigitalOcean App Platform

```bash
# Install doctl CLI
# Create app.yaml
cat > app.yaml << EOF
name: ordnungshub
services:
- name: backend
  github:
    repo: your-github/ordnungshub
    branch: main
  dockerfile_path: Dockerfile
  http_port: 8000
  health_check:
    http_path: /health
databases:
- name: db
  engine: PG
- name: redis
  engine: REDIS
EOF

# Deploy
doctl apps create --spec app.yaml
```

### Option B: AWS ECS with Copilot

```bash
# Install copilot
curl -Lo copilot https://github.com/aws/copilot-cli/releases/latest/download/copilot-linux
chmod +x copilot
sudo mv copilot /usr/local/bin/copilot

# Deploy
copilot app init ordnungshub
copilot env init --name production
copilot svc init --name api
copilot svc deploy --name api --env production
```

### Option C: Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/ordnungshub

# Deploy
gcloud run deploy ordnungshub \
  --image gcr.io/PROJECT-ID/ordnungshub \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "ENABLE_METRICS=true"
```

### Option D: Azure Container Instances

```bash
# Create resource group
az group create --name ordnungshub-rg --location eastus

# Create container
az container create \
  --resource-group ordnungshub-rg \
  --name ordnungshub \
  --image ordnungshub:latest \
  --dns-name-label ordnungshub \
  --ports 8000
```

## Production Best Practices

1. **Use managed databases**
2. **Set up auto-scaling**
3. **Configure monitoring**
4. **Enable backups**
5. **Use secrets management**