# ESO in the observability namespace may only READ observability secrets.
path "secret/data/observability/*" {
  capabilities = ["read"]
}