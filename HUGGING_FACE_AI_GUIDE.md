# Hugging Face AI Integration Guide

## Overview

This project uses **Hugging Face Sentence Transformers** to provide AI-powered job recommendations based on resume analysis. The system uses semantic similarity to match user resumes with job descriptions, providing more accurate and intelligent recommendations than traditional keyword matching.

---

## Libraries Used

### 1. **sentence-transformers** (Primary Library)
- **Version**: `2.2.2`
- **Purpose**: Provides pre-trained models for generating semantic embeddings
- **What it does**: Converts text (resumes and job descriptions) into numerical vectors that capture semantic meaning
- **Key Features**:
  - Pre-trained models optimized for semantic similarity
  - Easy-to-use API for encoding text
  - Built on top of PyTorch and Transformers

### 2. **torch** (PyTorch)
- **Version**: `>=2.0.0`
- **Purpose**: Deep learning framework (backend for sentence-transformers)
- **What it does**: Provides the computational engine for neural network operations
- **Why needed**: sentence-transformers uses PyTorch under the hood for model inference

### 3. **scikit-learn**
- **Version**: `>=1.3.0`
- **Purpose**: Machine learning utilities (used for similarity calculations)
- **What it does**: Provides efficient implementations of similarity metrics and nearest neighbor algorithms
- **Usage**: Used for cosine similarity calculations and distance metrics

### 4. **numpy**
- **Version**: `>=1.24.0`
- **Purpose**: Numerical computing library
- **What it does**: Handles array operations and mathematical computations
- **Why needed**: Embeddings are stored as NumPy arrays for efficient computation

### 5. **pandas**
- **Version**: `>=2.0.0`
- **Purpose**: Data manipulation and analysis
- **What it does**: Helps organize and process job data (though minimal usage in current implementation)
- **Note**: Included for potential future data processing needs

---

## How It Works: Step-by-Step

### Step 1: Model Loading
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
```

**What happens:**
- Downloads the pre-trained model from Hugging Face Hub (first time only)
- Loads the model into memory (~420MB)
- Model is cached locally for future use
- The model understands semantic relationships between words and sentences

**Model Details:**
- **Model Name**: `all-mpnet-base-v2`
- **Type**: MPNet (Masked and Permuted Pre-training for Language Understanding)
- **Size**: ~420MB
- **Capabilities**: 
  - Understands context and meaning
  - Handles synonyms and related concepts
  - Works with sentences and paragraphs

### Step 2: Resume Text Extraction

```python
from PyPDF2 import PdfReader
import docx

# Extract text from PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

# Extract text from DOCX
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])
```

**What happens:**
- Reads the uploaded resume file (PDF or DOCX)
- Extracts all text content
- Combines all text into a single string
- This text represents the user's skills, experience, and qualifications

### Step 3: Job Description Preparation

```python
def prepare_job_corpus(job):
    """Combine job fields into a single text corpus"""
    parts = []
    if job.title:
        parts.append(str(job.title))
    if job.company.name:
        parts.append(str(job.company.name))
    if job.location:
        parts.append(str(job.location))
    if job.description:
        parts.append(str(job.description))
    if job.skills_required:
        parts.append(" ".join(str(s) for s in job.skills_required))
    return " . ".join(parts)
```

**What happens:**
- Combines all relevant job information into one text string
- Includes: title, company, location, description, required skills
- Creates a comprehensive representation of the job
- This corpus will be converted to an embedding

### Step 4: Creating Embeddings

```python
# Encode resume text
resume_embedding = model.encode(resume_text, convert_to_tensor=True)

# Encode all job descriptions
job_embeddings = model.encode(job_corpus_texts, convert_to_tensor=True, show_progress_bar=True)
```

**What happens:**
- **Resume Embedding**: Converts resume text into a 768-dimensional vector
- **Job Embeddings**: Converts all job descriptions into vectors (batch processing)
- Each vector captures the semantic meaning of the text
- Similar meanings result in similar vectors (close in vector space)

**Vector Properties:**
- **Dimension**: 768 numbers (for all-mpnet-base-v2)
- **Type**: Floating point numbers
- **Meaning**: Each number represents some aspect of the text's meaning
- **Similarity**: Vectors with similar meanings are "close" in 768-dimensional space

### Step 5: Calculating Similarity

```python
from sentence_transformers import util

# Calculate cosine similarity
cos_scores = util.cos_sim(resume_embedding, job_embeddings)[0]

# Get top matches
top_indices = np.argsort(-cos_scores)[:top_k]
```

**What happens:**
- **Cosine Similarity**: Measures the angle between two vectors
- **Range**: -1 to 1 (we use 0 to 1, where 1 = identical, 0 = unrelated)
- **Interpretation**: 
  - 0.9+ = Very strong match
  - 0.7-0.9 = Good match
  - 0.5-0.7 = Moderate match
  - 0.3-0.5 = Weak match
  - <0.3 = Poor match (filtered out)

**Why Cosine Similarity?**
- Measures semantic similarity, not just word overlap
- Works well with high-dimensional vectors
- Normalized (not affected by text length)

### Step 6: Ranking and Filtering

```python
# Filter by similarity threshold (30%)
for idx in top_indices:
    score = float(cos_scores[idx])
    if score > 0.3:  # 30% similarity threshold
        results.append({
            'job': jobs_list[idx],
            'score': score,
            'match_percentage': round(score * 100, 2)
        })
```

**What happens:**
- Sorts jobs by similarity score (highest first)
- Filters out jobs with <30% similarity
- Returns top N recommendations (default: 10)
- Each recommendation includes the job and match percentage

---

## Architecture Flow

```
User Uploads Resume
        ↓
Extract Text (PDF/DOCX)
        ↓
Encode Resume → [768-dim vector]
        ↓
Load/Cache Job Embeddings
        ↓
Calculate Cosine Similarity
        ↓
Rank by Similarity Score
        ↓
Filter (score > 0.3)
        ↓
Return Top Recommendations
```

---

## Key Concepts Explained

### 1. **Semantic Embeddings**

**Traditional Keyword Matching:**
- "Python developer" matches "Python developer" (exact match)
- "Python developer" doesn't match "Python programmer" (different word)

**Semantic Embeddings:**
- "Python developer" and "Python programmer" are close in vector space
- "Software engineer" and "Developer" are similar
- Understands context and meaning, not just words

### 2. **Vector Space**

Think of embeddings as points in a 768-dimensional space:
- Similar texts are close together
- Different texts are far apart
- Distance = similarity measure

### 3. **Model Training**

The model was pre-trained on millions of text pairs:
- Learned to understand language semantics
- Understands synonyms, context, and relationships
- No training needed in this project (uses pre-trained model)

---

## Code Structure

### Main Module: `jobs/ai_recommender.py`

**Key Functions:**

1. **`get_model()`**
   - Loads or retrieves the cached model
   - Singleton pattern (loads once, reuses)

2. **`extract_text_from_resume(resume_file)`**
   - Handles PDF and DOCX extraction
   - Returns plain text string

3. **`prepare_job_corpus(job)`**
   - Combines job fields into text
   - Creates comprehensive job representation

4. **`get_job_embeddings(jobs_queryset)`**
   - Computes embeddings for all jobs
   - Caches results for 1 hour
   - Returns embeddings and job list

5. **`recommend_jobs_from_resume(resume_file, user, top_k)`**
   - Main recommendation function
   - Orchestrates the entire process
   - Returns list of recommended jobs with scores

---

## Performance Optimizations

### 1. **Model Caching**
- Model loaded once and reused
- Stored in global variable `_model`
- Avoids reloading on every request

### 2. **Embedding Caching**
- Job embeddings computed once
- Cached for 1 hour using Django cache
- Cache key based on job count and latest update time

### 3. **Batch Processing**
- All jobs encoded in one batch
- More efficient than one-by-one encoding
- Uses GPU if available (automatic)

### 4. **Tensor Operations**
- Uses PyTorch tensors for fast computation
- GPU acceleration when available
- Efficient similarity calculations

---

## Configuration

### Settings (`job_portal/settings.py`)

```python
AI_RECOMMENDATION_MODEL = 'sentence-transformers/all-mpnet-base-v2'
```

**Available Models:**

1. **`all-mpnet-base-v2`** (Default)
   - Best accuracy
   - 768 dimensions
   - ~420MB
   - Recommended for production

2. **`all-MiniLM-L6-v2`**
   - Faster, smaller
   - 384 dimensions
   - ~90MB
   - Good for development/testing

3. **`paraphrase-multilingual-mpnet-base-v2`**
   - Multilingual support
   - 768 dimensions
   - ~420MB
   - Use if you need multiple languages

---

## Example Usage

### In Django View

```python
from jobs.ai_recommender import recommend_jobs_from_resume

# When user uploads resume
profile = user.job_seeker_profile
if profile.resume:
    recommendations = recommend_jobs_from_resume(
        resume_file=profile.resume,
        user=user,
        top_k=10
    )
    
    # Each recommendation contains:
    # - job: Job model instance
    # - score: Similarity score (0-1)
    # - match_percentage: Percentage (0-100)
```

### Direct Function Call

```python
from jobs.ai_recommender import recommend_jobs_from_text

# If you already have resume text
resume_text = "Software engineer with 5 years Python experience..."
recommendations = recommend_jobs_from_text(
    resume_text=resume_text,
    user=user,
    top_k=5
)
```

---

## Advantages Over Rule-Based Matching

### Rule-Based (Old System)
- ❌ Exact keyword matching only
- ❌ Doesn't understand synonyms
- ❌ Misses related concepts
- ❌ Requires manual weight tuning
- ✅ Fast and simple

### AI-Powered (New System)
- ✅ Understands semantic meaning
- ✅ Handles synonyms and variations
- ✅ Captures related concepts
- ✅ Learns from pre-training
- ✅ More accurate matching
- ⚠️ Requires more resources

---

## Limitations and Considerations

### 1. **Resource Requirements**
- Model size: ~420MB
- Memory: ~500MB+ during inference
- First load: 1-2 minutes (download)
- Subsequent: Instant (cached)

### 2. **Processing Time**
- Resume encoding: <1 second
- Job encoding: ~1-2 seconds per 100 jobs
- Similarity calculation: <1 second
- Total: 2-5 seconds for 100 jobs

### 3. **Accuracy**
- Works best with detailed resumes
- Requires meaningful job descriptions
- May not capture very specific technical requirements
- Best for general skill matching

### 4. **Language**
- Default model: English only
- Use multilingual model for other languages
- May not work well with mixed languages

---

## Troubleshooting

### Model Download Issues
```python
# Check internet connection
# Verify Hugging Face Hub access
# Try smaller model: 'all-MiniLM-L6-v2'
```

### Memory Errors
```python
# Use smaller model
# Process fewer jobs at once
# Increase system RAM
```

### Slow Performance
```python
# Enable GPU if available (automatic)
# Use smaller model
# Reduce number of jobs processed
# Check cache is working
```

---

## Future Enhancements

### Potential Improvements:

1. **Fine-tuning**
   - Train model on job portal data
   - Better domain-specific understanding

2. **Multi-modal**
   - Include company images
   - Consider user preferences

3. **Real-time Updates**
   - Recompute when new jobs added
   - Update recommendations dynamically

4. **Explainability**
   - Show why job was recommended
   - Highlight matching skills/experience

5. **User Feedback Loop**
   - Learn from user interactions
   - Improve recommendations over time

---

## Summary

This project uses **Hugging Face Sentence Transformers** to provide intelligent job recommendations by:

1. **Converting text to vectors** using pre-trained AI models
2. **Measuring similarity** using cosine similarity
3. **Ranking jobs** by semantic match
4. **Providing accurate recommendations** based on meaning, not just keywords

The system is production-ready, cached for performance, and automatically falls back to rule-based recommendations if AI is unavailable.

---

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Model Hub](https://huggingface.co/models)
- [MPNet Paper](https://arxiv.org/abs/2004.09297)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)

