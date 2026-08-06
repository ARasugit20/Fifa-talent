#!/usr/bin/env bash
# Collect deployment evidence after a live AWS stack is running.
# Requires: aws CLI, terraform, python with project installed, valid AWS credentials.
# Do not run without understanding billable resources — see docs/deployment_evidence/RUNBOOK.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT}/docs/deployment_evidence"
TERRAFORM_DIR="${ROOT}/infra/terraform"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
RUN_DIR="${EVIDENCE_DIR}/runs/${TIMESTAMP}"

: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${AWS_REGION:=ap-south-1}"
: "${ECR_IMAGE_TAG:=$(git -C "${ROOT}" rev-parse HEAD 2>/dev/null || echo local)}"

BUCKET="india-football-funnel-data-${AWS_ACCOUNT_ID}"
GLUE_DB="iff_data_catalog"
GLUE_TABLE="public_sports_infrastructure"
ATHENA_WORKGROUP="iff-analytics"

mkdir -p "${RUN_DIR}"

log() {
  echo "[collect-evidence] $*"
}

save_plan() {
  log "Saving terraform plan to ${RUN_DIR}/terraform_plan.txt"
  (
    cd "${TERRAFORM_DIR}"
    terraform init -input=false
    terraform plan -input=false -no-color \
      -var="aws_account_id=${AWS_ACCOUNT_ID}" \
      -var="aws_region=${AWS_REGION}" \
      -var="ecr_image_tag=${ECR_IMAGE_TAG}" \
      | tee "${RUN_DIR}/terraform_plan.txt"
  )
}

upload_fixtures_and_trigger_etl() {
  log "Uploading fixture raw inputs and dataset-ready manifest"
  aws s3 sync "${ROOT}/tests/fixtures/raw/" "s3://${BUCKET}/raw/" --exclude ".gitkeep"
  python - <<'PY' > "${RUN_DIR}/dataset-ready.json"
from india_football_funnel.aws.infrastructure_etl import build_default_dataset_ready_manifest

print(build_default_dataset_ready_manifest().model_dump_json(indent=2))
PY
  aws s3 cp "${RUN_DIR}/dataset-ready.json" "s3://${BUCKET}/raw/dataset-ready.json"
  log "Waiting 30s for manifest-triggered ETL Lambda"
  sleep 30
}

capture_etl_logs() {
  log "Fetching recent iff-etl-processor log events"
  aws logs filter-log-events \
    --log-group-name /aws/lambda/iff-etl-processor \
    --start-time $(($(date +%s) * 1000 - 600000)) \
    --limit 50 \
    --query 'events[].message' \
    --output text \
    | tee "${RUN_DIR}/etl_lambda_log.txt" || true
}

capture_glue_schema() {
  log "Fetching Glue table schema for ${GLUE_DB}.${GLUE_TABLE}"
  aws glue get-table \
    --database-name "${GLUE_DB}" \
    --name "${GLUE_TABLE}" \
    --output json \
    | tee "${RUN_DIR}/glue_public_sports_infrastructure.json"
}

capture_athena_query() {
  log "Running Athena smoke query"
  local query
  query="SELECT canonical_state_ut, projects_total, amount_released_inr, denominator_value FROM ${GLUE_DB}.${GLUE_TABLE} ORDER BY canonical_state_ut LIMIT 10;"
  echo "${query}" > "${RUN_DIR}/athena_query.sql"

  local execution_id
  execution_id="$(
    aws athena start-query-execution \
      --query-string "${query}" \
      --work-group "${ATHENA_WORKGROUP}" \
      --query-execution-context "Database=${GLUE_DB}" \
      --result-configuration "OutputLocation=s3://${BUCKET}/athena-results/" \
      --query 'QueryExecutionId' \
      --output text
  )"
  echo "${execution_id}" > "${RUN_DIR}/athena_execution_id.txt"

  local state="RUNNING"
  while [[ "${state}" == "RUNNING" || "${state}" == "QUEUED" ]]; do
    sleep 2
    state="$(
      aws athena get-query-execution \
        --query-execution-id "${execution_id}" \
        --query 'QueryExecution.Status.State' \
        --output text
    )"
  done

  aws athena get-query-execution \
    --query-execution-id "${execution_id}" \
    --output json \
    | tee "${RUN_DIR}/athena_query_execution.json"

  if [[ "${state}" == "SUCCEEDED" ]]; then
    aws s3 cp "s3://${BUCKET}/athena-results/${execution_id}.csv" \
      "${RUN_DIR}/athena_query_result.csv" || true
  fi
}

capture_s3_artifacts() {
  log "Listing processed and results prefixes"
  {
    echo "=== processed/ ==="
    aws s3 ls "s3://${BUCKET}/processed/" || true
    echo
    echo "=== results/ ==="
    aws s3 ls "s3://${BUCKET}/results/" --recursive || true
  } | tee "${RUN_DIR}/s3_artifact_listing.txt"
}

write_summary() {
  cat > "${RUN_DIR}/README.txt" <<EOF
Deployment evidence run: ${TIMESTAMP}
AWS account: ${AWS_ACCOUNT_ID}
Region: ${AWS_REGION}
Bucket: ${BUCKET}
ECR image tag: ${ECR_IMAGE_TAG}

Files in this directory were captured by scripts/collect_deploy_evidence.sh.
Review and redact account-specific identifiers before committing to git.
Teardown: make destroy (see docs/deployment_evidence/RUNBOOK.md).
EOF
}

main() {
  local mode="${1:-all}"
  case "${mode}" in
    plan)
      save_plan
      ;;
    post-deploy)
      upload_fixtures_and_trigger_etl
      capture_etl_logs
      capture_glue_schema
      capture_athena_query
      capture_s3_artifacts
      write_summary
      ;;
    all)
      save_plan
      upload_fixtures_and_trigger_etl
      capture_etl_logs
      capture_glue_schema
      capture_athena_query
      capture_s3_artifacts
      write_summary
      ;;
    *)
      echo "Usage: $0 [plan|post-deploy|all]" >&2
      exit 1
      ;;
  esac
  log "Evidence saved under ${RUN_DIR}"
}

main "$@"
