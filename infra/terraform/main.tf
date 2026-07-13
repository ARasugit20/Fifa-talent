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

# Lambda images are pinned to an immutable git-SHA tag passed from CI deploy.
# Mutable :latest tags are avoided so each deployment traces to a specific commit.
variable "ecr_image_tag" {
  description = "Immutable ECR image tag (typically the git commit SHA)"
  type        = string
}

locals {
  account_id    = var.aws_account_id != "" ? var.aws_account_id : data.aws_caller_identity.current.account_id
  bucket_name   = "${var.project_name}-data-${local.account_id}"
  ecr_image_uri = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository_name}:${var.ecr_image_tag}"
}
