resource "aws_glue_catalog_database" "iff_catalog" {
  name = "iff_data_catalog"

  description = "Glue catalog for India football funnel processed and simulation data"
}

resource "aws_glue_catalog_table" "investment_outcome_observation" {
  name          = "investment_outcome_observation"
  database_name = aws_glue_catalog_database.iff_catalog.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification  = "parquet"
    compressionType = "none"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.id}/processed/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "state"
      type = "string"
    }
    columns {
      name = "district"
      type = "string"
    }
    columns {
      name = "year"
      type = "int"
    }
    columns {
      name = "census_year"
      type = "int"
    }
    columns {
      name = "youth_population_10_17"
      type = "int"
    }
    columns {
      name = "budget_allocation_inr"
      type = "double"
    }
    columns {
      name = "budget_per_capita"
      type = "double"
    }
    columns {
      name = "khelo_india_centres"
      type = "double"
    }
    columns {
      name = "facility_density"
      type = "double"
    }
    columns {
      name = "participation_count"
      type = "int"
    }
    columns {
      name = "participation_rate"
      type = "double"
    }
    columns {
      name = "medals"
      type = "int"
    }
    columns {
      name = "medals_per_participant"
      type = "double"
    }
    columns {
      name = "tournament_results_score"
      type = "double"
    }
    columns {
      name = "facility_data_status"
      type = "string"
    }
    columns {
      name = "source_file"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "simulation_results" {
  name          = "simulation_results"
  database_name = aws_glue_catalog_database.iff_catalog.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification  = "parquet"
    compressionType = "none"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.id}/results/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "scenario_name"
      type = "string"
    }
    columns {
      name = "n_runs"
      type = "int"
    }
    columns {
      name = "year"
      type = "int"
    }
    columns {
      name = "mean_medals"
      type = "double"
    }
    columns {
      name = "p10_medals"
      type = "double"
    }
    columns {
      name = "p90_medals"
      type = "double"
    }
    columns {
      name = "mean_participation_rate"
      type = "double"
    }
    columns {
      name = "final_medals_mean"
      type = "double"
    }
    columns {
      name = "final_medals_std"
      type = "double"
    }
  }
}

resource "aws_athena_workgroup" "analytics" {
  name = "iff-analytics"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.id}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  tags = {
    Project = var.project_name
  }
}
