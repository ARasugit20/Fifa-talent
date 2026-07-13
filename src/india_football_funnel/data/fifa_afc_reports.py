"""Manual ingestion helpers for FIFA/AFC PDF reports."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from india_football_funnel.models import PdfExtractedMetric

logger = logging.getLogger(__name__)


def _load_pdfplumber() -> Any:
    try:
        return importlib.import_module("pdfplumber")
    except ImportError as exc:
        msg = "Install pdfplumber before extracting FIFA/AFC PDF report metrics"
        raise RuntimeError(msg) from exc


def extract_text_metrics(
    pdf_path: Path,
    metric_terms: list[str],
) -> list[PdfExtractedMetric]:
    """Extract traceable text snippets for verified metrics from a PDF."""
    pdfplumber = _load_pdfplumber()
    extracted: list[PdfExtractedMetric] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for term in metric_terms:
                if term.lower() in text.lower():
                    extracted.append(
                        PdfExtractedMetric(
                            metric_name=term,
                            metric_value=term,
                            source_pdf=pdf_path.name,
                            source_page=page_idx,
                            extraction_note=(
                                "Term verified in page text; numeric value requires manual review"
                            ),
                        )
                    )
    logger.info("Extracted %d PDF metric traces from %s", len(extracted), pdf_path)
    return extracted


def extract_table_rows(pdf_path: Path) -> pd.DataFrame:
    """Extract PDF tables with source_pdf and source_page on every row."""
    pdfplumber = _load_pdfplumber()
    rows: list[dict[str, object]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                if not table:
                    continue
                header = [str(cell) if cell is not None else "" for cell in table[0]]
                for raw_row in table[1:]:
                    row = {
                        header[idx] if idx < len(header) and header[idx] else f"column_{idx}": cell
                        for idx, cell in enumerate(raw_row)
                    }
                    row["source_pdf"] = pdf_path.name
                    row["source_page"] = page_idx
                    rows.append(row)
    return pd.DataFrame(rows)


def metrics_to_frame(metrics: list[PdfExtractedMetric]) -> pd.DataFrame:
    """Convert extracted PDF metrics to a dataframe with citation fields."""
    return pd.DataFrame([metric.model_dump() for metric in metrics])
