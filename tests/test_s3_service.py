"""
Script para testar a funcionalidade do S3Service.
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_development.s3_service import S3Service, S3ServiceError
from app_development.items import Epic, Story, Task


def test_s3_service():
    """Testa as funcionalidades básicas do S3Service."""
    print("Iniciando teste do S3Service...")
    
    try:
        # Inicializa o serviço S3
        s3_service = S3Service()
        print(f"Serviço S3 inicializado com sucesso. Bucket: {s3_service.bucket}")
        
        # Cria um item de teste
        test_epic = Epic(
            summary="Épico de teste",
            description="Este é um épico de teste para o S3Service",
            labels=["teste", "s3"],
            epic_name="Teste S3"
        )
        
        # Salva o item no S3
        project_key = "TEST"
        item_type = "epic"
        key = s3_service.save_item(
            project_key=project_key,
            item_type=item_type,
            item=test_epic,
            metadata={"test": "true", "created_by": "test_script"}
        )
        print(f"Item salvo com sucesso. Chave: {key}")
        
        # Carrega o item do S3
        loaded_item = s3_service.load_item(key)
        print(f"Item carregado com sucesso: {loaded_item['summary']}")
        
        # Lista itens do projeto
        items = s3_service.load_items(project_key=project_key, item_type=item_type, limit=10)
        print(f"Itens carregados: {len(items)}")
        
        # Exclui o item de teste
        s3_service.delete_item(key)
        print(f"Item excluído com sucesso: {key}")
        
        print("Teste concluído com sucesso!")
        return True
    
    except S3ServiceError as e:
        print(f"Erro no teste do S3Service: {str(e)}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return False


if __name__ == "__main__":
    test_s3_service()
