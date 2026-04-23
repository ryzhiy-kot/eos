import base64
import uuid
from typing import Union, Literal
from pydantic import BaseModel, Field


class BarData(BaseModel):
    label: str = Field(description="Label for the bar")
    value: float = Field(description="Numeric value")


class LineData(BaseModel):
    time: Union[int, str] = Field(
        description="Unix timestamp or YYYY-MM-DD date string"
    )
    value: float = Field(description="Numeric value at this time point")


class CandleData(BaseModel):
    time: Union[int, str] = Field(
        description="Unix timestamp or YYYY-MM-DD date string"
    )
    open: float = Field(description="Open price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Close price")


class GaugeData(BaseModel):
    value: float = Field(description="Gauge scalar value")


ChartDataParam = Union[list[BarData], list[LineData], list[CandleData], list[GaugeData]]


class PdfTable(BaseModel):
    title: str = Field(default="", description="Table title")
    data: list[dict[str, Union[float, int, str, bool]]] = Field(
        description="Rows as key-value mappings"
    )


class PdfContent(BaseModel):
    title: str | None = Field(default=None, description="Title of the artifact")
    tables: list[PdfTable] | None = Field(
        default=None, description="List of tables to include"
    )
    text: str | None = Field(default=None, description="Text content for the PDF")


TableDataParam = list[dict[str, Union[float, int, str, bool]]]


class ArtifactCollector:
    """Captures artifacts generated during code execution.

    Each display function returns a dict that can be directly rendered by the GUI.
    """

    def __init__(self):
        self.artifacts = []

    def _transform_to_lightweight_charts(
        self,
        data: ChartDataParam,
        chart_type: Literal["bar", "candlestick", "line", "gauge"],
        title: str,
        **kwargs: Union[int, float, str, bool, None],
    ) -> dict:
        import pandas as pd

        # Internal standardization using Pydantic dumping if needed
        raw_data = (
            [d.model_dump() for d in data]
            if isinstance(data, list)
            and len(data) > 0
            and hasattr(data[0], "model_dump")
            else data
        )

        df = pd.DataFrame(raw_data)

        if chart_type == "bar":
            series = []
            for _, row in df.iterrows():
                value = row.get("value") or row.get("pnl") or row.get("rate") or 0
                label = row.get("name") or row.get("symbol") or row.get("label") or ""
                series.append({"value": float(value), "label": str(label)})

            return {
                "type": "bar",
                "data": series,
                "title": title,
            }

        elif chart_type == "candlestick":
            candle_data = []
            for _, row in df.iterrows():
                candle_data.append(
                    {
                        "time": row.get("timestamp") or row.get("date") or "",
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                    }
                )
            return {"type": "candlestick", "data": candle_data, "title": title}

        elif chart_type == "line":
            line_data = []
            for idx, row in enumerate(df.iterrows()):
                row = row[1]
                time_val = row.get("timestamp") or row.get("date") or row.get("time")
                if time_val and isinstance(time_val, str):
                    if time_val.isdigit():
                        time_val = int(time_val)
                    else:
                        try:
                            from datetime import datetime

                            dt = datetime.strptime(time_val, "%Y-%m-%d")
                            time_val = int(dt.timestamp())
                        except:
                            time_val = idx + 1
                else:
                    time_val = idx + 1

                value = float(
                    row.get("value") or row.get("rate") or row.get("pnl") or 0
                )
                line_data.append(
                    {
                        "time": time_val,
                        "value": value,
                    }
                )
            return {"type": "line", "data": line_data, "title": title}

        elif chart_type == "gauge":
            return {
                "type": "gauge",
                "value": float(df.iloc[0].get("value", 0) if len(df) > 0 else 0),
                "max": float(kwargs.get("max", 100)),
                "title": title,
            }

        return {"type": "unknown", "data": [], "title": title}

    def _transform_to_table(self, data: TableDataParam, max_rows: int = 50) -> dict:
        import pandas as pd

        df = pd.DataFrame(data)

        columns = list(df.columns)
        rows = df.head(max_rows).to_dict("records")

        return {"columns": columns, "rows": rows}

    def _generate_pdf(self, content: Union[PdfContent, str]) -> bytes:
        """Generate PDF from content."""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            if hasattr(content, "model_dump"):
                content = content.model_dump()

            if isinstance(content, dict):
                title = content.get("title", "Report")
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, txt=title, ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=10)
                if "tables" in content:
                    for table in content["tables"]:
                        pdf.set_font("Arial", "B", 12)
                        pdf.cell(200, 10, txt=table.get("title", ""), ln=True)
                        pdf.set_font("Arial", size=10)
                        for row in table.get("data", [])[:20]:
                            line = " | ".join(f"{k}: {v}" for k, v in row.items())
                            pdf.cell(200, 8, txt=line[:80], ln=True)
                        pdf.ln(5)
            else:
                text = str(content)
                for line in text.split("\n")[:50]:
                    pdf.cell(200, 8, txt=line[:80], ln=True)

            return pdf.output(dest="S").encode("latin-1")
        except ImportError:
            return b"PDF generation not available"

    def chart(
        self,
        data: ChartDataParam,
        chart_type: Literal["bar", "candlestick", "line", "gauge"] = "bar",
        title: str = "",
        **kwargs: Union[int, float, str, bool, None],
    ) -> dict:
        """Generate and register a chart artifact.

        Args:
            data: List of dicts or pandas DataFrame with chart data.
                For bar charts: [{"label": "FX", "value": 75000}, ...]
                For line charts: [{"time": "2024-01-15", "value": 1.085}, ...]
                For gauges: [{"value": 85}] or just the number
            chart_type: Type of chart. Options: "bar", "line", "candlestick", "gauge".
            title: Chart title for display in GUI.
            **kwargs: Additional options like "max" for gauge charts.

        Returns:
            dict: {
                "type": "chart",
                "chart_type": str,
                "title": str,
                "spec": {
                    "type": str,
                    "data": list,
                    "title": str
                }
            }
        """
        spec = self._transform_to_lightweight_charts(data, chart_type, title, **kwargs)
        artifact = {
            "type": "chart",
            "chart_type": chart_type,
            "spec": spec,
            "title": title,
            "id": f"chart_{uuid.uuid4().hex[:8]}",
        }
        self.artifacts.append(artifact)
        return artifact

    def table(
        self,
        data: TableDataParam,
        title: str = "",
        max_rows: int = 50,
        **kwargs: Union[int, float, str, bool, None],
    ) -> dict:
        """Generate and register a table artifact.

        Args:
            data: List of dicts or pandas DataFrame with tabular data.
                [{"symbol": "EURUSD", "pnl": 2500, "quantity": 5000}, ...]
            title: Table title for display in GUI.
            max_rows: Maximum rows to include. Default: 50.

        Returns:
            dict: {
                "type": "table",
                "title": str,
                "columns": list[str],
                "data": list[dict]
            }
        """
        table_data = self._transform_to_table(data, max_rows)
        artifact = {
            "type": "table",
            "title": title,
            "columns": table_data["columns"],
            "data": table_data["rows"],
            "id": f"table_{uuid.uuid4().hex[:8]}",
        }
        self.artifacts.append(artifact)
        return artifact

    def pdf(
        self,
        content: Union[PdfContent, str],
        title: str = "",
        **kwargs: Union[int, float, str, bool, None],
    ) -> dict:
        """Generate and register a PDF artifact.

        Args:
            content: Dict with report content or string.
                {"title": "Report Title", "tables": [...], "text": "..."}
                Or simply a string with the report text.
            title: Report title for display in GUI.

        Returns:
            dict: {
                "type": "pdf",
                "title": str,
                "data": str (base64 encoded PDF)
            }
        """
        pdf_bytes = self._generate_pdf(content)
        artifact = {
            "type": "pdf",
            "title": title,
            "data": base64.b64encode(pdf_bytes).decode(),
            "id": f"pdf_{uuid.uuid4().hex[:8]}",
        }
        self.artifacts.append(artifact)
        return artifact

    def text(
        self,
        content: str,
        format: Literal["markdown", "plain"] = "markdown",
        **kwargs: Union[int, float, str, bool, None],
    ) -> dict:
        """Generate and register a text artifact.

        Args:
            content: Text content to display. Can be markdown or plain text.
            format: Format type. Options: "markdown", "plain". Default: "markdown".

        Returns:
            dict: {
                "type": "text",
                "content": str,
                "format": str
            }
        """
        artifact = {
            "type": "text",
            "format": format,
            "content": str(content),
            "id": f"text_{uuid.uuid4().hex[:8]}",
        }
        self.artifacts.append(artifact)
        return artifact
