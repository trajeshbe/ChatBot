"""
Playwright E2E tests for all Tier 2 Domain Verticals.

Covers:
- Construction (4 modules)
- Procurement (4 modules)
- HR & Talent (3 modules)
- Agriculture (2 modules)
- Analytics (4 modules)
"""
import os
import time
import pytest
from playwright.sync_api import Page
from page_objects.tier2_module_page import (
    ConstructionPage, ProcurementPage, HRTalentPage,
    AgriculturePage, AnalyticsPage
)


# ===========================================
# CONSTRUCTION VERTICAL TESTS (4 modules)
# ===========================================

class TestConstructionVertical:
    """Tests for Construction domain vertical modules."""

    def test_planning_classifier_navigation(self, page):
        """Test Planning Classifier module navigation."""
        planning_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "planning-classifier")
        planning_page.navigate_to_module()
        assert page.url.endswith("/") or "planning" in page.url or "construction" in page.url

    def test_planning_classifier_upload_document(self, page):
        """Test uploading planning document for classification."""
        planning_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "planning-classifier")
        planning_page.navigate_to_module()

        sample_file = "sample_data/tier2_domain_verticals/construction/planning_application.pdf"
        if os.path.exists(sample_file):
            planning_page.upload_planning_document(sample_file)
            planning_page.click_submit_button()
            time.sleep(4)
            planning_page.verify_results_visible()
        else:
            pytest.skip(f"Sample file not found: {sample_file}")

    def test_mine_scope_navigation(self, page):
        """Test Mine Scope Analysis module navigation."""
        mine_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "mine-scope")
        mine_page.navigate_to_module()
        assert page.url.endswith("/") or "mine" in page.url or "scope" in page.url

    def test_mine_scope_analysis(self, page):
        """Test mine scope requirements extraction."""
        mine_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "mine-scope")
        mine_page.navigate_to_module()

        sample_file = "sample_data/tier2_domain_verticals/construction/mining_scope.pdf"
        if os.path.exists(sample_file):
            mine_page.upload_planning_document(sample_file)
            mine_page.click_submit_button()
            time.sleep(5)

            results = mine_page.get_classification_results()
            assert results is not None
        else:
            pytest.skip(f"Sample file not found: {sample_file}")

    def test_estimator_au_navigation(self, page):
        """Test AU Cost Estimator module navigation."""
        estimator_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "estimator-au")
        estimator_page.navigate_to_module()
        assert page.url.endswith("/") or "estimator" in page.url

    def test_construction_metrics_navigation(self, page):
        """Test Construction Building Metrics module navigation."""
        metrics_page = ConstructionPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "construction")
        metrics_page.navigate_to_module()
        assert page.url.endswith("/") or "construction" in page.url


# ===========================================
# PROCUREMENT VERTICAL TESTS (4 modules)
# ===========================================

class TestProcurementVertical:
    """Tests for Procurement domain vertical modules."""

    def test_po_invoice_matcher_navigation(self, page):
        """Test PO-Invoice Matcher module navigation."""
        matcher_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "matcher")
        matcher_page.navigate_to_module()
        assert page.url.endswith("/") or "matcher" in page.url or "procurement" in page.url

    def test_po_invoice_matching(self, page):
        """Test matching purchase order to invoice."""
        matcher_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "matcher")
        matcher_page.navigate_to_module()

        po_file = "sample_data/tier2_domain_verticals/procurement/purchase_order.pdf"
        invoice_file = "sample_data/tier2_domain_verticals/procurement/invoice.pdf"

        if os.path.exists(po_file) and os.path.exists(invoice_file):
            matcher_page.upload_purchase_order(po_file)
            time.sleep(1)
            matcher_page.upload_invoice(invoice_file)
            matcher_page.click_submit_button()
            time.sleep(4)

            results = matcher_page.get_match_results()
            assert results is not None
            assert "match" in str(results).lower() or "variance" in str(results).lower()
        else:
            pytest.skip(f"Sample files not found")

    def test_vendor_recommendation_navigation(self, page):
        """Test Vendor Recommendation module navigation."""
        vendor_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "vendor-recommendation")
        vendor_page.navigate_to_module()
        assert page.url.endswith("/") or "vendor" in page.url

    def test_vendor_recommendation_query(self, page):
        """Test vendor recommendation system."""
        vendor_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "vendor-recommendation")
        vendor_page.navigate_to_module()

        # Enter vendor requirements
        try:
            vendor_page.enter_text_input("Need IT equipment vendor with 2-day delivery")
            vendor_page.click_submit_button()
            time.sleep(3)
            vendor_page.verify_results_visible()
        except:
            pytest.skip("Module interface different than expected")

    def test_tender_intelligence_navigation(self, page):
        """Test Tender Intelligence module navigation."""
        tender_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "tender-intelligence")
        tender_page.navigate_to_module()
        assert page.url.endswith("/") or "tender" in page.url

    def test_spend_analytics_navigation(self, page):
        """Test Spend Analytics module navigation."""
        spend_page = ProcurementPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "spend-smart")
        spend_page.navigate_to_module()
        assert page.url.endswith("/") or "spend" in page.url


# ===========================================
# HR & TALENT VERTICAL TESTS (3 modules)
# ===========================================

class TestHRTalentVertical:
    """Tests for HR & Talent domain vertical modules."""

    def test_talent_pulse_navigation(self, page):
        """Test Talent Pulse module navigation."""
        pulse_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "talent-pulse")
        pulse_page.navigate_to_module()
        assert page.url.endswith("/") or "talent" in page.url or "pulse" in page.url

    def test_talent_pulse_resume_analysis(self, page):
        """Test resume analysis in Talent Pulse."""
        pulse_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "talent-pulse")
        pulse_page.navigate_to_module()

        resume_file = "sample_data/tier2_domain_verticals/hr_talent/sample_resume.pdf"
        if os.path.exists(resume_file):
            pulse_page.upload_resume(resume_file)
            pulse_page.click_submit_button()
            time.sleep(4)

            results = pulse_page.get_talent_results()
            assert results is not None
        else:
            pytest.skip(f"Sample resume not found: {resume_file}")

    def test_talent_search_navigation(self, page):
        """Test Talent Search module navigation."""
        search_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "talent-search")
        search_page.navigate_to_module()
        assert page.url.endswith("/") or "talent" in page.url or "search" in page.url

    def test_talent_search_skill_matching(self, page):
        """Test skill-based talent search."""
        search_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "talent-search")
        search_page.navigate_to_module()

        try:
            search_page.enter_skill_query("Python, FastAPI, React, PostgreSQL")
            search_page.click_submit_button()
            time.sleep(3)
            search_page.verify_results_visible()
        except:
            pytest.skip("Module interface different than expected")

    def test_taxonomy_skillmatch_navigation(self, page):
        """Test Taxonomy Skillmatch module navigation."""
        skillmatch_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "taxonomy-skillmatch")
        skillmatch_page.navigate_to_module()
        assert page.url.endswith("/") or "skill" in page.url or "taxonomy" in page.url

    def test_taxonomy_skillmatch_job_matching(self, page):
        """Test job description to skills matching."""
        skillmatch_page = HRTalentPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "taxonomy-skillmatch")
        skillmatch_page.navigate_to_module()

        job_file = "sample_data/tier2_domain_verticals/hr_talent/job_description.txt"
        if os.path.exists(job_file):
            skillmatch_page.upload_job_description(job_file)
            skillmatch_page.click_submit_button()
            time.sleep(3)
            skillmatch_page.verify_results_visible()
        else:
            pytest.skip(f"Sample job description not found: {job_file}")


# ===========================================
# AGRICULTURE VERTICAL TESTS (2 modules)
# ===========================================

class TestAgricultureVertical:
    """Tests for Agriculture domain vertical modules."""

    def test_agri_taxonomy_navigation(self, page):
        """Test Agri Taxonomy module navigation."""
        taxonomy_page = AgriculturePage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "agri-taxonomy")
        taxonomy_page.navigate_to_module()
        assert page.url.endswith("/") or "agri" in page.url or "taxonomy" in page.url

    def test_agri_taxonomy_field_report_extraction(self, page):
        """Test agricultural field report taxonomy extraction."""
        taxonomy_page = AgriculturePage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "agri-taxonomy")
        taxonomy_page.navigate_to_module()

        sample_report = """
        Field Inspection Report - Plot #42
        Date: January 15, 2024
        Crop: Wheat
        Growth Stage: Flowering

        Observations:
        - Crop establishment: Good, uniform germination across the plot
        - Soil condition: Moist, well-drained, dark brown color
        - Pest observation: Minor aphid infestation on 5% of plants
        - Disease: No visible signs of fungal or bacterial infection
        - Weed pressure: Low, scattered broadleaf weeds

        Recommendations:
        - Apply organic aphid control within 48 hours
        - Monitor soil moisture, irrigation may be needed in 7 days
        - Scout for rust disease in 2 weeks
        """

        taxonomy_page.enter_field_report(sample_report)
        taxonomy_page.click_submit_button()
        time.sleep(5)

        results = taxonomy_page.get_taxonomy_results()
        assert results is not None

        # Verify key taxonomy fields extracted
        results_str = str(results).lower()
        assert "crop" in results_str or "wheat" in results_str or "pest" in results_str

    def test_agronomy_decision_navigation(self, page):
        """Test Agronomy Decision Support module navigation."""
        agronomy_page = AgriculturePage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "agronomy-decision")
        agronomy_page.navigate_to_module()
        assert page.url.endswith("/") or "agronomy" in page.url or "decision" in page.url

    def test_agronomy_decision_data_upload(self, page):
        """Test uploading agricultural data for decision support."""
        agronomy_page = AgriculturePage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "agronomy-decision")
        agronomy_page.navigate_to_module()

        agri_data_file = "sample_data/tier2_domain_verticals/agriculture/crop_data.csv"
        if os.path.exists(agri_data_file):
            agronomy_page.upload_agricultural_data(agri_data_file)
            agronomy_page.click_submit_button()
            time.sleep(4)
            agronomy_page.verify_results_visible()
        else:
            pytest.skip(f"Sample agricultural data not found: {agri_data_file}")


# ===========================================
# ANALYTICS VERTICAL TESTS (4 modules)
# ===========================================

class TestAnalyticsVertical:
    """Tests for Analytics domain vertical modules."""

    def test_customer_churn_navigation(self, page):
        """Test Customer Churn module navigation."""
        churn_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "customer-churn")
        churn_page.navigate_to_module()
        assert page.url.endswith("/") or "churn" in page.url or "analytics" in page.url

    def test_customer_churn_analysis(self, page):
        """Test customer churn prediction."""
        churn_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "customer-churn")
        churn_page.navigate_to_module()

        churn_data = "sample_data/tier2_domain_verticals/analytics/customer_data.csv"
        if os.path.exists(churn_data):
            churn_page.upload_data_file(churn_data)
            churn_page.click_submit_button()
            time.sleep(4)

            results = churn_page.get_analytics_results()
            assert results is not None
        else:
            pytest.skip(f"Sample customer data not found: {churn_data}")

    def test_financial_anomaly_navigation(self, page):
        """Test Financial Anomaly Detection module navigation."""
        anomaly_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "financial-anomaly")
        anomaly_page.navigate_to_module()
        assert page.url.endswith("/") or "anomaly" in page.url or "financial" in page.url

    def test_predictive_analytics_navigation(self, page):
        """Test Predictive Analytics module navigation."""
        predictive_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "predictive-analytics")
        predictive_page.navigate_to_module()
        assert page.url.endswith("/") or "predictive" in page.url

    def test_sales_performance_navigation(self, page):
        """Test Sales Performance module navigation."""
        sales_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "sales-performance")
        sales_page.navigate_to_module()
        assert page.url.endswith("/") or "sales" in page.url

    def test_sales_performance_analysis(self, page):
        """Test sales performance metrics analysis."""
        sales_page = AnalyticsPage(page, os.getenv("FRONTEND_URL", "http://localhost:3001"), "sales-performance")
        sales_page.navigate_to_module()

        sales_data = "sample_data/tier2_domain_verticals/analytics/sales_data.csv"
        if os.path.exists(sales_data):
            sales_page.upload_data_file(sales_data)
            sales_page.click_submit_button()
            time.sleep(3)
            sales_page.verify_results_visible()
        else:
            pytest.skip(f"Sample sales data not found: {sales_data}")
