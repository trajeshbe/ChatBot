import psycopg2
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embedding for test query
query = "handwritten image text"
query_embedding = model.encode(query).tolist()

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ragchatbot",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# Test vector search
cur.execute("""
    SELECT 
        dc.content,
        d.filename,
        1 - (dc.embedding <=> %s::vector) as similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.filename = 'Handwritten.png'
    ORDER BY dc.embedding <=> %s::vector
    LIMIT 3;
""", (query_embedding, query_embedding))

results = cur.fetchall()
print(f"Found {len(results)} results:")
for content, filename, similarity in results:
    print(f"\nFilename: {filename}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Content: {content[:100]}...")

conn.close()
