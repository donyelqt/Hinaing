"""Semantic document chunking for RAG."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime

from ...schemas.rag import DocumentChunk
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Intelligent document chunking with overlap for context continuity."""
    
    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50
    ):
        """Initialize chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Overlap between chunks for context continuity
            min_chunk_size: Minimum chunk size (discard smaller chunks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_documents(self, documents: list[WebDocument]) -> list[DocumentChunk]:
        """Chunk multiple documents.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of document chunks
        """
        all_chunks: list[DocumentChunk] = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
            logger.debug(
                f"Chunked document '{doc.title[:50]}...' into {len(chunks)} chunks"
            )
        
        logger.info(f"Total chunks created: {len(all_chunks)} from {len(documents)} documents")
        return all_chunks
    
    def chunk_document(self, document: WebDocument) -> list[DocumentChunk]:
        """Chunk a single document semantically.
        
        Strategy:
        1. Combine title + snippet into full text
        2. Split into sentences
        3. Group sentences into chunks of target size
        4. Apply overlap for context continuity
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunks from this document
        """
        # Build full text
        title = document.title or ""
        snippet = document.snippet or ""
        full_text = f"{title}. {snippet}".strip()
        
        if not full_text or len(full_text) < self.min_chunk_size:
            logger.debug(f"Document too short to chunk: {len(full_text)} chars")
            return []
        
        # Split into sentences
        sentences = self._split_sentences(full_text)
        
        # Group sentences into chunks
        chunks = self._group_into_chunks(sentences)
        
        # Create DocumentChunk objects
        doc_chunks: list[DocumentChunk] = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue
            
            chunk_id = self._generate_chunk_id(document, i)
            base_metadata = {
                "sentiment": document.sentiment,
            }
            credibility = getattr(document, "credibility_score", None)
            if credibility is None:
                credibility = (document.metadata or {}).get("credibility_score")
            if credibility is not None:
                base_metadata["credibility_score"] = credibility

            platform = getattr(document, "platform", None)
            if platform is None:
                platform = (document.metadata or {}).get("platform")
            if platform is not None:
                base_metadata["platform"] = platform

            merged_metadata = {**base_metadata, **(document.metadata or {})}

            doc_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_url=str(document.url) if document.url else "",
                    source_title=document.title or "Untitled",
                    content=chunk_text.strip(),
                    chunk_index=i,
                    total_chunks=len(chunks),
                    published_at=document.published_at,
                    metadata=merged_metadata,
                )
            )
        
        return doc_chunks
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.
        
        Uses simple regex-based splitting on sentence boundaries.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Split on sentence boundaries (.!?) followed by space or end
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _group_into_chunks(self, sentences: list[str]) -> list[str]:
        """Group sentences into chunks with overlap.
        
        Args:
            sentences: List of sentences
            
        Returns:
            List of chunk texts
        """
        if not sentences:
            return []
        
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, finalize current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Calculate overlap: keep last N characters worth of sentences
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, 
                    self.chunk_overlap
                )
                current_chunk = overlap_sentences
                current_length = sum(len(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _get_overlap_sentences(
        self, 
        sentences: list[str], 
        target_overlap: int
    ) -> list[str]:
        """Get last N sentences that fit within target overlap size.
        
        Args:
            sentences: List of sentences
            target_overlap: Target overlap size in characters
            
        Returns:
            List of sentences for overlap
        """
        overlap: list[str] = []
        overlap_length = 0
        
        # Iterate backwards through sentences
        for sentence in reversed(sentences):
            if overlap_length + len(sentence) > target_overlap:
                break
            overlap.insert(0, sentence)
            overlap_length += len(sentence)
        
        return overlap
    
    @staticmethod
    def _generate_chunk_id(document: WebDocument, chunk_index: int) -> str:
        """Generate unique ID for a chunk.
        
        Args:
            document: Source document
            chunk_index: Index of this chunk
            
        Returns:
            Unique chunk ID
        """
        source_id = str(document.url) if document.url else document.title or "unknown"
        content = f"{source_id}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
