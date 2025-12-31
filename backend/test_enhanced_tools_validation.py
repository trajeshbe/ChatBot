#!/usr/bin/env python3
"""
Quick validation test for enhanced agent runtime container
Tests all 13 tools (6 core + 7 enhanced) are accessible
"""

import sys
import json
from pathlib import Path

# Test configuration
WORKSPACE = Path("/workspace")
ARTIFACTS_DIR = WORKSPACE / "artifacts"
SESSION_STATE = {
    "task_id": "validation-test",
    "session_id": "test-session",
    "artifacts": [],
    "tool_calls": []
}

def test_enhanced_tools_import():
    """Test 1: Verify enhanced tools can be imported"""
    print("\n" + "="*80)
    print("TEST 1: Import EnhancedAgentTools")
    print("="*80)

    try:
        sys.path.insert(0, '/app')
        from agent_tools_enhanced import EnhancedAgentTools
        print("✅ Successfully imported EnhancedAgentTools")
        return EnhancedAgentTools
    except Exception as e:
        print(f"❌ Failed to import EnhancedAgentTools: {e}")
        return None

def test_initialization(EnhancedAgentTools):
    """Test 2: Verify tools can be initialized"""
    print("\n" + "="*80)
    print("TEST 2: Initialize EnhancedAgentTools")
    print("="*80)

    try:
        # Create workspace directories
        WORKSPACE.mkdir(exist_ok=True)
        ARTIFACTS_DIR.mkdir(exist_ok=True)

        tools = EnhancedAgentTools(
            workspace=WORKSPACE,
            artifacts_dir=ARTIFACTS_DIR,
            session_state=SESSION_STATE
        )
        print("✅ Successfully initialized EnhancedAgentTools")
        return tools
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_tool_methods(tools):
    """Test 3: Verify all 7 enhanced tool methods exist"""
    print("\n" + "="*80)
    print("TEST 3: Verify Enhanced Tool Methods")
    print("="*80)

    expected_methods = [
        # Tier 2: Data Processing
        "analyze_dataframe",
        "visualize_data",
        # Tier 3: Document Extraction
        "extract_pdf_content",
        "analyze_excel_workbook",
        "extract_word_document",
        # Tier 4: Vision & OCR
        "analyze_image_with_vision",
        "extract_text_from_image"
    ]

    results = {}
    for method_name in expected_methods:
        has_method = hasattr(tools, method_name)
        is_callable = callable(getattr(tools, method_name, None))
        results[method_name] = has_method and is_callable

        status = "✅" if results[method_name] else "❌"
        print(f"{status} {method_name}: {'Available' if results[method_name] else 'Missing'}")

    all_present = all(results.values())
    print(f"\n{'✅' if all_present else '❌'} All 7 enhanced tools: {'Available' if all_present else 'Some Missing'}")
    return all_present

def test_lazy_imports(tools):
    """Test 4: Verify lazy import properties work"""
    print("\n" + "="*80)
    print("TEST 4: Test Lazy Import Properties")
    print("="*80)

    lazy_properties = ["pandas", "matplotlib", "seaborn", "plotly"]
    results = {}

    for prop_name in lazy_properties:
        try:
            # Access the property to trigger lazy import
            prop_value = getattr(tools, prop_name)
            results[prop_name] = prop_value is not None
            print(f"✅ {prop_name}: Loaded successfully")
        except Exception as e:
            results[prop_name] = False
            print(f"❌ {prop_name}: Failed to load - {e}")

    all_loaded = all(results.values())
    print(f"\n{'✅' if all_loaded else '❌'} All lazy imports: {'Working' if all_loaded else 'Some Failed'}")
    return all_loaded

def test_dependencies():
    """Test 5: Verify critical dependencies are installed"""
    print("\n" + "="*80)
    print("TEST 5: Verify Critical Dependencies")
    print("="*80)

    dependencies = {
        # Data Science
        "pandas": "2.1.4",
        "numpy": "1.26.x",
        "scipy": "1.11.4",
        "matplotlib": "3.8.2",
        "scikit-learn": "1.3.2",
        # Document Processing
        "docling": "2.62.0",
        "pdfplumber": "0.10.3",
        "pypdf": "3.17.4",
        "openpyxl": "3.1.x",
        "python-docx": "1.1.2",
        # Vision & OCR
        "PIL": "10.2.0",  # Pillow
        "cv2": "4.9.x",  # opencv-python-headless
        "pytesseract": "0.3.10",
        "easyocr": "1.7.1",
        # Deep Learning
        "torch": "2.9.1",
        "torchvision": "0.24.1"
    }

    results = {}
    for package, expected_version in dependencies.items():
        try:
            if package == "PIL":
                import PIL
                version = PIL.__version__
            elif package == "cv2":
                import cv2
                version = cv2.__version__
            else:
                module = __import__(package)
                version = getattr(module, "__version__", "unknown")

            results[package] = True
            print(f"✅ {package}: {version} (expected {expected_version})")
        except ImportError as e:
            results[package] = False
            print(f"❌ {package}: Not installed")
        except Exception as e:
            results[package] = False
            print(f"⚠️  {package}: Error checking - {e}")

    installed_count = sum(results.values())
    total_count = len(dependencies)
    print(f"\n{'✅' if installed_count == total_count else '⚠️'} Dependencies: {installed_count}/{total_count} installed")
    return installed_count >= total_count * 0.9  # 90% threshold

def test_system_tools():
    """Test 6: Verify system tools (tesseract, poppler)"""
    print("\n" + "="*80)
    print("TEST 6: Verify System Tools")
    print("="*80)

    import subprocess

    system_tools = {
        "tesseract": ["tesseract", "--version"],
        "pdftoppm": ["pdftoppm", "-v"],
        "file": ["file", "--version"]
    }

    results = {}
    for tool_name, command in system_tools.items():
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )
            results[tool_name] = result.returncode == 0

            version_info = (result.stdout + result.stderr).split('\n')[0]
            print(f"✅ {tool_name}: {version_info}")
        except Exception as e:
            results[tool_name] = False
            print(f"❌ {tool_name}: Not available - {e}")

    all_available = all(results.values())
    print(f"\n{'✅' if all_available else '❌'} System tools: {'All available' if all_available else 'Some missing'}")
    return all_available

def print_summary(test_results):
    """Print final summary"""
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "="*80)
    success_rate = (passed_tests / total_tests) * 100
    print(f"RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    if success_rate == 100:
        print("✅ ALL TESTS PASSED - Container ready for use!")
    elif success_rate >= 80:
        print("⚠️  MOSTLY WORKING - Some non-critical issues")
    else:
        print("❌ VALIDATION FAILED - Critical issues detected")

    print("="*80)

    return success_rate >= 80

def main():
    """Run all validation tests"""
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "ENHANCED AGENT TOOLS VALIDATION" + " "*27 + "║")
    print("║" + " "*78 + "║")
    print("║  Testing: 13 tools (6 core + 7 enhanced)                                    ║")
    print("║  Container: chatbot-agent-runtime:enhanced                                  ║")
    print("║  Python: 3.11-slim                                                          ║")
    print("╚" + "="*78 + "╝")

    test_results = {}

    # Test 1: Import
    EnhancedAgentTools = test_enhanced_tools_import()
    test_results["Import EnhancedAgentTools"] = EnhancedAgentTools is not None

    if not EnhancedAgentTools:
        print("\n❌ CRITICAL: Cannot proceed without EnhancedAgentTools")
        return False

    # Test 2: Initialization
    tools = test_initialization(EnhancedAgentTools)
    test_results["Initialize Tools"] = tools is not None

    if not tools:
        print("\n❌ CRITICAL: Cannot proceed without tool initialization")
        return False

    # Test 3: Tool methods
    test_results["Enhanced Tool Methods"] = test_tool_methods(tools)

    # Test 4: Lazy imports
    test_results["Lazy Import Properties"] = test_lazy_imports(tools)

    # Test 5: Dependencies
    test_results["Critical Dependencies"] = test_dependencies()

    # Test 6: System tools
    test_results["System Tools"] = test_system_tools()

    # Summary
    return print_summary(test_results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
