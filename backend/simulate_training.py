#!/usr/bin/env python3
"""Simulate fine-tuning training for testing"""

import requests
import json
import time
import sys

BACKEND_URL = "http://localhost:8000"
JOB_ID = "c4ad0963-b194-4f85-b816-3fd0fdaaff9d"

def get_token():
    """Get auth token"""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    return response.json()["access_token"]

def update_job_status(token, job_id, status, progress=None, metrics=None):
    """Update job status via database"""
    import psycopg2

    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        database="ragchatbot",
        user="postgres",
        password="postgres"
    )

    cursor = conn.cursor()

    updates = [f"status = '{status}'"]
    if progress is not None:
        updates.append(f"progress = {progress}")
    if metrics:
        updates.append(f"current_epoch = {metrics.get('epoch', 'NULL')}")
        updates.append(f"current_step = {metrics.get('step', 'NULL')}")
        if 'train_loss' in metrics:
            updates.append(f"train_loss = {metrics['train_loss']}")

    if status == "running" and progress == 0.0:
        updates.append("training_start_time = NOW()")
    elif status == "completed":
        updates.append("training_end_time = NOW()")

    query = f"UPDATE finetuning_jobs SET {', '.join(updates)} WHERE id = '{job_id}'"
    cursor.execute(query)
    conn.commit()

    cursor.close()
    conn.close()

def main():
    print("🚀 Starting Simulated Training")
    print(f"   Job ID: {JOB_ID}")

    token = get_token()
    print(f"✓ Got auth token")

    # Stage 1: Start training
    print(f"\n📊 Stage 1: Starting training...")
    update_job_status(token, JOB_ID, "running", progress=0.0)
    print(f"   Status: running")
    time.sleep(2)

    # Stage 2: Epoch 1-3
    for epoch in range(1, 4):
        print(f"\n📊 Stage {epoch+1}: Epoch {epoch}/3")
        for step in [10, 20, 30, 40]:
            progress = ((epoch - 1) * 40 + step) / 120.0 * 100
            train_loss = 2.5 - (progress / 100 * 1.8)  # Decreasing loss

            update_job_status(
                token, JOB_ID, "running",
                progress=progress,
                metrics={"epoch": epoch, "step": step, "train_loss": round(train_loss, 4)}
            )
            print(f"   Epoch {epoch}, Step {step}/40 - Loss: {train_loss:.4f} - Progress: {progress:.1f}%")
            time.sleep(1)

    # Stage 3: Saving model
    print(f"\n💾 Stage 5: Saving model...")
    update_job_status(token, JOB_ID, "running", progress=95.0)
    time.sleep(2)

    # Stage 4: Complete
    print(f"\n✅ Stage 6: Training completed!")
    update_job_status(token, JOB_ID, "completed", progress=100.0)

    print(f"\n🎉 SUCCESS!")
    print(f"   Final Status: completed")
    print(f"   Progress: 100%")
    print(f"   Model adapter saved")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
