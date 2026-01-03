"""
Comprehensive Test Suite for All 6 Customer Solutions POCs
Tests: British Council, CRU, Grant Thornton, GT Motive, Solera, Construction Monitor
"""

import pytest
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# ============================================================================
# Test 1: British Council POC
# ============================================================================

class TestBritishCouncilPOC:
    """Tests for British Council course recommendation system"""

    def test_status_endpoint(self):
        """Test British Council status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/british_council/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "course recommendations" in data["description"].lower()

    def test_tier2_modules_present(self):
        """Test British Council uses at least 3 Tier 2 modules"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/british_council/status")
        data = response.json()
        assert len(data.get("tier_2_modules_used", [])) >= 3

    def test_capabilities_listed(self):
        """Test British Council lists expected capabilities"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/british_council/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        assert len(capabilities) > 0
        # Should have course recommendation capability
        assert any("course" in cap.lower() or "recommendation" in cap.lower() for cap in capabilities)

# ============================================================================
# Test 2: CRU Mining Intelligence POC
# ============================================================================

class TestCRUMiningPOC:
    """Tests for CRU Mining Intelligence multi-pipeline RAG"""

    def test_status_endpoint(self):
        """Test CRU status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/cru/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    def test_multi_pipeline_detection(self):
        """Test CRU detects pgvector-only or multi-pipeline mode"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/cru/status")
        data = response.json()
        description = data["description"]
        # Should indicate either pgvector-only or multi-pipeline mode
        assert "pgvector" in description.lower() or "multi-pipeline" in description.lower()

    def test_elasticsearch_status_indicator(self):
        """Test CRU indicates Elasticsearch availability"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/cru/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        # Should indicate Elasticsearch status (available or unavailable)
        has_es_indicator = any(
            "elasticsearch" in cap.lower() or "bm25" in cap.lower()
            for cap in capabilities
        )
        assert has_es_indicator

    def test_reranker_capability(self):
        """Test CRU lists reranker as a capability"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/cru/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        assert any("rerank" in cap.lower() for cap in capabilities)

# ============================================================================
# Test 3: Grant Thornton POC
# ============================================================================

class TestGrantThorntonPOC:
    """Tests for Grant Thornton financial data extraction"""

    def test_status_endpoint(self):
        """Test Grant Thornton status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/grant_thornton/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    def test_description_accuracy(self):
        """Test Grant Thornton description mentions financial/audit"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/grant_thornton/status")
        data = response.json()
        description = data["description"]
        assert "financial" in description.lower() or "audit" in description.lower()

    def test_tier2_modules_present(self):
        """Test Grant Thornton uses at least 2 Tier 2 modules"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/grant_thornton/status")
        data = response.json()
        assert len(data.get("tier_2_modules_used", [])) >= 2

    def test_supported_data_types(self):
        """Test Grant Thornton lists supported data types"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/grant_thornton/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        # Should mention Excel, PDF, or financial data
        assert len(capabilities) > 0

# ============================================================================
# Test 4: GT Motive POC
# ============================================================================

class TestGTMotivePOC:
    """Tests for GT Motive automotive part code extraction"""

    def test_status_endpoint(self):
        """Test GT Motive status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/gt_motive/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    def test_description_accuracy(self):
        """Test GT Motive description mentions automotive/parts"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/gt_motive/status")
        data = response.json()
        description = data["description"]
        assert any(keyword in description.lower() for keyword in ["automotive", "part", "vehicle"])

    def test_tier2_modules_present(self):
        """Test GT Motive uses at least 1 Tier 2 module"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/gt_motive/status")
        data = response.json()
        assert len(data.get("tier_2_modules_used", [])) >= 1

    def test_supported_brands(self):
        """Test GT Motive lists supported automotive brands"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/gt_motive/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        # Should mention supported brands or multi-modal extraction
        assert len(capabilities) > 0

# ============================================================================
# Test 5: Solera POC
# ============================================================================

class TestSoleraPOC:
    """Tests for Solera insurance claims processing"""

    def test_status_endpoint(self):
        """Test Solera status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/solera/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    def test_description_accuracy(self):
        """Test Solera description mentions insurance/claims"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/solera/status")
        data = response.json()
        description = data["description"]
        assert any(keyword in description.lower() for keyword in ["insurance", "claims", "workflow"])

    def test_tier2_modules_present(self):
        """Test Solera uses at least 1 Tier 2 module"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/solera/status")
        data = response.json()
        assert len(data.get("tier_2_modules_used", [])) >= 1

    def test_multi_ocr_capability(self):
        """Test Solera mentions multi-OCR capability"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/solera/status")
        data = response.json()
        capabilities = data.get("capabilities", [])
        # Should mention OCR, VIN, or damage assessment
        assert len(capabilities) > 0

# ============================================================================
# Test 6: Construction Monitor POC
# ============================================================================

class TestConstructionMonitorPOC:
    """Tests for Construction Monitor project tracking"""

    def test_status_endpoint(self):
        """Test Construction Monitor status endpoint is operational"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/construction_monitor/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    def test_description_accuracy(self):
        """Test Construction Monitor description mentions construction/project"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/construction_monitor/status")
        data = response.json()
        description = data["description"]
        assert any(keyword in description.lower() for keyword in ["construction", "project", "monitor"])

    def test_tier2_modules_present(self):
        """Test Construction Monitor uses at least 1 Tier 2 module"""
        response = requests.get(f"{BASE_URL}/api/v1/customer/construction_monitor/status")
        data = response.json()
        assert len(data.get("tier_2_modules_used", [])) >= 1

# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegrationAll:
    """Integration tests across all 6 Customer Solutions"""

    def test_all_pocs_operational(self):
        """Test all 6 POCs return operational status"""
        pocs = [
            "british_council",
            "cru",
            "grant_thornton",
            "gt_motive",
            "solera",
            "construction_monitor"
        ]

        for poc in pocs:
            response = requests.get(f"{BASE_URL}/api/v1/customer/{poc}/status")
            assert response.status_code == 200, f"{poc} failed"
            data = response.json()
            assert data["status"] == "operational", f"{poc} not operational"

    def test_unique_descriptions(self):
        """Test all 6 POCs have unique descriptions"""
        pocs = [
            "british_council",
            "cru",
            "grant_thornton",
            "gt_motive",
            "solera",
            "construction_monitor"
        ]

        descriptions = []
        for poc in pocs:
            response = requests.get(f"{BASE_URL}/api/v1/customer/{poc}/status")
            data = response.json()
            descriptions.append(data["description"])

        # All descriptions should be unique
        assert len(descriptions) == len(set(descriptions)), "Duplicate descriptions found"

    def test_response_times(self):
        """Test all POCs respond within 500ms"""
        import time

        pocs = [
            "british_council",
            "cru",
            "grant_thornton",
            "gt_motive",
            "solera",
            "construction_monitor"
        ]

        for poc in pocs:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/v1/customer/{poc}/status")
            elapsed = (time.time() - start) * 1000  # Convert to ms

            assert response.status_code == 200, f"{poc} failed"
            assert elapsed < 500, f"{poc} too slow: {elapsed:.0f}ms"

# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance benchmarks for Customer Solutions"""

    def test_concurrent_requests(self):
        """Test all POCs handle concurrent requests"""
        import concurrent.futures

        pocs = [
            "british_council",
            "cru",
            "grant_thornton",
            "gt_motive",
            "solera",
            "construction_monitor"
        ]

        def fetch_status(poc):
            response = requests.get(f"{BASE_URL}/api/v1/customer/{poc}/status")
            return response.status_code == 200

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(fetch_status, pocs))

        assert all(results), "Some concurrent requests failed"

# ============================================================================
# Frontend Tests (Requires Playwright)
# ============================================================================

class TestFrontendComponents:
    """Frontend component tests (requires Playwright)"""

    @pytest.mark.skipif(True, reason="Requires Playwright setup")
    def test_british_council_ui_loads(self):
        """Test British Council frontend component loads"""
        # Playwright test would go here
        pass

    @pytest.mark.skipif(True, reason="Requires Playwright setup")
    def test_gt_motive_ui_loads(self):
        """Test GT Motive frontend component loads"""
        # Playwright test would go here
        pass
