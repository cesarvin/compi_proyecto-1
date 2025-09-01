from antlr4.error.ErrorListener import ErrorListener

class SyntaxErrorHandler(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []   # lista de dicts o strings

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = getattr(offendingSymbol, "text", None)
        self.errors.append({
            "line": line,
            "column": column,
            "message": msg,
            "offending": text
        })

    @property
    def has_errors(self):
        return len(self.errors) > 0

class ErrorHandler:
    def __init__(self):
        self.errors = []

    def add_error(self, message: str, line: int, column: int):
        error_details = {
            "message": message,
            "line": line,
            "column": column
        }
        self.errors.append(error_details)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report_errors(self):
        if not self.has_errors():
            print("No hay errores.")
            return
        
        for error in self.errors:
            print(f"[Línea {error['line']}:{error['column']}] -> Error: {error['message']}")

    def to_dict(self):
        return self.errors