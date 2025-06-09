from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine
from enterprise.financial_agent.tools.FinancialApi import FinancialModelingPrepAPI

# fmp = FinancialModelingPrepAPI()
gpt_engine = GPTAnalysisEngine()

def determine_company_model(company_profile, income_statement, balance_sheet):
    # Extract relevant data
    company_name = company_profile.get("companyName", "Unknown")
    sector = company_profile.get("sector", "Unknown")
    industry = company_profile.get("industry", "Unknown")
    market_cap = company_profile.get("mktCap", 0)
    revenue = income_statement.get("revenue", 0)
    profit = income_statement.get("grossProfit", 0)
    assets = balance_sheet.get("totalAssets", 0)
    
    debt_to_equity = balance_sheet.get("debtEquityRatio", None)
    revenue_growth = income_statement.get("revenueGrowth", None)
    profit_margin = income_statement.get("netProfitMargin", None)
    return_on_assets = balance_sheet.get("returnOnAssets", None)
    return_on_equity = balance_sheet.get("returnOnEquity", None)

    # Validate if essential data is missing
    if not all([revenue, profit, assets, market_cap]):
        return "Unknown", "Insufficient financial data to classify the company."

    # Enhanced prompt for AI
    prompt = f"""
    You are a financial analyst classifying companies into one of the following categories: 
    - **Stable Company** (Low risk, consistent revenue, stable profits, large market cap)  
    - **Asset-Heavy Company** (Significant tangible assets, high capital expenditures, e.g., manufacturing, real estate)  
    - **Growth Company** (Rapid revenue growth, high reinvestment, lower profitability margins, e.g., tech startups)  
    - **Conglomerate** (Multiple diverse businesses across industries, e.g., Berkshire Hathaway)  
    - **Others** (Companies that do not fit into the above categories)  

    **Company Data for Classification:**  
    - **Name:** {company_name}  
    - **Sector:** {sector}  
    - **Industry:** {industry}  
    - **Revenue:** {revenue}  
    - **Profit:** {profit}  
    - **Total Assets:** {assets}  
    - **Market Cap:** {market_cap}  
    - **Debt-to-Equity Ratio:** {debt_to_equity}  
    - **Revenue Growth Rate:** {revenue_growth}  
    - **Profit Margin:** {profit_margin}  
    - **Return on Assets (ROA):** {return_on_assets}  
    - **Return on Equity (ROE):** {return_on_equity}  

    Classify this company into one of the categories and provide a **detailed explanation** justifying your classification.

    Give json output with two keys classification and reasoning
    """

    context_data = {"company_profile": company_profile}

    # Use GPT model for classification
    response = gpt_engine.generate_analysis(prompt=prompt, data=context_data, output_format="json")
    response = json.loads(response)
    # print(response)

    # Extract classification and reasoning
    classification = response.get("classification", "Others")
    reasoning = response.get("reasoning", "No reasoning provided.")
    print(classification)
    print("**********************")
    print(reasoning)
    return classification, reasoning


import json

def determine_fair_value(company_profile, income_statement, balance_sheet, financial_data):
    """
    Calculate the fair value of a company based on its classification and multiple valuation models.
    Generates insights comparing fair value to current stock price.
    """

    fair_value_estimates = {}
    final_fair_value = 0
    weightings = {}

    company_classification, classification_reasoning = determine_company_model(company_profile, income_statement, balance_sheet)
    current_price = company_profile.get("price", 0)

    def is_invalid(*args):
        return any(x is None or x == 0 for x in args)

    # Helper to get value or fallback to 0
    def get_val(d, key):
        v = d.get(key, 0)
        return 0 if v is None else v

    # Model selection and fair value calculation
    dcf_value = get_val(company_profile, "dcf")
    pe_ratio = get_val(financial_data, "peRatio")
    net_income_per_share = get_val(financial_data, "netIncomePerShare")
    pe_based_value = pe_ratio * net_income_per_share

    if company_classification == "Stable Company":
        if is_invalid(dcf_value, pe_ratio, net_income_per_share):
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}
        else:
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}

    elif company_classification == "Asset-Heavy Company":
        total_assets = get_val(financial_data, "totalAssets")
        total_liabilities = get_val(financial_data, "totalLiabilities")
        net_assets = total_assets - total_liabilities
        if is_invalid(total_assets, total_liabilities):
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}
        else:
            fair_value_estimates["Asset-Based"] = net_assets
            weightings = {"Asset-Based": 1.0}

    elif company_classification == "Growth Company":
        free_cash_flow_per_share = get_val(financial_data, "freeCashFlowPerShare")
        shares_outstanding = get_val(financial_data, "sharesOutstanding") or 1
        fcfe_value = free_cash_flow_per_share * shares_outstanding
        if is_invalid(free_cash_flow_per_share, shares_outstanding, pe_ratio, net_income_per_share):
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}
        else:
            fair_value_estimates["FCFE"] = fcfe_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"FCFE": 0.7, "PE-Based": 0.3}

    elif company_classification == "Conglomerate":
        if is_invalid(dcf_value, pe_ratio, net_income_per_share):
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}
        else:
            fair_value_estimates["DCF"] = dcf_value
            fair_value_estimates["PE-Based"] = pe_based_value
            weightings = {"DCF": 0.6, "PE-Based": 0.4}

    else:
        fair_value_estimates["DCF"] = dcf_value
        fair_value_estimates["PE-Based"] = pe_based_value
        weightings = {"DCF": 0.6, "PE-Based": 0.4}

    # Weighted average fair value
    valid = [(fair_value_estimates[k], w) for k, w in weightings.items() if fair_value_estimates.get(k, 0) > 0]
    if valid:
        final_fair_value = sum(v * w for v, w in valid) / sum(w for _, w in valid)
    else:
        final_fair_value = 0

    if final_fair_value == 0:
        return {
            "classification": None,
            "classification_reasoning": None,
            "fair_value_estimates": None,
            "final_fair_value": None,
            "current_price": None,
            "valuation_status": None,
            "valuation_diff": None,
            "insights": None
        }

    valuation_diff = ((final_fair_value - current_price) / current_price) * 100 if current_price else 0
    valuation_status = "Undervalued" if final_fair_value > current_price else "Overvalued"

    prompt = f"""
    Analyze whether the stock is justified at its current price based on its fair value estimate.

    - **Classification**: {company_classification}
    - **Fair Value Estimate**: ${final_fair_value:.2f}
    - **Current Stock Price**: ${current_price:.2f}
    - **Valuation Status**: {valuation_status} by {abs(valuation_diff):.2f}%

    Provide insights:
    - **Endorse (Support Case)**: One sentence explaining why the stock deserves its current valuation.
    - **Critique (Counter Case)**: One sentence explaining why the stock might be mispriced.
    """

    context_data = {
        "classification": company_classification,
        "final_fair_value": final_fair_value,
        "current_price": current_price,
        "valuation_status": valuation_status,
        "valuation_diff": valuation_diff
    }

    response = gpt_engine.generate_analysis(prompt=prompt, data=context_data)
    insights = response

    return {
        "classification": company_classification,
        "classification_reasoning": classification_reasoning,
        "fair_value_estimates": fair_value_estimates,
        "final_fair_value": final_fair_value,
        "current_price": current_price,
        "valuation_status": valuation_status,
        "valuation_diff": valuation_diff,
        "insights": insights
    }
