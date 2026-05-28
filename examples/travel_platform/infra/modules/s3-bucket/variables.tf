variable "name" { type = string }
variable "versioning_enabled" { type = bool; default = true }
variable "tags" { type = map(string); default = {} }
