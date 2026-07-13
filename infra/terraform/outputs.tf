output "s3_bucket_name" {
  value = aws_s3_bucket.data_lake.id
}

output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_repo.repository_url
}

output "etl_lambda_arn" {
  value = aws_lambda_function.etl_processor.arn
}

output "simulation_lambda_arn" {
  value = aws_lambda_function.simulation_runner.arn
}

output "glue_database_name" {
  value = aws_glue_catalog_database.iff_catalog.name
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.analytics.name
}
