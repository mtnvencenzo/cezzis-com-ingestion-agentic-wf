## CloudSync
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync
```

## Local
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc
```