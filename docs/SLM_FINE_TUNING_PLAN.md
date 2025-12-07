# SLM Fine-Tuning Plan for Baguio City Sentiment Analysis

## Executive Summary

Fine-tune a **Small Language Model (SLM)** that runs entirely on your RTX 3050 laptop for domain-specific sentiment analysis. This approach enables local inference without cloud dependencies.

## Your Hardware

| Component | Spec | Status |
|-----------|------|--------|
| GPU | RTX 3050 (4GB VRAM) | ✅ Can run SLMs |
| RAM | 8GB | ⚠️ Tight, but workable |
| CPU | i5-12500H | ✅ Good |
| Storage | SSD | ✅ Good |

## 1. Model Selection

### 1.1 SLM Candidates for RTX 3050

| Model | Params | VRAM (Q4) | Quality | Taglish | Recommended |
|-------|--------|-----------|---------|---------|-------------|
| **Qwen2.5-1.5B-Instruct** | 1.5B | ~2GB | Good | ✅ Yes | ⭐ Best |
| Qwen2.5-0.5B-Instruct | 0.5B | ~1GB | Basic | ✅ Yes | Backup |
| SmolLM2-1.7B-Instruct | 1.7B | ~2GB | Good | ❌ Limited | Alternative |
| Phi-3.5-mini-instruct | 3.8B | ~3.5GB | Better | ❌ Limited | Risky (tight) |
| Gemma-2-2B-it | 2B | ~2.5GB | Good | ❌ Limited | Alternative |

### 1.2 Recommendation: Qwen2.5-1.5B-Instruct

Why:
- **Fits your GPU**: ~2GB VRAM when quantized
- **Multilingual**: Trained on Chinese + English, handles Taglish well
- **Instruction-tuned**: Good at following JSON output format
- **Apache 2.0**: Commercial use allowed
- **Active community**: Good fine-tuning support

## 2. Architecture: Triple Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                 Triple Ensemble Sentiment                    │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ RoBERTa (35%)   │  │ Qwen SLM (35%)  │  │ Gemini (30%)│ │
│  │ twitter-roberta │  │ Fine-tuned      │  │ API backup  │ │
│  │ CPU inference   │  │ LOCAL GPU       │  │ Cloud       │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └────────────────────┼───────────────────┘        │
│                                ▼                            │
│                    ┌───────────────────┐                    │
│                    │  Weighted Voting  │                    │
│                    │  Final Sentiment  │                    │
│                    └───────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of This Architecture

| Aspect | Benefit |
|--------|---------|
| **Offline capable** | SLM + RoBERTa work without internet |
| **Cost reduction** | Less Gemini API calls |
| **Domain-specific** | SLM trained on Baguio data |
| **Fallback** | If SLM fails, Gemini handles it |
| **Thesis value** | Novel contribution - local fine-tuned model |

## 3. Environment Setup

### 3.1 Install Dependencies

```bash
# Create virtual environment
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
pip install transformers datasets peft trl bitsandbytes accelerate
pip install llama-cpp-python  # For quantized inference
```

### 3.2 Verify GPU Access

```python
# backend/scripts/check_gpu.py
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

# Expected output:
# CUDA available: True
# GPU: NVIDIA GeForce RTX 3050 Laptop GPU
# VRAM: 4.00 GB
```

## 4. Dataset Preparation

### 4.1 Create Training Data

```python
# backend/scripts/prepare_slm_dataset.py

import json
from pathlib import Path
from datetime import datetime

# Baguio-specific training samples
TRAINING_DATA = [
    # Negative - Infrastructure
    {"text": "Traffic sa Kennon Road grabe na naman, 4 hours bago makarating!", "sentiment": "negative", "theme": "infrastructure"},
    {"text": "Session Road closed na naman dahil sa road repair", "sentiment": "negative", "theme": "infrastructure"},
    {"text": "Water interruption sa Baguio bukas hanggang Friday", "sentiment": "negative", "theme": "infrastructure"},
    {"text": "Brownout na naman sa Camp 7, third time this week", "sentiment": "negative", "theme": "infrastructure"},
    {"text": "Potholes sa Marcos Highway sobrang lala na", "sentiment": "negative", "theme": "infrastructure"},
    
    # Negative - Health
    {"text": "BGH emergency room puno na naman, 5 hours waiting time", "sentiment": "negative", "theme": "health"},
    {"text": "Dengue cases sa Baguio tumaas this month", "sentiment": "negative", "theme": "health"},
    {"text": "No available beds sa BGH, diverted to private hospital", "sentiment": "negative", "theme": "health"},
    
    # Negative - Safety
    {"text": "Landslide warning sa Benguet Road, be careful!", "sentiment": "negative", "theme": "safety"},
    {"text": "Snatching incident sa Session Road last night", "sentiment": "negative", "theme": "safety"},
    {"text": "Fire broke out sa Guisad, 3 houses burned", "sentiment": "negative", "theme": "safety"},
    
    # Negative - Economy
    {"text": "SM Baguio parking sobrang mahal na, P50 per hour!", "sentiment": "negative", "theme": "economy"},
    {"text": "Strawberry prices sa La Trinidad tumaas ng 50%", "sentiment": "negative", "theme": "economy"},
    {"text": "Vendors sa night market kinukulang sa customers", "sentiment": "negative", "theme": "economy"},
    
    # Positive - Tourism
    {"text": "Panagbenga Festival was amazing this year!", "sentiment": "positive", "theme": "tourism"},
    {"text": "Burnham Park lagoon finally cleaned, looks beautiful!", "sentiment": "positive", "theme": "positive"},
    {"text": "Session Road Sunday market is always fun!", "sentiment": "positive", "theme": "tourism"},
    {"text": "Strawberry taho sa Burnham the best!", "sentiment": "positive", "theme": "tourism"},
    {"text": "Mines View Park renovated, mas maganda na!", "sentiment": "positive", "theme": "tourism"},
    
    # Positive - Infrastructure
    {"text": "New road sa Asin finally completed!", "sentiment": "positive", "theme": "infrastructure"},
    {"text": "Traffic management sa Session Road improved", "sentiment": "positive", "theme": "infrastructure"},
    {"text": "Free WiFi sa Burnham Park working na!", "sentiment": "positive", "theme": "infrastructure"},
    
    # Positive - Health
    {"text": "BGH doctors are very helpful and kind", "sentiment": "positive", "theme": "health"},
    {"text": "Free vaccination sa Baguio Convention Center", "sentiment": "positive", "theme": "health"},
    {"text": "New dialysis center opened sa BGH", "sentiment": "positive", "theme": "health"},
    
    # Positive - Safety
    {"text": "CCTV cameras installed sa Session Road, safer na", "sentiment": "positive", "theme": "safety"},
    {"text": "Quick response ng BFP sa fire incident", "sentiment": "positive", "theme": "safety"},
    
    # Positive - Economy
    {"text": "Tourism boost helped local businesses recover", "sentiment": "positive", "theme": "economy"},
    {"text": "Night market vendors happy with increased sales", "sentiment": "positive", "theme": "economy"},
    
    # Neutral
    {"text": "City Mayor announced new infrastructure project", "sentiment": "neutral", "theme": "infrastructure"},
    {"text": "DPWH to start road widening next month", "sentiment": "neutral", "theme": "infrastructure"},
    {"text": "Weather forecast: expect rain in Baguio tomorrow", "sentiment": "neutral", "theme": "environment"},
    {"text": "City council meeting scheduled for Monday", "sentiment": "neutral", "theme": "infrastructure"},
    {"text": "New ordinance on plastic bags takes effect", "sentiment": "neutral", "theme": "environment"},
    {"text": "Baguio population reaches 400,000", "sentiment": "neutral", "theme": "economy"},
]

def create_chat_format(item: dict) -> dict:
    """Convert to chat format for instruction tuning."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are a sentiment classifier for Baguio City, Philippines civic content. Analyze the text and output JSON with sentiment (negative/neutral/positive) and confidence (0.0-1.0)."
            },
            {
                "role": "user",
                "content": f"Classify: {item['text']}"
            },
            {
                "role": "assistant",
                "content": json.dumps({
                    "sentiment": item["sentiment"],
                    "confidence": 0.95
                })
            }
        ]
    }

def main():
    output_dir = Path("data/slm_training")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create training samples
    samples = [create_chat_format(item) for item in TRAINING_DATA]
    
    # Split 90/10
    split_idx = int(len(samples) * 0.9)
    train_samples = samples[:split_idx]
    val_samples = samples[split_idx:]
    
    # Save
    with open(output_dir / "train.jsonl", "w", encoding="utf-8") as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    with open(output_dir / "val.jsonl", "w", encoding="utf-8") as f:
        for sample in val_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    print(f"Created {len(train_samples)} training samples")
    print(f"Created {len(val_samples)} validation samples")
    print(f"Output: {output_dir}")

if __name__ == "__main__":
    main()
```

### 4.2 Expand Dataset

To get better results, expand to 500-1000 samples:

```python
# backend/scripts/expand_dataset.py

import json
from pathlib import Path

# Use your existing ensemble to label more data
async def label_with_ensemble(texts: list[str]) -> list[dict]:
    """Use RoBERTa + Gemini to pre-label data."""
    from app.services.agents.sentiment_agent import EnsembleSentimentAgent
    
    agent = EnsembleSentimentAgent()
    results = []
    
    for text in texts:
        result = await agent.analyze(text)
        if result["confidence"] > 0.8:  # Only high-confidence labels
            results.append({
                "text": text,
                "sentiment": result["sentiment"],
                "confidence": result["confidence"]
            })
    
    return results
```

## 5. Fine-Tuning Script (Runs on Your Laptop)

### 5.1 Main Training Script

```python
# backend/scripts/finetune_slm.py

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
import os

# ============================================
# Configuration
# ============================================
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "./models/baguio-sentiment-slm"
DATA_DIR = "./data/slm_training"

# Reduce memory usage
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# ============================================
# Load Model with 4-bit Quantization
# ============================================
print("Loading model...")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print(f"Model loaded! VRAM used: {torch.cuda.memory_allocated()/1e9:.2f} GB")

# ============================================
# Configure LoRA (Low-Rank Adaptation)
# ============================================
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,  # Low rank for small GPU
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ============================================
# Load Dataset
# ============================================
print("Loading dataset...")

dataset = load_dataset("json", data_files={
    "train": f"{DATA_DIR}/train.jsonl",
    "validation": f"{DATA_DIR}/val.jsonl",
})

print(f"Train: {len(dataset['train'])}, Val: {len(dataset['validation'])}")

# ============================================
# Format Function
# ============================================
def formatting_func(example):
    messages = example["messages"]
    # Use Qwen chat template
    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=False
    )
    return text

# ============================================
# Training Arguments (Optimized for RTX 3050)
# ============================================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,  # Small batch for 4GB VRAM
    gradient_accumulation_steps=8,  # Effective batch = 8
    learning_rate=2e-4,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    logging_steps=5,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    fp16=True,
    optim="paged_adamw_8bit",
    max_grad_norm=0.3,
    gradient_checkpointing=True,  # Save memory
    report_to="none",  # Disable wandb
)

# ============================================
# Trainer
# ============================================
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    tokenizer=tokenizer,
    args=training_args,
    max_seq_length=512,  # Short for memory
    formatting_func=formatting_func,
)

# ============================================
# Train!
# ============================================
print("Starting training...")
print(f"VRAM before training: {torch.cuda.memory_allocated()/1e9:.2f} GB")

trainer.train()

# ============================================
# Save Model
# ============================================
print("Saving model...")
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"Model saved to {OUTPUT_DIR}")
print("Done!")
```

### 5.2 Run Training

```bash
cd backend
python scripts/finetune_slm.py
```

**Expected output:**
```
Loading model...
Model loaded! VRAM used: 1.8 GB
trainable params: 2,097,152 || all params: 1,545,000,000 || trainable%: 0.14%
Loading dataset...
Train: 32, Val: 4
Starting training...
VRAM before training: 2.1 GB
{'loss': 1.234, 'learning_rate': 0.0002, 'epoch': 1.0}
{'loss': 0.567, 'learning_rate': 0.0001, 'epoch': 2.0}
{'loss': 0.234, 'learning_rate': 0.00005, 'epoch': 3.0}
Saving model...
Model saved to ./models/baguio-sentiment-slm
Done!
```

**Training time**: ~30-60 minutes for 100 samples on RTX 3050

## 6. Inference Integration

### 6.1 Local SLM Agent

```python
# backend/app/services/agents/slm_agent.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LocalSLMAgent:
    """Local Small Language Model for Baguio sentiment analysis."""
    
    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: str = "./models/baguio-sentiment-slm",
    ):
        self.base_model = base_model
        self.adapter_path = adapter_path
        self._model = None
        self._tokenizer = None
    
    def _load_model(self):
        """Lazy load model to save memory."""
        if self._model is not None:
            return
        
        logger.info("Loading SLM model...")
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        # Load base model
        base = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load fine-tuned adapter
        self._model = PeftModel.from_pretrained(base, self.adapter_path)
        self._model.eval()
        
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.base_model, 
            trust_remote_code=True
        )
        
        logger.info(f"SLM loaded! VRAM: {torch.cuda.memory_allocated()/1e9:.2f} GB")
    
    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment using local fine-tuned SLM."""
        self._load_model()
        
        messages = [
            {
                "role": "system",
                "content": "You are a sentiment classifier for Baguio City, Philippines civic content. Analyze the text and output JSON with sentiment (negative/neutral/positive) and confidence (0.0-1.0)."
            },
            {
                "role": "user",
                "content": f"Classify: {text}"
            }
        ]
        
        # Tokenize
        input_text = self._tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        inputs = self._tokenizer(input_text, return_tensors="pt").to("cuda")
        
        # Generate
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        
        # Decode
        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        )
        
        return self._parse_response(response)
    
    def _parse_response(self, text: str) -> dict[str, Any]:
        """Parse JSON from model response."""
        try:
            # Find JSON in response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse SLM response: {text}")
        
        # Fallback
        return {"sentiment": "neutral", "confidence": 0.5}
    
    def unload(self):
        """Unload model to free VRAM."""
        if self._model is not None:
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            torch.cuda.empty_cache()
            logger.info("SLM unloaded")


# Singleton instance
slm_agent = LocalSLMAgent()
```

### 6.2 Updated Ensemble Agent

```python
# backend/app/services/agents/sentiment_agent.py (updated)

from .slm_agent import slm_agent
from .roberta_agent import roberta_agent
from .gemini_agent import gemini_agent

class TripleEnsembleSentimentAgent:
    """Three-model ensemble: RoBERTa + Local SLM + Gemini."""
    
    WEIGHTS = {
        "roberta": 0.35,    # Fast, social media trained
        "slm": 0.35,        # Local, Baguio-specific
        "gemini": 0.30,     # Cloud backup, context-aware
    }
    
    def __init__(self, use_slm: bool = True, use_gemini: bool = True):
        self.use_slm = use_slm
        self.use_gemini = use_gemini
    
    async def analyze(self, text: str) -> dict:
        results = {}
        weights = {}
        
        # Always use RoBERTa (CPU, fast)
        roberta_result = roberta_agent.predict(text)
        results["roberta"] = roberta_result
        weights["roberta"] = self.WEIGHTS["roberta"]
        
        # Use local SLM if available
        if self.use_slm:
            try:
                slm_result = slm_agent.analyze_sentiment(text)
                results["slm"] = slm_result
                weights["slm"] = self.WEIGHTS["slm"]
            except Exception as e:
                logger.warning(f"SLM failed: {e}")
                # Redistribute weight to others
                weights["roberta"] += self.WEIGHTS["slm"] / 2
                if self.use_gemini:
                    weights["gemini"] = self.WEIGHTS["gemini"] + self.WEIGHTS["slm"] / 2
        
        # Use Gemini for complex cases or as backup
        if self.use_gemini:
            try:
                gemini_result = await gemini_agent.analyze_sentiment(text)
                results["gemini"] = gemini_result
                weights["gemini"] = weights.get("gemini", self.WEIGHTS["gemini"])
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Weighted voting
        return self._weighted_vote(results, weights)
    
    def _weighted_vote(self, results: dict, weights: dict) -> dict:
        """Combine predictions with weighted voting."""
        sentiment_scores = {"negative": 0, "neutral": 0, "positive": 0}
        
        for model, result in results.items():
            sentiment = result.get("sentiment", "neutral")
            confidence = result.get("confidence", 0.5)
            weight = weights.get(model, 0)
            
            sentiment_scores[sentiment] += confidence * weight
        
        # Get winner
        final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        final_confidence = sentiment_scores[final_sentiment]
        
        return {
            "sentiment": final_sentiment,
            "confidence": round(final_confidence, 3),
            "method": "triple_ensemble",
            "models": list(results.keys()),
            "breakdown": {
                model: result.get("sentiment") 
                for model, result in results.items()
            }
        }
```

## 7. Testing

### 7.1 Test Script

```python
# backend/scripts/test_slm.py

from app.services.agents.slm_agent import slm_agent

test_cases = [
    "Traffic sa Kennon Road grabe na naman!",
    "Panagbenga Festival was amazing this year!",
    "City Mayor announced new infrastructure project",
    "BGH emergency room puno, 5 hours waiting",
    "Session Road Sunday market is always fun!",
    "Water interruption sa Baguio bukas",
]

print("Testing fine-tuned SLM...")
print("=" * 50)

for text in test_cases:
    result = slm_agent.analyze_sentiment(text)
    print(f"Text: {text}")
    print(f"Result: {result}")
    print("-" * 50)

# Cleanup
slm_agent.unload()
```

### 7.2 Expected Results

```
Testing fine-tuned SLM...
==================================================
Text: Traffic sa Kennon Road grabe na naman!
Result: {'sentiment': 'negative', 'confidence': 0.92}
--------------------------------------------------
Text: Panagbenga Festival was amazing this year!
Result: {'sentiment': 'positive', 'confidence': 0.95}
--------------------------------------------------
Text: City Mayor announced new infrastructure project
Result: {'sentiment': 'neutral', 'confidence': 0.88}
--------------------------------------------------
```

## 8. Performance Expectations

### 8.1 Accuracy Comparison

| Model | Expected Accuracy | Inference Time |
|-------|-------------------|----------------|
| RoBERTa only | ~78% | ~50ms |
| Gemini only | ~85% | ~2000ms |
| SLM only | ~80% | ~200ms |
| Triple Ensemble | ~88% | ~300ms |

### 8.2 Resource Usage

| Metric | Value |
|--------|-------|
| VRAM (inference) | ~2GB |
| VRAM (training) | ~3.5GB |
| RAM | ~4GB |
| Model size | ~1.5GB |

## 9. Timeline

| Day | Task |
|-----|------|
| 1 | Set up environment, verify GPU |
| 2 | Prepare 100 training samples |
| 3 | Fine-tune SLM (1 hour) |
| 4 | Test and evaluate accuracy |
| 5 | Integrate into ensemble |
| 6 | A/B testing vs current system |
| 7 | Document results for thesis |

## 10. Thesis Value

This SLM approach adds significant thesis contributions:

1. **Novel**: First Baguio-specific sentiment SLM
2. **Practical**: Runs on consumer hardware
3. **Reproducible**: Can be replicated by others
4. **Comparison**: Baseline for ensemble evaluation
5. **Cost-effective**: No cloud inference costs

## 11. Quick Start Commands

```bash
# 1. Setup
cd backend
pip install torch transformers datasets peft trl bitsandbytes accelerate

# 2. Prepare data
python scripts/prepare_slm_dataset.py

# 3. Fine-tune (30-60 min)
python scripts/finetune_slm.py

# 4. Test
python scripts/test_slm.py

# 5. Integrate
# Update sentiment_agent.py to use TripleEnsembleSentimentAgent
```

## 12. Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce batch_size to 1, enable gradient_checkpointing |
| Model too slow | Use smaller max_seq_length (256) |
| Poor accuracy | Add more training samples, increase epochs |
| Taglish not working | Add more Taglish samples to training data |

This plan enables you to fine-tune and run a domain-specific SLM entirely on your RTX 3050 laptop!
