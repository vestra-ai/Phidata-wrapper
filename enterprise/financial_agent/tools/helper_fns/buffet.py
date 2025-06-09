import json

def compute_financial_health(financial_data):
    """
    Computes financial health metrics using available data and compares against industry benchmarks.

    Args:
        financial_data (dict): Contains income statement, balance sheet, and cash flow statement.
        industry_benchmarks (dict): Standard industry values for comparison.

    Returns:
        dict: Computed metrics and pass/fail status.
    """

    ### 🏛 Extract Required Data ###
    income_stmt = financial_data.get("income_statement", {})
    balance_sheet = financial_data.get("balance_sheet", {})
    cash_flow_stmt = financial_data.get("cash_flow_statement", {})

    # Extract values safely with defaults
    revenue = income_stmt.get("revenue", 0)
    gross_profit = income_stmt.get("grossProfit", 0)
    operating_income = income_stmt.get("operatingIncome", 0)
    net_income = income_stmt.get("netIncome", 0)
    sga_expense = income_stmt.get("sellingGeneralAndAdministrativeExpenses", 0)
    depreciation = income_stmt.get("depreciationAndAmortization", 0)
    interest_expense = income_stmt.get("interestExpense", 0)

    total_liabilities = balance_sheet.get("totalLiabilities", 0)
    shareholders_equity = balance_sheet.get("totalStockholdersEquity", 0)
    retained_earnings = balance_sheet.get("retainedEarnings", 0)

    # industry_benchmarks = {
    # "Gross Margin": [0.40, 0.50],  # Example range for gross margin
    # "SG&A Margin": [0.25, 0.35],  # SG&A expense as % of gross profit
    # "Operating Margin": [0.10, 0.20],  # Profitability benchmark
    # "Depreciation Margin": [0.03, 0.08],  # Asset usage efficiency
    # "Interest Expense Margin": [0.01, 0.05],  # Debt cost control
    # "Net Margin": [0.10, 0.20],  # Profitability benchmark
    # "Debt-to-Equity Ratio": [0.8, 1.5],  # Leverage control
    # }
    industry_benchmarks = {
        "Gross Margin": [0.40, 0.9],  # Pass if ≥ 40%
        "SG&A Margin": [0, 0.30],  # Pass if ≤ 30%
        "R&D Margin": [0, 0.30],  # Pass if ≤ 30%
        "Depreciation Margin": [0, 0.10],  # Pass if ≤ 10%
        "Interest Expense Margin": [0, 0.15],  # Pass if ≤ 15%
        "Net Margin": [0.20,0.8],  # Pass if ≥ 20%
        "Debt-to-Equity Ratio": [0, 0.8],  # Pass if ≤ 0.8
    }


    ### 🔢 Compute Financial Ratios ###
    computed_metrics = {}

    # Gross Margin
    computed_metrics["Gross Margin"] = gross_profit / revenue if revenue else 0

    # SG&A Margin
    computed_metrics["SG&A Margin"] = sga_expense / gross_profit if gross_profit else 0

    # Operating Margin
    computed_metrics["Operating Margin"] = operating_income / revenue if revenue else 0

    # Depreciation Margin
    computed_metrics["Depreciation Margin"] = depreciation / gross_profit if gross_profit else 0

    # Interest Expense Margin
    computed_metrics["Interest Expense Margin"] = interest_expense / operating_income if operating_income else 0

    # Net Margin
    computed_metrics["Net Margin"] = net_income / revenue if revenue else 0

    # Debt-to-Equity Ratio
    computed_metrics["Debt-to-Equity Ratio"] = total_liabilities / shareholders_equity if shareholders_equity else 0

    # Retained Earnings Growth
    computed_metrics["Retained Earnings Growth"] = "Positive" if retained_earnings > 0 else "Negative"

    ### 📊 Compare with Industry Benchmarks ###
    comparison_results = {}

    for metric, value in computed_metrics.items():
        if isinstance(value, str):
            comparison_results[metric] = {"value": value, "benchmark": "N/A", "status": "N/A"}
            continue
        if metric in industry_benchmarks:
            benchmark = industry_benchmarks[metric]
            status = "Pass" if benchmark[0] <= value <= benchmark[1] else "Fail"
            comparison_results[metric] = {"value": f"{value:.2%}", "benchmark": benchmark, "status": status}
        else:
            comparison_results[metric] = {"value": f"{value:.2%}", "benchmark": "N/A", "status": "No Benchmark"}

    return {
        "computed_metrics": computed_metrics,
        "comparison_results": comparison_results
    }

# # Example Usage
# financial_data_example = {
#     "income_statement": [{
#         "revenue": 391035000000,
#         "grossProfit": 180683000000,
#         "operatingIncome": 123216000000,
#         "netIncome": 93736000000,
#         "sellingGeneralAndAdministrativeExpenses": 26097000000,
#         "depreciationAndAmortization": 11445000000,
#         "interestExpense": 8000000000
#     }],
#     "balance_sheet": [{
#         "totalLiabilities": 308030000000,
#         "totalStockholdersEquity": 56950000000,
#         "retainedEarnings": -19154000000
#     }]
# }



# result = compute_financial_health(financial_data_example, industry_benchmarks_example)
# print(json.dumps(result, indent=4))
