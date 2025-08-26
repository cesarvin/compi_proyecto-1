class ErrorHandler:
    def __init__(self):
        self._errors = []

    def add_error(self, message: str, line: int, column: int):
        error_details = {
            "message": message,
            "line": line,
            "column": column
        }
        self._errors.append(error_details)

    def has_errors(self) -> bool:
        return len(self._errors) > 0

    def report_errors(self):
        if not self.has_errors():
            print("Análisis completado sin errores")
            return
        
        for error in self._errors:
            print(f"[Línea {error['line']}:{error['column']}] -> Error: {error['message']}")