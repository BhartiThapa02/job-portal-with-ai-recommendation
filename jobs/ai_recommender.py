"""
AI-powered Job Recommendation System using Hugging Face Sentence Transformers
"""
import os
import numpy as np
from django.conf import settings
from django.core.cache import cache
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import docx
import logging

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model = None
_job_embeddings = None
_jobs_data = None


def get_model():
    """Get or load the sentence transformer model"""
    global _model
    if _model is None:
        model_name = getattr(settings, 'AI_RECOMMENDATION_MODEL', 'sentence-transformers/all-mpnet-base-v2')
        logger.info(f"Loading AI model: {model_name}")
        try:
            _model = SentenceTransformer(model_name)
            logger.info("AI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            raise
    return _model


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        text = []
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise


def extract_text_from_resume(resume_file):
    """
    Extract text from resume file (PDF, DOCX, or DOC)
    
    Args:
        resume_file: Django FileField or file path
        
    Returns:
        str: Extracted text from resume
    """
    # Handle Django FileField
    if hasattr(resume_file, 'path'):
        file_path = resume_file.path
    elif hasattr(resume_file, 'read'):
        # If it's an in-memory file, save temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp:
            for chunk in resume_file.chunks():
                tmp.write(chunk)
            file_path = tmp.name
    else:
        file_path = resume_file
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported resume file type: {ext}")
    
    # Clean up temporary file if created
    if hasattr(resume_file, 'read') and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except:
            pass
    
    return text


def prepare_job_corpus(job):
    """
    Combine job fields into a single text corpus for embedding
    
    Args:
        job: Job model instance
        
    Returns:
        str: Combined text from job fields
    """
    parts = []
    
    if job.title:
        parts.append(str(job.title))
    if hasattr(job, 'company') and job.company and job.company.name:
        parts.append(str(job.company.name))
    if job.location:
        parts.append(str(job.location))
    if job.description:
        parts.append(str(job.description))
    if job.skills_required:
        if isinstance(job.skills_required, list):
            parts.append(" ".join(str(s) for s in job.skills_required))
        else:
            parts.append(str(job.skills_required))
    if job.requirements:
        parts.append(str(job.requirements))
    
    return " . ".join(parts)


def get_job_embeddings(jobs_queryset, force_reload=False):
    """
    Get or compute embeddings for jobs
    
    Args:
        jobs_queryset: QuerySet of Job objects
        force_reload: Force recomputation of embeddings
        
    Returns:
        tuple: (embeddings, jobs_list)
    """
    global _job_embeddings, _jobs_data
    
    # Use cache key based on job count and latest update
    cache_key = f"job_embeddings_{jobs_queryset.count()}_{jobs_queryset.latest('updated_at').updated_at.timestamp() if jobs_queryset.exists() else 0}"
    
    if not force_reload:
        cached = cache.get(cache_key)
        if cached:
            _job_embeddings, _jobs_data = cached
            return _job_embeddings, _jobs_data
    
    model = get_model()
    
    # Prepare job corpus texts (queryset already filtered)
    jobs_list = list(jobs_queryset)
    corpus_texts = [prepare_job_corpus(job) for job in jobs_list]
    
    if not corpus_texts:
        return None, []
    
    logger.info(f"Encoding {len(corpus_texts)} job postings...")
    
    # Compute embeddings
    try:
        embeddings = model.encode(corpus_texts, convert_to_tensor=True, show_progress_bar=True)
        _job_embeddings = embeddings
        _jobs_data = jobs_list
        
        # Cache for 1 hour
        cache.set(cache_key, (embeddings, jobs_list), 3600)
        
        return embeddings, jobs_list
    except Exception as e:
        logger.error(f"Error computing job embeddings: {e}")
        raise


def recommend_jobs_from_resume(resume_file, user, top_k=10):
    """
    Recommend jobs based on resume content using AI
    
    Args:
        resume_file: Resume file (Django FileField)
        user: User instance
        top_k: Number of recommendations to return
        
    Returns:
        list: List of dicts with job and score information
    """
    from .models import Job
    from applications.models import Application
    
    try:
        # Extract text from resume
        logger.info(f"Extracting text from resume for user {user.email}")
        resume_text = extract_text_from_resume(resume_file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning("Resume text too short or empty")
            return []
        
        # Get active jobs (exclude expired jobs)
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()
        jobs_queryset = Job.objects.filter(is_active=True).filter(
            Q(deadline__isnull=True) | Q(deadline__gt=now)
        ).select_related('company')
        
        # Exclude jobs user already applied to
        applied_job_ids = Application.objects.filter(user=user).values_list('job_id', flat=True)
        jobs_queryset = jobs_queryset.exclude(id__in=applied_job_ids)
        
        if not jobs_queryset.exists():
            return []
        
        # Get job embeddings
        job_embeddings, jobs_list = get_job_embeddings(jobs_queryset)
        
        if job_embeddings is None or not jobs_list:
            return []
        
        # Get model and encode resume
        model = get_model()
        resume_emb = model.encode(resume_text, convert_to_tensor=True)
        
        # Compute cosine similarities
        cos_scores = util.cos_sim(resume_emb, job_embeddings)[0].cpu().numpy()
        
        # Get top indices
        top_idx = np.argsort(-cos_scores)[:top_k]
        
        # Build results
        results = []
        for idx in top_idx:
            job = jobs_list[idx]
            score = float(cos_scores[idx])
            
            # Only include jobs with score > 0.3 (30% similarity threshold)
            if score > 0.3:
                results.append({
                    'job': job,
                    'score': score,
                    'match_percentage': round(score * 100, 2)
                })
        
        logger.info(f"Generated {len(results)} AI recommendations for user {user.email}")
        
        # Save recommendations to database
        from .models import JobRecommendation
        for rec in results:
            JobRecommendation.objects.update_or_create(
                user=user,
                job=rec['job'],
                defaults={
                    'score': rec['score'] * 100,  # Convert to 0-100 scale for consistency
                    'reason': f"AI Match: {rec['match_percentage']}% similarity based on resume analysis"
                }
            )
        
        logger.info(f"Saved {len(results)} AI recommendations to database for user {user.email}")
        return results
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}", exc_info=True)
        return []


def recommend_jobs_from_text(resume_text, user, top_k=10):
    """
    Recommend jobs based on resume text (already extracted)
    
    Args:
        resume_text: Text content from resume
        user: User instance
        top_k: Number of recommendations to return
        
    Returns:
        list: List of dicts with job and score information
    """
    from .models import Job
    from applications.models import Application
    
    try:
        if not resume_text or len(resume_text.strip()) < 50:
            return []
        
        # Get active jobs (exclude expired jobs)
        from django.utils import timezone
        from django.db.models import Q
        now = timezone.now()
        jobs_queryset = Job.objects.filter(is_active=True).filter(
            Q(deadline__isnull=True) | Q(deadline__gt=now)
        ).select_related('company')
        
        # Exclude jobs user already applied to
        applied_job_ids = Application.objects.filter(user=user).values_list('job_id', flat=True)
        jobs_queryset = jobs_queryset.exclude(id__in=applied_job_ids)
        
        if not jobs_queryset.exists():
            return []
        
        # Get job embeddings
        job_embeddings, jobs_list = get_job_embeddings(jobs_queryset)
        
        if job_embeddings is None or not jobs_list:
            return []
        
        # Get model and encode resume text
        model = get_model()
        resume_emb = model.encode(resume_text, convert_to_tensor=True)
        
        # Compute cosine similarities
        cos_scores = util.cos_sim(resume_emb, job_embeddings)[0].cpu().numpy()
        
        # Get top indices
        top_idx = np.argsort(-cos_scores)[:top_k]
        
        # Build results
        results = []
        for idx in top_idx:
            job = jobs_list[idx]
            score = float(cos_scores[idx])
            
            if score > 0.3:  # 30% similarity threshold
                results.append({
                    'job': job,
                    'score': score,
                    'match_percentage': round(score * 100, 2)
                })
        
        # Save recommendations to database
        from .models import JobRecommendation
        for rec in results:
            JobRecommendation.objects.update_or_create(
                user=user,
                job=rec['job'],
                defaults={
                    'score': rec['score'] * 100,  # Convert to 0-100 scale for consistency
                    'reason': f"AI Match: {rec['match_percentage']}% similarity based on resume analysis"
                }
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations from text: {e}", exc_info=True)
        return []

