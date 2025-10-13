# games.py - Proactive Game System for Maitri AI

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class GameSystem:
    """Proactive game system for engagement and stress relief."""
    
    def __init__(self, db):
        self.db = db
        self.games_collection = db.game_sessions
        self.active_games = {}  # user_id -> game_state
        
        # Antakshari song database (Hindi songs)
        self.antakshari_songs = {
            'a': ['Ajeeb dastan hai yeh', 'Aap jaisa koi', 'Aaj phir jeene ki tamanna hai'],
            'b': ['Bahon mein chale aao', 'Bole chudiyan', 'Badtameez dil'],
            'c': ['Chura liya hai tumne', 'Chaiyya chaiyya', 'Chak de India'],
            'd': ['Dil hai ke manta nahin', 'Dekha ek khwab', 'Dil to pagal hai'],
            'e': ['Ek ladki ko dekha', 'Ek do teen', 'Ek ajnabee haseena se'],
            'f': ['Fanaa', 'Fevicol se'],
            'g': ['Ghar aaja pardesi', 'Gulabi aankhen', 'Guru Randhawa'],
            'h': ['Hum tum ek kamre mein', 'Halka halka suroor', 'Humma humma'],
            'i': ['Ishq wala love', 'Inteha ho gayi'],
            'j': ['Jaane nahin denge', 'Jeena jeena', 'Jhoom barabar jhoom'],
            'k': ['Kuch kuch hota hai', 'Kahin door jab', 'Kabira'],
            'l': ['Lag jaa gale', 'Lungi dance', 'Laila main laila'],
            'm': ['Main khiladi tu anari', 'Mere sapno ki rani', 'Masakali'],
            'n': ['Neele neele ambar', 'Nashe si chad gayi'],
            'o': ['O sathi re', 'Oh humsafar'],
            'p': ['Pyaar hua ikrar hua', 'Pehla nasha', 'Punjab'],
            'r': ['Radha kaise na jale', 'Roja', 'Rang de basanti'],
            's': ['Saathiya', 'Sheila ki jawani', 'Suraj hua maddham'],
            't': ['Tum hi ho', 'Tere bina', 'Tum se hi'],
            'u': ['Udja kale kawan', 'Urvasi urvasi'],
            'v': ['Vande mataram', 'Vaaste'],
            'y': ['Yeh dosti', 'Yeh jo des hai tera', 'Yeh ladka hai allah'],
            'z': ['Zara zara', 'Zoobi doobi']
        }
        
        # Riddles database
        self.riddles = [
            {
                'question': 'I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?',
                'answer': 'echo',
                'hints': ['Sound related', 'Bounces back', 'Mountains have me']
            },
            {
                'question': 'The more you take, the more you leave behind. What am I?',
                'answer': 'footsteps',
                'hints': ['Walking related', 'You make them', 'On the ground']
            },
            {
                'question': 'What has keys but no locks, space but no room, you can enter but not go inside?',
                'answer': 'keyboard',
                'hints': ['Computer related', 'You type on me', 'Has letters']
            }
        ]
        
        # Word association game
        self.word_chains = {
            'space': ['rocket', 'stars', 'astronaut', 'galaxy', 'moon'],
            'happy': ['joy', 'smile', 'laughter', 'celebration', 'sunshine'],
            'food': ['delicious', 'cooking', 'restaurant', 'chef', 'recipe'],
            'music': ['melody', 'song', 'dance', 'rhythm', 'harmony']
        }
    
    async def suggest_game(self, user_id: str, emotion: str, conversation_count: int) -> Optional[Dict]:
        """
        Proactively suggest a game based on user state.
        """
        suggestions = []
        
        # Suggest based on emotion
        if emotion in ['sad', 'stressed', 'anxious']:
            suggestions.append({
                'game': 'antakshari',
                'reason': 'Music can help lift your mood! Want to play Antakshari?',
                'priority': 3
            })
            suggestions.append({
                'game': 'riddle',
                'reason': 'A fun riddle might distract you. Interested?',
                'priority': 2
            })
        
        if emotion in ['bored', 'neutral']:
            suggestions.append({
                'game': 'word_association',
                'reason': 'Let\'s play a quick word game to energize!',
                'priority': 2
            })
        
        if emotion == 'happy':
            suggestions.append({
                'game': 'antakshari',
                'reason': 'You seem cheerful! Perfect time for Antakshari!',
                'priority': 3
            })
        
        # Suggest after certain conversation milestones
        if conversation_count > 0 and conversation_count % 10 == 0:
            suggestions.append({
                'game': 'trivia',
                'reason': 'We\'ve been chatting for a while. Quick trivia break?',
                'priority': 1
            })
        
        # Return highest priority suggestion
        if suggestions:
            best_suggestion = max(suggestions, key=lambda x: x['priority'])
            return best_suggestion
        
        return None
    
    async def start_game(self, user_id: str, game_type: str) -> Dict:
        """Initialize a new game session."""
        game_state = {
            'type': game_type,
            'started_at': datetime.utcnow(),
            'score': 0,
            'turn': 1,
            'status': 'active'
        }
        
        if game_type == 'antakshari':
            game_state.update(self._init_antakshari())
        elif game_type == 'riddle':
            game_state.update(self._init_riddle())
        elif game_type == 'word_association':
            game_state.update(self._init_word_association())
        elif game_type == 'trivia':
            game_state.update(self._init_trivia())
        
        # Store in active games
        self.active_games[user_id] = game_state
        
        # Save to database
        game_state['user_id'] = user_id
        await self.games_collection.insert_one(game_state.copy())
        
        return {
            'status': 'started',
            'message': game_state.get('welcome_message', 'Game started!'),
            'game_type': game_type,
            'instructions': game_state.get('instructions', '')
        }
    
    def _init_antakshari(self) -> Dict:
        """Initialize Antakshari game."""
        # AI starts with a random song
        starting_letter = random.choice(list(self.antakshari_songs.keys()))
        ai_song = random.choice(self.antakshari_songs[starting_letter])
        last_letter = ai_song[-1].lower()
        
        return {
            'last_song': ai_song,
            'last_letter': last_letter,
            'player': 'ai',
            'songs_played': [ai_song],
            'welcome_message': f'🎵 Let\'s play Antakshari! I\'ll start:\n"{ai_song}"\n\nYour turn! Sing a song starting with "{last_letter.upper()}"',
            'instructions': 'Sing a Hindi song starting with the last letter of my song!'
        }
    
    def _init_riddle(self) -> Dict:
        """Initialize riddle game."""
        riddle = random.choice(self.riddles)
        return {
            'current_riddle': riddle,
            'hints_used': 0,
            'attempts': 0,
            'welcome_message': f'🧩 Here\'s a riddle for you:\n\n{riddle["question"]}',
            'instructions': 'Try to guess the answer! Type "hint" if you need help.'
        }
    
    def _init_word_association(self) -> Dict:
        """Initialize word association game."""
        starting_word = random.choice(list(self.word_chains.keys()))
        return {
            'current_word': starting_word,
            'word_chain': [starting_word],
            'welcome_message': f'🔗 Word Association!\n\nI say: "{starting_word}"\n\nWhat\'s the first word that comes to mind?',
            'instructions': 'Say any word you associate with mine. Keep the chain going!'
        }
    
    def _init_trivia(self) -> Dict:
        """Initialize trivia game."""
        trivia_questions = [
            {
                'question': 'What is the largest planet in our solar system?',
                'answer': 'jupiter',
                'options': ['Mars', 'Jupiter', 'Saturn', 'Neptune']
            },
            {
                'question': 'Who painted the Mona Lisa?',
                'answer': 'leonardo da vinci',
                'options': ['Michelangelo', 'Leonardo da Vinci', 'Raphael', 'Donatello']
            },
            {
                'question': 'What is the capital of India?',
                'answer': 'new delhi',
                'options': ['Mumbai', 'Bangalore', 'New Delhi', 'Kolkata']
            }
        ]
        
        question = random.choice(trivia_questions)
        return {
            'current_question': question,
            'welcome_message': f'🎯 Trivia Time!\n\n{question["question"]}\n\nOptions: {", ".join(question["options"])}',
            'instructions': 'Choose the correct answer!'
        }
    
    async def process_game_input(self, user_id: str, user_input: str) -> Dict:
        """Process user input for active game."""
        if user_id not in self.active_games:
            return {'status': 'no_active_game'}
        
        game_state = self.active_games[user_id]
        game_type = game_state['type']
        
        if game_type == 'antakshari':
            return await self._process_antakshari(user_id, user_input, game_state)
        elif game_type == 'riddle':
            return await self._process_riddle(user_id, user_input, game_state)
        elif game_type == 'word_association':
            return await self._process_word_association(user_id, user_input, game_state)
        elif game_type == 'trivia':
            return await self._process_trivia(user_id, user_input, game_state)
        
        return {'status': 'unknown_game'}
    
    async def _process_antakshari(self, user_id: str, user_input: str, game_state: Dict) -> Dict:
        """Process Antakshari move."""
        required_letter = game_state['last_letter']
        user_song = user_input.strip()
        
        # Check if song starts with required letter
        if not user_song.lower().startswith(required_letter):
            return {
                'status': 'invalid_move',
                'message': f'❌ Song must start with "{required_letter.upper()}"! Try again.',
                'required_letter': required_letter
            }
        
        # Valid move - add to played songs
        game_state['songs_played'].append(user_song)
        game_state['score'] += 10
        game_state['turn'] += 1
        
        # AI's turn
        last_letter = user_song[-1].lower()
        
        # Find AI response
        if last_letter in self.antakshari_songs:
            available_songs = [s for s in self.antakshari_songs[last_letter] 
                             if s not in game_state['songs_played']]
            
            if available_songs:
                ai_song = random.choice(available_songs)
                game_state['last_song'] = ai_song
                game_state['last_letter'] = ai_song[-1].lower()
                game_state['songs_played'].append(ai_song)
                
                return {
                    'status': 'valid_move',
                    'message': f'✅ Great song!\n\n🎵 My turn: "{ai_song}"\n\nYour turn! Start with "{game_state["last_letter"].upper()}"',
                    'score': game_state['score'],
                    'ai_song': ai_song,
                    'next_letter': game_state['last_letter']
                }
        
        # AI can't continue - player wins!
        game_state['status'] = 'completed'
        return {
            'status': 'game_won',
            'message': f'🎉 Wow! I can\'t think of a song with "{last_letter.upper()}"! You win!\n\nFinal Score: {game_state["score"]} points',
            'final_score': game_state['score']
        }
    
    async def _process_riddle(self, user_id: str, user_input: str, game_state: Dict) -> Dict:
        """Process riddle answer."""
        user_input_lower = user_input.lower().strip()
        riddle = game_state['current_riddle']
        
        # Check for hint request
        if 'hint' in user_input_lower:
            hints_used = game_state['hints_used']
            if hints_used < len(riddle['hints']):
                hint = riddle['hints'][hints_used]
                game_state['hints_used'] += 1
                return {
                    'status': 'hint_given',
                    'message': f'💡 Hint {hints_used + 1}: {hint}\n\nTry again!',
                    'hints_remaining': len(riddle['hints']) - game_state['hints_used']
                }
            else:
                return {
                    'status': 'no_hints',
                    'message': 'No more hints available! Keep trying.'
                }
        
        # Check answer
        game_state['attempts'] += 1
        
        if riddle['answer'].lower() in user_input_lower:
            game_state['status'] = 'completed'
            points = max(100 - (game_state['attempts'] * 10) - (game_state['hints_used'] * 20), 10)
            game_state['score'] = points
            
            return {
                'status': 'correct',
                'message': f'🎉 Correct! The answer is "{riddle["answer"]}"!\n\nYou earned {points} points!',
                'score': points
            }
        else:
            return {
                'status': 'incorrect',
                'message': f'❌ Not quite! Try again. (Attempt {game_state["attempts"]})\n\nType "hint" for a clue.',
                'attempts': game_state['attempts']
            }
    
    async def _process_word_association(self, user_id: str, user_input: str, game_state: Dict) -> Dict:
        """Process word association."""
        user_word = user_input.strip().lower()
        
        # Validate it's a single word
        if len(user_word.split()) > 1:
            return {
                'status': 'invalid',
                'message': 'Please say just one word!'
            }
        
        # Add to chain
        game_state['word_chain'].append(user_word)
        game_state['score'] += 5
        game_state['turn'] += 1
        
        # AI responds with associated word
        ai_word = self._generate_associated_word(user_word)
        game_state['word_chain'].append(ai_word)
        game_state['current_word'] = ai_word
        
        return {
            'status': 'continue',
            'message': f'✅ {user_word} → {ai_word}\n\nYour turn!',
            'chain_length': len(game_state['word_chain']),
            'score': game_state['score']
        }
    
    async def _process_trivia(self, user_id: str, user_input: str, game_state: Dict) -> Dict:
        """Process trivia answer."""
        question = game_state['current_question']
        user_answer = user_input.lower().strip()
        
        if question['answer'].lower() in user_answer:
            game_state['status'] = 'completed'
            game_state['score'] = 50
            
            return {
                'status': 'correct',
                'message': f'🎉 Correct! The answer is "{question["answer"]}"!\n\nYou earned 50 points!',
                'score': 50
            }
        else:
            return {
                'status': 'incorrect',
                'message': f'❌ Not quite! The correct answer was "{question["answer"]}".\n\nBetter luck next time!',
                'correct_answer': question['answer']
            }
    
    def _generate_associated_word(self, word: str) -> str:
        """Generate an associated word using simple logic."""
        associations = {
            'space': 'stars', 'stars': 'night', 'night': 'moon',
            'happy': 'smile', 'smile': 'joy', 'joy': 'laughter',
            'food': 'hungry', 'hungry': 'eat', 'eat': 'delicious',
            'music': 'song', 'song': 'dance', 'dance': 'rhythm',
            'water': 'ocean', 'ocean': 'wave', 'wave': 'surf',
            'sun': 'bright', 'bright': 'light', 'light': 'shine'
        }
        
        # Try direct association
        if word in associations:
            return associations[word]
        
        # Random association from word chains
        chain_words = []
        for chain in self.word_chains.values():
            chain_words.extend(chain)
        
        return random.choice(chain_words)
    
    async def end_game(self, user_id: str) -> Dict:
        """End current game session."""
        if user_id not in self.active_games:
            return {'status': 'no_active_game'}
        
        game_state = self.active_games[user_id]
        game_state['status'] = 'ended'
        game_state['ended_at'] = datetime.utcnow()
        
        # Update in database
        await self.games_collection.update_one(
            {
                'user_id': user_id,
                'started_at': game_state['started_at']
            },
            {'$set': game_state}
        )
        
        # Remove from active games
        del self.active_games[user_id]
        
        return {
            'status': 'ended',
            'message': f'Game ended! Final score: {game_state.get("score", 0)} points',
            'score': game_state.get('score', 0)
        }
    
    def is_game_active(self, user_id: str) -> bool:
        """Check if user has an active game."""
        return user_id in self.active_games
    
    async def get_game_stats(self, user_id: str) -> Dict:
        """Get user's game statistics."""
        games = await self.games_collection.find({
            'user_id': user_id,
            'status': 'completed'
        }).to_list(length=100)
        
        stats = {
            'total_games': len(games),
            'total_score': sum(g.get('score', 0) for g in games),
            'games_by_type': {},
            'highest_score': max([g.get('score', 0) for g in games]) if games else 0
        }
        
        for game in games:
            game_type = game['type']
            if game_type not in stats['games_by_type']:
                stats['games_by_type'][game_type] = 0
            stats['games_by_type'][game_type] += 1
        
        return stats