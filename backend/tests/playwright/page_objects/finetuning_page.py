"""Page Object for Fine-Tuning UI."""
from playwright.sync_api import Page, expect
import time


class FineTuningPage:
    """Page object for Fine-Tuning Governance UI."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # Navigation
    def navigate_to_admin(self):
        """Navigate to admin page."""
        self.page.goto(f"{self.base_url}/admin")
        self.page.wait_for_load_state("networkidle")

    def navigate_to_finetuning(self):
        """Navigate to Fine-Tuning tab."""
        self.navigate_to_admin()
        # Click Fine-Tuning tab button
        finetuning_button = self.page.get_by_text("Fine-Tuning", exact=False)
        finetuning_button.click()
        time.sleep(1)  # Wait for tab to load

    # Section Navigation
    def click_models_section(self):
        """Click on Models section."""
        self.page.get_by_text("Models", exact=True).first.click()
        time.sleep(0.5)

    def click_datasets_section(self):
        """Click on Datasets section."""
        self.page.get_by_text("Datasets", exact=True).click()
        time.sleep(0.5)

    def click_jobs_section(self):
        """Click on Fine-tuning Jobs section."""
        self.page.get_by_text("Fine-tuning Jobs", exact=False).click()
        time.sleep(0.5)

    def click_evaluations_section(self):
        """Click on Evaluations section."""
        self.page.get_by_text("Evaluations", exact=True).click()
        time.sleep(0.5)

    def click_deployment_section(self):
        """Click on Deployment section."""
        self.page.get_by_text("Deployment", exact=True).click()
        time.sleep(0.5)

    def click_monitoring_section(self):
        """Click on Monitoring section."""
        self.page.get_by_text("Monitoring", exact=True).click()
        time.sleep(0.5)

    def click_governance_section(self):
        """Click on Governance & Audit section."""
        self.page.get_by_text("Governance & Audit", exact=False).click()
        time.sleep(0.5)

    # Models Section
    def get_base_models_count(self) -> int:
        """Get count of base models in dropdown."""
        self.click_models_section()
        # Try to find base models dropdown or list
        try:
            # Wait for models to load
            self.page.wait_for_selector('text="Base Models"', timeout=5000)
            # Count model cards or options
            models = self.page.locator('[data-testid="base-model-card"]')
            return models.count()
        except:
            return 0

    def verify_model_in_catalog(self, model_name: str) -> bool:
        """Verify a specific model appears in catalog."""
        self.click_models_section()
        try:
            self.page.wait_for_selector(f'text="{model_name}"', timeout=5000)
            return True
        except:
            return False

    def select_base_model(self, model_name: str):
        """Select a base model for fine-tuning."""
        # Click on the model card or dropdown option
        model_element = self.page.get_by_text(model_name, exact=False).first
        model_element.click()
        time.sleep(0.5)

    # Datasets Section
    def upload_dataset(self, file_path: str, dataset_name: str = "CloudSync Support QA"):
        """Upload a dataset file."""
        self.click_datasets_section()

        # Look for upload button or file input
        try:
            # Try to find file input (may be hidden)
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(file_path)
            time.sleep(1)

            # Fill in dataset name if there's a name field
            try:
                name_input = self.page.get_by_placeholder("Dataset name", exact=False)
                name_input.fill(dataset_name)
            except:
                pass

            # Click upload/submit button
            upload_button = self.page.get_by_role("button", name="Upload").or_(
                self.page.get_by_role("button", name="Submit")
            )
            upload_button.click()
            time.sleep(2)  # Wait for upload to process

            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def verify_dataset_uploaded(self, dataset_name: str) -> bool:
        """Verify dataset appears in dataset list."""
        self.click_datasets_section()
        try:
            self.page.wait_for_selector(f'text="{dataset_name}"', timeout=10000)
            return True
        except:
            return False

    def get_dataset_count(self) -> int:
        """Get count of datasets."""
        self.click_datasets_section()
        try:
            datasets = self.page.locator('[data-testid="dataset-row"]')
            return datasets.count()
        except:
            return 0

    # Fine-tuning Jobs Section
    def create_training_job(
        self,
        job_name: str,
        base_model: str,
        dataset_name: str,
        method: str = "qlora"
    ) -> bool:
        """Create a new training job."""
        self.click_jobs_section()

        try:
            # Click "Create Job" or "New Job" button
            create_button = self.page.get_by_role("button", name="Create Job").or_(
                self.page.get_by_role("button", name="New Job")
            )
            create_button.click()
            time.sleep(1)

            # Fill job name
            name_input = self.page.get_by_placeholder("Job name", exact=False)
            name_input.fill(job_name)

            # Select base model
            self.page.get_by_text(base_model, exact=False).click()

            # Select dataset
            self.page.get_by_text(dataset_name, exact=False).click()

            # Select fine-tuning method
            self.page.get_by_text(method, exact=False).click()

            # Submit job
            submit_button = self.page.get_by_role("button", name="Start Training").or_(
                self.page.get_by_role("button", name="Submit")
            )
            submit_button.click()
            time.sleep(2)

            return True
        except Exception as e:
            print(f"Job creation failed: {e}")
            return False

    def verify_job_created(self, job_name: str) -> bool:
        """Verify training job appears in jobs list."""
        self.click_jobs_section()
        try:
            self.page.wait_for_selector(f'text="{job_name}"', timeout=5000)
            return True
        except:
            return False

    def get_job_status(self, job_name: str) -> str:
        """Get status of a training job."""
        self.click_jobs_section()
        try:
            job_row = self.page.locator(f'text="{job_name}"').locator('..')
            status = job_row.locator('[data-testid="job-status"]').text_content()
            return status.strip()
        except:
            return "unknown"

    # Evaluation Hub Section
    def view_evaluation_metrics(self, model_name: str) -> dict:
        """View evaluation metrics for a model."""
        self.click_evaluations_section()
        metrics = {}

        try:
            # Click on model to view details
            self.page.get_by_text(model_name, exact=False).click()
            time.sleep(1)

            # Extract metrics (adjust selectors based on actual UI)
            metrics_elements = self.page.locator('[data-testid="metric"]')
            for i in range(metrics_elements.count()):
                element = metrics_elements.nth(i)
                label = element.locator('[data-testid="metric-label"]').text_content()
                value = element.locator('[data-testid="metric-value"]').text_content()
                metrics[label] = value

            return metrics
        except:
            return {}

    def compare_models(self, model1: str, model2: str) -> bool:
        """Compare two models in evaluation hub."""
        self.click_evaluations_section()

        try:
            # Select first model
            self.page.get_by_text(model1, exact=False).first.check()

            # Select second model
            self.page.get_by_text(model2, exact=False).first.check()

            # Click compare button
            compare_button = self.page.get_by_role("button", name="Compare")
            compare_button.click()
            time.sleep(1)

            return True
        except:
            return False

    # Deployment Section
    def deploy_model_to_ollama(self, model_name: str) -> bool:
        """Deploy a model to Ollama."""
        self.click_deployment_section()

        try:
            # Find model row
            model_row = self.page.locator(f'text="{model_name}"').locator('..')

            # Click deploy button
            deploy_button = model_row.get_by_role("button", name="Deploy")
            deploy_button.click()
            time.sleep(1)

            # Confirm deployment
            confirm_button = self.page.get_by_role("button", name="Confirm")
            confirm_button.click()
            time.sleep(2)

            return True
        except Exception as e:
            print(f"Deployment failed: {e}")
            return False

    def verify_model_deployed(self, model_name: str) -> bool:
        """Verify model is deployed."""
        self.click_deployment_section()
        try:
            # Look for deployed status indicator
            model_row = self.page.locator(f'text="{model_name}"').locator('..')
            deployed_badge = model_row.locator('text="Deployed"').or_(
                model_row.locator('text="Active"')
            )
            deployed_badge.wait_for(timeout=5000)
            return True
        except:
            return False

    # Monitoring Dashboard Section
    def verify_monitoring_charts_visible(self) -> bool:
        """Verify monitoring charts are displayed."""
        self.click_monitoring_section()
        try:
            # Look for chart containers
            charts = self.page.locator('[data-testid="chart"]').or_(
                self.page.locator('canvas')
            )
            return charts.count() > 0
        except:
            return False

    def get_active_jobs_count_from_monitoring(self) -> int:
        """Get count of active jobs from monitoring dashboard."""
        self.click_monitoring_section()
        try:
            count_element = self.page.locator('[data-testid="active-jobs-count"]')
            count_text = count_element.text_content()
            return int(count_text.strip())
        except:
            return 0

    # Governance & Audit Section
    def verify_audit_trail_exists(self, action: str) -> bool:
        """Verify an action appears in audit trail."""
        self.click_governance_section()
        try:
            self.page.wait_for_selector(f'text="{action}"', timeout=5000)
            return True
        except:
            return False

    def get_audit_logs_count(self) -> int:
        """Get count of audit log entries."""
        self.click_governance_section()
        try:
            logs = self.page.locator('[data-testid="audit-log-row"]')
            return logs.count()
        except:
            return 0

    def approve_model(self, model_name: str) -> bool:
        """Approve a model in governance workflow."""
        self.click_governance_section()

        try:
            # Find model in approval queue
            model_row = self.page.locator(f'text="{model_name}"').locator('..')

            # Click approve button
            approve_button = model_row.get_by_role("button", name="Approve")
            approve_button.click()
            time.sleep(1)

            # Confirm approval
            confirm_button = self.page.get_by_role("button", name="Confirm")
            confirm_button.click()
            time.sleep(1)

            return True
        except Exception as e:
            print(f"Approval failed: {e}")
            return False

    # Helper Methods
    def wait_for_section_to_load(self, timeout: int = 5000):
        """Wait for section content to load."""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        time.sleep(0.5)

    def take_screenshot(self, name: str):
        """Take screenshot of current page."""
        self.page.screenshot(path=f"backend/tests/playwright/test_results/{name}.png")

    def get_current_section(self) -> str:
        """Get currently active section name."""
        try:
            active_nav = self.page.locator('.bg-indigo-50, .bg-indigo-600').first
            return active_nav.text_content().strip()
        except:
            return "unknown"
