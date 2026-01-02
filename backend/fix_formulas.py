#!/usr/bin/env python3
"""
Fix formula syntax errors in Grant Thornton Excel files.

Fixes all formulas missing closing parentheses.
"""

import openpyxl
from pathlib import Path

def fix_formulas_in_sheet(ws, formula_col='D'):
    """Fix formulas in a worksheet by adding missing closing parentheses."""
    fixes_made = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):  # Skip header
        cell = row[ord(formula_col) - ord('A')]  # Get formula column

        if cell.value and isinstance(cell.value, str):
            formula = cell.value.strip()

            # Count parentheses
            open_parens = formula.count('(')
            close_parens = formula.count(')')

            if open_parens > close_parens:
                # Add missing closing parentheses
                missing = open_parens - close_parens
                fixed_formula = formula + ')' * missing

                fixes_made.append({
                    'row': row_idx,
                    'original': formula,
                    'fixed': fixed_formula,
                    'missing_parens': missing
                })

                cell.value = fixed_formula
                print(f"  Row {row_idx}: Added {missing} closing parenthesis")
                print(f"    BEFORE: {formula}")
                print(f"    AFTER:  {fixed_formula}")
                print()

    return fixes_made


def main():
    base_path = Path("app/services/grant_thornton/artifacts")

    # File 1: Sub-calculations
    print("=" * 80)
    print("FIXING: calculation_formula.xlsx (Sub-Calculations)")
    print("=" * 80)

    calc_file = base_path / "calculation_formula.xlsx"
    wb1 = openpyxl.load_workbook(calc_file)
    ws1 = wb1["Additional Formulas"]

    fixes1 = fix_formulas_in_sheet(ws1, formula_col='D')

    if fixes1:
        wb1.save(calc_file)
        print(f"✅ Fixed {len(fixes1)} formulas in calculation_formula.xlsx\n")
    else:
        print("✅ No fixes needed in calculation_formula.xlsx\n")

    # File 2: Financial Ratios
    print("=" * 80)
    print("FIXING: final_calculation_formula.xlsx (Financial Ratios)")
    print("=" * 80)

    ratio_file = base_path / "final_calculation_formula.xlsx"
    wb2 = openpyxl.load_workbook(ratio_file)
    ws2 = wb2["Ratios"]

    fixes2 = fix_formulas_in_sheet(ws2, formula_col='D')

    if fixes2:
        wb2.save(ratio_file)
        print(f"✅ Fixed {len(fixes2)} formulas in final_calculation_formula.xlsx\n")
    else:
        print("✅ No fixes needed in final_calculation_formula.xlsx\n")

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Sub-Calculations:  {len(fixes1)} formulas fixed")
    print(f"Financial Ratios:  {len(fixes2)} formulas fixed")
    print(f"Total:             {len(fixes1) + len(fixes2)} formulas fixed")
    print()
    print("✅ All formulas fixed successfully!")
    print()
    print("Next steps:")
    print("1. Restart backend: docker-compose restart backend")
    print("2. Re-upload PDF to test calculations")


if __name__ == "__main__":
    main()
