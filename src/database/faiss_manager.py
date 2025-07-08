import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional

class FAISSManager:
    def __init__(self, db_path: str = "faiss_db"):
        """Initialize FAISS database manager."""
        self.db_path = db_path
        self.index_file = os.path.join(db_path, "faiss.index")
        self.metadata_file = os.path.join(db_path, "metadata.pkl")
        self.documents_file = os.path.join(db_path, "documents.pkl")
        
        # Initialize embedding model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        # Initialize FAISS index and metadata
        self.index = None
        self.metadata = []
        self.documents = []
        
        # Create database directory
        os.makedirs(db_path, exist_ok=True)
        
        # Load existing database
        self.load_database()
    
    def load_database(self):
        """Load existing FAISS database and metadata."""
        try:
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
                print(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
                print("🆕 Created new FAISS index")
            
            # Load metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"✅ Loaded {len(self.metadata)} metadata records")
            
            # Load documents
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                print(f"✅ Loaded {len(self.documents)} document records")
                
        except Exception as e:
            print(f"⚠️ Error loading database: {e}")
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.metadata = []
            self.documents = []
    
    def save_database(self):
        """Save FAISS database and metadata to disk."""
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_file)
            
            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            # Save documents
            with open(self.documents_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print(f"💾 Database saved successfully")
            
        except Exception as e:
            print(f"❌ Error saving database: {e}")
    
    def add_document(self, content: str, metadata: Dict):
        """Add a document to the FAISS database."""
        try:
            # Create embedding
            embedding = self.encoder.encode([content])
            embedding = embedding.astype(np.float32)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding)
            
            # Add to FAISS index
            self.index.add(embedding)
            
            # Add metadata
            self.metadata.append(metadata)
            
            # Store original document
            self.documents.append(content)
            
            print(f"✅ Added document: {metadata.get('title', 'Untitled')}")
            
        except Exception as e:
            print(f"❌ Error adding document: {e}")
    
    def search(self, query: str, top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict]:
        """Search for similar documents."""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Create query embedding
            query_embedding = self.encoder.encode([query])
            query_embedding = query_embedding.astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS
            scores, indices = self.index.search(query_embedding, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= similarity_threshold and idx < len(self.metadata):
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.metadata[idx],
                        'similarity': float(score)
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def search_by_topic(self, topic: str, top_k: int = 3) -> Dict:
        """Hybrid search: metadata + content matching."""
        try:
            # Step 1: Search by metadata (titles, topics)
            metadata_matches = []
            for i, meta in enumerate(self.metadata):
                title = meta.get('title', '').lower()
                topic_tags = meta.get('topics', [])
                
                if topic.lower() in title or any(topic.lower() in tag.lower() for tag in topic_tags):
                    metadata_matches.append({
                        'content': self.documents[i],
                        'metadata': meta,
                        'similarity': 0.95,  # High score for exact matches
                        'match_type': 'metadata'
                    })
            
            # Step 2: Search by content similarity
            content_matches = self.search(topic, top_k=top_k, similarity_threshold=0.6)
            for match in content_matches:
                match['match_type'] = 'content'
            
            # Step 3: Combine and rank results
            all_matches = metadata_matches + content_matches
            
            # Remove duplicates and sort by similarity
            seen_indices = set()
            unique_matches = []
            
            for match in sorted(all_matches, key=lambda x: x['similarity'], reverse=True):
                match_id = match['metadata'].get('id', '')
                if match_id not in seen_indices:
                    seen_indices.add(match_id)
                    unique_matches.append(match)
            
            return {
                'matches': unique_matches[:top_k],
                'total_found': len(unique_matches),
                'has_exact_match': len(metadata_matches) > 0
            }
            
        except Exception as e:
            print(f"❌ Error in topic search: {e}")
            return {'matches': [], 'total_found': 0, 'has_exact_match': False}
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        return {
            'total_documents': self.index.ntotal if self.index else 0,
            'total_metadata': len(self.metadata),
            'database_size': f"{os.path.getsize(self.index_file) / 1024:.2f} KB" if os.path.exists(self.index_file) else "0 KB"
        }
    
    def clear_database(self):
        """Clear all data from database."""
        try:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.metadata = []
            self.documents = []
            
            # Remove files
            for file_path in [self.index_file, self.metadata_file, self.documents_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            print("🗑️ Database cleared successfully")
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")