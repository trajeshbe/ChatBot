#!/usr/bin/env python3
"""
Recovery script for training52 - Upload adapters to MinIO and register model

The training completed successfully but Celery worker was restarted mid-job,
so the post-processing didn't run. This script completes the missing steps.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from uuid import UUID

# Add backend to path
sys.path.insert(0, '/app/backend')

from minio import Minio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.finetuning_models import FineTunedModel, FineTuningJob

# Configuration
JOB_ID = "31c5a418-b7ff-43fe-8add-c57e18c3d919"
JOB_NAME = "choles-qa-real-training52"
WORKSPACE_PATH = f"/workspace/finetuning/{JOB_ID}"
ADAPTER_PATH = f"{WORKSPACE_PATH}/output/adapter_model"

# MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# Database connection
engine = create_engine(settings.SYNC_SQLALCHEMY_DATABASE_URI)
db = Session(engine)

def upload_to_minio():
    """Upload adapter files to MinIO"""
    print(f"📦 Uploading adapter files to MinIO...")

    # MinIO path structure
    minio_base = "technology/itm11/global/admin/finetuning/datasets/company_qa_dataset.jsonl"
    minio_checkpoint_dir = f"{minio_base}/checkpoints/{JOB_NAME}/{JOB_ID}/final/adapter_model"

    adapter_files = [
        "adapter_model.safetensors",
        "adapter_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "added_tokens.json",
        "chat_template.jinja",
        "README.md"
    ]

    uploaded = []
    for filename in adapter_files:
        local_file = Path(ADAPTER_PATH) / filename
        if not local_file.exists():
            print(f"   ⚠️  Skipping {filename} (not found)")
            continue

        minio_path = f"{minio_checkpoint_dir}/{filename}"

        try:
            minio_client.fput_object(
                "documents",
                minio_path,
                str(local_file)
            )
            file_size = local_file.stat().st_size
            print(f"   ✅ Uploaded: {filename} ({file_size:,} bytes)")
            uploaded.append(filename)
        except Exception as e:
            print(f"   ❌ Failed to upload {filename}: {e}")

    checkpoint_path = f"minio://documents/{minio_checkpoint_dir}/adapter_model.safetensors"
    print(f"\n✅ Uploaded {len(uploaded)}/{len(adapter_files)} files")
    print(f"📍 Checkpoint path: {checkpoint_path}")

    return checkpoint_path

def register_model(checkpoint_path: str):
    """Register the fine-tuned model in database"""
    print(f"\n📝 Registering model in database...")

    # Get job details
    job = db.query(FineTuningJob).filter(FineTuningJob.id == UUID(JOB_ID)).first()
    if not job:
        print(f"❌ Job {JOB_ID} not found in database!")
        return None

    # Create model record
    model = FineTunedModel(
        name=f"{JOB_NAME}_model",
        version="v1.0.0",
        description=f"Fine-tuned {job.base_model} using {job.finetuning_method} for {job.training_objective}",
        base_model=job.base_model,
        finetuning_method=job.finetuning_method,
        job_id=UUID(JOB_ID),
        minio_checkpoint_path=checkpoint_path,
        status="registered",
        created_by=job.created_by,
        project_id=job.project_id
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    print(f"✅ Model registered:")
    print(f"   ID: {model.id}")
    print(f"   Name: {model.name}")
    print(f"   Version: {model.version}")
    print(f"   Status: {model.status}")

    return model

def update_job_status():
    """Update job status to completed"""
    print(f"\n📝 Updating job status...")

    job = db.query(FineTuningJob).filter(FineTuningJob.id == UUID(JOB_ID)).first()
    if not job:
        print(f"❌ Job {JOB_ID} not found!")
        return

    # Update job
    job.status = "completed"
    job.progress = 100.0
    job.training_stage = "completed"
    job.train_loss = 3.5293  # From logs
    job.training_end_time = datetime.utcnow()

    # Calculate training time (from logs: model loading at 14:44:18, completion at 14:49:24)
    # Total: ~6 minutes = 360 seconds
    job.training_time_seconds = 306  # 5min 6s actual training time

    db.commit()

    print(f"✅ Job status updated:")
    print(f"   Status: {job.status}")
    print(f"   Progress: {job.progress}%")
    print(f"   Final loss: {job.train_loss}")
    print(f"   Training time: {job.training_time_seconds}s")

def main():
    """Main recovery process"""
    print("=" * 80)
    print("Training52 Recovery Script")
    print("=" * 80)
    print(f"Job ID: {JOB_ID}")
    print(f"Job Name: {JOB_NAME}")
    print(f"Adapter Path: {ADAPTER_PATH}")
    print("")

    try:
        # Step 1: Upload to MinIO
        checkpoint_path = upload_to_minio()

        # Step 2: Register model
        model = register_model(checkpoint_path)

        # Step 3: Update job status
        update_job_status()

        print("\n" + "=" * 80)
        print("✅ Recovery Complete!")
        print("=" * 80)
        print(f"\nNext steps:")
        print(f"1. Go to Admin → Fine-Tuning → Models tab")
        print(f"2. Find model: {JOB_NAME}_model (v1.0.0)")
        print(f"3. Click 'Merge Adapters' button")
        print(f"4. After merge completes, click 'Deploy to Ollama'")

    except Exception as e:
        print(f"\n❌ Recovery failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
