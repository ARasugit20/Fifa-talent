resource "aws_s3_bucket" "data_lake" {
  bucket = local.bucket_name

  tags = merge(local.common_tags, {
    Purpose = "data-lake"
  })
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "raw-to-glacier"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = var.raw_lifecycle_glacier_days
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_notification" "raw_upload" {
  bucket = aws_s3_bucket.data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.etl_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/dataset-ready.json"
  }

  depends_on = [aws_lambda_permission.allow_s3_etl]
}
