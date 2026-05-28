variable "name" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_ids" { type = list(string) }
variable "instance_class" { type = string; default = "db.t3.medium" }
variable "allocated_storage" { type = number; default = 100 }
variable "username" { type = string }
variable "password" { type = string; sensitive = true }
variable "skip_final_snapshot" { type = bool; default = false }
variable "backup_retention_days" { type = number; default = 7 }
variable "tags" { type = map(string); default = {} }
