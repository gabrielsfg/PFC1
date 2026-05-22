import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from src.persona_identifier import PersonaIdentifier
from src.file_monitor import FileMonitor


def setup_environment():
    """Configura o ambiente e verifica variáveis necessárias"""
    load_dotenv()
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Erro: ANTHROPIC_API_KEY não encontrada!")
        print("Configure o arquivo .env com sua chave da Anthropic")
        print("Copie .env.example para .env e adicione sua chave")
        sys.exit(1)
    
    print("Ambiente configurado")


def process_single_file(file_path: str, output_dir: str):
    """Processa um único arquivo de transcrição"""
    file = Path(file_path)
    
    if not file.exists():
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    if not file.suffix == '.txt':
        print(f"Formato inválido. Use arquivos .txt")
        sys.exit(1)
    
    identifier = PersonaIdentifier(output_dir)
    result = identifier.process_transcription(file)
    
    if result:
        print("\nProcessamento concluído com sucesso!")
    else:
        print("\nFalha no processamento")
        sys.exit(1)


def process_directory(input_dir: str, output_dir: str):
    """Processa todos os arquivos de um diretório"""
    identifier = PersonaIdentifier(output_dir)
    results = identifier.process_directory(input_dir)
    
    if results:
        print(f"\n{len(results)} arquivo(s) processado(s) com sucesso!")
    else:
        print("\nNenhum arquivo processado")


def start_monitor(input_dir: str, output_dir: str, processed_dir: str, check_interval: int):
    """Inicia o monitor de arquivos"""
    monitor = FileMonitor(
        input_dir=input_dir,
        output_dir=output_dir,
        processed_dir=processed_dir,
        check_interval=check_interval
    )
    
    monitor.start()


def main():
    parser = argparse.ArgumentParser(
        description="Agente de Identificação de Personas - Processa transcrições e identifica personas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  Monitorar diretório (modo recomendado):
    python main.py --monitor
  
  Processar um único arquivo:
    python main.py --file ../agente-transcricao/data/output/transcricao.txt
  
  Processar diretório completo:
    python main.py --dir ../agente-transcricao/data/output
  
  Monitorar com intervalo customizado:
    python main.py --monitor --check-interval 10
        """
    )
    
    # Modos de operação
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--file',
        type=str,
        help='Processa um único arquivo de transcrição'
    )
    mode_group.add_argument(
        '--dir',
        type=str,
        help='Processa todos os arquivos .txt de um diretório'
    )
    mode_group.add_argument(
        '--monitor',
        action='store_true',
        help='Monitora diretório e processa novos arquivos automaticamente'
    )
    
    # Configurações
    parser.add_argument(
        '--input-dir',
        type=str,
        default=os.getenv('INPUT_DIR', '../agente-transcricao/data/output'),
        help='Diretório de entrada (padrão: ../agente-transcricao/data/output)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=os.getenv('OUTPUT_DIR', './data/output'),
        help='Diretório de saída (padrão: ./data/output)'
    )
    parser.add_argument(
        '--processed-dir',
        type=str,
        default=os.getenv('PROCESSED_DIR', './data/processed'),
        help='Diretório para controle de arquivos processados (padrão: ./data/processed)'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=int(os.getenv('CHECK_INTERVAL', '5')),
        help='Intervalo de verificação em segundos para modo monitor (padrão: 5)'
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_environment()
    
    # Executa o modo selecionado
    try:
        if args.file:
            process_single_file(args.file, args.output_dir)
        
        elif args.dir:
            process_directory(args.dir, args.output_dir)
        
        elif args.monitor:
            start_monitor(
                input_dir=args.input_dir,
                output_dir=args.output_dir,
                processed_dir=args.processed_dir,
                check_interval=args.check_interval
            )
    
    except KeyboardInterrupt:
        print("\n\nEncerrando...")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()