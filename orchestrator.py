import subprocess
import time
import argparse
import sys
import os

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

CHART_PATH = "./helm"
RELEASE_NAME = "insider-test"
MAX_RETRIES = 30

def execute(command, ignore_errors=False):
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"\n{RED}[ERROR] Command failed: {command}{RESET}")
            print(f"{RED}{e.stderr.strip()}{RESET}\n")
        return None

def check_prerequisites():
    if not os.path.exists(CHART_PATH):
        print(f"{RED}[ERROR] Helm chart not found at '{CHART_PATH}'{RESET}")
        sys.exit(1)

def cleanup():
    print(f"{YELLOW}[Cleanup] Removing existing resources...{RESET}")
    execute(f"helm uninstall {RELEASE_NAME}", ignore_errors=True)
    
    resources = [
        "service/selenium-chrome-service",
        "deployment/chrome-node",
        "job/test-controller-job"
    ]
    for res in resources:
        execute(f"kubectl delete {res} --ignore-not-found=true", ignore_errors=True)
    
    time.sleep(5)

def deploy(node_count):
    print(f"{GREEN}[Deploy] Installing Helm chart (Nodes: {node_count})...{RESET}")
    cmd = f"helm install {RELEASE_NAME} {CHART_PATH} --set chrome.nodeCount={node_count}"
    if execute(cmd) is not None:
        print(f"{GREEN}   -> Deployment successful.{RESET}")
    else:
        sys.exit(1)

def health_check(node_count):
    print(f"{YELLOW}[Health Check] Waiting for Chrome Nodes...{RESET}")
    for i in range(MAX_RETRIES):
        res = execute("kubectl get pods -l app=chrome-node --no-headers | grep Running | wc -l")
        ready_count = int(res) if res and res.strip().isdigit() else 0
        
        if ready_count == node_count:
            print(f"{GREEN}   -> All {node_count} nodes are ready.{RESET}")
            return
        
        print(f"   -> Waiting... ({ready_count}/{node_count} ready) - Attempt {i+1}/{MAX_RETRIES}")
        time.sleep(5)
    
    print(f"{RED}[TIMEOUT] Nodes did not become ready.{RESET}")
    sys.exit(1)

def run_tests():
    print(f"{YELLOW}[Test Execution] Waiting for test completion...{RESET}")
    
    job_name = ""
    for _ in range(10):
        res = execute("kubectl get jobs -l app.kubernetes.io/managed-by=Helm --no-headers -o custom-columns=':metadata.name'", ignore_errors=True)
        if res:
            job_name = res.split()[0]
            break
        time.sleep(2)

    if not job_name:
        print(f"{RED}[ERROR] Test job not found.{RESET}")
        sys.exit(1)

    print(f"   -> Job found: {job_name}")
    execute(f"kubectl wait --for=condition=complete job/{job_name} --timeout=120s", ignore_errors=True)
    
    print(f"\n{GREEN}--- TEST LOGS ---{RESET}")
    logs = execute(f"kubectl logs job/{job_name}")
    if logs:
        print(logs)
        if "OK" in logs:
            print(f"\n{GREEN}[SUCCESS] Test Pipeline Completed.{RESET}")
        else:
            print(f"\n{RED}[FAILURE] Tests Failed.{RESET}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-count", type=int, default=1)
    args = parser.parse_args()

    check_prerequisites()
    cleanup()
    deploy(args.node_count)
    health_check(args.node_count)
    run_tests()

if __name__ == "__main__":
    main()