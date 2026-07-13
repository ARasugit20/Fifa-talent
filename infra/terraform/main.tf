terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  account_id   = var.aws_account_id != "" ? var.aws_account_id : data.aws_caller_identity.current.account_id
  bucket_name  = "${var.project_name}-data-${local.account_id}"
  ecr_image_uri = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository_name}:latest"
}
