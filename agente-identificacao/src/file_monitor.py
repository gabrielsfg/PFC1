import os
import time
from pathlib import Path
from typing import Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.persona_identifier import PersonaIdentifier


class TranscriptionHandler(FileSystemEventHandler):
    """Handler para processar novos arquivos de transcrição"""
    
    def __init__(self, persona_identifier: PersonaIdentifier, processed_dir: str):
        self.persona_identifier = persona_identifier
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_files: Set[str] = self._load_processed_files()
    
    def _load_processed_files(self) -> Set[str]:
        """Carrega lista de arquivos já processados"""
        processed_list_file = self.processed_dir / "processed_files.txt"
        
        if processed_list_file.exists():
            with open(processed_list_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        
        return set()
    
    def _mark_as_processed(self, filename: str):
        """Marca um arquivo como processado"""
        self.processed_files.add(filename)
        processed_list_file = self.processed_dir / "processed_files.txt"
        
        with open(processed_list_file, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
    
    def on_created(self, event):
        """Callback quando um novo arquivo é criado"""
        if event.is_directory:
            return
        
        # Processa apenas arquivos .txt
        if not event.src_path.endswith('.txt'):
            return
        
        file_path = Path(event.src_path)
        filename = file_path.name
        
        # Ignora se já foi processado
        if filename in self.processed_files:
            return
        
        # Aguarda o arquivo ser completamente escrito
        time.sleep(2)
        
        print(f"\n Novo arquivo detectado: {filename}")
        
        try:
            # Processa o arquivo
            result = self.persona_identifier.process_transcription(file_path)
            
            if result:
                self._mark_as_processed(filename)
                print(f"Arquivo {filename} processado com sucesso!")
            else:
                print(f"Falha ao processar {filename}")
                
        except Exception as e:
            print(f"Erro ao processar {filename}: {e}")


class FileMonitor:
    """Monitor que observa diretório de entrada por novos arquivos"""
    
    def __init__(
        self, 
        input_dir: str,
        output_dir: str,
        processed_dir: str,
        check_interval: int = 5
    ):
        self.input_dir = Path(input_dir)
        self.check_interval = check_interval
        
        # Cria diretórios se não existirem
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializa o identificador de personas
        self.persona_identifier = PersonaIdentifier(output_dir)
        
        # Inicializa o handler
        self.handler = TranscriptionHandler(
            self.persona_identifier,
            processed_dir
        )
        
        # Inicializa o observer
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.input_dir),
            recursive=False
        )
    
    def process_existing_files(self):
        """Processa arquivos existentes que ainda não foram processados"""
        txt_files = list(self.input_dir.glob("*.txt"))
        
        unprocessed = [
            f for f in txt_files 
            if f.name not in self.handler.processed_files
        ]
        
        if unprocessed:
            print(f"\nProcessando {len(unprocessed)} arquivo(s) existente(s)...\n")
            
            for txt_file in unprocessed:
                try:
                    result = self.persona_identifier.process_transcription(txt_file)
                    if result:
                        self.handler._mark_as_processed(txt_file.name)
                except Exception as e:
                    print(f"Erro ao processar {txt_file.name}: {e}")
    
    def start(self):
        """Inicia o monitoramento"""
        print(f"\n{'='*60}")
        print(f"AGENTE DE IDENTIFICAÇÃO DE PERSONAS")
        print(f"{'='*60}")
        print(f"Monitorando: {self.input_dir}")
        print(f"Modelo: {self.persona_identifier.openai_client.model}")
        print(f"Intervalo de verificação: {self.check_interval}s")
        print(f"{'='*60}\n")
        
        # Processa arquivos existentes primeiro
        self.process_existing_files()
        
        # Inicia o monitoramento
        self.observer.start()
        print("Monitoramento ativo. Pressione Ctrl+C para parar.\n")
        
        try:
            while True:
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Para o monitoramento"""
        print("\nEncerrando monitoramento...")
        self.observer.stop()
        self.observer.join()
        print("Monitor encerrado com sucesso!\n")