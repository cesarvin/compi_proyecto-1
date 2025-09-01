from flask import Flask, request, jsonify
from flask_cors import CORS
from antlr4 import InputStream 
import recursos.config as config
from Driver import * 

app = Flask(__name__)
#CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])

@app.route('/')
def home():
    return "API compilador Compiscript funcionando!"

@app.route('/compilador', methods=['POST'])
def compilador():
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': "No hay código para analizar"}), 400

        codetext = data['code']
        
        input_stream = InputStream(codetext)
        compilado, result, errores, symbol_table, type_table = compilar(input_stream)

        response_data = {
            'compilado': compilado,
            'result': result,
            'errors': errores,
            'symbol_table': symbol_table,
            'type_table': type_table
        }

        return jsonify(response_data), 200
    except Exception as e:
        print(f"ERROR INTERNO INESPERADO: {e}")
        return jsonify({'error': 'Error interno del servidor', 'error:': str(e)}), 500



@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)