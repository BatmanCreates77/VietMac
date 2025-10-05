# VietMac Compare - Docker Setup

This guide explains how to run VietMac Compare using Docker and Docker Compose.

## Prerequisites

- Docker Desktop installed (Mac/Windows) or Docker Engine (Linux)
- Docker Compose (included with Docker Desktop)

## Quick Start

### Development Mode (with hot reload)

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.dev.yml up -d --build
```

The application will be available at:
- **App**: http://localhost:3000
- **MongoDB Express**: http://localhost:8081 (admin/admin123)
- **MongoDB**: localhost:27017

### Production Mode

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

## Services

### 1. **VietMac App** (Next.js)
- Port: 3000
- Live price scraping from Vietnamese marketplaces
- Real-time currency conversion

### 2. **MongoDB**
- Port: 27017
- Persistent data storage
- Database: `vietmac_db`

### 3. **MongoDB Express** (Database UI)
- Port: 8081
- Username: `admin`
- Password: `admin123`
- View and manage database directly

## Docker Commands

### Start Services
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up
```

### Stop Services
```bash
# Development
docker-compose -f docker-compose.dev.yml down

# Production
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f mongo
```

### Rebuild After Code Changes
```bash
# Development (with hot reload, rebuilds automatically)
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose up --build
```

### Clean Up (Remove volumes and containers)
```bash
# Development
docker-compose -f docker-compose.dev.yml down -v

# Production
docker-compose down -v
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_URL=mongodb://mongo:27017
DB_NAME=vietmac_db

# Application
NEXT_PUBLIC_BASE_URL=http://localhost:3000
CORS_ORIGINS=*
NODE_ENV=development
```

## Development Workflow

1. **Make code changes** - Hot reload will automatically update the app
2. **View changes** - Go to http://localhost:3000
3. **Check database** - Go to http://localhost:8081 (MongoDB Express)
4. **View logs** - Run `docker-compose -f docker-compose.dev.yml logs -f app`

## Production Deployment

For production deployment to platforms like AWS, Azure, or DigitalOcean:

```bash
# Build production image
docker build -t vietmac-app .

# Tag for registry
docker tag vietmac-app your-registry/vietmac-app:latest

# Push to registry
docker push your-registry/vietmac-app:latest
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -ti:3000

# Kill the process
kill -9 <PID>
```

### MongoDB Connection Issues
```bash
# Check MongoDB is running
docker-compose ps

# Restart MongoDB
docker-compose restart mongo
```

### Clear Cache and Rebuild
```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build --force-recreate
```

## Features with Docker

✅ **Isolated environment** - No conflicts with local installations
✅ **Consistent setup** - Same environment for all developers
✅ **Easy MongoDB** - Database ready out of the box
✅ **Hot reload** - Development changes update instantly
✅ **Production ready** - Optimized build for deployment
✅ **Multiple services** - App, database, and admin UI together

## Performance Notes

- **Development mode**: Uses more resources for hot reload
- **Production mode**: Optimized and smaller image size
- **MongoDB**: Persists data in Docker volumes
- **Network**: Services communicate through Docker network

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Restart services: `docker-compose restart`
- Clean rebuild: `docker-compose down -v && docker-compose up --build`
