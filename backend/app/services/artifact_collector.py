import base64
import json
import random
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any


class ArtifactCollector:
    """Captures artifacts generated during code execution."""

    def __init__(self):
        self.artifacts = []

    def _transform_to_lightweight_charts(
        self, data: Any, chart_type: str, title: str, **kwargs
    ) -> dict:
        """Transform data to lightweight-charts format."""
        import pandas as pd

        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)

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
            for _, row in df.iterrows():
                line_data.append(
                    {
                        "time": row.get("timestamp") or row.get("date") or "",
                        "value": float(row.get("value") or row.get("rate") or row.get("pnl") or 0),
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

    def _transform_to_table(self, data: Any, max_rows: int = 50) -> dict:
        """Transform data to table format."""
        import pandas as pd

        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)

        columns = list(df.columns)
        rows = df.head(max_rows).to_dict("records")

        return {"columns": columns, "rows": rows}

    def _generate_pdf(self, content: Any) -> bytes:
        """Generate PDF from content."""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

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
                            pdf.cell(200, 8, txt=line, ln=True)
                        pdf.ln(5)
            else:
                text = str(content)
                for line in text.split("\n")[:50]:
                    pdf.cell(200, 8, txt=line[:80], ln=True)

            return pdf.output(dest="S").encode("latin-1")
        except ImportError:
            return b"PDF generation not available"

    def chart(self, data: Any, chart_type: str = "bar", title: str = "", **kwargs):
        """Generate and register a chart artifact."""
        spec = self._transform_to_lightweight_charts(data, chart_type, title, **kwargs)
        artifact = {
            "id": f"chart_{len(self.artifacts)}",
            "type": "chart",
            "chart_type": chart_type,
            "spec": spec,
            "title": title,
            "created_at": datetime.now().isoformat(),
        }
        self.artifacts.append(artifact)
        return f"[Chart {len(self.artifacts) - 1}]"

    def table(self, data: Any, title: str = "", max_rows: int = 50, **kwargs):
        """Generate and register a table artifact."""
        table_data = self._transform_to_table(data, max_rows)
        artifact = {
            "id": f"table_{len(self.artifacts)}",
            "type": "table",
            "title": title,
            "columns": table_data["columns"],
            "data": table_data["rows"],
            "created_at": datetime.now().isoformat(),
        }
        self.artifacts.append(artifact)
        return f"[Table {len(self.artifacts) - 1}]"

    def pdf(self, content: Any, title: str = "", **kwargs):
        """Generate and register a PDF artifact."""
        pdf_bytes = self._generate_pdf(content)
        artifact = {
            "id": f"pdf_{len(self.artifacts)}",
            "type": "pdf",
            "title": title,
            "data": base64.b64encode(pdf_bytes).decode(),
            "created_at": datetime.now().isoformat(),
        }
        self.artifacts.append(artifact)
        return f"[PDF {len(self.artifacts) - 1}]"

    def text(self, content: Any, format: str = "markdown"):
        """Generate and register a text artifact."""
        artifact = {
            "id": f"text_{len(self.artifacts)}",
            "type": "text",
            "format": format,
            "content": str(content),
            "created_at": datetime.now().isoformat(),
        }
        self.artifacts.append(artifact)
        return f"[Text {len(self.artifacts) - 1}]"


def create_collector() -> ArtifactCollector:
    """Factory function to create a new collector."""
    return ArtifactCollector()
