terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "travel-tfstate-dev"
    key    = "travel-platform/dev.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = local.common_tags }
}

locals {
  env = "dev"
  common_tags = {
    Environment = local.env
    Project     = "travel-platform"
    ManagedBy   = "terraform"
  }
}

module "vpc" {
  source               = "../../modules/vpc"
  name                 = "travel-${local.env}"
  cidr_block           = "10.10.0.0/16"
  public_subnet_cidrs  = ["10.10.0.0/24", "10.10.1.0/24"]
  private_subnet_cidrs = ["10.10.10.0/24", "10.10.11.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]
  tags                 = local.common_tags
}

module "db" {
  source             = "../../modules/rds"
  name               = "travel-${local.env}"
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = []
  username           = "travel"
  password           = var.db_password
  skip_final_snapshot = true
  tags               = local.common_tags
}

module "analytics_bucket" {
  source = "../../modules/s3-bucket"
  name   = "travel-analytics-${local.env}"
  tags   = local.common_tags
}
