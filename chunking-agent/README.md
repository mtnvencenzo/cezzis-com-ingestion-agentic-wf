## CloudSync
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync.yaml

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-cloudsync.yaml
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync.yaml

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-cloudsync.yaml
```

## Local
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc.yaml

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-loc.yaml
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc.yaml

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-loc.yaml
```