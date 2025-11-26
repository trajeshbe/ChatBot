"""
AI-Powered Navigation Agent for Smart Web Extraction (Improved Version)

This module enables natural language-driven website navigation using:
- LLM-powered instruction parsing
- Playwright for browser automation with text-based clicking
- URL change validation to prevent loops
- Intelligent link filtering
- Comprehensive debug logging

Example:
    URL: https://books.toscrape.com/
    Instructions: "get all books under Fantasy category"

    Agent will:
    1. Load homepage
    2. Find "Fantasy" text in links
    3. Click using text matching (more reliable than CSS selectors)
    4. Extract all books from the Fantasy page
"""

import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser
import json
import asyncio

logger = logging.getLogger(__name__)


class NavigationAgent:
    """
    AI agent that navigates websites based on natural language instructions

    Improvements over previous version:
    - Text-based clicking instead of CSS selectors
    - URL change validation to detect stuck loops
    - Better link filtering
    - Comprehensive logging for debugging
    """

    def __init__(self, llm_service=None):
        """
        Initialize navigation agent

        Args:
            llm_service: LLM service for AI-powered decision making
        """
        self.llm_service = llm_service
        self.logger = logger

    async def navigate_and_extract(
        self,
        url: str,
        user_instructions: str,
        llm_provider: str = "openai",
        model_id: str = "gpt-4-turbo",
        max_steps: int = 5,
        timeout: int = 60000
    ) -> Dict[str, Any]:
        """
        Navigate website based on natural language instructions and extract data

        Args:
            url: Starting URL (e.g., homepage)
            user_instructions: Natural language instructions (e.g., "get all books under Fantasy")
            llm_provider: LLM provider to use
            model_id: Specific model ID
            max_steps: Maximum navigation steps
            timeout: Page load timeout in milliseconds

        Returns:
            {
                "success": bool,
                "data": List[Dict],  # Extracted data
                "navigation_path": List[str],  # URLs visited
                "steps_taken": int,
                "final_url": str,
                "error": Optional[str]
            }
        """
        try:
            logger.info("="*80)
            logger.info("🧭 AI NAVIGATION AGENT INITIATED (IMPROVED VERSION)")
            logger.info(f"📍 Starting URL: {url}")
            logger.info(f"📋 Instructions: {user_instructions}")
            logger.info("="*80)

            navigation_path = [url]
            steps_taken = 0

            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()

                try:
                    # Step 1: Parse instructions to understand the goal
                    logger.info("\n📖 Step 1: Parsing navigation instructions...")
                    navigation_plan = await self._parse_navigation_instructions(
                        user_instructions,
                        url,
                        llm_provider,
                        model_id
                    )

                    logger.info(f"✅ Navigation plan: {json.dumps(navigation_plan, indent=2)}")

                    # Step 2: Load starting page
                    logger.info(f"\n🌐 Step 2: Loading starting page: {url}")
                    await page.goto(url, timeout=timeout, wait_until="networkidle")
                    await asyncio.sleep(2)  # Let JavaScript load

                    # Step 3: Execute navigation steps
                    current_url = url

                    # 🆕 FIX: Check if we're ALREADY on the target page before navigating
                    target_text = navigation_plan.get("target_category", "")
                    already_on_target = False

                    if target_text:
                        # Check if URL already contains the target category
                        target_slug = target_text.lower().replace(' ', '-').replace('_', '-')
                        current_url_lower = current_url.lower()

                        if target_slug in current_url_lower:
                            logger.info(f"\n✅ Already on target page! URL contains '{target_slug}'")
                            logger.info(f"   Current URL: {current_url}")
                            logger.info(f"   Skipping navigation, will extract directly from this page")
                            already_on_target = True

                    if navigation_plan.get("requires_navigation", False) and not already_on_target:
                        logger.info("\n🧭 Step 3: Executing navigation...")

                        for step_num in range(max_steps):
                            steps_taken += 1
                            previous_url = current_url

                            logger.info(f"\n🔍 Step {steps_taken}: Looking for link with text containing '{target_text}'")

                            # Get all visible link texts
                            links_info = await self._get_filtered_links(page, target_text)
                            logger.info(f"   Found {len(links_info)} relevant links")

                            if not links_info:
                                logger.warning(f"   ⚠️  No relevant links found for '{target_text}'")
                                break

                            # Ask AI which link to click
                            link_to_click = await self._select_best_link(
                                links_info,
                                target_text,
                                current_url,
                                user_instructions,
                                llm_provider,
                                model_id
                            )

                            if link_to_click["action"] == "extract":
                                logger.info(f"   ✅ AI says we're on target page, stopping navigation")
                                break

                            if link_to_click["action"] == "click":
                                link_text = link_to_click["text"]
                                logger.info(f"   🖱️  Attempting to click link: '{link_text}'")

                                # Try text-based clicking (most reliable)
                                try:
                                    await page.get_by_text(link_text, exact=False).first.click(timeout=10000)
                                    await page.wait_for_load_state("networkidle", timeout=timeout)
                                    await asyncio.sleep(2)

                                    current_url = page.url

                                    # Validate URL actually changed
                                    if current_url == previous_url:
                                        logger.warning(f"   ⚠️  URL unchanged after click, trying next link...")
                                        continue

                                    navigation_path.append(current_url)
                                    logger.info(f"   ✅ Successfully navigated to: {current_url}")

                                    # Check if we've reached a category/content page
                                    if await self._is_target_page(page, target_text):
                                        logger.info(f"   🎯 Reached target page!")
                                        break

                                except Exception as click_error:
                                    logger.error(f"   ❌ Click failed: {click_error}")
                                    logger.info(f"   🔄 Will try next step...")
                                    continue

                            else:
                                logger.warning(f"   ⚠️  Unknown action: {link_to_click['action']}")
                                break

                    # Step 4: Extract data from current page (with pagination support)
                    logger.info(f"\n📊 Step 4: Extracting data from final page...")
                    logger.info(f"   Final URL: {page.url}")

                    all_extracted_data = []
                    pages_processed = 0
                    max_pages = 10  # Safety limit to prevent infinite loops

                    while pages_processed < max_pages:
                        pages_processed += 1
                        logger.info(f"\n📄 Processing page {pages_processed}...")
                        logger.info(f"   Current URL: {page.url}")

                        # Extract data from current page
                        page_html = await page.content()
                        page_data = await self._extract_data_with_ai(
                            page_html,
                            user_instructions,
                            navigation_plan.get("extraction_target", ""),
                            llm_provider,
                            model_id
                        )

                        logger.info(f"   ✅ Extracted {len(page_data)} items from page {pages_processed}")
                        all_extracted_data.extend(page_data)

                        # 🆕 Check for "Next" button/link for pagination
                        has_next = False
                        try:
                            # Common pagination patterns
                            next_selectors = [
                                "a:has-text('Next')",
                                "a:has-text('next')",
                                "a.next",
                                "li.next > a",
                                "[rel='next']",
                                "a[aria-label*='Next']",
                                ".pager-next a",
                                ".pagination .next a"
                            ]

                            current_url_before_click = page.url

                            for selector in next_selectors:
                                try:
                                    next_button = page.locator(selector).first
                                    if await next_button.count() > 0:
                                        logger.info(f"   🔗 Found 'Next' button with selector: {selector}")

                                        # Click and wait for navigation
                                        await next_button.click(timeout=5000)
                                        await page.wait_for_load_state("networkidle", timeout=timeout)
                                        await asyncio.sleep(2)

                                        # Verify URL changed
                                        if page.url != current_url_before_click:
                                            logger.info(f"   ✅ Navigated to next page: {page.url}")
                                            navigation_path.append(page.url)
                                            has_next = True
                                            break
                                        else:
                                            logger.warning(f"   ⚠️  URL unchanged after clicking next button")
                                except Exception as e:
                                    # Try next selector
                                    continue

                        except Exception as pagination_error:
                            logger.info(f"   ℹ️  No more pages (pagination check failed: {pagination_error})")

                        if not has_next:
                            logger.info(f"   🏁 No more pages found. Finished pagination.")
                            break

                    logger.info(f"\n✅ Total extracted: {len(all_extracted_data)} items from {pages_processed} page(s)")

                    return {
                        "success": True,
                        "data": all_extracted_data,
                        "navigation_path": navigation_path,
                        "steps_taken": steps_taken,
                        "final_url": page.url,
                        "pages_processed": pages_processed,
                        "error": None
                    }

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Navigation agent error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "data": [],
                "navigation_path": navigation_path,
                "steps_taken": steps_taken,
                "final_url": url,
                "error": str(e)
            }

    async def _get_filtered_links(self, page: Page, target_keyword: str) -> List[Dict[str, str]]:
        """
        Get filtered list of links relevant to navigation target

        Filters out:
        - Footer links
        - Social media links
        - Navigation boilerplate

        Prioritizes:
        - Links containing target keyword
        - Category/section links
        """
        try:
            # Get all links using Playwright
            all_links = await page.locator('a').all()

            filtered_links = []
            target_lower = target_keyword.lower()

            # Blacklist of irrelevant link patterns
            blacklist = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube',
                        'terms', 'privacy', 'cookie', 'contact', 'about', 'help',
                        'login', 'signup', 'register', 'cart', 'checkout']

            for link in all_links[:100]:  # Limit to first 100 links
                try:
                    text = await link.inner_text(timeout=1000)
                    text = text.strip()
                    href = await link.get_attribute('href')

                    if not text or len(text) > 100:  # Skip empty or too long
                        continue

                    text_lower = text.lower()

                    # Skip blacklisted links
                    if any(keyword in text_lower for keyword in blacklist):
                        continue

                    # Prioritize links containing target keyword
                    relevance_score = 0
                    if target_lower in text_lower:
                        relevance_score = 10
                    elif target_lower in (href or '').lower():
                        relevance_score = 5

                    filtered_links.append({
                        "text": text,
                        "href": href or "",
                        "relevance": relevance_score
                    })

                except:
                    continue

            # Sort by relevance
            filtered_links.sort(key=lambda x: x["relevance"], reverse=True)

            # Return top 20 most relevant
            return filtered_links[:20]

        except Exception as e:
            logger.error(f"Error filtering links: {e}")
            return []

    async def _is_target_page(self, page: Page, target_keyword: str) -> bool:
        """Check if current page is the target page based on content"""
        try:
            # Check page title
            title = await page.title()
            if target_keyword.lower() in title.lower():
                return True

            # Check if page has category/listing indicators
            body_text = await page.inner_text('body')
            body_lower = body_text[:1000].lower()

            # Check for category page indicators
            indicators = [
                target_keyword.lower(),
                'showing',
                'results',
                'items',
                'products'
            ]

            matches = sum(1 for indicator in indicators if indicator in body_lower)
            return matches >= 2

        except:
            return False

    async def _parse_navigation_instructions(
        self,
        user_instructions: str,
        start_url: str,
        llm_provider: str,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Parse natural language instructions to understand navigation goals

        Returns:
            {
                "requires_navigation": bool,
                "target_category": str,  # e.g., "Fantasy"
                "extraction_target": str,  # e.g., "books"
                "data_fields": List[str]  # e.g., ["title", "price"]
            }
        """
        prompt = f"""Analyze this web extraction request and determine the navigation plan.

Starting URL: {start_url}
User Instructions: {user_instructions}

Determine:
1. Does this require navigating from the homepage? (true/false)
2. What category/section should we navigate to?
3. What type of data should be extracted?
4. What specific fields should be extracted?

Respond ONLY with valid JSON:
{{
    "requires_navigation": boolean,
    "target_category": "category name or null",
    "extraction_target": "what to extract (e.g., books, products, articles)",
    "data_fields": ["field1", "field2"]
}}

Examples:

Input: "get all books under Fantasy"
Output: {{"requires_navigation": true, "target_category": "Fantasy", "extraction_target": "books", "data_fields": ["title", "price", "availability"]}}

Input: "extract all products"
Output: {{"requires_navigation": false, "target_category": null, "extraction_target": "products", "data_fields": ["name", "price"]}}

Your response (JSON only):"""

        try:
            messages = [
                {"role": "system", "content": "You are a web navigation planning assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_service.generate(
                prompt=prompt,
                messages=messages,
                model_id=model_id,
                temperature=0.1,
                max_tokens=500
            )

            response_text = response.get('content', '').strip()

            if not response_text:
                raise ValueError("Empty response from LLM")

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            plan = json.loads(response_text)
            return plan

        except Exception as e:
            logger.warning(f"⚠️  Failed to parse navigation plan: {e}")
            # Fallback: assume simple extraction
            return {
                "requires_navigation": False,
                "target_category": None,
                "extraction_target": "items",
                "data_fields": []
            }

    async def _select_best_link(
        self,
        links: List[Dict[str, str]],
        target_category: str,
        current_url: str,
        user_instructions: str,
        llm_provider: str,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Ask AI to select the best link to click from filtered list

        Returns:
            {"action": "click", "text": "Fantasy"}
            or
            {"action": "extract"}
        """
        # If we have a highly relevant link (score 10), click it directly
        if links and links[0]["relevance"] >= 10:
            logger.info(f"   🎯 Found exact match: '{links[0]['text']}'")
            return {"action": "click", "text": links[0]["text"]}

        # Otherwise ask AI
        prompt = f"""You are a web navigation agent. Select the best link to click.

Current URL: {current_url}
User Goal: {user_instructions}
Target Category: {target_category}

Available Links:
{json.dumps([{"text": l["text"], "href": l["href"]} for l in links[:10]], indent=2)}

Task: Find the link that best matches "{target_category}"

If you find a matching link, respond with:
{{
    "action": "click",
    "text": "exact link text from the list",
    "reason": "why this link matches"
}}

If no matching link is found, respond with:
{{
    "action": "extract",
    "reason": "no matching link found"
}}

Your response (JSON only):"""

        try:
            messages = [
                {"role": "system", "content": "You are a web navigation assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_service.generate(
                prompt=prompt,
                messages=messages,
                model_id=model_id,
                temperature=0.1,
                max_tokens=300
            )

            response_text = response.get('content', '').strip()

            if not response_text:
                raise ValueError("Empty response from LLM")

            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            action = json.loads(response_text)

            logger.info(f"   💡 AI decision: {action.get('reason', 'No reason provided')}")

            return action

        except Exception as e:
            logger.warning(f"⚠️  Failed to select link: {e}")
            return {"action": "extract"}

    async def _extract_data_with_ai(
        self,
        page_html: str,
        user_instructions: str,
        extraction_target: str,
        llm_provider: str,
        model_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract structured data from HTML using AI
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_html, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Get cleaned text (limit size)
        text_content = soup.get_text(separator='\n', strip=True)
        text_content = text_content[:15000]  # Limit to 15k chars

        prompt = f"""Extract structured data from this web page content.

User Request: {user_instructions}
Extraction Target: {extraction_target}

Page Content:
{text_content}

Task: Extract ALL {extraction_target} from the page with their details.

Respond with a JSON array of objects. Each object should have relevant fields like:
- title/name
- price
- availability/stock
- any other relevant information

Example response:
[
    {{"title": "Book Title 1", "price": "$19.99", "availability": "In stock"}},
    {{"title": "Book Title 2", "price": "$24.99", "availability": "Out of stock"}}
]

Your response (JSON array only):"""

        try:
            messages = [
                {"role": "system", "content": "You are a data extraction assistant. Extract structured data from web pages and respond with valid JSON arrays."},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_service.generate(
                prompt=prompt,
                messages=messages,
                model_id=model_id,
                temperature=0.1,
                max_tokens=4000
            )

            response_text = response.get('content', '').strip()

            if not response_text:
                raise ValueError("Empty response from LLM")

            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)

            if not isinstance(data, list):
                logger.warning("⚠️  AI returned non-list data, wrapping in list")
                data = [data]

            return data

        except Exception as e:
            logger.error(f"❌ Failed to extract data with AI: {e}")
            return []
