terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "travel-tfstate-staging"
    key    = "travel-platform/staging.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = local.common_tags }
}

locals {
  env = "staging"
  common_tags = {
    Environment = local.env
    Project     = "travel-platform"
    ManagedBy   = "terraform"
  }
}

module "vpc" {
  source               = "../../modules/vpc"
  name                 = "travel-${local.env}"
  cidr_block           = "10.20.0.0/16"
  public_subnet_cidrs  = ["10.20.0.0/24", "10.20.1.0/24"]
  private_subnet_cidrs = ["10.20.10.0/24", "10.20.11.0/24"]
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
  instance_class     = "db.t3.large"
  tags               = local.common_tags
}
