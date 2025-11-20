#!/usr/bin/env python3
"""
Embedding Model Migration Script

This script allows administrators to change the embedding model and re-process
all historical document chunks with new embeddings.

⚠️  WARNING: This is a DESTRUCTIVE operation that will:
    1. Drop existing embedding indexes
    2. Alter database schema to match new vector dimensions
    3. Re-embed ALL document chunks (can take hours for large databases)
    4. Clear all query cache entries
    5. Update system metadata

Usage:
    python migrate_embedding_model.py --model <model_name> [options]

Examples:
    # Migrate to all-mpnet-base-v2 (768 dimensions)
    python migrate_embedding_model.py --model sentence-transformers/all-mpnet-base-v2

    # Dry run to see what would happen
    python migrate_embedding_model.py --model sentence-transformers/all-mpnet-base-v2 --dry-run

    # Process in smaller batches
    python migrate_embedding_model.py --model sentence-transformers/all-mpnet-base-v2 --batch-size 50

Supported Models:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) - CURRENT DEFAULT
    - sentence-transformers/all-mpnet-base-v2 (768 dimensions)
    - sentence-transformers/multi-qa-mpnet-base-dot-v1 (768 dimensions)
    - sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768 dimensions)
    - BAAI/bge-small-en-v1.5 (384 dimensions)
    - BAAI/bge-base-en-v1.5 (768 dimensions)
    - BAAI/bge-large-en-v1.5 (1024 dimensions)

Requirements:
    - Database credentials in environment variables or .env file
    - Admin access to PostgreSQL database
    - Sufficient disk space for new embeddings
    - GPU recommended for large datasets (optional)

Author: AI Assistant
Date: 2025-11-20
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'embedding_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Supported embedding models with metadata
SUPPORTED_MODELS = {
    "sentence-transformers/all-MiniLM-L6-v2": {
        "dimensions": 384,
        "description": "Fast and efficient, good for most use cases (CURRENT DEFAULT)",
        "max_seq_length": 256,
        "recommended_for": "General purpose, production"
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "dimensions": 768,
        "description": "Higher quality, better accuracy",
        "max_seq_length": 384,
        "recommended_for": "High accuracy requirements"
    },
    "sentence-transformers/multi-qa-mpnet-base-dot-v1": {
        "dimensions": 768,
        "description": "Optimized for question-answering",
        "max_seq_length": 384,
        "recommended_for": "QA and retrieval tasks"
    },
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": {
        "dimensions": 768,
        "description": "Supports 50+ languages",
        "max_seq_length": 128,
        "recommended_for": "Multilingual documents"
    },
    "BAAI/bge-small-en-v1.5": {
        "dimensions": 384,
        "description": "State-of-the-art small model",
        "max_seq_length": 512,
        "recommended_for": "Best quality at 384D"
    },
    "BAAI/bge-base-en-v1.5": {
        "dimensions": 768,
        "description": "State-of-the-art base model",
        "max_seq_length": 512,
        "recommended_for": "High accuracy, medium speed"
    },
    "BAAI/bge-large-en-v1.5": {
        "dimensions": 1024,
        "description": "State-of-the-art large model (slowest)",
        "max_seq_length": 512,
        "recommended_for": "Maximum accuracy, GPU required"
    }
}


class EmbeddingMigrator:
    """Handles embedding model migration with safety checks and rollback support."""

    def __init__(
        self,
        new_model_name: str,
        db_host: str,
        db_port: int,
        db_name: str,
        db_user: str,
        db_password: str,
        batch_size: int = 100,
        dry_run: bool = False,
        use_gpu: bool = True
    ):
        self.new_model_name = new_model_name
        self.new_model_info = SUPPORTED_MODELS.get(new_model_name)
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.use_gpu = use_gpu and torch.cuda.is_available()

        # Database connection parameters
        self.db_params = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }

        self.conn = None
        self.model = None
        self.current_model_name = None
        self.current_dimensions = None

    def connect_db(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info(f"✓ Connected to database: {self.db_params['database']}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            raise

    def get_current_model_info(self) -> Tuple[Optional[str], Optional[int]]:
        """Detect current embedding model and dimensions from database."""
        try:
            cursor = self.conn.cursor()

            # Query the comment on the embedding column
            cursor.execute("""
                SELECT obj_description(
                    (quote_ident(table_schema)||'.'||quote_ident(table_name)||'.'||quote_ident(column_name))::regclass,
                    'pg_class'
                ) as comment
                FROM information_schema.columns
                WHERE table_name = 'document_chunks' AND column_name = 'embedding';
            """)

            result = cursor.fetchone()
            comment = result[0] if result else None

            # Extract model name from comment
            model_name = None
            if comment and "using" in comment:
                # Comment format: "Vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2"
                model_name = comment.split("using")[-1].strip()

            # Get actual vector dimensions from schema
            cursor.execute("""
                SELECT atttypmod
                FROM pg_attribute
                WHERE attrelid = 'document_chunks'::regclass
                AND attname = 'embedding';
            """)

            result = cursor.fetchone()
            # atttypmod stores dimensions + 4 for vector type
            dimensions = (result[0] - 4) if result and result[0] > 0 else None

            cursor.close()

            return model_name, dimensions

        except Exception as e:
            logger.warning(f"Could not detect current model info: {e}")
            return None, None

    def validate_new_model(self):
        """Validate and load the new embedding model."""
        if not self.new_model_info:
            logger.error(f"✗ Unsupported model: {self.new_model_name}")
            logger.info("\nSupported models:")
            for model, info in SUPPORTED_MODELS.items():
                logger.info(f"  - {model}")
                logger.info(f"    Dimensions: {info['dimensions']}")
                logger.info(f"    Description: {info['description']}")
                logger.info(f"    Recommended for: {info['recommended_for']}\n")
            raise ValueError(f"Unsupported model: {self.new_model_name}")

        logger.info(f"✓ Model validation passed: {self.new_model_name}")
        logger.info(f"  Dimensions: {self.new_model_info['dimensions']}")
        logger.info(f"  Description: {self.new_model_info['description']}")

    def load_model(self):
        """Load the new embedding model."""
        try:
            device = 'cuda' if self.use_gpu else 'cpu'
            logger.info(f"Loading model on device: {device}")

            self.model = SentenceTransformer(self.new_model_name, device=device)

            logger.info(f"✓ Model loaded successfully: {self.new_model_name}")
            logger.info(f"  Model device: {self.model.device}")
            logger.info(f"  Max sequence length: {self.model.max_seq_length}")

        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise

    def get_statistics(self) -> Dict:
        """Get database statistics before migration."""
        cursor = self.conn.cursor()

        stats = {}

        # Total document chunks
        cursor.execute("SELECT COUNT(*) FROM document_chunks;")
        stats['total_chunks'] = cursor.fetchone()[0]

        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents;")
        stats['total_documents'] = cursor.fetchone()[0]

        # Query cache entries
        cursor.execute("SELECT COUNT(*) FROM query_cache;")
        stats['cache_entries'] = cursor.fetchone()[0]

        # Database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()));
        """)
        stats['database_size'] = cursor.fetchone()[0]

        # Chunks with embeddings
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;")
        stats['chunks_with_embeddings'] = cursor.fetchone()[0]

        cursor.close()

        return stats

    def create_backup_table(self):
        """Create backup table for embeddings (for rollback)."""
        if self.dry_run:
            logger.info("[DRY RUN] Would create backup table: document_chunks_backup_embeddings")
            return

        cursor = self.conn.cursor()

        # Drop existing backup if exists
        cursor.execute("DROP TABLE IF EXISTS document_chunks_backup_embeddings;")

        # Create backup table with just id and embedding
        cursor.execute("""
            CREATE TABLE document_chunks_backup_embeddings AS
            SELECT id, embedding
            FROM document_chunks
            WHERE embedding IS NOT NULL;
        """)

        cursor.execute("SELECT COUNT(*) FROM document_chunks_backup_embeddings;")
        backup_count = cursor.fetchone()[0]

        cursor.close()

        logger.info(f"✓ Created backup table with {backup_count} embeddings")

    def alter_schema(self):
        """Alter database schema to match new embedding dimensions."""
        new_dims = self.new_model_info['dimensions']

        if self.dry_run:
            logger.info(f"[DRY RUN] Would alter schema to vector({new_dims})")
            return

        cursor = self.conn.cursor()

        try:
            # Drop existing indexes
            logger.info("Dropping existing embedding indexes...")
            cursor.execute("DROP INDEX IF EXISTS idx_chunks_embedding;")
            cursor.execute("DROP INDEX IF EXISTS idx_query_cache_embedding;")

            # Alter document_chunks embedding column
            logger.info(f"Altering document_chunks.embedding to vector({new_dims})...")
            cursor.execute(f"""
                ALTER TABLE document_chunks
                ALTER COLUMN embedding TYPE vector({new_dims});
            """)

            # Alter query_cache embedding column
            logger.info(f"Altering query_cache.query_embedding to vector({new_dims})...")
            cursor.execute(f"""
                ALTER TABLE query_cache
                ALTER COLUMN query_embedding TYPE vector({new_dims});
            """)

            # Update column comments
            cursor.execute(f"""
                COMMENT ON COLUMN document_chunks.embedding IS
                'Vector embedding ({new_dims} dimensions) using {self.new_model_name}';
            """)

            cursor.execute(f"""
                COMMENT ON COLUMN query_cache.query_embedding IS
                'Query embedding ({new_dims} dimensions) using {self.new_model_name}';
            """)

            logger.info("✓ Schema altered successfully")

        except Exception as e:
            logger.error(f"✗ Schema alteration failed: {e}")
            raise
        finally:
            cursor.close()

    def clear_embeddings(self):
        """Clear all existing embeddings before re-processing."""
        if self.dry_run:
            logger.info("[DRY RUN] Would clear all embeddings")
            return

        cursor = self.conn.cursor()

        logger.info("Clearing existing embeddings...")
        cursor.execute("UPDATE document_chunks SET embedding = NULL;")
        cursor.execute("DELETE FROM query_cache;")

        cursor.close()

        logger.info("✓ Embeddings cleared")

    def re_embed_chunks(self):
        """Re-embed all document chunks with new model."""
        cursor = self.conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE content IS NOT NULL;")
        total_chunks = cursor.fetchone()[0]

        logger.info(f"Re-embedding {total_chunks} chunks (batch size: {self.batch_size})...")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would re-embed {total_chunks} chunks")
            cursor.close()
            return

        # Process in batches
        offset = 0
        success_count = 0
        error_count = 0

        with tqdm(total=total_chunks, desc="Re-embedding chunks", unit="chunk") as pbar:
            while offset < total_chunks:
                # Fetch batch
                cursor.execute(f"""
                    SELECT id, content
                    FROM document_chunks
                    WHERE content IS NOT NULL
                    ORDER BY id
                    LIMIT {self.batch_size} OFFSET {offset};
                """)

                batch = cursor.fetchall()
                if not batch:
                    break

                # Generate embeddings for batch
                try:
                    chunk_ids = [row[0] for row in batch]
                    texts = [row[1] for row in batch]

                    # Generate embeddings
                    embeddings = self.model.encode(
                        texts,
                        convert_to_numpy=True,
                        show_progress_bar=False,
                        normalize_embeddings=True
                    )

                    # Update database
                    for chunk_id, embedding in zip(chunk_ids, embeddings):
                        embedding_list = embedding.tolist()
                        cursor.execute(
                            "UPDATE document_chunks SET embedding = %s WHERE id = %s;",
                            (embedding_list, chunk_id)
                        )

                    success_count += len(batch)

                except Exception as e:
                    logger.error(f"Error processing batch at offset {offset}: {e}")
                    error_count += len(batch)

                offset += self.batch_size
                pbar.update(len(batch))

        cursor.close()

        logger.info(f"✓ Re-embedding completed: {success_count} success, {error_count} errors")

        return success_count, error_count

    def recreate_indexes(self):
        """Recreate vector indexes for performance."""
        if self.dry_run:
            logger.info("[DRY RUN] Would recreate vector indexes")
            return

        cursor = self.conn.cursor()

        logger.info("Recreating vector indexes (this may take several minutes)...")

        # Create IVFFlat index for document_chunks
        cursor.execute("""
            CREATE INDEX idx_chunks_embedding ON document_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

        logger.info("✓ Created index: idx_chunks_embedding")

        # Create index for query_cache (simpler since it's smaller)
        cursor.execute("""
            CREATE INDEX idx_query_cache_embedding ON query_cache
            USING ivfflat (query_embedding vector_cosine_ops)
            WITH (lists = 10);
        """)

        logger.info("✓ Created index: idx_query_cache_embedding")

        cursor.close()

    def update_metadata(self):
        """Update system metadata to record migration."""
        if self.dry_run:
            logger.info("[DRY RUN] Would update system metadata")
            return

        cursor = self.conn.cursor()

        # Create metadata table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metadata (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Record migration
        cursor.execute("""
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES ('embedding_model', %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW();
        """, (self.new_model_name,))

        cursor.execute("""
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES ('embedding_dimensions', %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW();
        """, (str(self.new_model_info['dimensions']),))

        cursor.execute("""
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES ('last_embedding_migration', %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW();
        """, (datetime.now().isoformat(),))

        cursor.close()

        logger.info("✓ System metadata updated")

    def cleanup_backup(self):
        """Remove backup table after successful migration."""
        if self.dry_run:
            logger.info("[DRY RUN] Would cleanup backup table")
            return

        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS document_chunks_backup_embeddings;")
        cursor.close()

        logger.info("✓ Backup table removed")

    def rollback(self):
        """Rollback migration by restoring from backup."""
        logger.warning("⚠️  Rolling back migration...")

        cursor = self.conn.cursor()

        # Check if backup exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'document_chunks_backup_embeddings'
            );
        """)

        has_backup = cursor.fetchone()[0]

        if not has_backup:
            logger.error("✗ No backup table found - cannot rollback")
            cursor.close()
            return False

        try:
            # Restore original dimensions (assume 384 for all-MiniLM-L6-v2)
            logger.info("Restoring original schema...")
            cursor.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384);")

            # Restore embeddings from backup
            logger.info("Restoring embeddings from backup...")
            cursor.execute("""
                UPDATE document_chunks dc
                SET embedding = b.embedding
                FROM document_chunks_backup_embeddings b
                WHERE dc.id = b.id;
            """)

            # Recreate indexes
            logger.info("Recreating indexes...")
            cursor.execute("""
                CREATE INDEX idx_chunks_embedding ON document_chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)

            cursor.close()

            logger.info("✓ Rollback completed successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Rollback failed: {e}")
            cursor.close()
            return False

    def run_migration(self):
        """Execute the full migration process."""
        try:
            logger.info("="*80)
            logger.info("EMBEDDING MODEL MIGRATION")
            logger.info("="*80)

            # Step 1: Connect to database
            logger.info("\n[Step 1/11] Connecting to database...")
            self.connect_db()

            # Step 2: Get current model info
            logger.info("\n[Step 2/11] Detecting current model...")
            self.current_model_name, self.current_dimensions = self.get_current_model_info()

            if self.current_model_name:
                logger.info(f"  Current model: {self.current_model_name}")
            if self.current_dimensions:
                logger.info(f"  Current dimensions: {self.current_dimensions}")

            # Step 3: Validate new model
            logger.info("\n[Step 3/11] Validating new model...")
            self.validate_new_model()

            # Check if already using this model
            if self.current_model_name == self.new_model_name:
                logger.warning(f"⚠️  Already using model: {self.new_model_name}")
                if not self.dry_run:
                    response = input("Continue anyway? (yes/no): ")
                    if response.lower() != 'yes':
                        logger.info("Migration cancelled")
                        return

            # Step 4: Get statistics
            logger.info("\n[Step 4/11] Gathering database statistics...")
            stats = self.get_statistics()
            logger.info(f"  Total documents: {stats['total_documents']}")
            logger.info(f"  Total chunks: {stats['total_chunks']}")
            logger.info(f"  Chunks with embeddings: {stats['chunks_with_embeddings']}")
            logger.info(f"  Query cache entries: {stats['cache_entries']}")
            logger.info(f"  Database size: {stats['database_size']}")

            # Calculate estimated time
            # Assuming ~50 chunks/second on CPU, ~500 chunks/second on GPU
            chunks_per_sec = 500 if self.use_gpu else 50
            estimated_seconds = stats['total_chunks'] / chunks_per_sec
            estimated_minutes = estimated_seconds / 60

            logger.info(f"\n  Estimated processing time: {estimated_minutes:.1f} minutes")
            logger.info(f"  Using: {'GPU' if self.use_gpu else 'CPU'}")

            # Step 5: Confirm migration
            if not self.dry_run:
                logger.warning("\n⚠️  WARNING: This will modify your database!")
                logger.warning("  - All existing embeddings will be replaced")
                logger.warning("  - Query cache will be cleared")
                logger.warning(f"  - Processing may take {estimated_minutes:.1f} minutes")
                logger.warning("  - A backup will be created for rollback")
                response = input("\nProceed with migration? (type 'YES' to confirm): ")
                if response != 'YES':
                    logger.info("Migration cancelled")
                    return

            # Step 6: Load new model
            logger.info("\n[Step 5/11] Loading new embedding model...")
            self.load_model()

            # Step 7: Create backup
            logger.info("\n[Step 6/11] Creating backup...")
            self.create_backup_table()

            # Step 8: Alter schema
            logger.info("\n[Step 7/11] Altering database schema...")
            self.alter_schema()

            # Step 9: Clear embeddings
            logger.info("\n[Step 8/11] Clearing existing embeddings...")
            self.clear_embeddings()

            # Step 10: Re-embed chunks
            logger.info("\n[Step 9/11] Re-embedding document chunks...")
            success_count, error_count = self.re_embed_chunks()

            if error_count > 0:
                logger.warning(f"⚠️  Completed with {error_count} errors")
                if not self.dry_run:
                    response = input("Continue with index creation? (yes/no): ")
                    if response.lower() != 'yes':
                        logger.info("Rolling back...")
                        self.rollback()
                        return

            # Step 11: Recreate indexes
            logger.info("\n[Step 10/11] Recreating vector indexes...")
            self.recreate_indexes()

            # Step 12: Update metadata
            logger.info("\n[Step 11/11] Updating system metadata...")
            self.update_metadata()

            # Success
            logger.info("\n" + "="*80)
            logger.info("✓ MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("="*80)

            if not self.dry_run:
                logger.info(f"\nNew embedding model: {self.new_model_name}")
                logger.info(f"Dimensions: {self.new_model_info['dimensions']}")
                logger.info(f"Chunks processed: {success_count}")
                logger.info(f"\nBackup table 'document_chunks_backup_embeddings' preserved for safety.")
                logger.info("To remove backup: DROP TABLE document_chunks_backup_embeddings;")
                logger.info("\nREMEMBER: Update your .env file with:")
                logger.info(f"  EMBEDDING_MODEL={self.new_model_name}")

        except Exception as e:
            logger.error(f"\n✗ Migration failed: {e}")
            logger.error("Run with --rollback to restore from backup")
            raise

        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate embedding model and re-process all document chunks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate to all-mpnet-base-v2
  python migrate_embedding_model.py --model sentence-transformers/all-mpnet-base-v2

  # Dry run to see what would happen
  python migrate_embedding_model.py --model sentence-transformers/all-mpnet-base-v2 --dry-run

  # Use smaller batches for memory-constrained systems
  python migrate_embedding_model.py --model BAAI/bge-base-en-v1.5 --batch-size 50

  # Force CPU usage (no GPU)
  python migrate_embedding_model.py --model sentence-transformers/all-MiniLM-L6-v2 --no-gpu

Supported Models:
        """
        + "\n".join([f"  {model} ({info['dimensions']}D)" for model, info in SUPPORTED_MODELS.items()])
    )

    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='New embedding model name (e.g., sentence-transformers/all-mpnet-base-v2)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for re-embedding (default: 100)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without making changes'
    )

    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Force CPU usage even if GPU is available'
    )

    parser.add_argument(
        '--db-host',
        type=str,
        default=os.getenv('POSTGRES_HOST', 'localhost'),
        help='PostgreSQL host (default: from POSTGRES_HOST env or localhost)'
    )

    parser.add_argument(
        '--db-port',
        type=int,
        default=int(os.getenv('POSTGRES_PORT', '5432')),
        help='PostgreSQL port (default: from POSTGRES_PORT env or 5432)'
    )

    parser.add_argument(
        '--db-name',
        type=str,
        default=os.getenv('POSTGRES_DB', 'ragchatbot'),
        help='Database name (default: from POSTGRES_DB env or ragchatbot)'
    )

    parser.add_argument(
        '--db-user',
        type=str,
        default=os.getenv('POSTGRES_USER', 'postgres'),
        help='Database user (default: from POSTGRES_USER env or postgres)'
    )

    parser.add_argument(
        '--db-password',
        type=str,
        default=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        help='Database password (default: from POSTGRES_PASSWORD env or postgres)'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all supported models and exit'
    )

    args = parser.parse_args()

    # List models and exit
    if args.list_models:
        print("\nSupported Embedding Models:")
        print("="*80)
        for model, info in SUPPORTED_MODELS.items():
            print(f"\n{model}")
            print(f"  Dimensions: {info['dimensions']}")
            print(f"  Description: {info['description']}")
            print(f"  Max sequence length: {info['max_seq_length']}")
            print(f"  Recommended for: {info['recommended_for']}")
        print("\n")
        return

    # Create migrator
    migrator = EmbeddingMigrator(
        new_model_name=args.model,
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        use_gpu=not args.no_gpu
    )

    # Run migration
    migrator.run_migration()


if __name__ == '__main__':
    main()
