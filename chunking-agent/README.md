## CloudSync
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync
```

## Local
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc
```