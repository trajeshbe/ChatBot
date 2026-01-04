"""
End-to-End Test for Relation Extractor Module

This test verifies the complete workflow:
1. Upload a document
2. Extract entities and relations
3. Verify the results
"""

import pytest
import uuid
import json
from pathlib import Path


@pytest.fixture
def sample_text_document(tmp_path):
    """Create a sample text document with entity relationships."""
    content = """
    Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976.

    In 2011, Tim Cook became the CEO of Apple Inc. after Steve Jobs stepped down.

    Apple acquired Beats Electronics for $3 billion in 2014, bringing Dr. Dre
    and Jimmy Iovine into the company.

    Apple is headquartered in Cupertino, California and operates globally.
    The company developed the iPhone, which revolutionized mobile technology.

    In 2021, Apple partnered with Hyundai to develop autonomous vehicles.
    """

    doc_path = tmp_path / "apple_relationships.txt"
    doc_path.write_text(content)
    return doc_path


class TestRelationExtractorE2E:
    """End-to-end tests for Relation Extractor module."""

    def test_module_loaded(self, client):
        """Test that Relation Extractor module is loaded."""
        response = client.get("/api/v1/modules")
        assert response.status_code == 200

        modules = response.json()
        relation_extractor = next(
            (m for m in modules if m.get("id") == "relation-extractor"),
            None
        )
        assert relation_extractor is not None, "Relation Extractor module not found"
        assert relation_extractor["enabled"] is True
        print(f"✅ Module loaded: {relation_extractor['name']}")

    def test_upload_document(self, client, sample_text_document):
        """Test document upload for relation extraction."""
        with open(sample_text_document, "rb") as f:
            response = client.post(
                "/api/v1/upload",
                files={"file": ("apple_relationships.txt", f, "text/plain")},
                data={"session_id": "test-relation-extractor"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "apple_relationships.txt"

        print(f"✅ Document uploaded: {data['document_id']}")
        return data["document_id"]

    def test_extract_relations_auto_mode(self, client, sample_text_document):
        """Test relation extraction in auto mode."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract relations
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "extraction_mode": "auto",
                "min_confidence": 0.5,
                "deduplicate": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "extraction_id" in data
        assert "document_id" in data
        assert data["document_id"] == document_id
        assert "relations" in data
        assert "graph" in data
        assert "extraction_mode" in data

        print(f"✅ Extraction ID: {data['extraction_id']}")
        print(f"✅ Found {len(data['relations'])} relations")
        print(f"✅ Extraction mode: {data['extraction_mode']}")

        # Verify we found some relations
        assert data["total_relations_found"] > 0, "No relations found"

        # Verify graph structure
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert graph["num_entities"] > 0
        assert graph["num_relations"] > 0

        print(f"✅ Graph has {graph['num_entities']} entities and {graph['num_relations']} relations")

        # Print sample relations
        if data["relations"]:
            print("\n📊 Sample Relations:")
            for i, rel in enumerate(data["relations"][:3], 1):
                print(f"\n{i}. {rel['subject']['text']} --[{rel['relation']}]--> {rel['object']['text']}")
                print(f"   Context: {rel['context'][:100]}...")
                print(f"   Confidence: {rel['confidence']:.2f}")

        return data

    def test_extract_relations_with_filters(self, client, sample_text_document):
        """Test relation extraction with specific relation type filters."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract only specific relation types
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "relation_types": ["FOUNDER_OF", "CEO_OF", "ACQUIRED", "HEADQUARTERED_IN"],
                "entity_types": ["PERSON", "ORGANIZATION", "LOCATION"],
                "extraction_mode": "auto",
                "min_confidence": 0.6
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify filtered results
        assert len(data["relations"]) > 0

        # Check that relations match requested types
        requested_types = {"FOUNDER_OF", "CEO_OF", "ACQUIRED", "HEADQUARTERED_IN"}
        for rel in data["relations"]:
            assert rel["relation"].upper() in requested_types or rel["relation"] in requested_types

        print(f"✅ Filtered extraction found {len(data['relations'])} relations")
        return data

    def test_extract_relations_text_mode(self, client, sample_text_document):
        """Test relation extraction in text-only mode."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract using text mode
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "extraction_mode": "text",
                "min_confidence": 0.5
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["extraction_mode"] == "text"
        assert "llm_service" in data.get("tier_1_services_used", []) or \
               data.get("extraction_mode") == "text"

        print(f"✅ Text mode extraction found {data['total_relations_found']} relations")
        return data

    def test_relation_quality_metrics(self, client, sample_text_document):
        """Test that quality metrics are included in results."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract relations
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "min_confidence": 0.5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify quality metrics
        assert "avg_confidence" in data
        assert "high_confidence_count" in data
        assert "extraction_time_seconds" in data

        assert 0.0 <= data["avg_confidence"] <= 1.0
        assert data["high_confidence_count"] >= 0
        assert data["extraction_time_seconds"] > 0

        print(f"✅ Average confidence: {data['avg_confidence']:.2f}")
        print(f"✅ High confidence relations: {data['high_confidence_count']}")
        print(f"✅ Extraction time: {data['extraction_time_seconds']:.2f}s")

    def test_missing_document_id(self, client):
        """Test error handling when document_id is missing."""
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "extraction_mode": "auto"
            }
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

        # Check that error mentions document_id
        error_msg = str(data["detail"])
        assert "document_id" in error_msg.lower()

        print(f"✅ Validation error correctly caught: {data['detail']}")

    def test_invalid_document_id(self, client):
        """Test error handling with non-existent document."""
        fake_id = str(uuid.uuid4())

        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": fake_id,
                "extraction_mode": "auto"
            }
        )

        # Should return error (not found or processing error)
        assert response.status_code in [404, 422, 500]

        print(f"✅ Invalid document ID correctly rejected")

    def test_entity_types_in_results(self, client, sample_text_document):
        """Test that entities have correct types."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract relations
        response = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "min_confidence": 0.5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check entity types
        valid_entity_types = {
            "person", "organization", "location", "product", "event",
            "date", "money", "percent", "quantity", "other"
        }

        for relation in data["relations"]:
            assert "subject" in relation
            assert "object" in relation

            subject_type = relation["subject"]["type"].lower()
            object_type = relation["object"]["type"].lower()

            assert subject_type in valid_entity_types, f"Invalid subject type: {subject_type}"
            assert object_type in valid_entity_types, f"Invalid object type: {object_type}"

        print(f"✅ All entities have valid types")

    def test_confidence_filtering(self, client, sample_text_document):
        """Test that min_confidence filtering works."""
        # Upload document
        document_id = self.test_upload_document(client, sample_text_document)

        # Extract with high confidence threshold
        response_high = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "min_confidence": 0.8  # High threshold
            }
        )

        # Extract with low confidence threshold
        response_low = client.post(
            "/api/v1/modules/relation-extractor/extract",
            json={
                "document_id": document_id,
                "min_confidence": 0.3  # Low threshold
            }
        )

        assert response_high.status_code == 200
        assert response_low.status_code == 200

        data_high = response_high.json()
        data_low = response_low.json()

        # Low confidence should have more or equal relations
        assert data_low["total_relations_found"] >= data_high["total_relations_found"]

        # Verify all relations meet confidence threshold
        for rel in data_high["relations"]:
            assert rel["confidence"] >= 0.8

        print(f"✅ High confidence (0.8): {data_high['total_relations_found']} relations")
        print(f"✅ Low confidence (0.3): {data_low['total_relations_found']} relations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
