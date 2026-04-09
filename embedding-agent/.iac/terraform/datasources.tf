
data "azurerm_resource_group" "cocktails_resource_group" {
  name = "rg-${var.sub}-${var.region}-${var.environment}-${var.domain}-${var.sequence}"
}

data "azurerm_key_vault" "cocktails_onprem_keyvault" {
  name                = "kv-${var.sub}-${var.region}-prm-${var.shortdomain}-${var.short_sequence}"
  resource_group_name = data.azurerm_resource_group.cocktails_resource_group.name
}