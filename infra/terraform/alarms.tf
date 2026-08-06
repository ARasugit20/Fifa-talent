variable "monthly_cost_threshold_usd" {
  description = "Estimated monthly AWS spend threshold for billing alarm (USD)"
  type        = number
  default     = 25
}

variable "lambda_error_threshold" {
  description = "ETL Lambda error count threshold over one 5-minute period"
  type        = number
  default     = 1
}

variable "alarm_email" {
  description = "Optional email address for cost/error alarm notifications"
  type        = string
  default     = ""
}

resource "aws_sns_topic" "ops_alerts" {
  count = var.alarm_email != "" ? 1 : 0
  name  = "${var.project_name}-ops-alerts"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "ops_alerts_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.ops_alerts[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "estimated_charges" {
  alarm_name          = "${var.project_name}-estimated-monthly-charges"
  alarm_description   = "Estimated AWS charges exceeded the configured monthly threshold."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400
  statistic           = "Maximum"
  threshold           = var.monthly_cost_threshold_usd
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.ops_alerts[0].arn] : []

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "etl_lambda_errors" {
  alarm_name          = "${var.project_name}-etl-lambda-errors"
  alarm_description   = "ETL Lambda reported one or more errors in a 5-minute window."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.etl_processor.function_name
  }

  alarm_actions = var.alarm_email != "" ? [aws_sns_topic.ops_alerts[0].arn] : []

  tags = local.common_tags
}
