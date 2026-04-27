## CloudSync
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync.yaml

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-cloudsync.yaml
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync.yaml

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-cloudsync.yaml
```

The Argo CD Application manifest includes the `resources-finalizer.argocd.argoproj.io` finalizer so deleting the Application also cascades deletion to the managed Kubernetes resources.

## Local
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc.yaml

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-loc.yaml
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc.yaml

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-loc.yaml
```

The Argo CD Application manifest includes the `resources-finalizer.argocd.argoproj.io` finalizer so deleting the Application also cascades deletion to the managed Kubernetes resources.