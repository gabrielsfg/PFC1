import time
from pathlib import Path
from typing import Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.diagrams_processor import DiagramsProcessor


class _JSONHandler(FileSystemEventHandler):
    def __init__(self, processor: DiagramsProcessor, processed_dir: Path):
        self.processor = processor
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.processed_files: Set[str] = self._load_processed()

    def _load_processed(self) -> Set[str]:
        record = self.processed_dir / "processed_files.txt"
        if record.exists():
            return set(record.read_text(encoding="utf-8").splitlines())
        return set()

    def _mark_processed(self, filename: str) -> None:
        self.processed_files.add(filename)
        record = self.processed_dir / "processed_files.txt"
        with open(record, "a", encoding="utf-8") as f:
            f.write(f"{filename}\n")

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return
        file_path = Path(event.src_path)
        if file_path.name in self.processed_files:
            return
        time.sleep(2)
        print(f"\nNovo arquivo detectado: {file_path.name}")
        try:
            result = self.processor.process(file_path)
            if result:
                self._mark_processed(file_path.name)
        except Exception as e:
            print(f"Erro ao processar {file_path.name}: {e}")


class FileMonitor:
    def __init__(self, input_dir: str, output_dir: str, processed_dir: str, check_interval: int = 5):
        self.input_dir = Path(input_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.check_interval = check_interval
        self.processor = DiagramsProcessor(output_dir)
        self.handler = _JSONHandler(self.processor, Path(processed_dir))
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.input_dir), recursive=False)

    def _process_existing(self) -> None:
        unprocessed = [
            f for f in self.input_dir.glob("*.json")
            if f.name not in self.handler.processed_files
        ]
        if unprocessed:
            print(f"\nProcessando {len(unprocessed)} arquivo(s) existente(s)...\n")
            for f in unprocessed:
                try:
                    result = self.processor.process(f)
                    if result:
                        self.handler._mark_processed(f.name)
                except Exception as e:
                    print(f"Erro: {e}")

    def start(self) -> None:
        print(f"\n{'='*60}")
        print("AGENTE DIAGRAMAS — Diagrama de Domínio + Documento Final")
        print(f"{'='*60}")
        print(f"Monitorando: {self.input_dir}")
        print(f"Modelo: {self.processor.generator.llm.model}")
        print(f"{'='*60}\n")
        self._process_existing()
        self.observer.start()
        print("Monitoramento ativo. Pressione Ctrl+C para parar.\n")
        try:
            while True:
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        print("\nEncerrando monitoramento...")
        self.observer.stop()
        self.observer.join()
        print("Monitor encerrado.\n")
