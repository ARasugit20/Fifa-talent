variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "aws_account_id" {
  description = "AWS account ID (optional; inferred from caller identity if empty)"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "india-football-funnel"
}

variable "ecr_repository_name" {
  description = "ECR repository name for Lambda container images"
  type        = string
  default     = "india-football-funnel"
}

variable "raw_lifecycle_glacier_days" {
  description = "Days before raw data transitions to Glacier"
  type        = number
  default     = 90
}
