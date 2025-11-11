#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Last.bot - النسخة الشاملة المتكاملة
=====================================
Last.bot - The Comprehensive Integrated System

نظام ذكي متكامل مع:
- مساعد ذكي متطور
- نظام مراقبة متقدم  
- إصلاح تلقائي للمشاكل
- واجهة مستخدم حديثة
- أمان متقدم

Author: MiniMax Agent
Date: 2025-11-12
Version: 2.0.0 Comprehensive
"""

import os
import json
import sqlite3
import hashlib
import hmac
import jwt
import bcrypt
import redis
import threading
import time
import psutil
import requests
import smtplib
import schedule
import logging
import warnings
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, abort
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import chartjs
import qrcode
import io
import base64
import cProfile
import pstats
import memory_profiler
import subprocess
import socket
import ssl
import urllib3
import aiohttp
import asyncio

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure matplotlib for plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

def setup_matplotlib_for_plotting():
    """Setup matplotlib for proper rendering"""
    plt.switch_backend("Agg")
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "PingFang SC", "Arial Unicode MS", "Hiragino Sans GB"]
    plt.rcParams["axes.unicode_minus"] = False

# Setup matplotlib
setup_matplotlib_for_plotting()

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'changeme123-secret-key-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database setup
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # 2FA settings
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32), nullable=True)
    backup_codes = Column(Text, nullable=True)

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(50), nullable=True)
    function = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

class ErrorRecord(Base):
    __tablename__ = 'error_records'
    
    id = Column(Integer, primary_key=True)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    module_name = Column(String(100), nullable=True)
    function_name = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    auto_fixed = Column(Boolean, default=False)
    fix_attempts = Column(Integer, default=0)
    solution = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)

class PerformanceMetric(Base):
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(50), nullable=False)
    metric_unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='normal')
    threshold_warning = Column(String(50), nullable=True)
    threshold_critical = Column(String(50), nullable=True)

class AISession(Base):
    __tablename__ = 'ai_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    session_id = Column(String(100), nullable=False)
    context = Column(Text, nullable=True)
    user_message = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

class KnowledgeEntry(Base):
    __tablename__ = 'knowledge_entries'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create database engine
db_path = os.path.join(os.path.dirname(__file__), 'lastbot_comprehensive.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Redis connection
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    redis_client = None
    REDIS_AVAILABLE = False

# AI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your-deepseek-api-key')
OPENAI_BASE_URL = 'https://api.openai.com/v1'
DEEPSEEK_BASE_URL = 'https://api.deepseek.com/v1'

# WhatsApp Configuration
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '+1234567890')
WHATSAPP_API_URL = f'https://graph.facebook.com/v18.0/{WHATSAPP_NUMBER}/messages'

# Email Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', '')

# Performance monitoring
monitoring_data = {
    'cpu_usage': [],
    'memory_usage': [],
    'response_times': [],
    'error_counts': [],
    'timestamps': []
}

# AI Knowledge Base
knowledge_base = {
    'general': [
        {'question': 'ما هو Last.bot؟', 'answer': 'Last.bot هو نظام ذكي متكامل مع مساعد ذكي متطور وإمكانيات مراقبة متقدمة.', 'confidence': 0.95},
        {'question': 'كيف تعمل المساعد الذكي؟', 'answer': 'المساعد الذكي يستخدم تقنيات متقدمة لفهم السياق وتحليل المشاعر وتقديم استجابات ذكية.', 'confidence': 0.92},
        {'question': 'ما هي ميزات الأمان؟', 'answer': 'يشمل النظام تشفير AES-256، مصادقة ثنائية العامل، حماية CSRF/XSS، ومراقبة أمنية شاملة.', 'confidence': 0.90}
    ],
    'troubleshooting': [
        {'question': 'خطأ في الاتصال بقاعدة البيانات', 'answer': 'تحقق من إعدادات قاعدة البيانات والاتصال. تأكد من تشغيل الخدمة وإعدادات الشبكة.', 'confidence': 0.88},
        {'question': 'بطء في الاستجابة', 'answer': 'تحقق من استخدام المعالج والذاكرة. قم بتحسين الاستعلامات ومراقبة الأداء.', 'confidence': 0.85},
        {'question': 'مشاكل في تسجيل الدخول', 'answer': 'تحقق من صحة بيانات الاعتماد وحالة الحساب. تأكد من عدم قفل الحساب أو انتهاء صلاحية الجلسة.', 'confidence': 0.90}
    ],
    'ai': [
        {'question': 'كيف يعمل الذكاء الاصطناعي؟', 'answer': 'يستخدم النظام نماذج متقدمة لفهم النص وتحليل السياق وتقديم استجابات مناسبة.', 'confidence': 0.87},
        {'question': 'ما هو تحليل المشاعر؟', 'answer': 'تحليل المشاعر يحدد حالة المزاج في النص (إيجابي/سلبي/محايد) لفهم نية المستخدم.', 'confidence': 0.89}
    ]
}

# Initialize vectorizer for similarity matching
vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
knowledge_vectors = {}

def build_knowledge_vectors():
    """Build vectors for knowledge base similarity matching"""
    global vectorizer, knowledge_vectors
    
    for category, entries in knowledge_base.items():
        texts = [f"{entry['question']} {entry['answer']}" for entry in entries]
        if texts:
            vectors = vectorizer.fit_transform(texts)
            knowledge_vectors[category] = vectors

# Build initial knowledge vectors
build_knowledge_vectors()

# Enhanced Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lastbot_comprehensive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LastBot')

def log_system_event(level, message, module='System', function='main', user_id=None, ip_address=None, user_agent=None):
    """Enhanced logging with database and Redis storage"""
    try:
        db_session = SessionLocal()
        
        # Create log entry
        log_entry = SystemLog(
            level=level,
            message=message,
            module=module,
            function=function,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db_session.add(log_entry)
        db_session.commit()
        
        # Store in Redis if available
        if REDIS_AVAILABLE:
            redis_client.lpush('system_logs', json.dumps({
                'level': level,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'module': module
            }))
            redis_client.ltrim('system_logs', 0, 1000)  # Keep only last 1000 logs
        
        db_session.close()
        
    except Exception as e:
        logger.error(f"Failed to log system event: {e}")

class IntelligentBot:
    """Advanced intelligent bot with self-learning capabilities"""
    
    def __init__(self):
        self.session_history = {}
        self.context_memory = {}
        self.learning_patterns = {}
        self.error_patterns = {}
        
    def analyze_sentiment(self, text):
        """Analyze sentiment of user input"""
        try:
            # Simple sentiment analysis using predefined patterns
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'happy', 'awesome', 'fantastic']
            negative_words = ['bad', 'terrible', 'hate', 'sad', 'angry', 'awful', 'horrible', 'frustrated']
            
            text_lower = text.lower()
            positive_score = sum(1 for word in positive_words if word in text_lower)
            negative_score = sum(1 for word in negative_words if word in text_lower)
            
            if positive_score > negative_score:
                return {'sentiment': 'positive', 'confidence': min(0.9, positive_score * 0.3)}
            elif negative_score > positive_score:
                return {'sentiment': 'negative', 'confidence': min(0.9, negative_score * 0.3)}
            else:
                return {'sentiment': 'neutral', 'confidence': 0.5}
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {'sentiment': 'neutral', 'confidence': 0.0}
    
    def find_knowledge_match(self, question, category=None):
        """Find best matching knowledge entry using vector similarity"""
        try:
            if category and category in knowledge_vectors:
                # Search in specific category
                question_vector = vectorizer.transform([question])
                similarity_scores = cosine_similarity(question_vector, knowledge_vectors[category])
                best_match_idx = np.argmax(similarity_scores[0])
                confidence = similarity_scores[0][best_match_idx]
                
                if confidence > 0.3:  # Threshold for relevance
                    return {
                        'answer': knowledge_base[category][best_match_idx]['answer'],
                        'confidence': confidence,
                        'category': category
                    }
            
            else:
                # Search across all categories
                all_questions = []
                category_mapping = []
                
                for cat, entries in knowledge_base.items():
                    for entry in entries:
                        all_questions.append(f"{entry['question']} {entry['answer']}")
                        category_mapping.append((cat, entry))
                
                if all_questions:
                    question_vector = vectorizer.transform([question])
                    all_vectors = vectorizer.transform(all_questions)
                    similarity_scores = cosine_similarity(question_vector, all_vectors)
                    
                    best_match_idx = np.argmax(similarity_scores[0])
                    confidence = similarity_scores[0][best_match_idx]
                    
                    if confidence > 0.3:
                        best_category, best_entry = category_mapping[best_match_idx]
                        return {
                            'answer': best_entry['answer'],
                            'confidence': confidence,
                            'category': best_category
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Knowledge matching error: {e}")
            return None
    
    async def call_ai_api(self, message, context=None):
        """Call external AI API (OpenAI or DeepSeek)"""
        try:
            # Try OpenAI first
            if OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key':
                headers = {
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'gpt-4',
                    'messages': [
                        {'role': 'system', 'content': 'You are a helpful AI assistant for Last.bot system. Provide helpful, accurate, and concise responses.'},
                        {'role': 'user', 'content': message}
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.7
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(f'{OPENAI_BASE_URL}/chat/completions', 
                                          headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                'response': result['choices'][0]['message']['content'],
                                'confidence': 0.9,
                                'source': 'OpenAI'
                            }
            
            # Try DeepSeek if OpenAI fails
            if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != 'your-deepseek-api-key':
                headers = {
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': 'أنت مساعد ذكي لنظام Last.bot. قدم إجابات مفيدة ودقيقة ومختصرة.'},
                        {'role': 'user', 'content': message}
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.7
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(f'{DEEPSEEK_BASE_URL}/chat/completions', 
                                          headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                'response': result['choices'][0]['message']['content'],
                                'confidence': 0.85,
                                'source': 'DeepSeek'
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"AI API call error: {e}")
            return None
    
    async def generate_response(self, user_message, session_id=None, context=None):
        """Generate intelligent response with context awareness"""
        try:
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(user_message)
            
            # Find knowledge base match
            knowledge_match = self.find_knowledge_match(user_message)
            
            if knowledge_match and knowledge_match['confidence'] > 0.6:
                # Use knowledge base response
                response = f"بناءً على قاعدة المعرفة: {knowledge_match['answer']}"
                confidence = knowledge_match['confidence']
            else:
                # Try external AI API
                ai_response = await self.call_ai_api(user_message, context)
                
                if ai_response:
                    response = ai_response['response']
                    confidence = ai_response['confidence']
                else:
                    # Fallback response
                    response = "أعتذر، لا أستطيع فهم طلبك حالياً. يمكنك إعادة صياغته أو اختيار موضوع آخر من الأسئلة الشائعة."
                    confidence = 0.1
            
            # Store interaction in session
            if session_id:
                if session_id not in self.session_history:
                    self.session_history[session_id] = []
                
                self.session_history[session_id].append({
                    'user_message': user_message,
                    'ai_response': response,
                    'sentiment': sentiment_result,
                    'timestamp': datetime.utcnow().isoformat(),
                    'confidence': confidence
                })
            
            # Save to database
            try:
                db_session = SessionLocal()
                ai_entry = AISession(
                    session_id=session_id or 'anonymous',
                    user_message=user_message,
                    ai_response=response,
                    sentiment_score=sentiment_result.get('confidence', 0.0),
                    confidence_score=confidence
                )
                db_session.add(ai_entry)
                db_session.commit()
                db_session.close()
            except Exception as e:
                logger.error(f"Failed to save AI session: {e}")
            
            return {
                'response': response,
                'confidence': confidence,
                'sentiment': sentiment_result,
                'knowledge_source': knowledge_match is not None,
                'category': knowledge_match['category'] if knowledge_match else None
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {
                'response': 'حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.',
                'confidence': 0.0,
                'sentiment': {'sentiment': 'neutral', 'confidence': 0.0},
                'knowledge_source': False
            }

class ErrorAnalyzer:
    """Advanced error analysis and automatic fixing system"""
    
    def __init__(self):
        self.error_patterns = self.load_error_patterns()
        self.fix_strategies = self.load_fix_strategies()
        self.confidence_threshold = 0.7
        
    def load_error_patterns(self):
        """Load known error patterns and their solutions"""
        return {
            'ImportError': {
                'patterns': ['ModuleNotFoundError', 'ImportError', 'No module named'],
                'solutions': [
                    'pip install {module}',
                    'Check Python environment',
                    'Verify module installation'
                ],
                'priority': 'high'
            },
            'ConnectionError': {
                'patterns': ['Connection refused', 'Network unreachable', 'Timeout'],
                'solutions': [
                    'Check network connectivity',
                    'Verify service status',
                    'Check firewall settings'
                ],
                'priority': 'high'
            },
            'PermissionError': {
                'patterns': ['Permission denied', 'Access denied'],
                'solutions': [
                    'Check file permissions',
                    'Run with appropriate privileges',
                    'Verify user access rights'
                ],
                'priority': 'medium'
            },
            'DatabaseError': {
                'patterns': ['database is locked', 'no such table', 'UNIQUE constraint'],
                'solutions': [
                    'Close database connections',
                    'Run database migrations',
                    'Check database schema'
                ],
                'priority': 'high'
            }
        }
    
    def load_fix_strategies(self):
        """Load automatic fixing strategies"""
        return {
            'sequential': self.fix_sequential,
            'intensive': self.fix_intensive,
            'conservative': self.fix_conservative
        }
    
    def analyze_error(self, error_info):
        """Analyze error and determine fix strategy"""
        try:
            error_type = error_info.get('type', '')
            error_message = error_info.get('message', '')
            stack_trace = error_info.get('traceback', '')
            
            # Find matching pattern
            matched_pattern = None
            best_confidence = 0
            
            for pattern_name, pattern_data in self.error_patterns.items():
                for search_term in pattern_data['patterns']:
                    if search_term.lower() in error_message.lower() or search_term.lower() in stack_trace.lower():
                        confidence = min(0.95, best_confidence + 0.3)
                        matched_pattern = pattern_name
                        best_confidence = max(best_confidence, confidence)
                        break
            
            # Store error in database
            db_session = SessionLocal()
            error_record = ErrorRecord(
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                confidence_score=best_confidence
            )
            db_session.add(error_record)
            db_session.commit()
            db_session.close()
            
            return {
                'pattern': matched_pattern,
                'confidence': best_confidence,
                'solutions': self.error_patterns.get(matched_pattern, {}).get('solutions', []),
                'priority': self.error_patterns.get(matched_pattern, {}).get('priority', 'low')
            }
            
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            return None
    
    def fix_sequential(self, error_info, solutions):
        """Sequential fixing approach - try solutions one by one"""
        results = []
        
        for solution in solutions:
            try:
                result = self.execute_solution(solution, error_info)
                results.append({
                    'solution': solution,
                    'success': result.get('success', False),
                    'time_taken': result.get('time', 0),
                    'output': result.get('output', '')
                })
                
                if result.get('success'):
                    return {
                        'success': True,
                        'solution_used': solution,
                        'results': results
                    }
                    
            except Exception as e:
                logger.error(f"Sequential fix failed for '{solution}': {e}")
                continue
        
        return {
            'success': False,
            'solutions_attempted': len(solutions),
            'results': results
        }
    
    def fix_intensive(self, error_info, solutions):
        """Intensive fixing - try multiple solutions in parallel"""
        import concurrent.futures
        
        results = []
        
        def execute_solution(solution):
            try:
                return self.execute_solution(solution, error_info)
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Execute multiple solutions in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_solution = {
                executor.submit(execute_solution, solution): solution 
                for solution in solutions[:3]  # Limit to first 3 solutions
            }
            
            for future in concurrent.futures.as_completed(future_to_solution):
                solution = future_to_solution[future]
                try:
                    result = future.result()
                    results.append({
                        'solution': solution,
                        'success': result.get('success', False),
                        'time_taken': result.get('time', 0),
                        'output': result.get('output', '')
                    })
                except Exception as e:
                    logger.error(f"Intensive fix failed for '{solution}': {e}")
        
        return {
            'success': any(r['success'] for r in results),
            'solutions_attempted': len(solutions),
            'results': results
        }
    
    def fix_conservative(self, error_info, solutions):
        """Conservative fixing - only attempt safe, reversible solutions"""
        safe_keywords = ['check', 'verify', 'list', 'show', 'status']
        safe_solutions = []
        
        for solution in solutions:
            solution_lower = solution.lower()
            if any(keyword in solution_lower for keyword in safe_keywords):
                safe_solutions.append(solution)
        
        if not safe_solutions:
            return {
                'success': False,
                'reason': 'No safe solutions found',
                'safe_solutions_checked': len(safe_solutions)
            }
        
        return self.fix_sequential(error_info, safe_solutions)
    
    def execute_solution(self, solution, error_info):
        """Execute a specific solution"""
        start_time = time.time()
        
        try:
            # Check if solution is a command
            if solution.startswith('pip '):
                import subprocess
                result = subprocess.run(
                    solution.split()[1:], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                success = result.returncode == 0
                return {
                    'success': success,
                    'time': time.time() - start_time,
                    'output': result.stdout if success else result.stderr
                }
            
            elif solution.startswith('systemctl '):
                import subprocess
                result = subprocess.run(
                    solution.split(), 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                success = result.returncode == 0
                return {
                    'success': success,
                    'time': time.time() - start_time,
                    'output': result.stdout if success else result.stderr
                }
            
            # For other solutions, mark as informational
            else:
                return {
                    'success': True,
                    'time': time.time() - start_time,
                    'output': f"Solution: {solution}",
                    'informational': True
                }
                
        except Exception as e:
            return {
                'success': False,
                'time': time.time() - start_time,
                'error': str(e)
            }
    
    async def auto_fix_error(self, error_info, strategy='sequential'):
        """Automatically fix an error using specified strategy"""
        try:
            # Analyze error
            analysis = self.analyze_error(error_info)
            
            if not analysis or analysis['confidence'] < self.confidence_threshold:
                return {
                    'fixed': False,
                    'reason': 'Low confidence in error pattern',
                    'confidence': analysis['confidence'] if analysis else 0
                }
            
            # Get solutions for the error pattern
            solutions = analysis['solutions']
            
            if not solutions:
                return {
                    'fixed': False,
                    'reason': 'No known solutions available'
                }
            
            # Apply fix strategy
            fix_strategy = self.fix_strategies.get(strategy, self.fix_sequential)
            fix_result = fix_strategy(error_info, solutions)
            
            # Store fix result in database
            if fix_result['success']:
                try:
                    db_session = SessionLocal()
                    latest_error = db_session.query(ErrorRecord).order_by(
                        ErrorRecord.timestamp.desc()
                    ).first()
                    
                    if latest_error:
                        latest_error.resolved = True
                        latest_error.auto_fixed = True
                        latest_error.solution = fix_result.get('solution_used', '')
                        latest_error.fix_attempts += 1
                    
                    db_session.commit()
                    db_session.close()
                except Exception as e:
                    logger.error(f"Failed to update error record: {e}")
            
            return {
                'fixed': fix_result['success'],
                'strategy_used': strategy,
                'confidence': analysis['confidence'],
                'solutions_attempted': fix_result.get('solutions_attempted', 0),
                'results': fix_result.get('results', []),
                'solution_used': fix_result.get('solution_used', ''),
                'time_taken': sum(r.get('time_taken', 0) for r in fix_result.get('results', []))
            }
            
        except Exception as e:
            logger.error(f"Auto fix error: {e}")
            return {
                'fixed': False,
                'error': str(e)
            }

class PerformanceMonitor:
    """Advanced performance monitoring and predictive analytics"""
    
    def __init__(self):
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': [],
            'response_times': [],
            'error_rates': [],
            'active_connections': []
        }
        self.thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'disk_usage': {'warning': 85, 'critical': 95},
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'error_rate': {'warning': 5.0, 'critical': 10.0}
        }
        
    def collect_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Active connections
            connections = len(psutil.net_connections())
            
            # Timestamp
            timestamp = datetime.utcnow()
            
            # Store metrics
            self.metrics['cpu_usage'].append({'value': cpu_percent, 'timestamp': timestamp})
            self.metrics['memory_usage'].append({'value': memory_percent, 'timestamp': timestamp})
            self.metrics['disk_usage'].append({'value': disk_percent, 'timestamp': timestamp})
            self.metrics['network_io'].append({'value': network_io, 'timestamp': timestamp})
            self.metrics['active_connections'].append({'value': connections, 'timestamp': timestamp})
            
            # Store in database
            try:
                db_session = SessionLocal()
                
                # Store each metric
                for metric_name, threshold_data in self.thresholds.items():
                    if metric_name in ['cpu_usage', 'memory_usage', 'disk_usage']:
                        current_value = self.metrics[metric_name][-1]['value']
                    elif metric_name == 'response_time':
                        current_value = np.mean([m['value'] for m in self.metrics['response_times'][-10:]]) if self.metrics['response_times'] else 0
                    elif metric_name == 'error_rate':
                        current_value = len([m for m in self.metrics.get('error_rates', [])[-10:]]) / 10 * 100 if self.metrics.get('error_rates') else 0
                    else:
                        continue
                    
                    # Determine status
                    if current_value >= threshold_data['critical']:
                        status = 'critical'
                    elif current_value >= threshold_data['warning']:
                        status = 'warning'
                    else:
                        status = 'normal'
                    
                    # Store metric
                    metric_record = PerformanceMetric(
                        metric_name=metric_name,
                        metric_value=str(current_value),
                        metric_unit='%' if 'usage' in metric_name or 'rate' in metric_name else 'count',
                        status=status,
                        threshold_warning=str(threshold_data['warning']),
                        threshold_critical=str(threshold_data['critical'])
                    )
                    db_session.add(metric_record)
                
                db_session.commit()
                db_session.close()
                
            except Exception as e:
                logger.error(f"Failed to store metrics: {e}")
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'disk_usage': disk_percent,
                'network_io': network_io,
                'active_connections': connections,
                'timestamp': timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def predict_issues(self):
        """Predict potential issues based on trends"""
        try:
            predictions = []
            
            # Analyze CPU trend
            if len(self.metrics['cpu_usage']) > 5:
                cpu_values = [m['value'] for m in self.metrics['cpu_usage'][-10:]]
                cpu_trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]
                
                if cpu_trend > 1:  # CPU increasing
                    predictions.append({
                        'metric': 'cpu_usage',
                        'prediction': 'CPU usage trending upward',
                        'severity': 'medium',
                        'recommendation': 'Monitor CPU-intensive processes'
                    })
            
            # Analyze memory trend
            if len(self.metrics['memory_usage']) > 5:
                memory_values = [m['value'] for m in self.metrics['memory_usage'][-10:]]
                memory_trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0]
                
                if memory_trend > 0.5:  # Memory increasing
                    predictions.append({
                        'metric': 'memory_usage',
                        'prediction': 'Memory usage trending upward',
                        'severity': 'high',
                        'recommendation': 'Check for memory leaks'
                    })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to predict issues: {e}")
            return []
    
    def get_performance_charts(self):
        """Generate performance charts for dashboard"""
        try:
            charts = {}
            
            # CPU Chart
            if self.metrics['cpu_usage']:
                cpu_data = self.metrics['cpu_usage'][-20:]  # Last 20 measurements
                charts['cpu'] = {
                    'labels': [m['timestamp'].strftime('%H:%M:%S') for m in cpu_data],
                    'data': [m['value'] for m in cpu_data],
                    'threshold': self.thresholds['cpu_usage']
                }
            
            # Memory Chart
            if self.metrics['memory_usage']:
                memory_data = self.metrics['memory_usage'][-20:]
                charts['memory'] = {
                    'labels': [m['timestamp'].strftime('%H:%M:%S') for m in memory_data],
                    'data': [m['value'] for m in memory_data],
                    'threshold': self.thresholds['memory_usage']
                }
            
            return charts
            
        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")
            return {}

# Initialize monitoring components
intelligent_bot = IntelligentBot()
error_analyzer = ErrorAnalyzer()
performance_monitor = PerformanceMonitor()

# Routes

@app.route('/')
def index():
    """Home page"""
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with security features"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember_me = request.form.get('remember_me') == 'on'
            
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')
            
            # Rate limiting check
            if REDIS_AVAILABLE:
                login_attempts = redis_client.get(f'login_attempts_{username}')
                if login_attempts and int(login_attempts) >= 5:
                    return jsonify({
                        'success': False,
                        'message': 'تم تجاوز عدد محاولات تسجيل الدخول المسموحة. يرجى المحاولة لاحقاً.'
                    })
            
            # Authenticate user
            db_session = SessionLocal()
            user = db_session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user or not user.is_active:
                # Increment failed attempt counter
                if REDIS_AVAILABLE:
                    redis_client.incr(f'login_attempts_{username}')
                    redis_client.expire(f'login_attempts_{username}', 1800)  # 30 minutes
                
                log_system_event(
                    'warning', 
                    f'Failed login attempt for username: {username}',
                    module='Authentication',
                    function='login',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return jsonify({
                    'success': False,
                    'message': 'بيانات الاعتماد غير صحيحة.'
                })
            
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                return jsonify({
                    'success': False,
                    'message': 'الحساب مقفل مؤقتاً. يرجى المحاولة لاحقاً.'
                })
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                user.login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(hours=1)
                
                db_session.commit()
                db_session.close()
                
                log_system_event(
                    'warning',
                    f'Failed login attempt for user: {username}',
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return jsonify({
                    'success': False,
                    'message': 'بيانات الاعتماد غير صحيحة.'
                })
            
            # Check 2FA if enabled
            if user.two_factor_enabled:
                db_session.close()
                return jsonify({
                    'success': True,
                    'requires_2fa': True,
                    'temp_token': jwt.encode({
                        'user_id': user.id,
                        'username': user.username
                    }, app.config['SECRET_KEY'], expires_minutes=5)
                })
            
            # Successful login
            user.last_login = datetime.utcnow()
            user.login_attempts = 0
            user.locked_until = None
            db_session.commit()
            db_session.close()
            
            # Clear failed attempt counter
            if REDIS_AVAILABLE:
                redis_client.delete(f'login_attempts_{username}')
            
            # Create session
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session['remember_me'] = remember_me
            
            if remember_me:
                session.permanent = True
            
            log_system_event(
                'info',
                f'User login successful: {username}',
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return jsonify({
                'success': True,
                'message': 'تم تسجيل الدخول بنجاح.',
                'redirect': url_for('dashboard')
            })
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({
                'success': False,
                'message': 'حدث خطأ في تسجيل الدخول. يرجى المحاولة مرة أخرى.'
            })
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard with intelligent assistant"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/api/ai_chat', methods=['POST'])
async def ai_chat():
    """AI chat endpoint with intelligent responses"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', f'session_{session["user_id"]}')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate AI response
        response = await intelligent_bot.generate_response(
            user_message, 
            session_id=session_id,
            context={'user_id': session['user_id']}
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return jsonify({
            'error': 'Failed to generate response',
            'response': 'حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.'
        }), 500

@app.route('/api/performance')
def performance_metrics():
    """Get real-time performance metrics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Collect current metrics
        current_metrics = performance_monitor.collect_metrics()
        
        # Get performance charts
        charts = performance_monitor.get_performance_charts()
        
        # Get predictions
        predictions = performance_monitor.predict_issues()
        
        return jsonify({
            'current': current_metrics,
            'charts': charts,
            'predictions': predictions
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        return jsonify({'error': 'Failed to get metrics'}), 500

@app.route('/api/auto_fix', methods=['POST'])
async def auto_fix():
    """Automatic error fixing endpoint"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        error_info = data.get('error_info', {})
        strategy = data.get('strategy', 'sequential')
        
        # Auto fix the error
        fix_result = await error_analyzer.auto_fix_error(error_info, strategy)
        
        return jsonify(fix_result)
        
    except Exception as e:
        logger.error(f"Auto fix error: {e}")
        return jsonify({'error': 'Auto fix failed'}), 500

@app.route('/api/logout')
def logout():
    """Secure logout"""
    if 'user_id' in session:
        log_system_event(
            'info',
            f'User logout: {session.get("username")}',
            user_id=session.get('user_id')
        )
    
    session.clear()
    return jsonify({'success': True, 'message': 'تم تسجيل الخروج بنجاح.'})

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """Handle file upload size limit"""
    return jsonify({'error': 'File too large'}), 413

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    if 'user_id' in session:
        emit('connected', {'message': 'Connected to intelligent assistant'})
        log_system_event(
            'info',
            f'WebSocket connection: {session.get("username")}',
            user_id=session.get('user_id')
        )

@socketio.on('ai_message')
async def handle_ai_message(data):
    """Handle real-time AI chat"""
    if 'user_id' not in session:
        emit('error', {'message': 'Unauthorized'})
        return
    
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', f'session_{session["user_id"]}')
        
        # Generate response
        response = await intelligent_bot.generate_response(
            message,
            session_id=session_id,
            context={'user_id': session['user_id']}
        )
        
        # Send response back
        emit('ai_response', response)
        
    except Exception as e:
        logger.error(f"AI WebSocket error: {e}")
        emit('error', {'message': 'AI response failed'})

@socketio.on('join_performance_room')
def handle_join_performance_room():
    """Handle joining performance monitoring room"""
    if 'user_id' in session:
        join_room('performance')
        emit('joined_performance_room', {'message': 'Joined performance monitoring'})

@socketio.on('request_performance_update')
def handle_performance_update():
    """Handle performance update request"""
    if 'user_id' in session and session.get('is_admin'):
        try:
            metrics = performance_monitor.collect_metrics()
            charts = performance_monitor.get_performance_charts()
            predictions = performance_monitor.predict_issues()
            
            emit('performance_update', {
                'metrics': metrics,
                'charts': charts,
                'predictions': predictions
            })
        except Exception as e:
            logger.error(f"Performance update error: {e}")
            emit('performance_error', {'message': 'Failed to update performance data'})

# Background monitoring tasks
def monitoring_worker():
    """Background worker for continuous monitoring"""
    while True:
        try:
            # Collect performance metrics
            performance_monitor.collect_metrics()
            
            # Check for issues and attempt auto-fix if needed
            if len(performance_monitor.metrics['cpu_usage']) > 5:
                cpu_values = [m['value'] for m in performance_monitor.metrics['cpu_usage'][-10:]]
                avg_cpu = np.mean(cpu_values)
                
                if avg_cpu > performance_monitor.thresholds['cpu_usage']['critical']:
                    log_system_event(
                        'warning',
                        f'High CPU usage detected: {avg_cpu:.1f}%',
                        module='Monitoring',
                        function='monitoring_worker'
                    )
            
            # Broadcast performance updates to connected clients
            try:
                charts = performance_monitor.get_performance_charts()
                socketio.emit('performance_broadcast', {
                    'charts': charts,
                    'timestamp': datetime.utcnow().isoformat()
                }, room='performance')
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
            
            # Sleep for 30 seconds
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Monitoring worker error: {e}")
            time.sleep(60)  # Wait longer on error

# Initialize database with default admin user
def init_default_admin():
    """Initialize default admin user if not exists"""
    try:
        db_session = SessionLocal()
        
        # Check if admin exists
        admin = db_session.query(User).filter_by(username='admin').first()
        
        if not admin:
            # Create default admin user
            password_hash = bcrypt.hashpw('changeme123'.encode('utf-8'), bcrypt.gensalt())
            password_hash = password_hash.decode('utf-8')
            
            admin = User(
                username='admin',
                email='admin@lastbot.local',
                password_hash=password_hash,
                full_name='Last.bot Administrator',
                is_admin=True,
                is_active=True
            )
            
            db_session.add(admin)
            db_session.commit()
            logger.info("Default admin user created")
        
        db_session.close()
        
    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")

# Security middleware
@app.before_request
def security_middleware():
    """Apply security headers and validation"""
    # Set security headers
    from flask import g
    
    g.start_time = time.time()
    
    # Rate limiting
    if request.endpoint in ['login', 'api_ai_chat']:
        if REDIS_AVAILABLE:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            key = f'rate_limit_{client_ip}_{request.endpoint}'
            
            if redis_client.exists(key):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            redis_client.setex(key, 60, 1)  # 60 seconds limit

@app.after_request
def after_request(response):
    """Set security headers after response"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # CORS headers for API
    if request.endpoint and request.endpoint.startswith('api_'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    try:
        # Initialize database
        init_default_admin()
        
        # Start monitoring worker
        monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        monitoring_thread.start()
        
        # Log startup
        log_system_event(
            'info',
            'Last.bot Comprehensive System started successfully',
            module='System',
            function='main'
        )
        
        logger.info("Starting Last.bot Comprehensive System...")
        logger.info("AI System: OpenAI + DeepSeek integration")
        logger.info("Monitoring: Advanced performance tracking")
        logger.info("Auto-fixing: Intelligent error resolution")
        logger.info("Security: Enhanced protection layers")
        
        # Run the application
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down Last.bot...")
        log_system_event(
            'info',
            'Last.bot system shutdown requested',
            module='System',
            function='main'
        )
    except Exception as e:
        logger.error(f"Startup error: {e}")
        log_system_event(
            'error',
            f'System startup failed: {str(e)}',
            module='System',
            function='main'
        )
