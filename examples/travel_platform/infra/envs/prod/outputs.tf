output "vpc_id" { value = module.vpc.vpc_id }
output "db_endpoint" { value = module.db.endpoint }
output "analytics_bucket" { value = module.analytics_bucket.bucket_name }
output "task_role_arn" { value = module.task_role.role_arn }
