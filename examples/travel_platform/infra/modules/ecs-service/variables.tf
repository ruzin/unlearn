variable "service_name" { type = string }
variable "cluster_arn" { type = string }
variable "image" { type = string }
variable "cpu" { type = number; default = 512 }
variable "memory" { type = number; default = 1024 }
variable "container_port" { type = number; default = 8000 }
variable "desired_count" { type = number; default = 2 }
variable "subnet_ids" { type = list(string) }
variable "security_group_ids" { type = list(string) }
variable "execution_role_arn" { type = string }
variable "task_role_arn" { type = string }
variable "environment" { type = map(string); default = {} }
variable "tags" { type = map(string); default = {} }
