# AI & Recommendations System Documentation

## Current Implementation

### Job Recommendations System

The job recommendations feature now supports **both AI-powered and rule-based matching**:

1. **AI-Powered Recommendations** (Primary) - Uses Hugging Face Sentence Transformers
   - **Location**: `jobs/ai_recommender.py`
   - **Model**: `sentence-transformers/all-mpnet-base-v2` (configurable)
   - **When used**: When user has uploaded a resume
   - **How it works**:
     - Extracts text from uploaded resume (PDF/DOCX)
     - Uses sentence transformers to create embeddings of resume and job descriptions
     - Calculates cosine similarity between resume and jobs
     - Returns top matches with similarity scores

2. **Rule-Based Recommendations** (Fallback) - Traditional matching algorithm
   - **Location**: `jobs/utils.py`
   - **When used**: When user hasn't uploaded a resume or AI fails
   - **How it works**:
     - Calculates match scores based on weighted criteria:
       - Skills matching (40% weight)
       - Experience level matching (20% weight)
       - Location matching (15% weight)
       - Work mode preference (10% weight)
       - Education matching (10% weight)
       - Resume availability (5% weight)

## Hugging Face Integration

**Status**: ✅ **Now Integrated!**

This project now uses Hugging Face Sentence Transformers for AI-powered job recommendations.

### Dependencies
- `sentence-transformers==2.2.2`
- `torch>=2.0.0`
- `scikit-learn>=1.3.0`
- `numpy>=1.24.0`
- `pandas>=2.0.0`

### Model Configuration

The AI model can be configured in `settings.py`:
```python
AI_RECOMMENDATION_MODEL = 'sentence-transformers/all-mpnet-base-v2'
```

**Available Models:**
- `sentence-transformers/all-mpnet-base-v2` (default) - Best accuracy
- `sentence-transformers/all-MiniLM-L6-v2` - Faster, smaller
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` - Multilingual support

### How It Works

1. **Resume Upload**: When a user uploads a resume (PDF/DOCX), the system:
   - Extracts text from the resume
   - Generates AI recommendations automatically
   - Shows success message with recommendation count

2. **Recommendation Generation**:
   - Resume text is encoded into a vector embedding
   - All active job postings are encoded into embeddings
   - Cosine similarity is calculated between resume and jobs
   - Top matches (score > 0.3 or 30%) are returned

3. **Caching**: Job embeddings are cached for 1 hour to improve performance

### Features

- ✅ Automatic AI recommendations when resume is uploaded
- ✅ Semantic matching (understands meaning, not just keywords)
- ✅ Handles PDF and DOCX resume formats
- ✅ Excludes jobs user already applied to
- ✅ Shows match percentage scores
- ✅ Falls back to rule-based if AI unavailable
- ✅ Caching for performance

## Usage

### For Users

1. Upload your resume in the profile settings
2. AI recommendations are automatically generated
3. View recommendations at `/jobs/recommendations/`
4. Recommendations show match percentage based on resume analysis

### For Developers

```python
from jobs.ai_recommender import recommend_jobs_from_resume

# Get AI recommendations for a user's resume
recommendations = recommend_jobs_from_resume(
    resume_file=user.job_seeker_profile.resume,
    user=user,
    top_k=10
)

# Each recommendation contains:
# - job: Job model instance
# - score: Similarity score (0-1)
# - match_percentage: Percentage match (0-100)
```

## Performance Considerations

- **First Load**: Model download and initial encoding can take 1-2 minutes
- **Subsequent Loads**: Cached embeddings load instantly
- **Memory**: Model requires ~400MB RAM
- **CPU/GPU**: Works on CPU, faster on GPU if available

## Troubleshooting

### If AI recommendations don't work:

1. **Check dependencies**: Ensure all packages are installed
   ```bash
   pip install sentence-transformers torch scikit-learn numpy pandas
   ```

2. **Check logs**: Look for errors in Django logs
   - Model download issues
   - Memory errors
   - File extraction errors

3. **Fallback**: System automatically falls back to rule-based recommendations

## Summary

- **Hugging Face**: ✅ Now integrated and actively used
- **AI/ML Models**: ✅ Sentence Transformers for semantic matching
- **Recommendations**: Hybrid system (AI-first, rule-based fallback)
- **Status**: Production-ready with automatic fallback
