import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.openai_client import OpenAIClient
from config.prompts import (
    SYSTEM_MESSAGE,
    get_identification_prompt,
    get_user_stories_prompt
)


class PersonaIdentifier:
    """Identifica personas em transcrições e cria user stories"""
    
    def __init__(self, output_dir: str = "./data/output"):
        self.openai_client = OpenAIClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_transcription(self, transcription_path: Path) -> Dict:
        """
        Processa uma transcrição completa: identifica personas e cria user stories
        
        Args:
            transcription_path: Caminho para o arquivo de transcrição (.txt)
            
        Returns:
            Dicionário com personas e user stories identificadas
        """
        print(f"\n{'='*60}")
        print(f"Processando: {transcription_path.name}")
        print(f"{'='*60}")
        
        # Ler transcrição
        transcription = self._read_transcription(transcription_path)
        
        if not transcription:
            print("Transcrição vazia ou inválida")
            return None
        
        print(f"Transcrição lida ({len(transcription)} caracteres)")
        
        # Passo 1: Identificar personas
        print("\n[1/2] Identificando personas...")
        personas_result = self._identify_personas(transcription)
        
        if not personas_result:
            print("Falha ao identificar personas")
            return None
        
        print(f"{len(personas_result.get('personas', []))} persona(s) identificada(s)")
        
        # Passo 2: Criar user stories
        print("\n[2/2] Criando histórias de usuário...")
        user_stories_result = self._create_user_stories(
            personas_result, 
            transcription
        )
        
        if not user_stories_result:
            print("Falha ao criar user stories")
            return None
        
        total_stories = sum(
            len(p.get('historias', [])) 
            for p in user_stories_result.get('user_stories', [])
        )
        print(f"{total_stories} história(s) de usuário criada(s)")
        
        # Combinar resultados
        final_result = {
            "metadata": {
                "arquivo_origem": transcription_path.name,
                "data_processamento": datetime.now().isoformat(),
                "modelo_usado": self.openai_client.model
            },
            "analise_personas": personas_result,
            "historias_usuario": user_stories_result
        }
        
        # Salvar resultado
        output_file = self._save_result(transcription_path.stem, final_result)
        print(f"\nResultado salvo em: {output_file}")
        
        return final_result
    
    def _read_transcription(self, file_path: Path) -> Optional[str]:
        """Lê o conteúdo de um arquivo de transcrição"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Erro ao ler arquivo {file_path}: {e}")
            return None
    
    def _identify_personas(self, transcription: str) -> Optional[Dict]:
        """Identifica personas na transcrição usando LLM"""
        try:
            prompt = get_identification_prompt(transcription)
            
            response = self.openai_client.generate_completion(
                prompt=prompt,
                system_message=SYSTEM_MESSAGE,
                temperature=0.3  # Baixa temperatura para respostas mais consistentes
            )
            
            # Parse JSON da resposta
            personas_data = self._parse_json_response(response)
            return personas_data
            
        except Exception as e:
            print(f"Erro ao identificar personas: {e}")
            return None
    
    def _create_user_stories(
        self, 
        personas_result: Dict, 
        transcription: str
    ) -> Optional[Dict]:
        """Cria user stories baseadas nas personas identificadas"""
        try:
            personas_json = json.dumps(personas_result, ensure_ascii=False, indent=2)
            prompt = get_user_stories_prompt(personas_json, transcription)
            
            response = self.openai_client.generate_completion(
                prompt=prompt,
                system_message=SYSTEM_MESSAGE,
                temperature=0.5
            )
            
            # Parse JSON da resposta
            stories_data = self._parse_json_response(response)
            return stories_data
            
        except Exception as e:
            print(f"Erro ao criar user stories: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse da resposta JSON do LLM, com tratamento de erros"""
        try:
            # Remove possíveis marcadores de código
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
            
        except json.JSONDecodeError as e:
            print(f"Erro ao fazer parse do JSON: {e}")
            print(f"Resposta recebida: {response[:200]}...")
            return None
    
    def _save_result(self, base_name: str, result: Dict) -> Path:
        """Salva o resultado em arquivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{base_name}_personas_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def process_directory(self, input_dir: str) -> List[Dict]:
        """
        Processa todos os arquivos .txt de um diretório
        
        Args:
            input_dir: Diretório com arquivos de transcrição
            
        Returns:
            Lista com resultados de cada arquivo processado
        """
        input_path = Path(input_dir)
        txt_files = list(input_path.glob("*.txt"))
        
        if not txt_files:
            print(f"Nenhum arquivo .txt encontrado em {input_dir}")
            return []
        
        print(f"\nEncontrados {len(txt_files)} arquivo(s) para processar\n")
        
        results = []
        for txt_file in txt_files:
            result = self.process_transcription(txt_file)
            if result:
                results.append(result)
        
        print(f"\n{'='*60}")
        print(f"Processamento concluído: {len(results)}/{len(txt_files)} sucesso")
        print(f"{'='*60}\n")
        
        return results