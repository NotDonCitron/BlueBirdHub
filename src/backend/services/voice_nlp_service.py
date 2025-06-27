"""
Natural Language Processing Service for Voice Commands
Provides advanced NLP capabilities for understanding voice commands
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import dateparser
from dataclasses import dataclass
from enum import Enum

@dataclass
class NLPEntity:
    """Represents an extracted entity from text"""
    type: str
    value: Any
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = None

@dataclass
class NLPIntent:
    """Represents the intent of a command"""
    primary_intent: str
    secondary_intents: List[str]
    confidence: float
    entities: List[NLPEntity]
    sentiment: str
    urgency_level: float

class VoiceNLPService:
    """Natural Language Processing for voice commands"""
    
    def __init__(self):
        self.initialize_patterns()
        self.initialize_entity_extractors()
    
    def initialize_patterns(self):
        """Initialize regex patterns for various entities"""
        self.patterns = {
            'priority_levels': {
                r'\b(urgent|critical|emergency)\b': 'urgent',
                r'\b(high|important|asap)\b': 'high',
                r'\b(medium|normal|regular)\b': 'medium',
                r'\b(low|minor|whenever)\b': 'low'
            },
            'time_indicators': {
                r'\b(right now|immediately|asap|urgent)\b': 'immediate',
                r'\b(today|by end of day|eod)\b': 'today',
                r'\b(tomorrow|tmrw)\b': 'tomorrow',
                r'\b(this week|by friday)\b': 'this_week',
                r'\b(next week)\b': 'next_week',
                r'\b(this month)\b': 'this_month',
                r'\b(next month)\b': 'next_month'
            },
            'action_verbs': {
                r'\b(create|add|new|make)\b': 'create',
                r'\b(update|change|modify|edit)\b': 'update',
                r'\b(delete|remove|cancel|trash)\b': 'delete',
                r'\b(complete|finish|done|mark as done)\b': 'complete',
                r'\b(find|search|show|list|get)\b': 'search',
                r'\b(assign|delegate|give to)\b': 'assign',
                r'\b(schedule|plan|set time)\b': 'schedule'
            },
            'object_types': {
                r'\b(task|todo|to-do|item)\b': 'task',
                r'\b(meeting|appointment|event)\b': 'event',
                r'\b(note|memo|reminder)\b': 'note',
                r'\b(workspace|project|folder)\b': 'workspace',
                r'\b(file|document|attachment)\b': 'file'
            },
            'people_patterns': {
                r'@(\w+)': 'mention',
                r'\b(me|myself|I)\b': 'self',
                r'\b(team|everyone|all)\b': 'team',
                r'\bfor (\w+)\b': 'assignee',
                r'\bwith (\w+)\b': 'collaborator'
            }
        }
    
    def initialize_entity_extractors(self):
        """Initialize entity extraction functions"""
        self.entity_extractors = {
            'date': self.extract_dates,
            'time': self.extract_times,
            'duration': self.extract_duration,
            'people': self.extract_people,
            'priority': self.extract_priority,
            'tags': self.extract_tags,
            'numbers': self.extract_numbers,
            'urls': self.extract_urls,
            'emails': self.extract_emails
        }
    
    def analyze_command(self, text: str) -> NLPIntent:
        """Analyze a voice command and extract intent and entities"""
        text_lower = text.lower()
        
        # Extract all entities
        entities = self.extract_all_entities(text)
        
        # Determine primary intent
        primary_intent = self.determine_primary_intent(text_lower, entities)
        
        # Determine secondary intents
        secondary_intents = self.determine_secondary_intents(text_lower, primary_intent)
        
        # Analyze sentiment and urgency
        sentiment = self.analyze_sentiment(text_lower)
        urgency_level = self.analyze_urgency(text_lower, entities)
        
        # Calculate confidence
        confidence = self.calculate_confidence(primary_intent, entities, text_lower)
        
        return NLPIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=confidence,
            entities=entities,
            sentiment=sentiment,
            urgency_level=urgency_level
        )
    
    def extract_all_entities(self, text: str) -> List[NLPEntity]:
        """Extract all entities from text"""
        entities = []
        
        for entity_type, extractor in self.entity_extractors.items():
            extracted = extractor(text)
            entities.extend(extracted)
        
        # Sort by position
        entities.sort(key=lambda e: e.start_pos)
        
        return entities
    
    def extract_dates(self, text: str) -> List[NLPEntity]:
        """Extract date entities from text"""
        entities = []
        
        # Use dateparser for natural date parsing
        try:
            # Common date patterns
            date_patterns = [
                (r'\b(today)\b', 0),
                (r'\b(tomorrow)\b', 1),
                (r'\b(yesterday)\b', -1),
                (r'\b(next week)\b', 7),
                (r'\b(next month)\b', 30),
                (r'\bin (\d+) days?\b', None),
                (r'\bon (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', None)
            ]
            
            for pattern, days_offset in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if days_offset is not None:
                        date_value = datetime.now() + timedelta(days=days_offset)
                    else:
                        # Parse the matched text
                        parsed = dateparser.parse(match.group(0))
                        if parsed:
                            date_value = parsed
                        else:
                            continue
                    
                    entities.append(NLPEntity(
                        type='date',
                        value=date_value.isoformat(),
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={'original_text': match.group(0)}
                    ))
            
            # Try to parse the entire text for dates
            parsed_date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
            if parsed_date and not any(e.type == 'date' for e in entities):
                entities.append(NLPEntity(
                    type='date',
                    value=parsed_date.isoformat(),
                    confidence=0.7,
                    start_pos=0,
                    end_pos=len(text),
                    metadata={'original_text': text}
                ))
                
        except Exception as e:
            pass
        
        return entities
    
    def extract_times(self, text: str) -> List[NLPEntity]:
        """Extract time entities from text"""
        entities = []
        
        # Time patterns
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',
            r'\b(\d{1,2})\s*(am|pm)\b',
            r'\b(morning|afternoon|evening|night)\b',
            r'\b(noon|midnight)\b'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(NLPEntity(
                    type='time',
                    value=match.group(0),
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    metadata={'pattern': pattern}
                ))
        
        return entities
    
    def extract_duration(self, text: str) -> List[NLPEntity]:
        """Extract duration entities from text"""
        entities = []
        
        duration_pattern = r'\b(\d+)\s*(hour|hr|minute|min|day|week|month)s?\b'
        matches = re.finditer(duration_pattern, text, re.IGNORECASE)
        
        for match in matches:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            # Normalize to minutes
            if unit in ['hour', 'hr']:
                minutes = value * 60
            elif unit in ['minute', 'min']:
                minutes = value
            elif unit == 'day':
                minutes = value * 24 * 60
            elif unit == 'week':
                minutes = value * 7 * 24 * 60
            elif unit == 'month':
                minutes = value * 30 * 24 * 60
            else:
                minutes = value
            
            entities.append(NLPEntity(
                type='duration',
                value=minutes,
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={
                    'original_value': value,
                    'unit': unit,
                    'text': match.group(0)
                }
            ))
        
        return entities
    
    def extract_people(self, text: str) -> List[NLPEntity]:
        """Extract people/user entities from text"""
        entities = []
        
        # Extract @mentions
        mention_pattern = r'@(\w+)'
        matches = re.finditer(mention_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='person',
                value=match.group(1),
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={'mention_type': 'direct'}
            ))
        
        # Extract names after certain keywords
        assign_patterns = [
            r'\b(?:assign to|for|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:will|should|needs to)\b'
        ]
        
        for pattern in assign_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(NLPEntity(
                    type='person',
                    value=match.group(1),
                    confidence=0.8,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    metadata={'mention_type': 'contextual'}
                ))
        
        return entities
    
    def extract_priority(self, text: str) -> List[NLPEntity]:
        """Extract priority levels from text"""
        entities = []
        text_lower = text.lower()
        
        for patterns, priority_level in self.patterns['priority_levels'].items():
            if re.search(patterns, text_lower):
                match = re.search(patterns, text_lower)
                entities.append(NLPEntity(
                    type='priority',
                    value=priority_level,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    metadata={'original_text': match.group(0)}
                ))
                break
        
        return entities
    
    def extract_tags(self, text: str) -> List[NLPEntity]:
        """Extract hashtags and labels from text"""
        entities = []
        
        # Extract hashtags
        hashtag_pattern = r'#(\w+)'
        matches = re.finditer(hashtag_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='tag',
                value=match.group(1),
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={'tag_type': 'hashtag'}
            ))
        
        # Extract labels in square brackets
        label_pattern = r'\[([^\]]+)\]'
        matches = re.finditer(label_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='tag',
                value=match.group(1),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={'tag_type': 'label'}
            ))
        
        return entities
    
    def extract_numbers(self, text: str) -> List[NLPEntity]:
        """Extract numeric entities from text"""
        entities = []
        
        # Extract numbers
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        matches = re.finditer(number_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='number',
                value=float(match.group(1)),
                confidence=1.0,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={'is_float': '.' in match.group(1)}
            ))
        
        return entities
    
    def extract_urls(self, text: str) -> List[NLPEntity]:
        """Extract URL entities from text"""
        entities = []
        
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        matches = re.finditer(url_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='url',
                value=match.group(0),
                confidence=1.0,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={}
            ))
        
        return entities
    
    def extract_emails(self, text: str) -> List[NLPEntity]:
        """Extract email entities from text"""
        entities = []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(email_pattern, text)
        for match in matches:
            entities.append(NLPEntity(
                type='email',
                value=match.group(0),
                confidence=1.0,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={}
            ))
        
        return entities
    
    def determine_primary_intent(self, text: str, entities: List[NLPEntity]) -> str:
        """Determine the primary intent of the command"""
        # Check for action verbs
        for patterns, action in self.patterns['action_verbs'].items():
            if re.search(patterns, text):
                return action
        
        # Default intents based on entities
        if any(e.type == 'date' for e in entities):
            return 'schedule'
        elif any(e.type == 'person' for e in entities):
            return 'assign'
        elif re.search(r'\?', text):
            return 'search'
        
        return 'unknown'
    
    def determine_secondary_intents(self, text: str, primary_intent: str) -> List[str]:
        """Determine secondary intents"""
        secondary = []
        
        # Check for additional actions
        if re.search(r'\b(and then|after that|also)\b', text):
            secondary.append('chain_action')
        
        if re.search(r'\b(remind|notification|alert)\b', text):
            secondary.append('set_reminder')
        
        if re.search(r'\b(repeat|recurring|every)\b', text):
            secondary.append('make_recurring')
        
        if re.search(r'\b(private|confidential|secret)\b', text):
            secondary.append('set_private')
        
        return secondary
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the command"""
        positive_words = ['please', 'thanks', 'great', 'awesome', 'good']
        negative_words = ['urgent', 'asap', 'problem', 'issue', 'bug', 'error']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_urgency(self, text: str, entities: List[NLPEntity]) -> float:
        """Analyze urgency level (0-1)"""
        urgency_score = 0.5  # Default
        
        # Check for urgency indicators
        if re.search(r'\b(urgent|asap|critical|emergency|immediately)\b', text, re.IGNORECASE):
            urgency_score = 0.9
        elif re.search(r'\b(soon|quickly|fast)\b', text, re.IGNORECASE):
            urgency_score = 0.7
        
        # Check priority entities
        priority_entities = [e for e in entities if e.type == 'priority']
        if priority_entities:
            priority = priority_entities[0].value
            if priority == 'urgent':
                urgency_score = max(urgency_score, 0.9)
            elif priority == 'high':
                urgency_score = max(urgency_score, 0.7)
        
        # Check date entities
        date_entities = [e for e in entities if e.type == 'date']
        if date_entities:
            try:
                date_value = datetime.fromisoformat(date_entities[0].value.replace('Z', '+00:00'))
                days_until = (date_value - datetime.now()).days
                if days_until <= 1:
                    urgency_score = max(urgency_score, 0.8)
                elif days_until <= 3:
                    urgency_score = max(urgency_score, 0.6)
            except:
                pass
        
        return urgency_score
    
    def calculate_confidence(self, intent: str, entities: List[NLPEntity], text: str) -> float:
        """Calculate overall confidence score"""
        confidence = 0.5  # Base confidence
        
        # Intent found
        if intent != 'unknown':
            confidence += 0.3
        
        # Entities found
        if entities:
            confidence += min(0.2, len(entities) * 0.05)
        
        # Text length (longer commands might be more specific)
        if len(text.split()) > 5:
            confidence += 0.1
        
        # Has question mark (queries are usually clearer)
        if '?' in text:
            confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def generate_structured_command(self, nlp_intent: NLPIntent) -> Dict[str, Any]:
        """Generate a structured command from NLP intent"""
        command = {
            'intent': nlp_intent.primary_intent,
            'confidence': nlp_intent.confidence,
            'parameters': {}
        }
        
        # Map entities to parameters
        for entity in nlp_intent.entities:
            if entity.type == 'date':
                command['parameters']['deadline'] = entity.value
            elif entity.type == 'priority':
                command['parameters']['priority'] = entity.value
            elif entity.type == 'person':
                command['parameters']['assignee'] = entity.value
            elif entity.type == 'tag':
                if 'tags' not in command['parameters']:
                    command['parameters']['tags'] = []
                command['parameters']['tags'].append(entity.value)
        
        # Add metadata
        command['metadata'] = {
            'urgency': nlp_intent.urgency_level,
            'sentiment': nlp_intent.sentiment,
            'secondary_intents': nlp_intent.secondary_intents
        }
        
        return command

# Global instance
voice_nlp_service = VoiceNLPService()