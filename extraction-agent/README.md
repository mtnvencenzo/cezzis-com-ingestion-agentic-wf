## CloudSync
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync
```

## Local
### Deploy

``` shell
# app
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc

# image updater
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc
```

### Remove 
``` shell
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc

kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc
```