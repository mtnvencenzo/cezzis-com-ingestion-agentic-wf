resource "azurerm_key_vault_secret" "cocktails_embedding_agent_oauth_client_secret" {
  name         = "cocktails-embedding-agent-oauth-client-secret"
  value        = "n/a"
  key_vault_id = data.azurerm_key_vault.cocktails_keyvault.id

  lifecycle {
    ignore_changes = [value]
  }

  tags = local.tags
}