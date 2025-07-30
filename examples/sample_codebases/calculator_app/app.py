"""
Main application file for the Calculator Web App.
This is a simple Flask-based calculator with multiple components for testing AutoGraph.
"""

from flask import Flask, request, jsonify, render_template
from calculator.services.calculator_service import CalculatorService
from calculator.services.history_service import HistoryService
from calculator.models.calculation import Calculation
from calculator.utils.validators import validate_input
from calculator.utils.formatters import format_result
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize services
calculator_service = CalculatorService()
history_service = HistoryService()


@app.route('/')
def index():
    """Main page of the calculator."""
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """API endpoint for calculations."""
    try:
        data = request.get_json()
        
        # Validate input
        if not validate_input(data):
            return jsonify({'error': 'Invalid input'}), 400
        
        # Extract calculation parameters
        operation = data.get('operation')
        operands = data.get('operands', [])
        
        # Perform calculation
        result = calculator_service.calculate(operation, operands)
        
        # Format result
        formatted_result = format_result(result)
        
        # Save to history
        calculation = Calculation(operation, operands, result)
        history_service.add_calculation(calculation)
        
        return jsonify({
            'result': formatted_result,
            'calculation_id': calculation.id
        })
        
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return jsonify({'error': 'Calculation failed'}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get calculation history."""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = history_service.get_history(limit)
        
        return jsonify({
            'history': [calc.to_dict() for calc in history]
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve history'}), 500


@app.route('/api/history/<calculation_id>', methods=['GET'])
def get_calculation(calculation_id):
    """Get a specific calculation by ID."""
    try:
        calculation = history_service.get_calculation(calculation_id)
        
        if not calculation:
            return jsonify({'error': 'Calculation not found'}), 404
        
        return jsonify(calculation.to_dict())
        
    except Exception as e:
        logger.error(f"Calculation retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve calculation'}), 500


@app.route('/api/clear-history', methods=['DELETE'])
def clear_history():
    """Clear calculation history."""
    try:
        history_service.clear_history()
        return jsonify({'message': 'History cleared successfully'})
        
    except Exception as e:
        logger.error(f"History clearing error: {e}")
        return jsonify({'error': 'Failed to clear history'}), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'services': {
            'calculator': calculator_service.is_healthy(),
            'history': history_service.is_healthy()
        }
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 