import datetime

class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def _write(self, level: str, text: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, mode="a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {level}: {text}\n")

    def log_error(self, text: str) -> None:
        self._write("ERROR", text)

    def log_process(self, text: str) -> None:
        self._write("PROCESS", text)

    def log_success(self, text: str) -> None:
        self._write("SUCCESS", text)