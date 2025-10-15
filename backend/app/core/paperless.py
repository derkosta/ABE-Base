"""
Paperless-ngx integration utilities
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class PaperlessClient:
    """Client for Paperless-ngx API integration"""
    
    def __init__(self):
        self.base_url = settings.PAPERLESS_BASE_URL.rstrip('/')
        self.api_token = settings.PAPERLESS_API_TOKEN
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Accept": "application/json"
        }
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload document to Paperless"""
        url = f"{self.base_url}/api/documents/post_document/"
        
        files = {"document": (filename, file_content, "application/pdf")}
        data = {}
        
        if title:
            data["title"] = title
        if tags:
            data["tags"] = ",".join(tags)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    files=files,
                    data=data,
                    headers=self.headers,
                    timeout=300.0  # 5 minutes for large uploads
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Paperless upload failed: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Upload failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Paperless upload error: {e}")
                raise Exception(f"Upload error: {str(e)}")
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get document metadata from Paperless"""
        url = f"{self.base_url}/api/documents/{doc_id}/"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Paperless get document failed: {e.response.status_code}")
                if e.response.status_code == 404:
                    raise Exception("Document not found")
                raise Exception(f"Failed to get document: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Paperless get document error: {e}")
                raise Exception(f"Error getting document: {str(e)}")
    
    async def download_document(self, doc_id: str) -> bytes:
        """Download document content from Paperless"""
        url = f"{self.base_url}/api/documents/{doc_id}/download/"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                logger.error(f"Paperless download failed: {e.response.status_code}")
                if e.response.status_code == 404:
                    raise Exception("Document not found")
                raise Exception(f"Download failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Paperless download error: {e}")
                raise Exception(f"Download error: {str(e)}")
    
    async def get_document_thumb(self, doc_id: str) -> Optional[bytes]:
        """Get document thumbnail from Paperless"""
        url = f"{self.base_url}/api/documents/{doc_id}/thumb/"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None  # No thumbnail available
                logger.error(f"Paperless thumbnail failed: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Paperless thumbnail error: {e}")
                return None
    
    async def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get document text content from Paperless"""
        url = f"{self.base_url}/api/documents/{doc_id}/"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("content", "")
            except httpx.HTTPStatusError as e:
                logger.error(f"Paperless content failed: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Paperless content error: {e}")
                return None
    
    async def search_documents(
        self, 
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search documents in Paperless"""
        url = f"{self.base_url}/api/documents/"
        params = {"page_size": limit}
        
        if query:
            params["search"] = query
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except httpx.HTTPStatusError as e:
                logger.error(f"Paperless search failed: {e.response.status_code}")
                raise Exception(f"Search failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Paperless search error: {e}")
                raise Exception(f"Search error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test connection to Paperless API"""
        url = f"{self.base_url}/api/documents/"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Paperless connection test failed: {e}")
                return False

# Global client instance
paperless_client = PaperlessClient()
