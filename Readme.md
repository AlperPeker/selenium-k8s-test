# Distributed Selenium Testing on Kubernetes (AWS EKS)

This is a demonstrative project for a distributed testing infrastructure utilizing **Selenium Grid** on **Kubernetes**. The system can be run both on the cloud (**AWS EKS**) and a local kubernetes distribution (**Minikube**). The system runs are automated using a **Python** script for both scenerios.

## System Overview

The architecture follows a "Controller-Worker" pattern deployed on Kubernetes:

1.  **Test Controller Pod:**
    * A Python container running the test logic (`test-main.py`).
    * Manages the runs of tests on the worker (Chrome) nodes.

2.  **Chrome Node Pods (Selenium Grid):**
    * Scalable worker nodes running Headless Chrome and ChromeDriver.
    * They execute the actual browser commands sent by the controller.
    * Managed by a Kubernetes Deployment for scaling the number of browsers (e.g., `--node-count 5`).

3.  **Orchestrator:**
    * An all in one script (`orchestrator.py`) that automates infrastructure management: creating the K8s cluster (on AWS), installing Helm charts, and triggering the test job.

### Inter-Pod Communication

Communication between the Controller and the Nodes is handled via Kubernetes **ClusterIP Services**:

* **Service Discovery:** A Kubernetes Service named `selenium-chrome-service` exposes the Chrome pods on port `4444`.
* **Pod to Pod Connection:** Test controller pods uses the service name and port to connect to the Active Chrome nodes. The connection is established by Kubernetes using Cluster IP which can direct the connections using the service name.

---

## Deployment Guide

### Prerequisites
* Docker
* Kubernetes CLI (`kubectl`)
* Helm
* AWS CLI (configured for EKS access)
* `eksctl` (for creating AWS clusters)
* Minikube (optional, for local testing)

### Option 1: Running on AWS EKS (Cloud)

1.  **Configure AWS Credentials:**
    ```bash
    aws configure
    ```
2.  **Create the Cluster:**
    You can use the orchestrator or `eksctl` manually:
    ```bash
    eksctl create cluster --name insider-selenium-cluster --region eu-central-1 --nodegroup-name standard-workers --node-type t3.small --nodes 2
    ```
3.  **Deploy and Run Tests:**
    Run the orchestrator script to deploy Helm charts and start the test job:
    ```bash
    python3 orchestrator.py --node-count 2
    ```

### Option 2A: Running Locally with Automation Script (Minikube)

1.  Start Minikube:
    ```bash
    minikube start
    ```
2.  Run the Orchestrator:
    ```bash
    python3 orchestrator.py --node-count 1
    ```

### Option 2B: Running Locally and Manually (Minikube)

1.  Start Minikube:
    ```bash
    minikube start
    ```
2.  Apply the Kubernetes manifest file:
    ```bash
    kubectl apply -f services.yaml
    ```

Check the logs of the Kubernetes pods to confirm system runs without issues. 
NOTE: Even if you run multiple Chrome nodes, a single test session will be routed to one available node by the Kubernetes Service (Load Balancing).

---

## Project Structure

* **test-main.py**: The core Selenium test logic (Client) that executes the Insider QA test scenario.
* **orchestrator.py**: Python automation script to manage AWS EKS cluster creation, Helm deployment, and test execution.
* **Dockerfile**: Docker definition for building the Test Controller image.
* **services.yaml**: Kubernetes service, deployment and job manifest for application via kubectl.
* **helm/**: The directory containing the Kubernetes Helm Chart.
* **helm/values.yaml**: Configuration file to control image names, replica counts (node count), and resources.
* **helm/templates/**: Contains the Kubernetes YAML manifests (Deployment, Service, Job).
* **README.md**: Project documentation and setup guide.