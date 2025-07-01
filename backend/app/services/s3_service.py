import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import AWS_S3_BUCKET, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
            region_name=AWS_REGION
        )
        self.s3_client = session.client('s3')
        self.bucket = AWS_S3_BUCKET
    
    async def save_item_context(self, item_key: str, item_type: str, summary: str, 
                               description: str, user_context: Optional[str] = None):
        """Save item context to S3 for future conflict detection"""
        try:
            context_data = {
                "item_key": item_key,
                "item_type": item_type,
                "summary": summary,
                "description": description,
                "user_context": user_context,
                "created_at": datetime.now().isoformat(),
                "keywords": self._extract_keywords(summary + " " + description)
            }
            
            key = f"contexts/{item_type.lower()}/{item_key}.json"
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(context_data, ensure_ascii=False),
                ContentType='application/json'
            )
            
            logger.info(f"Context saved for item {item_key}")
            
        except Exception as e:
            logger.error(f"Error saving context to S3: {str(e)}")
            raise
    
    async def check_conflicts(self, summary: str, description: str, item_type: str, 
                             user_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for conflicts with existing items"""
        try:
            conflicts = []
            keywords = self._extract_keywords(summary + " " + description)
            
            prefix = f"contexts/{item_type.lower()}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return conflicts
            
            for obj in response['Contents']:
                try:
                    obj_response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=obj['Key']
                    )
                    
                    existing_context = json.loads(obj_response['Body'].read().decode('utf-8'))
                    
                    if self._has_conflict(keywords, existing_context, summary, description):
                        conflicts.append({
                            "item_key": existing_context.get("item_key"),
                            "summary": existing_context.get("summary"),
                            "created_at": existing_context.get("created_at"),
                            "conflict_reason": "Palavras-chave similares detectadas"
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing object {obj['Key']}: {str(e)}")
                    continue
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {str(e)}")
            return []
    
    async def get_user_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's historical context"""
        try:
            context_items = []
            prefix = f"contexts/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return context_items
            
            for obj in response['Contents']:
                try:
                    obj_response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=obj['Key']
                    )
                    
                    context_data = json.loads(obj_response['Body'].read().decode('utf-8'))
                    
                    if context_data.get("user_context") == user_id:
                        context_items.append(context_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing context object {obj['Key']}: {str(e)}")
                    continue
            
            context_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return context_items[:50]
            
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for conflict detection"""
        import re
        
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        stop_words = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das', 
                     'para', 'por', 'com', 'em', 'no', 'na', 'nos', 'nas', 'que', 'e', 
                     'ou', 'se', 'não', 'é', 'são', 'foi', 'foram', 'ser', 'estar'}
        
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return list(set(keywords))[:20]
    
    def _has_conflict(self, new_keywords: List[str], existing_context: Dict[str, Any], 
                     new_summary: str, new_description: str) -> bool:
        """Check if there's a conflict between new item and existing context"""
        existing_keywords = existing_context.get("keywords", [])
        
        common_keywords = set(new_keywords) & set(existing_keywords)
        
        if len(common_keywords) >= 3:
            return True
        
        existing_summary = existing_context.get("summary", "").lower()
        if new_summary.lower() in existing_summary or existing_summary in new_summary.lower():
            return True
        
        return False
