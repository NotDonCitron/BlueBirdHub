# BlueBirdHub Docker Deployment

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/BlueBirdHub.git
cd BlueBirdHub

# 2. Set up environment
cp config/env.example .env.production
# Edit .env.production with your values

# 3. Deploy
docker-compose -f docker-compose.bluebbird.yml up -d --build
```

## Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Essential Commands

```bash
# View logs
docker-compose -f docker-compose.bluebbird.yml logs -f

# Stop services
docker-compose -f docker-compose.bluebbird.yml down

# Restart services
docker-compose -f docker-compose.bluebbird.yml restart

# Access backend shell
docker-compose -f docker-compose.bluebbird.yml exec bluebbird-backend bash
```

## Required Environment Variables

Edit `.env.production` with these required values:

- `DB_PASSWORD` - Database password
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT secret key
- `REDIS_PASSWORD` - Redis password
- At least one AI API key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.)

## Files

- `docker-compose.bluebbird.yml` - Simplified Docker Compose configuration
- `docker-compose.yml` - Original configuration (uses "ordnungshub" naming)
- `Dockerfile` - Application container definition
- `config/env.example` - Environment template
- `scripts/deploy-docker.sh` - Automated deployment script

## Troubleshooting

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Container won't start**: Check logs with `docker-compose logs`
3. **Database issues**: Verify DB_PASSWORD is set correctly
4. **Health check fails**: Ensure all required env vars are set

For detailed instructions, see [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md) 