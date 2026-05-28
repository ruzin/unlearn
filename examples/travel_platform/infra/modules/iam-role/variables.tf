variable "name" { type = string }
variable "assume_role_service" { type = string }
variable "managed_policy_arns" { type = list(string); default = [] }
variable "tags" { type = map(string); default = {} }
