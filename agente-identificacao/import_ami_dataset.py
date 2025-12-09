import os
from pathlib import Path
from datasets import load_dataset
import json


def download_ami_dataset(output_dir: str = "./data/ami_dataset", num_samples: int = 10):
    """
    Baixa o dataset AMI e converte para arquivos .txt
    
    Args:
        output_dir: Diretório onde salvar as transcrições
        num_samples: Número de amostras para baixar (default: 10 para testes)
    """
    print("Baixando dataset AMI do Hugging Face...")
    print(f"Salvando em: {output_dir}\n")
    
    # Criar diretório de saída
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Carregar dataset
        print("Carregando dataset... (pode demorar na primeira vez)")
        dataset = load_dataset("knkarthick/AMI", split="train")
        
        print(f"Dataset carregado! Total de {len(dataset)} reuniões disponíveis\n")
        
        # Limitar número de amostras
        if num_samples and num_samples < len(dataset):
            dataset = dataset.select(range(num_samples))
            print(f"Processando {num_samples} amostras para teste\n")
        
        # Processar cada reunião
        metadata_list = []
        
        for idx, sample in enumerate(dataset):
            # O campo correto é 'dialogue', não 'transcript'
            meeting_id = sample.get('id', f'meeting_{idx}')
            dialogue = sample.get('dialogue', '')
            summary = sample.get('summary', '')
            
            if not dialogue:
                print(f"Pulando meeting_{meeting_id} - sem diálogo")
                continue
            
            # Nome do arquivo
            filename = f"meeting_{meeting_id}.txt"
            filepath = output_path / filename
            
            # Salvar transcrição em .txt
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(dialogue)
            
            # Coletar metadados
            metadata = {
                "meeting_id": meeting_id,
                "filename": filename,
                "dialogue_length": len(dialogue),
                "num_words": len(dialogue.split()),
                "summary": summary if summary else "N/A"
            }
            
            metadata_list.append(metadata)
            
            print(f"Salvo: {filename} ({metadata['num_words']} palavras)")
        
        # Salvar metadados em JSON
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Importação concluída!")
        print(f"{'='*60}")
        print(f"Arquivos salvos em: {output_path}")
        print(f"Total de transcrições: {len(metadata_list)}")
        print(f"Metadados salvos em: {metadata_file}")
        print(f"{'='*60}\n")
        
        return metadata_list
        
    except Exception as e:
        print(f"Erro ao baixar dataset: {e}")
        print("\nDica: Verifique sua conexão com a internet")
        return None


def copy_to_transcription_agent(
    source_dir: str = "./data/ami_dataset",
    dest_dir: str = "../agente-transcricao/data/output",
    num_files: int = 3
):
    """
    Copia alguns arquivos para o diretório do agente-transcricao para teste
    
    Args:
        source_dir: Diretório com arquivos AMI
        dest_dir: Diretório do agente-transcricao
        num_files: Quantos arquivos copiar
    """
    import shutil
    
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    # Criar diretório de destino se não existir
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Pegar arquivos .txt
    txt_files = list(source_path.glob("*.txt"))
    
    if not txt_files:
        print("Nenhum arquivo .txt encontrado para copiar")
        return
    
    # Copiar os primeiros N arquivos
    files_to_copy = txt_files[:num_files]
    
    print(f"\nCopiando {len(files_to_copy)} arquivo(s) para teste...\n")
    
    for txt_file in files_to_copy:
        dest_file = dest_path / txt_file.name
        shutil.copy2(txt_file, dest_file)
        print(f"Copiado: {txt_file.name} → {dest_dir}")
    
    print(f"\nArquivos prontos para processamento pelo agente-transcricao!")


def show_sample(file_path: str):
    """Mostra uma amostra do conteúdo de um arquivo"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n{'='*60}")
    print(f"Amostra de: {path.name}")
    print(f"{'='*60}")
    print(content[:500] + "..." if len(content) > 500 else content)
    print(f"\n{'='*60}")
    print(f"Total: {len(content)} caracteres, {len(content.split())} palavras")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Importa dataset AMI de reuniões do Hugging Face"
    )
    
    parser.add_argument(
        '--samples',
        type=int,
        default=10,
        help='Número de amostras para baixar (padrão: 10)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./data/ami_dataset',
        help='Diretório de saída (padrão: ./data/ami_dataset)'
    )
    
    parser.add_argument(
        '--copy-to-agent',
        action='store_true',
        help='Copiar alguns arquivos para o agente-transcricao'
    )
    
    parser.add_argument(
        '--show-sample',
        type=str,
        help='Mostrar amostra de um arquivo específico'
    )
    
    args = parser.parse_args()
    
    # Mostrar amostra se solicitado
    if args.show_sample:
        show_sample(args.show_sample)
    else:
        # Baixar dataset
        metadata = download_ami_dataset(
            output_dir=args.output_dir,
            num_samples=args.samples
        )
        
        if metadata and args.copy_to_agent:
            # Copiar para agente-transcricao
            copy_to_transcription_agent(
                source_dir=args.output_dir,
                num_files=3
            )