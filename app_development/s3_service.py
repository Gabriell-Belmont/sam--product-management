"""
Serviço para interação com o AWS S3 para armazenamento de contexto e itens do Jira.
"""
import json
import boto3
import uuid
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from botocore.exceptions import ClientError

from app_development.config import AWS_S3_BUCKET, AWS_REGION, AWS_S3_PREFIX

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('s3_service')


class S3ServiceError(Exception):
    """Exceção personalizada para erros do serviço S3."""
    pass


class S3Service:
    """
    Classe para gerenciar o armazenamento de itens e contextos no S3.
    
    Esta classe fornece métodos para salvar e recuperar itens do Jira e seus contextos
    no Amazon S3, organizando-os por tipo de item, projeto e data.
    """
    
    def __init__(self, bucket: str = None, prefix: str = None, region: str = None):
        """
        Inicializa o serviço S3.
        
        Args:
            bucket: Nome do bucket S3. Se não fornecido, usa a configuração.
            prefix: Prefixo para os objetos S3. Se não fornecido, usa a configuração.
            region: Região AWS. Se não fornecido, usa a configuração.
        """
        self.bucket = bucket or AWS_S3_BUCKET
        self.prefix = prefix or AWS_S3_PREFIX
        self.region = region or AWS_REGION
        
        try:
            self.s3 = boto3.client('s3', region_name=self.region)
            # Verifica se o bucket existe
            self.s3.head_bucket(Bucket=self.bucket)
            logger.info(f"Conectado ao bucket S3: {self.bucket}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                logger.error(f"O bucket {self.bucket} não existe")
                raise S3ServiceError(f"O bucket {self.bucket} não existe")
            elif error_code == '403':
                logger.error(f"Sem permissão para acessar o bucket {self.bucket}")
                raise S3ServiceError(f"Sem permissão para acessar o bucket {self.bucket}")
            else:
                logger.error(f"Erro ao conectar ao S3: {str(e)}")
                raise S3ServiceError(f"Erro ao conectar ao S3: {str(e)}")
    
    def _build_key(self, project_key: str, item_type: str, item_id: str = None) -> str:
        """
        Constrói a chave S3 para um item.
        
        Args:
            project_key: Chave do projeto Jira.
            item_type: Tipo do item (epic, story, task, etc).
            item_id: ID único do item. Se não fornecido, gera um UUID.
            
        Returns:
            str: Chave S3 formatada.
        """
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        if item_id is None:
            item_id = str(uuid.uuid4())
        
        return f"{self.prefix}{project_key}/{item_type}/{date_str}/{item_id}.json"
    
    def _serialize_item(self, item: Union[Dict[str, Any], object]) -> str:
        """
        Serializa um item para JSON.
        
        Args:
            item: Item a ser serializado (dicionário ou objeto com método to_dict).
            
        Returns:
            str: Representação JSON do item.
        """
        if hasattr(item, 'to_dict'):
            data = item.to_dict()
        elif hasattr(item, '__dict__'):
            # Para objetos dataclass ou similares
            data = item.__dict__.copy()
            # Converte datetime para string ISO
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
        else:
            data = item
        
        return json.dumps(data, default=str)
    
    def _deserialize_item(self, json_str: str) -> Dict[str, Any]:
        """
        Deserializa um item de JSON.
        
        Args:
            json_str: String JSON a ser deserializada.
            
        Returns:
            Dict[str, Any]: Dicionário com os dados do item.
        """
        data = json.loads(json_str)
        
        # Converte strings ISO para datetime
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value and value.endswith('Z'):
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
        
        return data
    
    def save_item(self, project_key: str, item_type: str, item: Union[Dict[str, Any], object], 
                  item_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Salva um item no S3.
        
        Args:
            project_key: Chave do projeto Jira.
            item_type: Tipo do item (epic, story, task, etc).
            item: Item a ser salvo (dicionário ou objeto).
            item_id: ID único do item. Se não fornecido, gera um UUID.
            metadata: Metadados adicionais para o objeto S3.
            
        Returns:
            str: Chave S3 onde o item foi salvo.
        """
        key = self._build_key(project_key, item_type, item_id)
        
        # Prepara os metadados
        s3_metadata = {}
        if metadata:
            # Converte os valores para string, pois S3 só aceita strings como metadados
            s3_metadata = {k: str(v) for k, v in metadata.items()}
        
        try:
            # Serializa o item
            item_json = self._serialize_item(item)
            
            # Salva no S3
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=item_json,
                ContentType='application/json',
                Metadata=s3_metadata
            )
            
            logger.info(f"Item salvo com sucesso: {key}")
            return key
        
        except ClientError as e:
            logger.error(f"Erro ao salvar item no S3: {str(e)}")
            raise S3ServiceError(f"Erro ao salvar item no S3: {str(e)}")
    
    def load_item(self, key: str) -> Dict[str, Any]:
        """
        Carrega um item específico do S3.
        
        Args:
            key: Chave S3 do item.
            
        Returns:
            Dict[str, Any]: Dicionário com os dados do item.
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            item_json = response['Body'].read().decode('utf-8')
            item = self._deserialize_item(item_json)
            
            # Adiciona os metadados do S3 ao item
            if 'Metadata' in response and response['Metadata']:
                item['_metadata'] = response['Metadata']
            
            return item
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                logger.error(f"Item não encontrado: {key}")
                raise S3ServiceError(f"Item não encontrado: {key}")
            else:
                logger.error(f"Erro ao carregar item do S3: {str(e)}")
                raise S3ServiceError(f"Erro ao carregar item do S3: {str(e)}")
    
    def load_items(self, project_key: str, item_type: str = None, 
                   since_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Carrega múltiplos itens do S3 com base em filtros.
        
        Args:
            project_key: Chave do projeto Jira.
            item_type: Tipo do item (epic, story, task, etc). Se None, carrega todos os tipos.
            since_date: Data a partir da qual carregar itens. Se None, carrega todos.
            limit: Número máximo de itens a retornar.
            
        Returns:
            List[Dict[str, Any]]: Lista de itens.
        """
        prefix = f"{self.prefix}{project_key}/"
        if item_type:
            prefix += f"{item_type}/"
        
        if since_date:
            date_str = since_date.strftime("%Y/%m/%d")
            prefix += date_str
        
        try:
            # Lista os objetos no S3
            paginator = self.s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter='/',
                PaginationConfig={
                    'MaxItems': limit,
                    'PageSize': limit  # opcional: controla quantos itens por página
                }
            )
            
            items = []
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    items.append(self.load_item(obj['Key']))
                # opcional: pare cedo se coletou o suficiente
                if len(items) >= limit:
                    break

            # Ordena por data de modificação (mais recente primeiro)
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return items[:limit]
        
        except ClientError as e:
            logger.error(f"Erro ao listar itens do S3: {str(e)}")
            raise S3ServiceError(f"Erro ao listar itens do S3: {str(e)}")
    
    def delete_item(self, key: str) -> bool:
        """
        Exclui um item do S3.
        
        Args:
            key: Chave S3 do item.
            
        Returns:
            bool: True se o item foi excluído com sucesso.
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            
            logger.info(f"Item excluído com sucesso: {key}")
            return True
        
        except ClientError as e:
            logger.error(f"Erro ao excluir item do S3: {str(e)}")
            raise S3ServiceError(f"Erro ao excluir item do S3: {str(e)}")
    
    def get_item_history(self, project_key: str, days: int = 30, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtém o histórico de itens criados em um projeto.
        
        Args:
            project_key: Chave do projeto Jira.
            days: Número de dias para olhar para trás.
            limit: Número máximo de itens a retornar por tipo.
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dicionário com listas de itens por tipo.
        """
        # Calcula a data de início
        start_date = datetime.utcnow()
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Obtém todos os tipos de itens
        try:
            # Lista os prefixos (tipos de itens) no projeto
            result = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.prefix}{project_key}/",
                Delimiter='/'
            )
            
            history = {}
            
            if 'CommonPrefixes' in result:
                for prefix in result['CommonPrefixes']:
                    # Extrai o tipo de item do prefixo
                    item_type = prefix['Prefix'].split('/')[-2]
                    
                    # Carrega os itens deste tipo
                    items = self.load_items(
                        project_key=project_key,
                        item_type=item_type,
                        limit=limit
                    )
                    
                    history[item_type] = items
            
            return history
        
        except ClientError as e:
            logger.error(f"Erro ao obter histórico de itens: {str(e)}")
            raise S3ServiceError(f"Erro ao obter histórico de itens: {str(e)}")


class S3ContextService:
    """Classe para gerenciar o armazenamento de contexto no S3."""
    
    def __init__(self, bucket: str = None, prefix: str = None, region: str = None):
        """
        Inicializa o serviço S3.
        
        Args:
            bucket: Nome do bucket S3. Se não fornecido, usa a configuração.
            prefix: Prefixo para os objetos S3. Se não fornecido, usa a configuração.
            region: Região AWS. Se não fornecido, usa a configuração.
        """
        self.bucket = bucket or AWS_S3_BUCKET
        self.prefix = prefix or AWS_S3_PREFIX
        self.region = region or AWS_REGION
        
        self.s3 = boto3.client('s3', region_name=self.region)
    
    def save_context(self, user_id: str, context_data: Dict[str, Any]) -> str:
        """
        Salva o contexto de uma interação no S3.
        
        Args:
            user_id: ID do usuário.
            context_data: Dados de contexto a serem salvos.
            
        Returns:
            str: Chave do objeto S3 onde o contexto foi salvo.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        key = f"{self.prefix}{user_id}/{timestamp}.json"
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(context_data),
            ContentType='application/json'
        )
        
        return key
    
    def get_recent_contexts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém os contextos mais recentes de um usuário.
        
        Args:
            user_id: ID do usuário.
            limit: Número máximo de contextos a retornar.
            
        Returns:
            List[Dict[str, Any]]: Lista de contextos.
        """
        prefix = f"{self.prefix}{user_id}/"
        
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=limit
        )
        
        contexts = []
        if 'Contents' in response:
            for obj in sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[:limit]:
                obj_response = self.s3.get_object(
                    Bucket=self.bucket,
                    Key=obj['Key']
                )
                context = json.loads(obj_response['Body'].read().decode('utf-8'))
                contexts.append(context)
        
        return contexts
