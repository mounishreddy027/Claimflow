# Deployment Architecture — ClaimFlow

Complete deployment strategy spanning development, staging, and production environments with CI/CD pipeline and infrastructure topology.

## Deployment Environments

### Development (Local)

**Stack**
- Docker Compose orchestration
- Python 3.11+ FastAPI backend (hot reload)
- React 18+ frontend dev server (hot reload)
- PostgreSQL 14+ database
- Local filesystem for document storage

**Startup**
```bash
./init.sh
```

**Containers**
- `claimflow-backend`: FastAPI on port 8000
- `claimflow-frontend`: React dev server on port 3000
- `claimflow-db`: PostgreSQL on port 5432
- `claimflow-redis`: Redis cache (optional, for future)

**File: docker-compose.yml**
```yaml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@claimflow-db:5432/claimflow
      ENVIRONMENT: development
      DEBUG: "true"
    volumes:
      - ./backend/src:/app/src:cached
    depends_on:
      - db
    command: "uvicorn claimflow.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000/api
    volumes:
      - ./frontend/src:/app/src:cached
    command: "npm start"

  db:
    image: postgres:14-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: claimflow
    volumes:
      - claimflow_db_data:/var/lib/postgresql/data

volumes:
  claimflow_db_data:
```

**Database Initialization**
```bash
# Run migrations
alembic upgrade head

# Seed test data
python scripts/seed_test_data.py
```

---

### Staging

**Stack**
- Docker containers on staging cluster (Kubernetes or Docker Swarm)
- Python 3.11 FastAPI backend (no hot reload)
- React 18 frontend (static build)
- PostgreSQL 14 database with daily snapshots
- S3 for document storage
- CloudFront CDN for static assets
- Secrets management: AWS Secrets Manager

**Deployment**
```bash
# Build production Docker images
docker build -t claimflow-backend:latest -f Dockerfile.backend ./backend
docker build -t claimflow-frontend:latest -f Dockerfile.frontend ./frontend

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag claimflow-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:staging
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:staging

# Deploy to Kubernetes
kubectl apply -f k8s/staging/deployment.yaml
```

**Configuration**
- Environment: ENVIRONMENT=staging
- Database: PostgreSQL on managed RDS
- Backup: Automated daily snapshots to S3
- Logging: CloudWatch logs
- Monitoring: Prometheus + Grafana

**Health Checks**
- Readiness probe: GET /api/health
- Liveness probe: TCP port 8000
- Interval: 10s
- Timeout: 5s

---

### Production

**Stack**
- Kubernetes cluster with auto-scaling (AWS EKS or GKE)
- Python 3.11 FastAPI backend (stateless)
- React 18 frontend (static build on CloudFront)
- PostgreSQL 14 with automated failover (Multi-AZ)
- S3 for document storage with encryption
- Secrets management: AWS Secrets Manager or HashiCorp Vault
- Load balancing: AWS ALB
- Rate limiting: API Gateway with WAF rules
- Monitoring: CloudWatch, Prometheus, Grafana
- Logging: ELK stack or Splunk
- Backup: Automated hourly snapshots with 30-day retention

**Deployment**
```bash
# Manual approval required before prod deployment
# CI/CD pipeline creates release candidate
# Manual approval triggers:

# 1. Scale up production database
kubectl patch statefulset claimflow-db -p '{"spec":{"replicas":3}}'

# 2. Deploy new backend version (rolling update)
kubectl set image deployment/claimflow-backend claimflow-backend=claimflow-backend:v1.2.3

# 3. Run smoke tests
./scripts/smoke-tests.sh --environment production

# 4. Deploy frontend (blue-green)
# Old frontend on /static/v1.2.2/
# New frontend on /static/v1.2.3/
# Wait 5 minutes for client redirects
# Switch CloudFront cache invalidation to new version
# Monitor error rates for 15 minutes
# If errors < 0.1%, mark deployment as successful
```

**Database Replication**
- Primary: Writable in us-east-1
- Read replicas in us-west-2 (async replication)
- Failover: Automatic on primary failure (RTO < 2 min)

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File: .github/workflows/build-test-deploy.yml**

```yaml
name: Build, Test, Deploy

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # Stage 1: Lint & Type Check (on every push)
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install uv
          uv sync
      
      - name: Lint with ruff
        run: cd backend && uv run ruff check .
      
      - name: Type check with mypy
        run: cd backend && uv run mypy src/
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Lint frontend
        run: |
          cd frontend
          npm ci
          npm run lint
      
      - name: Type check frontend
        run: cd frontend && npm run typecheck

  # Stage 2: Unit & Integration Tests
  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14-alpine
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: claimflow_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install uv
          uv sync
      
      - name: Run backend tests
        env:
          DATABASE_URL: postgresql://postgres:password@localhost:5432/claimflow_test
        run: cd backend && uv run pytest -x -q --cov=src
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm ci
          npm test -- --coverage --watchAll=false

  # Stage 3: Build Docker Images (on main branch only)
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to ECR
        uses: aws-actions/amazon-ecr-login@v1
        env:
          AWS_REGION: us-east-1
      
      - name: Build and push backend image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          file: ./backend/Dockerfile.backend
          push: true
          tags: |
            123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:${{ github.sha }}
            123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:${{ github.ref_name }}-latest
      
      - name: Build and push frontend image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          file: ./frontend/Dockerfile.frontend
          push: true
          tags: |
            123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-frontend:${{ github.sha }}
            123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-frontend:${{ github.ref_name }}-latest

  # Stage 4: Deploy to Staging
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: us-east-1
      
      - name: Update EKS kubeconfig
        run: |
          aws eks update-kubeconfig --region us-east-1 --name claimflow-staging
      
      - name: Deploy to staging
        run: |
          kubectl set image deployment/claimflow-backend \
            claimflow-backend=123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:${{ github.sha }} \
            --namespace=claimflow-staging
          kubectl set image deployment/claimflow-frontend \
            claimflow-frontend=123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-frontend:${{ github.sha }} \
            --namespace=claimflow-staging
      
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/claimflow-backend --namespace=claimflow-staging
          kubectl rollout status deployment/claimflow-frontend --namespace=claimflow-staging

  # Stage 5: E2E Tests on Staging
  e2e-staging:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Playwright
        run: npx playwright install
      
      - name: Run E2E tests on staging
        env:
          REACT_APP_API_URL: https://api-staging.claimflow.io/api
        run: cd frontend && npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/

  # Stage 6: Manual Approval for Production (on main branch)
  approve-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Request manual approval
        run: |
          echo "::notice::Production deployment requires manual approval. Review test results and approve in GitHub Actions."

  # Stage 7: Deploy to Production (manual approval required)
  deploy-production:
    needs: [build, approve-production]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://claimflow.io
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: us-east-1
      
      - name: Update EKS kubeconfig
        run: |
          aws eks update-kubeconfig --region us-east-1 --name claimflow-production
      
      - name: Blue-Green Deployment
        run: |
          # Deploy new version (green) alongside old (blue)
          kubectl set image deployment/claimflow-backend-green \
            claimflow-backend=123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:${{ github.sha }} \
            --namespace=claimflow-production
          
          # Wait for green to be ready
          kubectl rollout status deployment/claimflow-backend-green --namespace=claimflow-production
          
          # Run smoke tests on green
          ./scripts/smoke-tests.sh --environment production --target green
          
          # Switch traffic to green
          kubectl patch service claimflow-api -p '{"spec":{"selector":{"version":"green"}}}' \
            --namespace=claimflow-production
          
          # Monitor for 15 minutes
          sleep 900
          
          # Check error rate
          ERROR_RATE=$(kubectl logs -l app=claimflow-backend,version=green --namespace=claimflow-production --tail=1000 | grep "ERROR" | wc -l)
          if [ $ERROR_RATE -gt 10 ]; then
            # Rollback to blue
            kubectl patch service claimflow-api -p '{"spec":{"selector":{"version":"blue"}}}' \
              --namespace=claimflow-production
            exit 1
          fi
          
          # Decommission blue
          kubectl scale deployment claimflow-backend-blue --replicas=0 --namespace=claimflow-production
```

---

## Database Migrations

**Tool: Alembic**

```bash
# Create migration
alembic revision --autogenerate -m "Add Settlement table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Migration Versioning**
- Semantic versioning: 001_initial_schema.py, 002_immutability_triggers.py
- Immutability triggers applied in separate migration
- Zero-downtime migrations (add columns as nullable first)

---

## Secrets Management

### Development (Local)

**File: .env.local** (git-ignored)
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/claimflow
DEBUG=true
SECRET_KEY=dev-key-not-for-production
```

### Staging & Production

**AWS Secrets Manager**

```bash
# Store secret
aws secretsmanager create-secret --name claimflow/staging/database-url \
  --secret-string "postgresql://user:pass@host:5432/claimflow"

# Retrieve secret in deployment
DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id claimflow/staging/database-url --query SecretString --output text)
```

**Rotated Secrets**
- Database passwords: rotated every 90 days
- API keys: rotated every 30 days
- JWT secrets: rotated on deployment

---

## Infrastructure as Code

**Kubernetes Manifests (k8s/production/)**

```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claimflow-backend
  namespace: claimflow-production
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: claimflow-backend
  template:
    metadata:
      labels:
        app: claimflow-backend
    spec:
      containers:
      - name: claimflow-backend
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/claimflow-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: claimflow-secrets
              key: database-url
        - name: ENVIRONMENT
          value: production
        livenessProbe:
          tcpSocket:
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
```

---

## Monitoring & Observability

### Application Metrics

- Request latency (histogram)
- Error rate (counter)
- Fraud score distribution (histogram)
- Settlement success rate (gauge)
- Document upload size distribution (histogram)

### Infrastructure Metrics

- CPU utilization
- Memory utilization
- Disk usage
- Network I/O
- Database query latency
- Database connection pool size

### Logging

**Structured JSON logging**

```json
{
  "timestamp": "2026-10-04T14:30:00Z",
  "correlation_id": "corr-uuid-123",
  "level": "INFO",
  "module": "claim_intake",
  "message": "Claim filed successfully",
  "claim_id": "claim-uuid",
  "actor_id": "customer-uuid",
  "actor_role": "ROLE_CUSTOMER",
  "duration_ms": 245
}
```

### Alerting

- Error rate > 1% → Page oncall
- Latency p99 > 1 second → Notify team
- Database disk usage > 80% → Notify ops
- Failed healthchecks → Immediate rollback

---

## Rollback Procedure

**Automatic Rollback**
- Error rate > 1% after 5 minutes → Automatic rollback
- Liveness probe failures → Automatic pod restart
- OOM kills → Automatic pod restart

**Manual Rollback**
```bash
# Check deployment history
kubectl rollout history deployment/claimflow-backend -n claimflow-production

# Rollback to previous version
kubectl rollout undo deployment/claimflow-backend -n claimflow-production
```

**Time to Recovery**
- RTO (Recovery Time Objective): 5 minutes
- RPO (Recovery Point Objective): 15 minutes (hourly database snapshots)

---

## Disaster Recovery

**Backup Strategy**
- Database: hourly snapshots, 30-day retention
- Document storage: cross-region replication
- Configuration: version controlled in Git
- Secrets: AWS Secrets Manager with audit trail

**Recovery Time Estimates**
- Database restoration: 10 minutes
- Full environment restoration: 30 minutes
- Partial data recovery: 1 hour (query backup logs)

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Claim intake endpoint | < 200ms p95 |
| Fraud evaluation | < 500ms p95 |
| Assessment decision | < 300ms p95 |
| Settlement confirmation | < 200ms p95 |
| API availability | 99.95% SLA |
| Database durability | RPO 15 minutes |

---

## Cost Optimization

**Staging**
- Auto-scale down to 1 replica after 6 PM
- Spot instances for non-critical workloads
- Estimated: $500/month

**Production**
- Reserve 70% of compute capacity (RI discount)
- Auto-scale 1-5 replicas based on load
- Multi-AZ for failover (no cost difference for RDS)
- Estimated: $3,000/month

---

## Summary

ClaimFlow deployment follows:
- **Development**: Docker Compose with hot reload for rapid iteration
- **Staging**: Full-featured copy of production for testing
- **Production**: Kubernetes with blue-green deployments, auto-scaling, and comprehensive monitoring
- **CI/CD**: GitHub Actions pipeline with automatic testing and manual approval gates
- **Disaster Recovery**: Hourly snapshots with 30-minute RTO
- **Compliance**: Encrypted secrets, audit trails, immutable records on disk
