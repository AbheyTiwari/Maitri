# memory_system.py - Memory System with Ollama Gemma Embeddings

from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
import ollama
import re
from collections import Counter

class EmbeddingMemorySystem:
    """Advanced memory system using Ollama Gemma embeddings for semantic search."""
    
    def __init__(self, db, model: str = 'nomic-embed-text'):
        self.db = db
        self.conversations_collection = db.conversations
        self.memory_collection = db.user_memories
        self.facts_collection = db.user_facts
        
        # Use Ollama's embedding model passed from app.py
        self.embedding_model = model
        
        print(f"Using Ollama embedding model: {self.embedding_model}")
        
        # Test embedding generation
        try:
            test_embedding = ollama.embeddings(
                model=self.embedding_model,
                prompt="test"
            )
            print(f"✓ Ollama embeddings ready (dimension: {len(test_embedding['embedding'])})")
        except Exception as e:
            print(f"✗ Embedding model error: {e}")
            print(f"Run: ollama pull {self.embedding_model}")
        
        # Fact extraction patterns
        self.fact_patterns = {
            'name': [
                r"my name is (\w+)",
                r"i'm (\w+)",
                r"i am (\w+)",
                r"call me (\w+)"
            ],
            'job': [
                r"i work as (?:a|an) ([\w\s]+?)(?:\.|,|$)",
                r"i'm (?:a|an) ([\w\s]+?)(?:\.|,|$)",
                r"i am (?:a|an) ([\w\s]+?)(?:\.|,|$)",
                r"my job is ([\w\s]+?)(?:\.|,|$)",
                r"i do ([\w\s]+?) for work"
            ],
            'hobby': [
                r"i (?:love|like|enjoy) ([\w\s]+?)(?:\.|,|$)",
                r"my hobby is ([\w\s]+?)(?:\.|,|$)",
                r"i'm into ([\w\s]+?)(?:\.|,|$)",
                r"i play ([\w\s]+?)(?:\.|,|$)"
            ],
            'location': [
                r"i live in ([\w\s]+?)(?:\.|,|$)",
                r"i'm from ([\w\s]+?)(?:\.|,|$)",
                r"i am from ([\w\s]+?)(?:\.|,|$)",
                r"i'm in ([\w\s]+?)(?:\.|,|$)"
            ],
            'family': [
                r"my (?:wife|husband|partner|spouse) (?:is |)(\w+)",
                r"i have (\d+) (?:kids|children)",
                r"my (?:son|daughter) (?:is |)(\w+)",
                r"my (?:mom|dad|mother|father) (?:is |)(\w+)"
            ],
            'preference': [
                r"i (?:prefer|like) ([\w\s]+?) over",
                r"i'd rather ([\w\s]+?)(?:\.|,|$)",
                r"my favorite ([\w\s]+?) is ([\w\s]+?)(?:\.|,|$)"
            ],
            'feeling': [
                r"i feel ([\w\s]+?)(?:\.|,|$)",
                r"i'm feeling ([\w\s]+?)(?:\.|,|$)",
                r"feeling (anxious|stressed|happy|sad|tired|excited|worried)",
                r"i've been ([\w\s]+?) lately"
            ],
            'goal': [
                r"i want to ([\w\s]+?)(?:\.|,|$)",
                r"my goal is ([\w\s]+?)(?:\.|,|$)",
                r"i'm trying to ([\w\s]+?)(?:\.|,|$)"
            ]
        }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        try:
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return []
    
    async def store_conversation_with_memory(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        emotion: str,
        recalled_context: dict
    ):
        """Store conversation with Ollama embedding and extract facts."""
        
        embedding = self._generate_embedding(user_message)
        extracted_facts = self._extract_facts(user_message)
        
        conversation_doc = {
            'user_id': user_id,
            'user_message': user_message,
            'assistant_response': assistant_response,
            'emotion': emotion,
            'embedding': embedding,
            'timestamp': datetime.utcnow(),
            'context_strength': recalled_context.get('context_strength', 0),
            'facts_extracted': len(extracted_facts)
        }
        
        await self.conversations_collection.insert_one(conversation_doc)
        
        for fact in extracted_facts:
            await self._store_fact(user_id, fact)
        
        await self._update_memory_themes(user_id, user_message, emotion)
        
        return conversation_doc
    
    def _extract_facts(self, text: str) -> List[Dict]:
        """Extract facts from user message using patterns."""
        facts = []
        text_lower = text.lower()
        
        for fact_type, patterns in self.fact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    fact_value = match if isinstance(match, str) else ' '.join(filter(None, match))
                    fact_value = fact_value.strip()
                    
                    if len(fact_value) > 2 and fact_value not in ['the', 'and', 'but', 'for']:
                        facts.append({
                            'type': fact_type,
                            'value': fact_value,
                            'confidence': 0.8,
                            'source': text[:100]
                        })
        
        return facts
    
    async def _store_fact(self, user_id: str, fact: Dict):
        """Store or update a user fact."""
        
        existing_fact = await self.facts_collection.find_one({
            'user_id': user_id,
            'type': fact['type'],
            'value': {'$regex': f"^{re.escape(fact['value'])}$", '$options': 'i'}
        })
        
        if existing_fact:
            await self.facts_collection.update_one(
                {'_id': existing_fact['_id']},
                {
                    '$set': {'last_mentioned': datetime.utcnow(), 'confidence': min(existing_fact.get('confidence', 0.5) + 0.1, 1.0)},
                    '$inc': {'mention_count': 1}
                }
            )
        else:
            fact_doc = {
                'user_id': user_id,
                'type': fact['type'],
                'value': fact['value'],
                'confidence': fact['confidence'],
                'source': fact['source'],
                'first_mentioned': datetime.utcnow(),
                'last_mentioned': datetime.utcnow(),
                'mention_count': 1
            }
            await self.facts_collection.insert_one(fact_doc)
    
    async def _update_memory_themes(self, user_id: str, message: str, emotion: str):
        """Update thematic memory clusters."""
        themes = self._extract_themes(message)
        
        for theme in themes:
            await self.memory_collection.update_one(
                {'user_id': user_id, 'theme': theme},
                {
                    '$inc': {'frequency': 1},
                    '$set': {'last_discussed': datetime.utcnow()},
                    '$push': {
                        'emotions': emotion,
                        'snippets': {'$each': [message[:100]], '$slice': -5}
                    }
                },
                upsert=True
            )
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract thematic topics from text."""
        theme_keywords = {
            'work': ['work', 'job', 'office', 'boss', 'colleague', 'project', 'deadline', 'career'],
            'family': ['family', 'mother', 'father', 'parent', 'sibling', 'wife', 'husband', 'child', 'mom', 'dad'],
            'relationships': ['relationship', 'friend', 'friendship', 'partner', 'love', 'dating', 'breakup'],
            'health': ['health', 'exercise', 'sleep', 'energy', 'tired', 'sick', 'doctor'],
            'stress': ['stress', 'anxiety', 'worry', 'nervous', 'pressure', 'overwhelm', 'tense'],
            'hobby': ['hobby', 'interest', 'enjoy', 'fun', 'leisure', 'game', 'music', 'movie'],
            'future': ['future', 'goal', 'plan', 'dream', 'hope', 'want', 'wish', 'aspire'],
            'education': ['study', 'school', 'college', 'exam', 'course', 'learning', 'class']
        }
        
        text_lower = text.lower()
        detected_themes = [theme for theme, keywords in theme_keywords.items() if any(keyword in text_lower for keyword in keywords)]
        return detected_themes if detected_themes else ['general']
    
    async def recall_relevant_context(
        self,
        user_id: str,
        current_query: str,
        k: int = 5
    ) -> Dict:
        """Recall relevant context using Ollama semantic similarity."""
        query_embedding = np.array(self._generate_embedding(current_query))
        if query_embedding.size == 0:
            return {'relevant_conversations': [], 'facts': {}, 'themes': [], 'context_strength': 0}

        conversations = await self.conversations_collection.find(
            {'user_id': user_id, 'embedding': {'$exists': True, '$ne': []}}
        ).sort('timestamp', -1).limit(100).to_list(length=100)
        
        if not conversations:
            return {'relevant_conversations': [], 'facts': {}, 'themes': [], 'context_strength': 0}
        
        similarities = []
        for conv in conversations:
            conv_embedding = np.array(conv['embedding'])
            if conv_embedding.size == query_embedding.size:
                similarity = self._cosine_similarity(query_embedding, conv_embedding)
                similarities.append({'conversation': conv, 'similarity': float(similarity)})
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        relevant_convs = [{
            'message': s['conversation']['user_message'],
            'response': s['conversation']['assistant_response'],
            'emotion': s['conversation']['emotion'],
            'timestamp': s['conversation']['timestamp'],
            'similarity': s['similarity']
        } for s in similarities[:k]]
        
        facts = await self._get_user_facts(user_id)
        themes = await self._get_memory_themes(user_id)
        avg_similarity = np.mean([s['similarity'] for s in similarities[:k]]) if similarities else 0
        
        return {
            'relevant_conversations': relevant_convs,
            'facts': facts,
            'themes': themes,
            'context_strength': float(avg_similarity)
        }
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0: return 0.0
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    async def _get_user_facts(self, user_id: str) -> Dict[str, List[Dict]]:
        """Get all facts about a user, grouped by type."""
        facts = await self.facts_collection.find({'user_id': user_id}).sort('confidence', -1).to_list(length=100)
        facts_by_type = {}
        for fact in facts:
            fact_type = fact['type']
            if fact_type not in facts_by_type:
                facts_by_type[fact_type] = []
            facts_by_type[fact_type].append({
                'type': fact_type,
                'value': fact['value'],
                'confidence': fact.get('confidence', 0.5),
                'mention_count': fact.get('mention_count', 1)
            })
        return facts_by_type
    
    async def _get_memory_themes(self, user_id: str) -> List[Dict]:
        """Get memory themes for user."""
        themes = await self.memory_collection.find({'user_id': user_id}).sort('frequency', -1).limit(5).to_list(length=5)
        return [{
            'theme': t['theme'],
            'frequency': t.get('frequency', 0),
            'last_discussed': t.get('last_discussed'),
            'dominant_emotions': Counter(t.get('emotions', [])).most_common(3)
        } for t in themes]
    
    async def get_user_profile_summary(self, user_id: str) -> Dict:
        """Get comprehensive user profile summary."""
        facts = await self._get_user_facts(user_id)
        total_conversations = await self.conversations_collection.count_documents({'user_id': user_id})
        
        recent_convs = await self.conversations_collection.find({'user_id': user_id}).sort('timestamp', -1).limit(20).to_list(length=20)
        emotions = [c['emotion'] for c in recent_convs if 'emotion' in c]
        dominant_emotion = Counter(emotions).most_common(1)[0][0] if emotions else 'neutral'
        
        themes = await self._get_memory_themes(user_id)
        
        profile = {fact_type: [f['value'] for f in fact_list[:3]] for fact_type, fact_list in facts.items() if fact_list}
        
        return {
            'total_conversations': total_conversations,
            'dominant_emotion': dominant_emotion,
            'profile': profile,
            'themes': [t['theme'] for t in themes],
            'facts_count': sum(len(f) for f in facts.values())
        }

