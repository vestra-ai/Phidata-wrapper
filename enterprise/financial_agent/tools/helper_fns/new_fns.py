from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine
from enterprise.financial_agent.tools.helper_fns.allFns import get_fmp_detail

def competitor_analysis(ticker, fmp_data=None):
    """
    Generate a competitor analysis for a given stock using GPT and FMP data.
    - Finds 3 competitors (tickers) using GPT.
    - Fetches their price, market cap, revenue, and net income.
    - Compares these with the target stock.
    - Returns a list of dicts with the comparison data.
    If an error occurs, returns a string error message.
    """
    try:
        gpt_engine = GPTAnalysisEngine()
        # Step 1: Get company profile if not provided
        if not fmp_data:
            fmp_data = get_fmp_detail(ticker)
            
        company_profile = fmp_data.get("company_profile", [{}])[0]
        sector = company_profile.get("sector", "")
        industry = company_profile.get("industry", "")

        # Step 2: Ask GPT for 3 competitor tickers in the same sector/industry
        prompt = (
            f"List 3 major public company competitors (Same country-listed if possible) for {ticker} "
            f"in the same sector ('{sector}') or industry ('{industry}'). "
            f"For each, provide only the stock ticker symbol. Respond in the json format {{'competitors': [ticker1, ticker2, ticker3]}}."
        )
        competitors_resp = gpt_engine.generate_analysis(prompt=prompt, data={"company_profile": company_profile}, output_format="json")
        print(f"Competitors response")
        print(competitors_resp)
        import json
        try:
            competitors_json = json.loads(competitors_resp)
            competitor_tickers = competitors_json.get("competitors", [])
            if not isinstance(competitor_tickers, list):
                competitor_tickers = []
        except Exception:
            competitor_tickers = []

        # Step 3: Fetch standard data for each competitor
        def extract_standard_data(fmp_data):
            cp = fmp_data.get("company_profile", [{}])[0]
            income = fmp_data.get("income_statement", {})
            return {
                "ticker": cp.get("symbol"),
                "name": cp.get("companyName"),
                "price": cp.get("price"),
                "market_cap": cp.get("mktCap"),
                "revenue": income.get("revenue"),
                "net_income": income.get("netIncome"),
                "eps": income.get("eps")
            }

        # Get data for the main stock
        main_data = extract_standard_data(fmp_data)
        competitors_data = []
        for comp_ticker in competitor_tickers:
            try:
                comp_fmp = get_fmp_detail(comp_ticker)
                competitors_data.append(extract_standard_data(comp_fmp))
            except Exception:
                continue
        result = [main_data]
        result.extend(competitors_data)
        return result
    except Exception as e:
        return f"Error in competitor_analysis: {str(e)}"

def product_wise_revenue_breakdown(ticker, fmp_data=None):
    """
    Returns a dict with product/service names as keys and their % revenue share as values (max 5-6 items).
    Tries FMP API first, falls back to GPT if not available.
    """
    from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine
    from enterprise.financial_agent.tools.helper_fns.allFns import get_fmp_detail
    fmp = None
    try:
        from enterprise.financial_agent.tools.FinancialApi import FinancialModelingPrepAPI
        fmp = FinancialModelingPrepAPI()
    except Exception:
        pass

    # Try FMP API for revenue segmentation
    revenue_data = None
    if fmp:
        try:
            revenue_data = fmp.get_revenue_product_segmentation(ticker)
            # If API returns error or empty, treat as unavailable
            if isinstance(revenue_data, dict) and revenue_data.get("Error Message"):
                revenue_data = None
            elif isinstance(revenue_data, list) and revenue_data and "Error Message" in revenue_data[0]:
                revenue_data = None
        except Exception:
            revenue_data = None

    # If valid data found, format as requested
    if revenue_data and isinstance(revenue_data, list) and len(revenue_data) > 0:
        # Assume structure: [{"product": ..., "revenuePercentage": ...}, ...]
        breakdown = {}
        for item in revenue_data[:6]:
            product = item.get("product") or item.get("segment") or item.get("name")
            percent = item.get("revenuePercentage") or item.get("percentage") or item.get("revenue_percent")
            if product and percent:
                breakdown[product] = percent
        if breakdown:
            return breakdown

    # Fallback: Use GPT to generate breakdown
    gpt_engine = GPTAnalysisEngine(default_model="gpt-4.1")
    if fmp_data is None:
        fmp_data = get_fmp_detail(ticker)
    prompt = (
        f"Based on all available company data and public sources, provide a product/service-wise revenue breakdown "
        f"for the last fiscal year for {ticker}. List the top 5-6 products or services and their estimated percentage "
        f"share of total revenue. Respond as a JSON object with product/service names as keys and their % revenue share as values."
    )
    gpt_resp = gpt_engine.generate_analysis(prompt=prompt, data=fmp_data, output_format="json")
    import json
    try:
        breakdown = json.loads(gpt_resp)
        if isinstance(breakdown, dict):
            # Limit to 6 items
            return dict(list(breakdown.items())[:6])
    except Exception:
        pass
    return {}

def ai_risk_analysis(report):
    prompt = (
        """Given the following structured stock report, generate 3-5 bullet points for each of these risk categories, from the perspective of an investor in this company.\n"""
        "1. Key External Risks\n"
        "2. Customer, Supplier, & Geographic Risks\n"
        "3. Legal, Environmental, and Reputational Risks\n"
        "4. Financial Market Risks\n"
        "5. Operational Risks\n"
        "For each subtopic, use company-specific data and context. Format as a json output with keys: 'key_external_risks', 'customer_supplier_geographic_risks', 'legal_environmental_reputational_risks', 'financial_market_risks', 'operational_risks'. Each value should be a list of 3-5 concise bullet points.\n"
    )
    try:
        gpt_engine = GPTAnalysisEngine()
        ai_risks = gpt_engine.generate_analysis(prompt=prompt, model="gpt-4.1", data=report, output_format="json")
        import json
        return json.loads(ai_risks)
    except Exception as e:
        print(f"AI risk analysis error: {e}")
        return {}

def ai_overview_json(report):
    prompt = (
        """Given the following structured stock report, generate a JSON summary for an investor.\n"""
        "Include these sections (add more if relevant):\n"
        "- Market Conditions (with date if available)\n"
        "- Investment Strategy Options (with 2-3 actionable strategies)\n"
        "- Financial Health Check (Buffett Test, Piotroski Score, etc.)\n"
        "- Valuation & Analyst Ratings (Fair Value, Analyst Coverage)\n"
        "- Market Sentiment (Fear & Greed, Social, Put/Call, News, Buzzwords)\n"
        "- Official Risk Disclosures (SEC 10-K, etc.)\n"
        "For each section, use company-specific and market data from the report.\n"
        "For each section, return a JSON object with:\n"
        "- 'points': a list of 3-5 concise bullet points for the section\n"
        "- 'ai_insight': a concise summary/insight for the section\n"
        "Format the output as a JSON object with keys for each section, each containing 'points' and 'ai_insight'."
        )
    try:
        gpt_engine = GPTAnalysisEngine()
        ai_overview = gpt_engine.generate_analysis(prompt=prompt, model="gpt-4.1", data=report, output_format="json")
        import json
        return json.loads(ai_overview)
    except Exception as e:
        print(f"AI overview json error: {e}")
        return {}