resource "aws_iam_role" "etl_lambda" {
  name = "iff-etl-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "etl_lambda" {
  name = "iff-etl-lambda-policy"
  role = aws_iam_role.etl_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/iff-etl-processor:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectTagging",
          "s3:PutObjectTagging"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/raw/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObjectTagging",
          "s3:PutObjectTagging"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/processed/*"
      }
    ]
  })
}

resource "aws_iam_role" "simulation_lambda" {
  name = "iff-simulation-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "simulation_lambda" {
  name = "iff-simulation-lambda-policy"
  role = aws_iam_role.simulation_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/iff-simulation-runner:*"
      },
      {
        Effect = "Allow"
        Action = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.data_lake.arn}/results/*"
      }
    ]
  })
}

resource "aws_lambda_permission" "allow_s3_etl" {
  statement_id  = "AllowS3InvokeETL"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.etl_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake.arn
}
