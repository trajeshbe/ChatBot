"""
Test British Council Export Package Generation
Tests the export functionality for British Council module
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.export_service import ExportService
from app.core.database import SessionLocal
from pathlib import Path
import json

def test_british_council_export():
    """Test British Council module export package generation"""
    print("\n" + "="*80)
    print("BRITISH COUNCIL - Export Package Generation Test")
    print("="*80)
    
    db = SessionLocal()
    export_service = ExportService(db)
    
    try:
        # Create export package for British Council module
        print("\n📦 Creating British Council export package...")
        
        result = export_service.create_export_package(
            customer_name="Test Customer",
            module_ids=["british_council"],
            include_documents=True,
            include_embeddings=True,
            session_id=None  # Export all British Council data
        )
        
        print(f"\n✅ Export package created successfully!")
        print(f"\nPackage Details:")
        print(f"  📄 Filename: {result['filename']}")
        print(f"  📊 Size: {result['size']:,} bytes ({result['size']/1024/1024:.2f} MB)")
        print(f"  🔑 Package ID: {result['package_id']}")
        print(f"  📅 Created: {result['created_at']}")
        print(f"  ⚙️ Status: {result['status']}")
        
        if 'metadata' in result and result['metadata']:
            metadata = result['metadata']
            print(f"\n📋 Package Contents:")
            print(f"  📚 Documents: {metadata.get('document_count', 0)}")
            print(f"  🔢 Embeddings: {metadata.get('embedding_count', 0)}")
            print(f"  📄 Backend files: {metadata.get('backend_files', 0)}")
            print(f"  🏗️ Tier1 files: {metadata.get('tier1_files', 0)}")
            print(f"  📦 Dependencies: {metadata.get('python_deps', 0)}")
        
        # Verify the file exists
        export_dir = Path("/app/backend/exports")
        export_file = export_dir / result['filename']
        
        if export_file.exists():
            print(f"\n✅ Export file verified at: {export_file}")
            actual_size = export_file.stat().st_size
            print(f"  📊 Actual file size: {actual_size:,} bytes ({actual_size/1024/1024:.2f} MB)")
            
            # List contents
            print(f"\n📂 Package Contents:")
            import subprocess
            contents = subprocess.run(
                ['tar', '-tzf', str(export_file)],
                capture_output=True,
                text=True
            )
            
            if contents.returncode == 0:
                lines = contents.stdout.strip().split('\n')
                print(f"  Total files: {len(lines)}")
                print(f"\n  Top-level structure:")
                for line in lines[:20]:
                    print(f"    {line}")
                if len(lines) > 20:
                    print(f"    ... and {len(lines) - 20} more files")
            
            return True
        else:
            print(f"\n❌ Export file not found at: {export_file}")
            return False
            
    except Exception as e:
        print(f"\n❌ Export generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_british_council_export()
    print("\n" + "="*80)
    if success:
        print("RESULT: ✅ British Council export package generated and verified")
    else:
        print("RESULT: ❌ British Council export package generation failed")
    print("="*80)
    exit(0 if success else 1)
