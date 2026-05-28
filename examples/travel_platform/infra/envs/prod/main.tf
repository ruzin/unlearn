terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "travel-tfstate-prod"
    key    = "travel-platform/prod.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = local.common_tags }
}

locals {
  env = "prod"
  common_tags = {
    Environment = local.env
    Project     = "travel-platform"
    ManagedBy   = "terraform"
  }
}

module "vpc" {
  source               = "../../modules/vpc"
  name                 = "travel-${local.env}"
  cidr_block           = "10.30.0.0/16"
  public_subnet_cidrs  = ["10.30.0.0/24", "10.30.1.0/24", "10.30.2.0/24"]
  private_subnet_cidrs = ["10.30.10.0/24", "10.30.11.0/24", "10.30.12.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
  tags                 = local.common_tags
}

module "db" {
  source                 = "../../modules/rds"
  name                   = "travel-${local.env}"
  subnet_ids             = module.vpc.private_subnet_ids
  security_group_ids     = []
  username               = "travel"
  password               = var.db_password
  instance_class         = "db.r6g.xlarge"
  allocated_storage      = 500
  backup_retention_days  = 30
  tags                   = local.common_tags
}

module "analytics_bucket" {
  source             = "../../modules/s3-bucket"
  name               = "travel-analytics-${local.env}"
  versioning_enabled = true
  tags               = local.common_tags
}

module "task_role" {
  source              = "../../modules/iam-role"
  name                = "travel-${local.env}-task"
  assume_role_service = "ecs-tasks.amazonaws.com"
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
  ]
  tags = local.common_tags
}
