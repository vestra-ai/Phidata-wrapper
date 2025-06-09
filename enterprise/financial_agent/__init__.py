import os

from flask import Blueprint, request, jsonify

stock_bp = Blueprint('stock', __name__)

import concurrent.futures

@stock_bp.route('/stock-report', methods=['GET'])
def stock_report():
    from enterprise.financial_agent.tools.helper_fns.allFns import (
        get_fmp_detail, get_company_overview, market_indicies_data, analyst_stock_forecast,
        fear_and_greed, cot_report, put_call_ratios, analyze_stock_sentiment, piotroski_score,
        pe_ratios, debt_equity_ratio
    )
    from enterprise.financial_agent.tools.helper_fns.fair_value import determine_fair_value
    from enterprise.financial_agent.tools.helper_fns.buffet import compute_financial_health
    from enterprise.financial_agent.tools.helper_fns.new_fns import ( 
        competitor_analysis, product_wise_revenue_breakdown, ai_risk_analysis, ai_overview_json
    )
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "ticker_symbol_required"}), 400
    ticker = ticker.upper()

    results = {}
    errors = {}
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_map = {
                "fmp_data": executor.submit(get_fmp_detail, ticker),
                "market_indices": executor.submit(market_indicies_data),
                "analyst_forecast": executor.submit(analyst_stock_forecast, ticker),
                "fear_and_greed": executor.submit(fear_and_greed),
                "cot_report": executor.submit(cot_report),
                "put_call_ratio": executor.submit(put_call_ratios, ticker),
                "social_sentiment": executor.submit(analyze_stock_sentiment, ticker),
                "competitor_data": executor.submit(competitor_analysis, ticker),
                "revenue_segmentation": executor.submit(product_wise_revenue_breakdown, ticker),
                "piotroski_score": executor.submit(piotroski_score, ticker)
            }
            # Wait for fmp_data to finish (needed for dependent calls)
            fmp_data = future_map["fmp_data"].result()
            if not fmp_data or not fmp_data.get("company_profile"):
                return jsonify({"error": "company_profile_not_found"}), 404
            company_profile = fmp_data.get("company_profile")
            price_data = fmp_data.get("price_data", {})
            financial_metrics = fmp_data.get("financial_metrics", {})
            income_statement = fmp_data.get("income_statement", {})
            balance_sheet = fmp_data.get("balance_sheet", {})
            cash_flow = fmp_data.get("cash_flow", {})

            # Now dependent calls
            fair_value_future = executor.submit(determine_fair_value, company_profile[0], income_statement, balance_sheet, financial_metrics)
            buffet_future = executor.submit(
                compute_financial_health,
                {"income_statement": income_statement, "balance_sheet": balance_sheet, "cash_flow_statement": cash_flow}
            )
            sector = company_profile[0].get("sector", None)
            pe_ratios_future = executor.submit(pe_ratios, ticker, sector)
            debt_equity_ratio_future = executor.submit(debt_equity_ratio, financial_metrics, company_profile[0])

            # Gather all results with error handling
            def safe_result(future, key):
                try:
                    return future.result()
                except Exception as e:
                    errors[key] = str(e)
                    return None

            results["market_indices"] = safe_result(future_map["market_indices"], "market_indices")
            analyst_forecast = safe_result(future_map["analyst_forecast"], "analyst_forecast") or {}
            results["fear_and_greed"] = safe_result(future_map["fear_and_greed"], "fear_and_greed")
            results["cot_report"] = safe_result(future_map["cot_report"], "cot_report")
            results["put_call_ratio"] = safe_result(future_map["put_call_ratio"], "put_call_ratio")
            results["social_sentiment"] = safe_result(future_map["social_sentiment"], "social_sentiment")
            results["competitor_data"] = safe_result(future_map["competitor_data"], "competitor_data")
            results["revenue_segmentation"] = safe_result(future_map["revenue_segmentation"], "revenue_segmentation")
            results["piotroski_score"] = safe_result(future_map["piotroski_score"], "piotroski_score")
            results["fair_value"] = safe_result(fair_value_future, "fair_value")
            results["buffet"] = safe_result(buffet_future, "buffet")
            results["pe_ratios_val"] = safe_result(pe_ratios_future, "pe_ratios_val")
            results["debt_equity_ratio_val"] = safe_result(debt_equity_ratio_future, "debt_equity_ratio_val")

        analyst_ratings = analyst_forecast.get("analyst_ratings")
        forecast = {
            key: value
            for key, value in analyst_forecast.items()
            if key != "analyst_ratings"
        }

        report = {
            "slide_1": {
                "company_overview": get_company_overview(company_profile[0]),
                "market_indices": results["market_indices"],
                "analyst_ratings": analyst_ratings,
                "price_data": price_data.get("historical", [{}])[0] if price_data else None,
                "competitors": results["competitor_data"],
                "revenue_segmentation": results["revenue_segmentation"]
            },
            "slide_2": {
                "fair_value": results["fair_value"],
                "forecast": forecast
            },
            "slide_3": {
                "sentiment_analysis": {
                    "fear_and_greed_index": results["fear_and_greed"],
                    "commitments_of_traders_cot_report": results["cot_report"],
                    "put_call_ratio": results["put_call_ratio"],
                    "news_sentiment": results["social_sentiment"]
                }
            },
            "slide_4": {
                "investment_frameworks": {
                    "piotroski_score": results["piotroski_score"],
                    "buffet_table": results["buffet"]
                }
            },
            "slide_5": {
                "pe_ratios": results["pe_ratios_val"],
                "debt_equity_ratio": results["debt_equity_ratio_val"]
            }
        }

        # Run AI analysis in parallel with max_workers=2
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ai_executor:
            ai_risks_future = ai_executor.submit(ai_risk_analysis, report)
            ai_overview_future = ai_executor.submit(ai_overview_json, report)
            ai_risks = ai_risks_future.result()
            ai_overview = ai_overview_future.result()
        report["slide_6"] = {"ai_risks": ai_risks}
        report["slide_1"]["ai_overview"] = ai_overview
        response = {"status": "success", "data": report}
        if errors:
            response["errors"] = errors
            return jsonify(response), 200
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@stock_bp.route('/try', methods=['GET'])
def try_route():
    from enterprise.financial_agent.tools.helper_fns.allFns import piotroski_score
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker symbol is required"}), 400
    ticker = ticker.upper()
    
    try:
        result = piotroski_score(ticker)
        return jsonify({"piotroski_score": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500