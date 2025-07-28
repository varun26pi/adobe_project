from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import fitz  # PyMuPDF
import pdfplumber
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import json
import io
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Load NLP models (will be loaded on startup)
nlp = None
tfidf_vectorizer = None

def load_models():
    global nlp, tfidf_vectorizer
    try:
        # Load spaCy model (download if not available)
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logging.info("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
        
        # Initialize TfidfVectorizer
        tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        logging.info("Models loaded successfully")
    except Exception as e:
        logging.error(f"Error loading models: {e}")

# Define Models
class HeadingInfo(BaseModel):
    level: str
    text: str
    page: int

class DocumentOutline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    outline: List[HeadingInfo]
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SectionInfo(BaseModel):
    document: str
    page_number: int
    section_title: str
    importance_rank: int

class SubSectionInfo(BaseModel):
    document: str
    refined_text: str
    page_number: int

class PersonaAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    persona: str
    job_to_be_done: str
    input_documents: List[str]
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    extracted_sections: List[SectionInfo]
    sub_section_analysis: List[SubSectionInfo]

class PersonaRequest(BaseModel):
    persona: str
    job_to_be_done: str
    document_ids: List[str]

class PDFProcessor:
    @staticmethod
    def extract_title_and_outline(pdf_bytes: bytes, filename: str) -> DocumentOutline:
        """Extract title and heading outline from PDF"""
        try:
            # Open PDF with PyMuPDF for structure analysis
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract title from first page
            title = PDFProcessor._extract_title(doc)
            
            # Extract headings
            outline = PDFProcessor._extract_headings(doc)
            
            doc.close()
            
            return DocumentOutline(
                title=title,
                outline=outline,
                filename=filename
            )
            
        except Exception as e:
            logging.error(f"Error processing PDF {filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    
    @staticmethod
    def _extract_title(doc) -> str:
        """Extract title using multiple heuristics"""
        title_candidates = []
        
        # Get first page
        page = doc[0]
        blocks = page.get_text("dict")["blocks"]
        
        # Look for text blocks in upper portion of first page
        for block in blocks[:5]:  # Check first 5 blocks
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        font_size = span["size"]
                        
                        # Title heuristics
                        if (len(text) > 10 and len(text) < 200 and 
                            font_size > 14 and
                            not text.lower().startswith(('abstract', 'introduction', 'chapter'))):
                            title_candidates.append((text, font_size, span["bbox"][1]))  # y-coordinate
        
        # Sort by font size and position (higher on page = lower y-coordinate)
        if title_candidates:
            title_candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
            return title_candidates[0][0]
        
        # Fallback: use metadata or filename
        title = doc.metadata.get('title', '')
        if title and len(title) > 3:
            return title
        
        return "Untitled Document"
    
    @staticmethod
    def _extract_headings(doc) -> List[HeadingInfo]:
        """Extract headings with intelligent level detection"""
        headings = []
        font_sizes = []
        
        # First pass: collect all text with font sizes
        text_elements = []
        
        for page_num, page in enumerate(doc, 1):
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        line_size = 0
                        line_bold = False
                        
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                line_text += text + " "
                                line_size = max(line_size, span["size"])
                                if span["flags"] & 2**4:  # Bold flag
                                    line_bold = True
                        
                        line_text = line_text.strip()
                        if line_text and len(line_text) > 3:
                            text_elements.append({
                                'text': line_text,
                                'size': line_size,
                                'bold': line_bold,
                                'page': page_num,
                                'bbox': line["bbox"]
                            })
                            font_sizes.append(line_size)
        
        # Determine font size thresholds
        if not font_sizes:
            return headings
        
        font_sizes = sorted(set(font_sizes), reverse=True)
        
        # Create thresholds for heading levels
        if len(font_sizes) >= 4:
            h1_threshold = font_sizes[1]  # Second largest (largest might be title)
            h2_threshold = font_sizes[2]
            h3_threshold = font_sizes[3]
        elif len(font_sizes) >= 3:
            h1_threshold = font_sizes[0]
            h2_threshold = font_sizes[1]
            h3_threshold = font_sizes[2]
        else:
            # Use median as threshold
            median_size = np.median(font_sizes)
            h1_threshold = median_size + 2
            h2_threshold = median_size + 1
            h3_threshold = median_size
        
        # Second pass: identify headings
        for element in text_elements:
            text = element['text']
            size = element['size']
            
            # Skip very long lines (likely paragraphs)
            if len(text) > 150:
                continue
            
            # Heading patterns
            is_heading = (
                # Size-based
                size >= h3_threshold or
                # Pattern-based
                re.match(r'^\d+\.?\s+[A-Z]', text) or  # "1. Introduction" or "1 Introduction"
                re.match(r'^[A-Z][A-Z\s]+$', text) or  # "INTRODUCTION"
                re.match(r'^Chapter\s+\d+', text, re.IGNORECASE) or  # "Chapter 1"
                (element['bold'] and len(text) < 100) or  # Bold and short
                re.match(r'^\d+\.\d+\.?\s+', text)  # "1.1 Subsection"
            )
            
            if is_heading:
                # Determine level
                if size >= h1_threshold or re.match(r'^\d+\.?\s+[A-Z]', text):
                    level = "H1"
                elif size >= h2_threshold or re.match(r'^\d+\.\d+\.?\s+', text):
                    level = "H2"
                else:
                    level = "H3"
                
                # Clean up text
                clean_text = re.sub(r'^\d+\.?\s*', '', text)
                clean_text = re.sub(r'^\d+\.\d+\.?\s*', '', clean_text)
                clean_text = clean_text.strip()
                
                if clean_text:
                    headings.append(HeadingInfo(
                        level=level,
                        text=clean_text,
                        page=element['page']
                    ))
        
        return headings

class PersonaProcessor:
    @staticmethod
    async def analyze_documents(persona: str, job_to_be_done: str, document_ids: List[str]) -> PersonaAnalysis:
        """Analyze documents based on persona and job requirements"""
        try:
            # Get documents from database
            documents = []
            for doc_id in document_ids:
                doc = await db.document_outlines.find_one({"id": doc_id})
                if doc:
                    documents.append(doc)
            
            if not documents:
                raise HTTPException(status_code=404, detail="No documents found")
            
            # Analyze relevance and extract sections
            extracted_sections, sub_sections = PersonaProcessor._extract_relevant_sections(
                documents, persona, job_to_be_done
            )
            
            return PersonaAnalysis(
                persona=persona,
                job_to_be_done=job_to_be_done,
                input_documents=[doc["filename"] for doc in documents],
                extracted_sections=extracted_sections,
                sub_section_analysis=sub_sections
            )
            
        except Exception as e:
            logging.error(f"Error in persona analysis: {e}")
            raise HTTPException(status_code=400, detail=f"Error analyzing documents: {str(e)}")
    
    @staticmethod
    def _extract_relevant_sections(documents: List[Dict], persona: str, job_to_be_done: str) -> tuple:
        """Extract and rank sections based on persona and job"""
        global tfidf_vectorizer
        
        if not tfidf_vectorizer:
            raise HTTPException(status_code=500, detail="TFIDF vectorizer not loaded")
        
        # Collect all section texts
        all_texts = []
        section_info = []
        
        # Add job description as the query
        query_text = f"{persona} {job_to_be_done}"
        all_texts.append(query_text)
        
        # Add all section texts
        for doc in documents:
            outline = doc.get("outline", [])
            for heading in outline:
                section_text = heading['text']
                all_texts.append(section_text)
                section_info.append({
                    'document': doc['filename'],
                    'section': heading,
                    'text': section_text
                })
        
        if len(all_texts) <= 1:  # Only query, no sections
            return [], []
        
        # Create TF-IDF vectors
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
        except ValueError:
            # If fit_transform fails, create a new vectorizer
            tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
        
        # Calculate similarity between query and all sections
        query_vector = tfidf_matrix[0]  # First item is the query
        section_vectors = tfidf_matrix[1:]  # Rest are sections
        
        similarities = cosine_similarity(query_vector, section_vectors).flatten()
        
        # Score sections
        section_scores = []
        for i, (similarity, info) in enumerate(zip(similarities, section_info)):
            # Bonus scoring for keywords
            keyword_bonus = PersonaProcessor._calculate_keyword_bonus(
                info['text'], persona, job_to_be_done
            )
            
            final_score = similarity + keyword_bonus
            section_scores.append({
                'document': info['document'],
                'section': info['section'],
                'score': final_score
            })
        
        # Sort by score and select top sections
        section_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Create extracted sections (top 10)
        extracted_sections = []
        for i, item in enumerate(section_scores[:10]):
            extracted_sections.append(SectionInfo(
                document=item['document'],
                page_number=item['section']['page'],
                section_title=item['section']['text'],
                importance_rank=i + 1
            ))
        
        # Create sub-section analysis (top 5 with refined text)
        sub_sections = []
        for i, item in enumerate(section_scores[:5]):
            refined_text = PersonaProcessor._refine_section_text(
                item['section']['text'], persona, job_to_be_done
            )
            sub_sections.append(SubSectionInfo(
                document=item['document'],
                refined_text=refined_text,
                page_number=item['section']['page']
            ))
        
        return extracted_sections, sub_sections
    
    @staticmethod
    def _calculate_keyword_bonus(text: str, persona: str, job: str) -> float:
        """Calculate bonus score based on keyword matches"""
        text_lower = text.lower()
        persona_lower = persona.lower()
        job_lower = job.lower()
        
        bonus = 0.0
        
        # Persona-specific keywords
        persona_keywords = persona_lower.split()
        for keyword in persona_keywords:
            if keyword in text_lower:
                bonus += 0.1
        
        # Job-specific keywords
        job_keywords = job_lower.split()
        for keyword in job_keywords:
            if keyword in text_lower:
                bonus += 0.15
        
        return min(bonus, 0.5)  # Cap bonus at 0.5
    
    @staticmethod
    def _refine_section_text(section_text: str, persona: str, job: str) -> str:
        """Refine section text based on persona and job"""
        # Simple refinement - in a real system, this could use more sophisticated NLP
        return f"[{persona}] {section_text} - Relevant for: {job}"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "PDF Document Intelligence API"}

@api_router.post("/upload-pdf", response_model=DocumentOutline)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF for outline extraction"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content
    pdf_bytes = await file.read()
    
    # Process PDF
    outline = PDFProcessor.extract_title_and_outline(pdf_bytes, file.filename)
    
    # Store in database
    await db.document_outlines.insert_one(outline.dict())
    
    return outline

@api_router.get("/documents", response_model=List[DocumentOutline])
async def get_documents():
    """Get all processed documents"""
    documents = await db.document_outlines.find().to_list(100)
    return [DocumentOutline(**doc) for doc in documents]

@api_router.post("/analyze-persona", response_model=PersonaAnalysis)
async def analyze_persona(request: PersonaRequest):
    """Analyze documents based on persona and job-to-be-done"""
    analysis = await PersonaProcessor.analyze_documents(
        request.persona,
        request.job_to_be_done,
        request.document_ids
    )
    
    # Store analysis in database
    await db.persona_analyses.insert_one(analysis.dict())
    
    return analysis

@api_router.get("/analyses", response_model=List[PersonaAnalysis])
async def get_analyses():
    """Get all persona analyses"""
    analyses = await db.persona_analyses.find().to_list(100)
    return [PersonaAnalysis(**analysis) for analysis in analyses]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    load_models()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()