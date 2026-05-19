# Wisecow — AccuKnox DevOps Assessment

Containerization and deployment of the [Wisecow](https://github.com/nyrahul/wisecow) application on Kubernetes with CI/CD and TLS.

---

## Repository Structure

```
wisecow/
├── wisecow.sh                        # Original app source
├── Dockerfile                        # Container image definition
├── generate-tls.sh                   # Self-signed TLS cert helper script
├── k8s/
│   ├── deployment.yaml               # Kubernetes Deployment (2 replicas)
│   ├── service.yaml                  # ClusterIP Service
│   └── ingress.yaml                  # Nginx Ingress with TLS
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD: build → push → deploy
├── scripts/
│   ├── system_health.py              # PS2: System health monitor
│   └── app_health_checker.py         # PS2: App uptime checker
└── kubearmor/
    ├── policy.yaml                   # PS3: Zero-trust KubeArmor policy
    └── violation-screenshot.png      # PS3: Screenshot of policy violation
```

---

## Problem Statement 1 — Wisecow on Kubernetes

### Prerequisites

- Docker
- Kind (`brew install kind` on macOS)
- kubectl (`brew install kubectl`)
- Helm (`brew install helm`)

---

### Step 1 — Create Kind Cluster

```bash
kind create cluster --name wisecow
kubectl cluster-info --context kind-wisecow
```

### Step 2 — Install Nginx Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Step 3 — Build Docker Image Locally (for testing)

```bash
docker build -t wisecow:local .
kind load docker-image wisecow:local --name wisecow
```

### Step 4 — TLS Setup (Self-signed)

```bash
chmod +x generate-tls.sh
./generate-tls.sh
```

Then add to `/etc/hosts`:
```
127.0.0.1  wisecow.local
```

### Step 5 — Deploy to Kubernetes

> **Before deploying**, update `k8s/deployment.yaml` — replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods
kubectl get svc
kubectl get ingress
```

### Step 6 — Test

```bash
# Port-forward for quick test (no ingress needed)
kubectl port-forward svc/wisecow-service 8080:80
curl http://localhost:8080

# With TLS via ingress
curl -k https://wisecow.local
```

---

## CI/CD — GitHub Actions

### How it works

| Trigger | Job | What happens |
|---|---|---|
| Push to `main` | `build-and-push` | Builds Docker image, pushes to GHCR with `latest` + `sha-XXXXXX` tags |
| Push to `main` (after build) | `deploy` | Updates K8s deployment image, waits for rollout |
| Pull request | `build-and-push` | Builds image only (no push, no deploy) |

### Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `KUBE_CONFIG` | `cat ~/.kube/config \| base64` (your cluster kubeconfig, base64-encoded) |

> `GITHUB_TOKEN` is automatic — no setup needed for GHCR push.

### Image URL

After first push, your image will be at:
```
ghcr.io/YOUR_GITHUB_USERNAME/wisecow:latest
```

---

## Problem Statement 2 — Scripts

### Script 1: System Health Monitor

```bash
pip install psutil
python scripts/system_health.py
```

Monitors CPU, memory, disk, and process count every 10 seconds.  
Alerts logged to `health_monitor.log` when any threshold is exceeded.

**Thresholds (configurable at top of file):**
- CPU > 80%
- Memory > 80%
- Disk > 85%
- Processes > 300

### Script 2: Application Health Checker

```bash
pip install requests
python scripts/app_health_checker.py

# Or pass URLs directly:
python scripts/app_health_checker.py https://example.com https://api.myapp.com
```

Checks HTTP status codes every 30 seconds, reports UP/DOWN with response time.  
Results logged to `app_health.log`.

---

## Problem Statement 3 — KubeArmor Zero-Trust Policy

### Install KubeArmor

```bash
helm repo add kubearmor https://kubearmor.github.io/charts
helm repo update
helm upgrade --install kubearmor kubearmor/kubearmor -n kube-system
```

### Install karmor CLI

```bash
curl -sfL https://raw.githubusercontent.com/kubearmor/KubeArmor/main/contrib/get-karmor.sh | sh
```

### Apply the Policy

```bash
kubectl apply -f kubearmor/policy.yaml

# Verify
kubectl get kubearmorpolicy -n default
```

### Trigger and View a Violation

```bash
# Exec into the pod
kubectl exec -it $(kubectl get pod -l app=wisecow -o jsonpath='{.items[0].metadata.name}') -- bash

# Try something that should be blocked (e.g., curl, wget, apt)
curl https://google.com     # this should be blocked/logged
apt update                  # this should be blocked/logged
```

View violations:
```bash
# Using karmor
karmor log --namespace default

# Or via KubeArmor pod logs
kubectl logs -n kube-system -l kubearmor-app=kubearmor --tail=50
```

Take a screenshot of the violation output and save it as `kubearmor/violation-screenshot.png`.

---

## Access

Repository access has been granted to: **nyrahul**
