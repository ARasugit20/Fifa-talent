resource "aws_lambda_function" "etl_processor" {
  function_name = "iff-etl-processor"
  role          = aws_iam_role.etl_lambda.arn
  package_type  = "Image"
  image_uri     = local.ecr_image_uri
  timeout       = 120
  memory_size   = 512

  image_config {
    command = ["india_football_funnel.aws.lambda_handlers.etl_handler"]
  }

  environment {
    variables = {
      IFF_S3_BUCKET  = aws_s3_bucket.data_lake.id
      IFF_LOCAL_MODE = "false"
      AWS_REGION     = var.aws_region
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "simulation_runner" {
  function_name = "iff-simulation-runner"
  role          = aws_iam_role.simulation_lambda.arn
  package_type  = "Image"
  image_uri     = local.ecr_image_uri
  timeout       = 300
  memory_size   = 1024

  image_config {
    command = ["india_football_funnel.aws.lambda_handlers.simulation_handler"]
  }

  environment {
    variables = {
      IFF_S3_BUCKET  = aws_s3_bucket.data_lake.id
      IFF_LOCAL_MODE = "false"
      AWS_REGION     = var.aws_region
    }
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "etl_lambda" {
  name              = "/aws/lambda/iff-etl-processor"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "simulation_lambda" {
  name              = "/aws/lambda/iff-simulation-runner"
  retention_in_days = 14
}
