# ☁️ Deploy OrdnungsHub to Google Cloud

## Cloud Run Deployment (Serverless)

### Prerequisites
- Google Cloud account ($300 free credit)
- gcloud CLI installed
- Docker Hub or GCR access

---

## Quick Deploy with Cloud Run

### 1. Set Up Project
```bash
# Create new project
gcloud projects create ordnungshub-prod --name="OrdnungsHub"

# Set as current project
gcloud config set project ordnungshub-prod

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com
```

### 2. Build and Push Image
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/ordnungshub-prod/ordnungshub:latest

# Or use Artifact Registry (newer)
gcloud artifacts repositories create ordnungshub-repo \
  --repository-format=docker \
  --location=us-central1

gcloud builds submit --tag us-central1-docker.pkg.dev/ordnungshub-prod/ordnungshub-repo/ordnungshub:latest
```

### 3. Deploy to Cloud Run
```bash
gcloud run deploy ordnungshub \
  --image gcr.io/ordnungshub-prod/ordnungshub:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "ENABLE_METRICS=true,LOG_LEVEL=INFO"
```

---

## Set Up Database and Cache

### 1. Cloud SQL (PostgreSQL)
```bash
# Create PostgreSQL instance
gcloud sql instances create ordnungshub-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create ordnungshub \
  --instance=ordnungshub-db

# Create user
gcloud sql users create ordnungshub \
  --instance=ordnungshub-db \
  --password=SECURE_PASSWORD
```

### 2. Connect Cloud Run to Cloud SQL
```bash
# Get connection name
gcloud sql instances describe ordnungshub-db --format="value(connectionName)"

# Update Cloud Run service
gcloud run services update ordnungshub \
  --add-cloudsql-instances=PROJECT_ID:REGION:ordnungshub-db \
  --set-env-vars DATABASE_URL=postgresql://ordnungshub:PASSWORD@/ordnungshub?host=/cloudsql/CONNECTION_NAME
```

### 3. Memorystore (Redis)
```bash
# Create Redis instance
gcloud redis instances create ordnungshub-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0

# Get Redis host
gcloud redis instances describe ordnungshub-cache --region=us-central1 --format="value(host)"

# Connect via VPC connector
gcloud compute networks vpc-access connectors create ordnungshub-connector \
  --region=us-central1 \
  --subnet=default \
  --range=10.8.0.0/28

# Update Cloud Run with connector
gcloud run services update ordnungshub \
  --vpc-connector=ordnungshub-connector \
  --set-env-vars REDIS_URL=redis://REDIS_HOST:6379
```

---

## Advanced: GKE Deployment

### 1. Create GKE Cluster
```bash
# Create autopilot cluster (serverless Kubernetes)
gcloud container clusters create-auto ordnungshub-cluster \
  --region us-central1

# Get credentials
gcloud container clusters get-credentials ordnungshub-cluster --region us-central1
```

### 2. Deploy with Kubernetes
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ordnungshub
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ordnungshub
  template:
    metadata:
      labels:
        app: ordnungshub
    spec:
      containers:
      - name: ordnungshub
        image: gcr.io/ordnungshub-prod/ordnungshub:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: ordnungshub-service
spec:
  selector:
    app: ordnungshub
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Apply configuration
kubectl apply -f deployment.yaml

# Get external IP
kubectl get service ordnungshub-service
```

---

## Monitoring and Logging

### 1. Enable Cloud Monitoring
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ordnungshub" --limit 50

# Create log-based metrics
gcloud logging metrics create error_count \
  --description="Count of errors" \
  --log-filter='resource.type="cloud_run_revision"
  severity="ERROR"'
```

### 2. Set Up Alerts
```bash
# Create notification channel
gcloud alpha monitoring channels create \
  --display-name="OrdnungsHub Alerts" \
  --type=email \
  --channel-labels=email_address=your-email@example.com

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-name="Error rate > 5%" \
  --condition="CONDITION_THRESHOLD" \
  --if='metric.type="run.googleapis.com/request_count" AND
       metric.label.response_code_class="5xx"' \
  --aggregation='{"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_RATE"}'
```

---

## Custom Domain Setup

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service ordnungshub \
  --domain ordnungshub.com \
  --region us-central1

# Get DNS records to add
gcloud run domain-mappings describe \
  --domain ordnungshub.com \
  --region us-central1
```

---

## 🎉 Your App is Live on Google Cloud!

### Access URLs
- **Cloud Run**: `https://ordnungshub-xxx-uc.a.run.app`
- **Custom Domain**: `https://ordnungshub.com` (after setup)

### Cost Optimization
- Cloud Run scales to zero (pay per request)
- Use Cloud SQL Proxy for secure connections
- Enable VPC for private networking
- Use Cloud CDN for static assets

### Best Practices
- Enable Binary Authorization
- Use Cloud Armor for DDoS protection
- Implement Cloud IAM properly
- Use Secret Manager for credentials
- Enable Container Analysis