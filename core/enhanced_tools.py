from typing import Dict, Any, List, Optional
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)


class CalculatorTools:
    """Advanced calculator tools for financial analysis"""
    
    def compound_interest(self, principal: float, rate: float, time: float, frequency: int = 12) -> Dict[str, float]:
        """Calculate compound interest"""
        try:
            rate_decimal = rate / 100
            amount = principal * (1 + rate_decimal / frequency) ** (frequency * time)
            interest_earned = amount - principal
            
            return {
                "principal": principal,
                "final_amount": amount,
                "interest_earned": interest_earned,
                "total_return": (interest_earned / principal) * 100
            }
        except Exception as e:
            logger.error(f"Error calculating compound interest: {e}")
            return {"error": str(e)}
    
    def investment_portfolio_analysis(self, investments: List[Dict]) -> Dict[str, Any]:
        """Analyze investment portfolio"""
        try:
            total_value = sum(inv.get('value', 0) for inv in investments)
            total_invested = sum(inv.get('invested', 0) for inv in investments)
            
            if total_invested == 0:
                return {"error": "Nenhum investimento encontrado"}
            
            total_return = total_value - total_invested
            total_return_percentage = (total_return / total_invested) * 100
            
            # Calculate allocation
            allocation = {}
            for inv in investments:
                category = inv.get('category', 'Outros')
                value = inv.get('value', 0)
                allocation[category] = allocation.get(category, 0) + value
            
            # Calculate percentage allocation
            percentage_allocation = {}
            for category, value in allocation.items():
                percentage_allocation[category] = (value / total_value) * 100
            
            return {
                "total_value": total_value,
                "total_invested": total_invested,
                "total_return": total_return,
                "total_return_percentage": total_return_percentage,
                "allocation": allocation,
                "percentage_allocation": percentage_allocation,
                "summary": f"Portfolio: R$ {total_value:.2f}, Retorno: {total_return_percentage:.2f}%"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {"error": str(e)}
    
    def retirement_planning(self, current_age: int, retirement_age: int, current_savings: float, 
                          monthly_contribution: float, expected_return: float) -> Dict[str, Any]:
        """Calculate retirement planning"""
        try:
            years_to_retirement = retirement_age - current_age
            months_to_retirement = years_to_retirement * 12
            
            # Calculate future value
            monthly_rate = expected_return / 100 / 12
            future_value = current_savings * (1 + expected_return / 100) ** years_to_retirement
            
            if monthly_rate > 0:
                future_value += monthly_contribution * ((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate
            
            return {
                "years_to_retirement": years_to_retirement,
                "future_value": future_value,
                "total_contributions": monthly_contribution * months_to_retirement,
                "interest_earned": future_value - current_savings - (monthly_contribution * months_to_retirement),
                "monthly_contribution_needed": self._calculate_required_contribution(
                    current_savings, 0, years_to_retirement, expected_return, 1000000  # Target 1M
                )
            }
        except Exception as e:
            logger.error(f"Error calculating retirement planning: {e}")
            return {"error": str(e)}
    
    def _calculate_required_contribution(self, current_savings: float, target_amount: float, 
                                       years: int, rate: float, target: float) -> float:
        """Calculate required monthly contribution to reach target"""
        try:
            future_value_current = current_savings * (1 + rate / 100) ** years
            needed_from_contributions = target - future_value_current
            
            if needed_from_contributions <= 0:
                return 0
            
            monthly_rate = rate / 100 / 12
            months = years * 12
            
            if monthly_rate > 0:
                required_monthly = needed_from_contributions * monthly_rate / ((1 + monthly_rate) ** months - 1)
            else:
                required_monthly = needed_from_contributions / months
            
            return required_monthly
        except Exception as e:
            logger.error(f"Error calculating required contribution: {e}")
            return 0


class ChartTools:
    """Tools for generating charts and visualizations"""
    
    def generate_portfolio_chart_data(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Generate data for portfolio allocation chart"""
        try:
            allocation = portfolio_data.get('percentage_allocation', {})
            
            chart_data = {
                "type": "pie",
                "labels": list(allocation.keys()),
                "data": list(allocation.values()),
                "colors": [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
                    "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
                ]
            }
            
            return chart_data
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return {"error": str(e)}
    
    def generate_expense_trend_data(self, expenses_data: List[Dict]) -> Dict[str, Any]:
        """Generate data for expense trend chart"""
        try:
            # Group by month
            monthly_expenses = {}
            
            for expense in expenses_data:
                date_str = expense.get('date', '')
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        month_key = date.strftime('%Y-%m')
                        amount = expense.get('amount', 0)
                        monthly_expenses[month_key] = monthly_expenses.get(month_key, 0) + amount
                    except:
                        continue
            
            # Sort by date
            sorted_months = sorted(monthly_expenses.keys())
            
            chart_data = {
                "type": "line",
                "labels": sorted_months,
                "data": [monthly_expenses[month] for month in sorted_months],
                "title": "Gastos Mensais",
                "yAxisLabel": "Valor (R$)"
            }
            
            return chart_data
        except Exception as e:
            logger.error(f"Error generating trend data: {e}")
            return {"error": str(e)}


# Tool registry for easy access - ONLY REAL TOOLS
ENHANCED_TOOLS = {
    "CalculatorTools": CalculatorTools,
    "ChartTools": ChartTools
}
