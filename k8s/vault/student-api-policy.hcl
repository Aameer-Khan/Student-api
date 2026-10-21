# ESO may only READ the student-api secrets. Nothing else.
path "secret/data/student-api/*" {
  capabilities = ["read"]
}