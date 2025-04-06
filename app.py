import os
import sqlite3
import json
from datetime import datetime
import logging
from flask import Flask, render_template, request, g, url_for # Removed redirect, session, flash
# Removed Flask-Session and werkzeug imports
# Removed functools wraps import
from azure.storage.blob import BlobServiceClient, ContainerClient
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
CONTAINER_SAS_URL = os.environ.get("AZURE_CONTAINER_SAS_URL")
DATABASE_FILE = 'feedback.db'
CHECK_INTERVAL_MINUTES = 15
FLASK_PORT = 8888
FLASK_HOST = '0.0.0.0'
# Removed Authentication Configuration
# Removed SECRET_KEY configuration

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)
# Removed Session initialization

# Removed Login Required Decorator

# --- Database Setup ---
# ... (get_db, close_db, init_db functions remain the same as the version WITH the source_blob_path column) ...
def get_db():
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
            logging.debug("Database connection opened.")
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database {DATABASE_FILE}: {e}")
            raise
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None: db.close(); logging.debug("Database connection closed.")
    if error: logging.error(f"Error during request teardown: {error}")

def init_db():
    logging.info(f"Attempting to initialize/update database schema in '{DATABASE_FILE}'...")
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE); cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS feedback_logs (id TEXT PRIMARY KEY, timestamp TIMESTAMP, user_id TEXT, user_email TEXT, session_id TEXT, feedback_type TEXT, content TEXT, _fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, source_blob_path TEXT)""")
        logging.info("CREATE TABLE IF NOT EXISTS executed.")
        try:
            cursor.execute("ALTER TABLE feedback_logs ADD COLUMN source_blob_path TEXT"); logging.info("Added 'source_blob_path' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower(): logging.info("'source_blob_path' column exists.")
            else: raise e
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback_logs (timestamp)")
        conn.commit(); logging.info("Database initialization/update check complete.")
    except sqlite3.Error as e: logging.error(f"Failed to initialize/update database schema: {e}")
    finally:
        if conn: conn.close()


# --- Azure Blob Interaction ---
# ... (fetch_data_from_azure function remains the same) ...
def fetch_data_from_azure():
    if not CONTAINER_SAS_URL: logging.error("AZURE_CONTAINER_SAS_URL env var not set."); return "AZURE_CONTAINER_SAS_URL not configured"
    logging.info("Starting Azure Blob data fetch...")
    new_records_count = 0; processed_files_count = 0; error_message = None; conn = None
    try:
        container_client = ContainerClient.from_container_url(CONTAINER_SAS_URL); conn = sqlite3.connect(DATABASE_FILE); cursor = conn.cursor()
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            blob_filename = blob.name.split('/')[-1]
            if blob_filename.startswith("feedback_log_") and blob_filename.endswith(".jsonl"):
                logging.info(f"Processing blob: {blob.name}"); processed_files_count += 1
                try:
                    blob_client = container_client.get_blob_client(blob)
                    downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8', timeout=60)
                    blob_content = downloader.readall()
                    for line_num, line in enumerate(blob_content.splitlines(), 1):
                        line = line.strip();
                        if not line: continue
                        try:
                            data = json.loads(line)
                            feedback_id=data.get("id"); timestamp_str=data.get("timestamp"); user_id=data.get("user_id"); user_email=data.get("user_email"); session_id=data.get("session_id"); feedback_type=data.get("feedback_type"); content=data.get("content")
                            if not all([feedback_id, timestamp_str]): logging.warning(f"Skip line {line_num} missing id/ts in {blob.name}: {line[:100]}..."); continue
                            try: timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            except ValueError:
                                try: timestamp_dt = datetime.strptime(timestamp_str.replace('Z', '+00:00'), '%Y-%m-%dT%H:%M:%S+00:00')
                                except Exception as ts_err: logging.warning(f"Could not parse ts '{timestamp_str}' line {line_num} in {blob.name}: {ts_err}. Skip."); continue
                            cursor.execute("""INSERT OR IGNORE INTO feedback_logs (id, timestamp, user_id, user_email, session_id, feedback_type, content, source_blob_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (feedback_id, timestamp_dt, user_id, user_email, session_id, feedback_type, content, blob.name))
                            if cursor.rowcount > 0: new_records_count += 1
                        except json.JSONDecodeError as json_err: logging.warning(f"Invalid JSON line {line_num} in {blob.name}: {line[:100]}... Err: {json_err}")
                        except Exception as parse_err: logging.error(f"Error parsing record line {line_num} from {blob.name}: {line[:100]}... Err: {parse_err}")
                except Exception as blob_err: logging.error(f"Error processing blob {blob.name}: {blob_err}"); error_message = f"Error processing {blob.name}: {blob_err}"
        conn.commit(); logging.info(f"Azure fetch complete. Processed {processed_files_count} relevant files. Added {new_records_count} new records.")
    except Exception as e: logging.error(f"Failed Azure fetch task: {e}"); error_message = f"Failed Azure fetch task: {e}"
    finally:
        if conn: conn.close(); logging.debug("Fetch task db conn closed.")
    return error_message

# --- Flask Routes ---
# Removed Login and Logout Routes

@app.route('/')
# Removed @login_required
def index():
    """Main route to display the feedback data, handles sorting and searching."""
    db = None; feedback_data = []; fetch_error = None;
    search_term = request.args.get('search', '').strip() # Keep search term handling
    global last_fetch_error
    if last_fetch_error: fetch_error = f"Last fetch failed: {last_fetch_error}"; last_fetch_error = None
    try:
        db = get_db(); cursor = db.cursor(); sort_by = request.args.get('sort_by', 'timestamp'); order = request.args.get('order', 'desc').lower()
        allowed_sort_columns = ['id', 'timestamp', 'user_id', 'user_email', 'session_id', 'feedback_type']
        if sort_by not in allowed_sort_columns: sort_by = 'timestamp'
        if order not in ['asc', 'desc']: order = 'desc'
        base_query = "SELECT id, strftime('%Y-%m-%d %H:%M:%S UTC', timestamp) as timestamp, user_id, user_email, session_id, feedback_type, content, source_blob_path FROM feedback_logs"
        params = []; where_clauses = []
        if search_term:
            search_columns = ['id', 'user_id', 'user_email', 'session_id', 'feedback_type', 'content', 'source_blob_path']; search_pattern = f"%{search_term}%"
            for col in search_columns: where_clauses.append(f"{col} LIKE ?"); params.append(search_pattern)
            base_query += " WHERE (" + " OR ".join(where_clauses) + ")"
        query = base_query + f" ORDER BY {sort_by} {order.upper()}"
        logging.debug(f"Query: {query}, Params: {params}"); cursor.execute(query, params); feedback_data = cursor.fetchall()
    except sqlite3.Error as db_err: logging.error(f"DB query error: {db_err}"); db_error_msg = f"Database error: {db_err}"; fetch_error = f"{fetch_error}\n{db_error_msg}" if fetch_error else db_error_msg; feedback_data = []
    except Exception as e: logging.error(f"Unexpected index error: {e}"); general_error_msg = f"Unexpected error: {e}"; fetch_error = f"{fetch_error}\n{general_error_msg}" if fetch_error else general_error_msg; feedback_data = []
    # Note: No need to pass search_term explicitly if template uses request.args directly
    return render_template('index.html', feedback_data=feedback_data, error=fetch_error) # Removed search_term=search_term

@app.route('/about')
# Removed @login_required
def about():
    """Renders the about page."""
    return render_template('about.html')

# --- Scheduler Setup ---
# ... (scheduler setup and scheduled_task function remain the same) ...
scheduler = BackgroundScheduler(daemon=True, timezone='UTC')
last_fetch_error = None
def scheduled_task():
    global last_fetch_error; logging.info("Scheduler trigger: Azure fetch task.")
    with app.app_context():
         try:
            last_fetch_error = fetch_data_from_azure()
            if last_fetch_error: logging.warning(f"Scheduled fetch error: {last_fetch_error}")
            else: logging.info("Scheduled fetch OK.")
         except Exception as e: logging.error(f"Scheduler wrapper exception: {e}", exc_info=True); last_fetch_error = f"Scheduler wrapper exception: {e}"

# --- Initialization ---
init_db()
scheduler.add_job( scheduled_task, 'interval', minutes=CHECK_INTERVAL_MINUTES, id='azure_fetch_job', next_run_time=datetime.utcnow(), misfire_grace_time=60)
scheduler.start()
logging.info(f"Scheduler started. Check Azure every {CHECK_INTERVAL_MINUTES} mins.")
import atexit
atexit.register(lambda: scheduler.shutdown())

# --- Main Execution Block ---
if __name__ == '__main__':
    is_direct_run = os.environ.get('WERKZEUG_RUN_MAIN') != 'true'
    is_gunicorn = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')
    if is_direct_run and not is_gunicorn:
         # Removed checks for auth env vars
         logging.info(f"Starting Flask dev server on {FLASK_HOST}:{FLASK_PORT}")
         app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
