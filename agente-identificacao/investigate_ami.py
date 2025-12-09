"""
Script para investigar a estrutura do dataset AMI
"""
from datasets import load_dataset
import os
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv("HUGGINGFACE_TOKEN")

print("🔍 Carregando dataset AMI...")
dataset = load_dataset("knkarthick/AMI", split="train", token=hf_token)

print(f"\n📊 Total de amostras: {len(dataset)}")
print(f"\n🔑 Colunas disponíveis: {dataset.column_names}")

# Mostrar primeira amostra
print(f"\n{'='*60}")
print("📄 PRIMEIRA AMOSTRA:")
print(f"{'='*60}")
sample = dataset[0]
for key, value in sample.items():
    if isinstance(value, str):
        preview = value[:200] + "..." if len(value) > 200 else value
    else:
        preview = value
    print(f"\n{key}: {preview}")

print(f"\n{'='*60}")
print("📄 SEGUNDA AMOSTRA:")
print(f"{'='*60}")
sample = dataset[1]
for key, value in sample.items():
    if isinstance(value, str):
        preview = value[:200] + "..." if len(value) > 200 else value
    else:
        preview = value
    print(f"\n{key}: {preview}")