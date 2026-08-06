"""Static validation tests for Terraform alarm resources."""

from __future__ import annotations

from pathlib import Path

TERRAFORM_DIR = Path(__file__).resolve().parents[2] / "infra" / "terraform"


def test_alarms_tf_declares_cost_and_error_alarms() -> None:
    content = (TERRAFORM_DIR / "alarms.tf").read_text(encoding="utf-8")
    assert 'resource "aws_cloudwatch_metric_alarm" "estimated_charges"' in content
    assert 'resource "aws_cloudwatch_metric_alarm" "etl_lambda_errors"' in content
    assert "AWS/Billing" in content
    assert "EstimatedCharges" in content


def test_tags_tf_declares_shared_cost_allocation_tags() -> None:
    content = (TERRAFORM_DIR / "tags.tf").read_text(encoding="utf-8")
    assert "common_tags" in content
    assert "CostCenter" in content
    assert "ManagedBy" in content


def test_iam_allows_s3_tagging_for_etl_idempotency() -> None:
    content = (TERRAFORM_DIR / "iam.tf").read_text(encoding="utf-8")
    assert "s3:GetObjectTagging" in content
    assert "s3:PutObjectTagging" in content
    assert "s3:ListBucket" in content
    assert "/results/*" in content


def test_s3_notification_triggers_on_dataset_ready_manifest_only() -> None:
    content = (TERRAFORM_DIR / "s3.tf").read_text(encoding="utf-8")
    assert 'filter_prefix       = "raw/dataset-ready.json"' in content
    assert 'filter_suffix       = ".csv"' not in content


def test_glue_declares_public_sports_infrastructure_table() -> None:
    content = (TERRAFORM_DIR / "glue_athena.tf").read_text(encoding="utf-8")
    assert 'resource "aws_glue_catalog_table" "public_sports_infrastructure"' in content
    assert "canonical_state_ut" in content
    assert "provenance_sha256" in content
    assert "legacy_table" in content
