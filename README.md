# FocusFlow — CI/CD Pipeline with Jenkins & Kubernetes

A full CI/CD pipeline for **FocusFlow**, a lightweight Flask task-management app. On every push to `main`, Jenkins automatically tests the app, builds and pushes a versioned Docker image to Docker Hub, and updates the Kubernetes deployment manifest so the cluster always runs the latest build.

The Jenkins server itself is provisioned on AWS EC2 using **Ansible** (a one-time setup step, separate from the pipeline).

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Application](#application)
- [Prerequisites](#prerequisites)
- [Initial Server Setup (Ansible)](#initial-server-setup-ansible)
- [Jenkins Configuration](#jenkins-configuration)
- [CI/CD Pipeline](#cicd-pipeline)
- [Kubernetes Manifests](#kubernetes-manifests)
- [Local Development](#local-development)
- [Running Tests](#running-tests)
- [Deployment Flow](#deployment-flow)
- [Credentials Reference](#credentials-reference)

---

## Architecture Overview

```
Developer pushes to main
          │
          ▼
      Jenkins (on EC2)
          │
          ├── Stage 1: Test
          │     └── Run pytest inside python:3.12-alpine container
          │
          ├── Stage 2: Build & Push
          │     └── docker build → docker push devopstimi/focusflow-cicd:<BUILD_NUMBER>
          │
          └── Stage 3: Update Deployment File
                └── sed replaceImageTag → <BUILD_NUMBER> in deploy/deployment.yml
                    └── git commit & push to GitHub
                              │
                              ▼
                    ArgoCD / GitOps operator detects change
                              │
                              ▼
                    Kubernetes cluster pulls new image
                    and rolls out updated Deployment (2 replicas)
```

The pipeline follows a **GitOps pattern**: Jenkins does not deploy directly to Kubernetes. Instead, it updates the image tag in the Git repository, and a GitOps tool (e.g., ArgoCD) detects the change and syncs the cluster.

---

## Project Structure

```
cicd-focusflow-deploy/
├── Dockerfile                    # Containerizes the Flask app
├── Jenkinsfile                   # Declarative pipeline: test → build → update manifest
├── requirements.txt              # Python dependencies (Flask, pytest)
├── run.py                        # App entry point
├── ansible/
│   ├── inventory.ini             # EC2 host + SSH config for Ansible
│   └── setup-pipe.yml            # Playbook: installs Jenkins, Docker, Java on EC2
├── app/
│   ├── __init__.py               # Flask app factory
│   ├── models.py                 # In-memory task store
│   ├── routes.py                 # Blueprint: task list, add, toggle
│   ├── static/
│   │   ├── app.js                # Frontend JavaScript
│   │   └── style.css             # Stylesheet
│   └── templates/
│       ├── base.html             # Base layout
│       └── tasks.html            # Task list page
├── deploy/
│   ├── deployment.yml            # Kubernetes Deployment (2 replicas, image tag placeholder)
│   └── service.yml               # Kubernetes Service (NodePort, port 80 → 5000)
└── tests/
    └── test_app.py               # Pytest suite: page load, add task, toggle task
```

---

## Application

FocusFlow is a minimal **Flask** task manager with an in-memory task store.

- **Framework:** Flask
- **Port:** `5000`
- **Entry point:** `run.py` → `app.create_app()`
- **Storage:** In-memory list (resets on container restart — no database)

### Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Renders the task list |
| `POST` | `/` | Adds a new task (form field: `title`) |
| `POST` | `/toggle/<task_id>` | Toggles a task's completed status (returns `204`) |

---

## Prerequisites

- An **AWS EC2 instance** running Ubuntu (to host Jenkins)
- A **Docker Hub account** with a repository named `focusflow-cicd`
- A **GitHub account** with a personal access token (for the pipeline to push commits)
- A **Kubernetes cluster** with a GitOps operator (e.g., ArgoCD) watching this repository
- **Ansible** installed on your local machine (for the one-time Jenkins setup)

---

## Initial Server Setup (Ansible)

> **Note:** The `ansible/` folder is a **one-time bootstrapping tool**, not part of the automated pipeline. Run it once to provision the EC2 instance with Jenkins. After that, all automation is handled by Jenkins itself.

### What the Playbook Does

`ansible/setup-pipe.yml` performs the following on the target EC2 host:

1. Updates the apt package cache
2. Installs `docker.io`
3. Installs **OpenJDK 21** (required by Jenkins)
4. Adds the Jenkins apt signing key and repository
5. Installs **Jenkins**
6. Starts and enables the Jenkins systemd service

### Running the Playbook

1. Update `ansible/inventory.ini` with your EC2 instance's public IP and the path to your SSH key:

```ini
<YOUR_EC2_IP> ansible_user=ubuntu ansible_ssh_private_key_file=/path/to/your-key.pem
```

2. Run the playbook:

```bash
ansible-playbook -i ansible/inventory.ini ansible/setup-pipe.yml
```

3. Once complete, access Jenkins at `http://<YOUR_EC2_IP>:8080` to complete the initial setup wizard.

---

## Jenkins Configuration

After provisioning, configure Jenkins with the following before running the pipeline:

### Install Plugins

- **Docker Pipeline** — allows pipeline stages to run inside Docker containers
- **Git** — for cloning and pushing to GitHub

### Add Credentials

Navigate to **Manage Jenkins → Credentials** and add:

| Credential ID | Type | Description |
|---------------|------|-------------|
| `docker-cred` | Username with password | Docker Hub username and password/token |
| `github` | Secret text | GitHub personal access token (with `repo` scope) |

### Create a Pipeline Job

1. New Item → Pipeline
2. Under **Pipeline**, set **Definition** to `Pipeline script from SCM`
3. Set SCM to **Git** and point to this repository
4. Set **Script Path** to `Jenkinsfile`
5. Enable **GitHub hook trigger for GITScm polling** (or configure a webhook)

---

## CI/CD Pipeline

The `Jenkinsfile` defines a declarative pipeline with three stages.

### Stage 1: Test App

Runs inside a `python:3.12-alpine` Docker container (as root, using `-u 0`).

```
pip install -r requirements.txt
python3 -m pytest tests/test_app.py
```

If any test fails, the pipeline stops here and the image is never built or pushed.

### Stage 2: Build and Push Docker Image

Runs on the Jenkins agent directly. The image is tagged with Jenkins' `BUILD_NUMBER` for full traceability.

```
Image: devopstimi/focusflow-cicd:<BUILD_NUMBER>
Registry: Docker Hub (index.docker.io/v1/)
Credentials: docker-cred
```

### Stage 3: Update Deployment File

Clones the repository into a temporary directory, replaces the `replaceImageTag` placeholder in `deploy/deployment.yml` with the current `BUILD_NUMBER`, commits, and pushes back to `main`.

```bash
sed -i "s/replaceImageTag/${BUILD_NUMBER}/g" deploy/deployment.yml
git commit -m "Update deployment image to version ${BUILD_NUMBER}"
git push origin main
```

This commit triggers the GitOps operator to reconcile the cluster with the new image tag.

---

## Kubernetes Manifests

### `deploy/deployment.yml`

Deploys the app as a Kubernetes **Deployment** with 2 replicas.

| Field | Value |
|-------|-------|
| Name | `focusflow-app` |
| Namespace | `default` |
| Replicas | `2` |
| Container port | `5000` |
| Image | `devopstimi/focusflow-cicd:replaceImageTag` ← updated by pipeline |

### `deploy/service.yml`

Exposes the deployment via a Kubernetes **Service**.

| Field | Value |
|-------|-------|
| Name | `focusflow-service` |
| Type | `NodePort` |
| Service port | `80` |
| Target port | `5000` |

> The `nodePort: 30500` line is commented out — Kubernetes will assign a random NodePort unless you uncomment and set a specific value.

### Applying Manifests Manually

If not using a GitOps operator, you can apply the manifests directly:

```bash
kubectl apply -f deploy/deployment.yml
kubectl apply -f deploy/service.yml
```

---

## Local Development

### Without Docker

```bash
pip install -r requirements.txt
python run.py
```

App available at `http://localhost:5000`.

### With Docker

```bash
docker build -t focusflow-cicd .
docker run -p 5000:5000 focusflow-cicd
```

App available at `http://localhost:5000`.

---

## Running Tests

```bash
pip install -r requirements.txt
python3 -m pytest tests/test_app.py
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_page_loads` | GET `/` returns HTTP 200 and contains "FocusFlow" in the response |
| `test_add_task` | POST to `/` with a title, then GET `/` to confirm the task appears |
| `test_toggle_task` | POST to `/toggle/1` returns HTTP 204 (no content) |

---

## Deployment Flow

```
git push → main
      │
      ▼
Jenkins Pipeline triggered
      │
      ├── [Stage 1] pytest inside python:3.12-alpine
      │       └── PASS → continue  |  FAIL → pipeline stops
      │
      ├── [Stage 2] docker build -t devopstimi/focusflow-cicd:<N> .
      │             docker push devopstimi/focusflow-cicd:<N>
      │
      └── [Stage 3] Clone repo → sed replaceImageTag → <N>
                    git commit "Update deployment image to version <N>"
                    git push → main
                          │
                          ▼
                  ArgoCD detects deploy/deployment.yml change
                          │
                          ▼
                  kubectl apply → Kubernetes rolls out
                  devopstimi/focusflow-cicd:<N> across 2 replicas
```

---

## Credentials Reference

| Credential ID | Where Used | What It Is |
|---------------|------------|------------|
| `docker-cred` | Stage 2 — `docker.withRegistry(...)` | Docker Hub username + password/access token |
| `github` | Stage 3 — `withCredentials([string(...)])` | GitHub personal access token with `repo` write scope |