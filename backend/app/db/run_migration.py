import os
import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.smetttihilrpbucbhsmf:SB8YAmxREv4hrsux@aws-1-eu-west-3.pooler.supabase.com:5432/postgres"
)

def run_migration():
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_migration.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"Connecting to Supabase PostgreSQL at aws-1-eu-west-3.pooler.supabase.com:5432...")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()

    print("Running migration SQL script...")
    cur.execute(sql_content)
    cur.close()
    conn.close()
    print("Migration completed successfully! All tables and indexes are ready.")

if __name__ == "__main__":
    run_migration()
