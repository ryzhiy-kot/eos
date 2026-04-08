import pytest
from app.services.artifact_collector import ArtifactCollector


class TestArtifactCollector:
    """Tests for ArtifactCollector ensuring unique IDs."""

    def test_chart_generates_unique_id(self):
        """Each chart call should generate a unique ID."""
        collector = ArtifactCollector()
        
        result1 = collector.chart([{"name": "A", "value": 100}], chart_type="bar", title="Chart 1")
        result2 = collector.chart([{"name": "B", "value": 200}], chart_type="bar", title="Chart 2")
        
        assert result1["id"] is not None
        assert result2["id"] is not None
        assert result1["id"] != result2["id"]
        assert result1["id"].startswith("chart_")
        assert result2["id"].startswith("chart_")

    def test_table_generates_unique_id(self):
        """Each table call should generate a unique ID."""
        collector = ArtifactCollector()
        
        result1 = collector.table([{"symbol": "AAPL", "pnl": 100}], title="Table 1")
        result2 = collector.table([{"symbol": "GOOG", "pnl": 200}], title="Table 2")
        
        assert result1["id"] is not None
        assert result2["id"] is not None
        assert result1["id"] != result2["id"]
        assert result1["id"].startswith("table_")
        assert result2["id"].startswith("table_")

    def test_pdf_generates_unique_id(self):
        """Each PDF call should generate a unique ID."""
        collector = ArtifactCollector()
        
        result1 = collector.pdf({"title": "Report 1", "tables": []}, title="Report 1")
        result2 = collector.pdf({"title": "Report 2", "tables": []}, title="Report 2")
        
        assert result1["id"] is not None
        assert result2["id"] is not None
        assert result1["id"] != result2["id"]
        assert result1["id"].startswith("pdf_")
        assert result2["id"].startswith("pdf_")

    def test_text_generates_unique_id(self):
        """Each text call should generate a unique ID."""
        collector = ArtifactCollector()
        
        result1 = collector.text("Content 1", format="markdown")
        result2 = collector.text("Content 2", format="markdown")
        
        assert result1["id"] is not None
        assert result2["id"] is not None
        assert result1["id"] != result2["id"]
        assert result1["id"].startswith("text_")
        assert result2["id"].startswith("text_")

    def test_multiple_artifacts_all_have_unique_ids(self):
        """All artifacts in a session should have unique IDs."""
        collector = ArtifactCollector()
        
        collector.chart([{"name": "A", "value": 100}], chart_type="bar", title="Chart")
        collector.table([{"symbol": "AAPL", "pnl": 100}], title="Table")
        collector.text("Some text", format="markdown")
        collector.pdf({"title": "Report", "tables": []}, title="PDF")
        
        ids = [a["id"] for a in collector.artifacts]
        assert len(ids) == len(set(ids)), "All artifact IDs should be unique"

    def test_chart_id_format(self):
        """Chart IDs should follow expected format."""
        collector = ArtifactCollector()
        result = collector.chart([{"name": "Test", "value": 100}], chart_type="bar", title="Test Chart")
        
        assert "id" in result
        assert result["id"].startswith("chart_")
        assert len(result["id"]) > len("chart_")

    def test_artifacts_list_populated(self):
        """All artifact types should be added to the artifacts list."""
        collector = ArtifactCollector()
        
        collector.chart([{"name": "A", "value": 100}], chart_type="bar", title="Chart")
        collector.table([{"symbol": "AAPL", "pnl": 100}], title="Table")
        collector.text("Content", format="markdown")
        collector.pdf({"title": "Report", "tables": []}, title="PDF")
        
        assert len(collector.artifacts) == 4
        assert all("id" in a for a in collector.artifacts)
