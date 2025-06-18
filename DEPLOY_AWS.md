# 🚀 Deploy OrdnungsHub to AWS

## AWS ECS with Fargate Deployment

### Prerequisites
- AWS Account
- AWS CLI installed
- Docker Hub account

---

## Option 1: AWS Copilot (Easiest)

### 1. Install Copilot
```bash
# macOS
brew install aws/tap/copilot-cli

# Linux
curl -Lo copilot https://github.com/aws/copilot-cli/releases/latest/download/copilot-linux
chmod +x copilot
sudo mv copilot /usr/local/bin/copilot
```

### 2. Initialize and Deploy
```bash
# Initialize application
copilot app init ordnungshub

# Create environment
copilot env init --name production

# Deploy backend service
copilot svc init --name api
# Choose: Backend Service
# Port: 8000

# Deploy!
copilot svc deploy --name api --env production
```

### 3. Add Database and Cache
```bash
# Add RDS PostgreSQL
copilot storage init
# Choose: Aurora Serverless PostgreSQL

# Add ElastiCache Redis
# Edit copilot/environments/production/env.yaml
```

---

## Option 2: Traditional ECS Setup

### 1. Push to ECR
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [YOUR_ECR_URI]

# Create repository
aws ecr create-repository --repository-name ordnungshub

# Tag and push
docker tag ordnungshub:latest [YOUR_ECR_URI]/ordnungshub:latest
docker push [YOUR_ECR_URI]/ordnungshub:latest
```

### 2. Create Task Definition
```json
{
  "family": "ordnungshub",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "ordnungshub",
      "image": "[YOUR_ECR_URI]/ordnungshub:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENABLE_METRICS", "value": "true"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:db-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:app-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ordnungshub",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 3. Create Service
```bash
# Create cluster
aws ecs create-cluster --cluster-name ordnungshub-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster ordnungshub-cluster \
  --service-name ordnungshub-api \
  --task-definition ordnungshub:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### 4. Set Up Load Balancer
```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name ordnungshub-alb \
  --subnets subnet-xxx subnet-yyy

# Create target group
aws elbv2 create-target-group \
  --name ordnungshub-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip
```

---

## Infrastructure as Code (Terraform)

```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

module "ordnungshub" {
  source = "./modules/ecs-fargate"
  
  app_name = "ordnungshub"
  image_uri = "${aws_ecr_repository.app.repository_url}:latest"
  
  cpu = 512
  memory = 1024
  
  environment_variables = {
    ENABLE_METRICS = "true"
    LOG_LEVEL = "INFO"
  }
  
  secrets = {
    DATABASE_URL = aws_secretsmanager_secret.db_url.arn
    SECRET_KEY = aws_secretsmanager_secret.app_secret.arn
  }
}

resource "aws_rds_cluster" "postgres" {
  cluster_identifier = "ordnungshub-db"
  engine = "aurora-postgresql"
  engine_mode = "serverless"
  
  scaling_configuration {
    min_capacity = 2
    max_capacity = 16
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id = "ordnungshub-cache"
  engine = "redis"
  node_type = "cache.t3.micro"
}
```

---

## Monitoring and Scaling

### CloudWatch Dashboards
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name OrdnungsHub \
  --dashboard-body file://dashboard.json
```

### Auto Scaling
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ordnungshub-cluster/ordnungshub-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/ordnungshub-cluster/ordnungshub-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## 🎉 Your App is Live on AWS!

### Access Points
- **Load Balancer**: `ordnungshub-alb-xxx.region.elb.amazonaws.com`
- **CloudFront**: Add for global distribution
- **Route 53**: Configure custom domain

### Cost Optimization
- Use Fargate Spot for 70% savings
- Enable auto-scaling
- Use Aurora Serverless for database
- Configure lifecycle policies for logs

### Security Best Practices
- Use AWS WAF for protection
- Enable AWS Shield
- Implement VPC endpoints
- Use AWS Secrets Manager
- Enable container insights