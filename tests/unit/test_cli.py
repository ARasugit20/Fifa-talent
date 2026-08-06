"""Unit tests for CLI and config."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from tests.conftest import raw_fixture_root

import india_football_funnel.cli as cli_module
from india_football_funnel.cli import (
    main,
    main_reproduce,
    parse_reproduce_options,
    provenance_hash,
    provenance_init,
    provenance_main,
    provenance_verify,
    reproduce,
    simulate,
)
from india_football_funnel.cli_options import ReproduceOptions
from india_football_funnel.config import Settings, get_settings
from india_football_funnel.simulation.run_simulation import load_simulation_summary
from india_football_funnel.simulation.scenarios import get_scenario_by_name


def test_settings_resolved_bucket() -> None:
    settings = Settings(aws_account_id="123456789012")
    assert settings.resolved_bucket_name == "india-football-funnel-data-123456789012"


def test_get_settings_cached() -> None:
    assert get_settings() is get_settings()


def test_unknown_scenario_raises() -> None:
    with pytest.raises(ValueError, match="Unknown scenario"):
        get_scenario_by_name("nonexistent")


def test_reproduce_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_dir = raw_fixture_root()
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"
    for target in (
        "india_football_funnel.cli",
        "india_football_funnel.config",
    ):
        monkeypatch.setattr(f"{target}.RAW_DATA_DIR", raw_dir)
        monkeypatch.setattr(f"{target}.PROCESSED_DATA_DIR", processed_dir)
        monkeypatch.setattr(f"{target}.RESULTS_DATA_DIR", results_dir)
    monkeypatch.setattr("india_football_funnel.data.infrastructure_pipeline.RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr(
        "india_football_funnel.data.infrastructure_pipeline.PROCESSED_DATA_DIR",
        processed_dir,
    )

    reproduce()

    assert (processed_dir / "public_sports_infrastructure.parquet").exists()
    assert (processed_dir / "infrastructure_by_state.csv").exists()
    assert (results_dir / "analysis" / "infrastructure_summaries.json").exists()
    assert (results_dir / "data_quality_report.json").exists()
    assert (results_dir / "state_reconciliation_report.csv").exists()
    assert (results_dir / "run_manifest.json").exists()

    manifest = json.loads((results_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 10
    assert "not football-specific" in manifest["caveat"]
    assert manifest["data_quality"]["stale_denominator_count"] == 10


def test_reproduce_skip_quality_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir = raw_fixture_root()
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"
    for target in (
        "india_football_funnel.cli",
        "india_football_funnel.config",
    ):
        monkeypatch.setattr(f"{target}.RAW_DATA_DIR", raw_dir)
        monkeypatch.setattr(f"{target}.PROCESSED_DATA_DIR", processed_dir)
        monkeypatch.setattr(f"{target}.RESULTS_DATA_DIR", results_dir)
    monkeypatch.setattr("india_football_funnel.data.infrastructure_pipeline.RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr(
        "india_football_funnel.data.infrastructure_pipeline.PROCESSED_DATA_DIR",
        processed_dir,
    )

    reproduce(
        ReproduceOptions(
            skip_quality=True,
            skip_manifest=True,
            skip_summaries=True,
            skip_reconciliation=True,
        )
    )

    assert (processed_dir / "public_sports_infrastructure.parquet").exists()
    assert not (results_dir / "data_quality_report.json").exists()
    assert not (results_dir / "run_manifest.json").exists()


def test_parse_reproduce_options_from_argv() -> None:
    options = parse_reproduce_options(["--skip-quality", "--skip-manifest"])
    assert options.skip_quality is True
    assert options.skip_manifest is True
    assert options.skip_summaries is False


def test_parse_reproduce_options_supports_all_skip_flags() -> None:
    options = parse_reproduce_options(
        [
            "--skip-summaries",
            "--skip-quality",
            "--skip-reconciliation",
            "--skip-manifest",
            "--skip-csv-export",
        ]
    )

    assert options == ReproduceOptions(
        skip_summaries=True,
        skip_quality=True,
        skip_reconciliation=True,
        skip_manifest=True,
        skip_csv_export=True,
    )


def test_parse_reproduce_options_rejects_unknown_flag() -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse_reproduce_options(["--unknown"])

    assert exc_info.value.code == 2


def test_reproduce_parses_argv_and_logs_manifest_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    processed_path = tmp_path / "processed.parquet"
    captured: dict[str, ReproduceOptions] = {}

    def fake_run(
        raw_root: Path,
        processed_dir: Path,
        results_dir: Path,
        options: ReproduceOptions | None = None,
    ) -> dict[str, Path]:
        assert raw_root == cli_module.RAW_DATA_DIR
        assert processed_dir == cli_module.PROCESSED_DATA_DIR
        assert results_dir == cli_module.RESULTS_DATA_DIR
        assert options is not None
        captured["options"] = options
        return {"processed": processed_path}

    monkeypatch.setattr(cli_module, "ensure_local_data_dirs", lambda: None)
    monkeypatch.setattr(cli_module, "run_reproduce_pipeline", fake_run)
    caplog.set_level(logging.INFO, logger=cli_module.__name__)

    reproduce(argv=["--skip-manifest", "--skip-csv-export"])

    assert captured["options"].skip_manifest is True
    assert captured["options"].skip_csv_export is True
    assert "manifest skipped" in caplog.text


def test_reproduce_explicit_options_take_precedence_over_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_path = tmp_path / "processed.parquet"
    explicit = ReproduceOptions(skip_quality=True)
    run_pipeline = MagicMock(return_value={"processed": processed_path})
    monkeypatch.setattr(cli_module, "ensure_local_data_dirs", lambda: None)
    monkeypatch.setattr(cli_module, "run_reproduce_pipeline", run_pipeline)

    reproduce(options=explicit, argv=["--unknown"])

    assert run_pipeline.call_args.kwargs["options"] is explicit


def test_provenance_init_hash_verify_roundtrip(tmp_path: Path) -> None:
    raw_file = tmp_path / "financial_assistance.csv"
    raw_file.write_text(
        "state,financial_assistance,source_unit\nKerala,1,crore\n", encoding="utf-8"
    )

    provenance_path = provenance_init(raw_file)
    assert provenance_path.exists()

    digest = provenance_hash(raw_file)
    assert len(digest) == 64
    provenance_verify(raw_file)


def test_provenance_init_rejects_unconfigured_filename(tmp_path: Path) -> None:
    raw_file = tmp_path / "unknown.csv"
    raw_file.write_text("value\n1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No configured raw-file role"):
        provenance_init(raw_file)


@pytest.mark.parametrize("command", ["init", "hash", "verify"])
def test_provenance_main_dispatches_commands(
    command: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_file = tmp_path / "financial_assistance.csv"
    raw_file.write_text("state\nKerala\n", encoding="utf-8")
    init_mock = MagicMock(return_value=raw_file.with_suffix(".csv.provenance.json"))
    hash_mock = MagicMock(return_value="a" * 64)
    verify_mock = MagicMock()
    monkeypatch.setattr(cli_module, "provenance_init", init_mock)
    monkeypatch.setattr(cli_module, "provenance_hash", hash_mock)
    monkeypatch.setattr(cli_module, "provenance_verify", verify_mock)

    provenance_main([command, str(raw_file)])

    expected = {"init": init_mock, "hash": hash_mock, "verify": verify_mock}
    expected[command].assert_called_once_with(raw_file)


@pytest.mark.parametrize("argv", [[], ["init"], ["unknown", "file.csv"]])
def test_provenance_main_rejects_invalid_arguments(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        provenance_main(argv)

    assert exc_info.value.code == 2


def test_provenance_main_rejects_unexpected_parsed_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = MagicMock()
    parser.parse_args.return_value = SimpleNamespace(command="unexpected", raw_file=Path("raw.csv"))
    monkeypatch.setattr(cli_module, "_build_provenance_parser", lambda: parser)

    with pytest.raises(SystemExit, match="Unknown provenance command"):
        provenance_main([])


def test_reproduce_fails_without_required_raw_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty_raw = tmp_path / "raw"
    empty_raw.mkdir()
    monkeypatch.setattr("india_football_funnel.cli.RAW_DATA_DIR", empty_raw)

    with pytest.raises(FileNotFoundError, match="Required official raw inputs are missing"):
        reproduce()


def test_simulate_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    results_dir = tmp_path / "results"
    monkeypatch.setattr(
        "india_football_funnel.simulation.run_simulation.RESULTS_DATA_DIR",
        results_dir,
    )

    simulate()

    assert (results_dir / "baseline" / "simulation_summary.json").exists()
    assert (results_dir / "baseline" / "simulation_results.parquet").exists()


def test_load_simulation_summary(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "scenario_name": "baseline",
                "n_runs": 10,
                "years": 2,
                "annual_results": [
                    {
                        "year": 1,
                        "mean_medals": 5.0,
                        "p10_medals": 3.0,
                        "p90_medals": 7.0,
                        "mean_participation_rate": 0.012,
                    }
                ],
                "final_medals_mean": 6.0,
                "final_medals_std": 1.0,
                "assumption_based": True,
                "uncalibrated": True,
            }
        ),
        encoding="utf-8",
    )
    result = load_simulation_summary(summary_path)
    assert result.scenario_name == "baseline"
    assert result.n_runs == 10


def test_main_reproduce_forwards_process_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reproduce_mock = MagicMock()
    monkeypatch.setattr(cli_module, "reproduce", reproduce_mock)
    monkeypatch.setattr("sys.argv", ["iff-reproduce", "--skip-quality"])

    main_reproduce()

    reproduce_mock.assert_called_once_with(argv=["--skip-quality"])


def test_main_delegates_to_main_reproduce(monkeypatch: pytest.MonkeyPatch) -> None:
    main_reproduce_mock = MagicMock()
    monkeypatch.setattr(cli_module, "main_reproduce", main_reproduce_mock)

    main()

    main_reproduce_mock.assert_called_once_with()
