import os
import sqlite3
import json
from datetime import datetime
import logging
from flask import Flask, render_template, request, g, url_for, redirect, session, flash # Added redirect, session, flash
from flask_session import Session # <-- ADDED IMPORT
from werkzeug.security import generate_password_hash, check_password_hash # <-- ADDED IMPORT
from functools import wraps # <-- ADDED IMPORT for decorator

from azure.storage.blob import BlobServiceClient, ContainerClient
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv # Optional: for local .env file loading

load_dotenv() # Load environment variables from .env file if it exists

# --- Configuration ---
CONTAINER_SAS_URL = os.environ.get("AZURE_CONTAINER_SAS_URL")
DATABASE_FILE = 'feedback.db'
CHECK_INTERVAL_MINUTES = 15
FLASK_PORT = 8888
FLASK_HOST = '0.0.0.0'

# --- Authentication Configuration ---
# WARNING: Hardcoding credentials is NOT recommended for production.
# Move these to environment variables later.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
# Generate a strong hash ONCE for your desired password using a separate script
# Example (run this in a python interpreter):
# >>> from werkzeug.security import generate_password_hash
# >>> print(generate_password_hash('YourChosenPassword', method='pbkdf2:sha256'))
# Then paste the output hash below (or preferably load from env var)
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "pbkdf2:sha256:600000$keyLength...$salt...hash..." # <-- REPLACE WITH YOUR ACTUAL HASH!
)


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Session Configuration ---
# IMPORTANT: Set a strong, random secret key! Load from env var in production.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback-secret-key-CHANGE-ME!')
# Configure session type (filesystem is simple, requires write access in container)
app.config['SESSION_TYPE'] = 'filesystem'
# Optional: Configure session directory (default is flask_session)
# app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
Session(app) # Initialize the session extension
# --- End Session Configuration ---


# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
# --- End Login Required Decorator ---


# --- Database Setup ---
# ... (get_db, close_db, init_db functions remain the same) ...
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
            logging.debug("Database connection opened.")
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database {DATABASE_FILE}: {e}")
            raise # Re-raise the exception to handle it upstream if necessary
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logging.debug("Database connection closed.")
    if error:
        logging.error(f"Error during request teardown: {error}")

def init_db():
    """Initializes the database schema, adding the source_blob_path column if needed."""
    logging.info(f"Attempting to initialize/update database schema in '{DATABASE_FILE}'...")
    conn = None # Initialize conn
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_logs (
                id TEXT PRIMARY KEY, timestamp TIMESTAMP, user_id TEXT, user_email TEXT,
                session_id TEXT, feedback_type TEXT, content TEXT,
                _fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, source_blob_path TEXT
            )""")
        logging.info("CREATE TABLE IF NOT EXISTS executed.")
        try:
            cursor.execute("ALTER TABLE feedback_logs ADD COLUMN source_blob_path TEXT")
            logging.info("Successfully added 'source_blob_path' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logging.info("'source_blob_path' column already exists.")
            else: raise e
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback_logs (timestamp)")
        conn.commit()
        logging.info("Database initialization/update check complete.")
    except sqlite3.Error as e: logging.error(f"Failed to initialize/update database schema: {e}")
    finally:
        if conn: conn.close()


# --- Azure Blob Interaction ---
# ... (fetch_data_from_azure function remains the same) ...
def fetch_data_from_azure():
    """Fetches data from Azure Blob Storage and updates the local database."""
    if not CONTAINER_SAS_URL:
        logging.error("AZURE_CONTAINER_SAS_URL environment variable is not set.")
        return "AZURE_CONTAINER_SAS_URL not configured" # Return error message

    logging.info("Starting Azure Blob data fetch...")
    new_records_count = 0
    processed_files_count = 0
    error_message = None
    conn = None # Initialize connection variable

    try:
        container_client = ContainerClient.from_container_url(CONTAINER_SAS_URL)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            blob_filename = blob.name.split('/')[-1]
            if blob_filename.startswith("feedback_log_") and blob_filename.endswith(".jsonl"):
                logging.info(f"Processing blob: {blob.name}")
                processed_files_count += 1
                try:
                    blob_client = container_client.get_blob_client(blob)
                    downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8', timeout=60)
                    blob_content = downloader.readall()
                    for line_num, line in enumerate(blob_content.splitlines(), 1):
                        line = line.strip()
                        if not line: continue
                        try:
                            data = json.loads(line)
                            feedback_id = data.get("id"); timestamp_str = data.get("timestamp")
                            user_id = data.get("user_id"); user_email = data.get("user_email")
                            session_id = data.get("session_id"); feedback_type = data.get("feedback_type")
                            content = data.get("content")
                            if not all([feedback_id, timestamp_str]):
                                logging.warning(f"Skipping record (line {line_num}) due to missing id/ts in blob {blob.name}: {line[:100]}...")
                                continue
                            try: timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            except ValueError:
                                try: timestamp_dt = datetime.strptime(timestamp_str.replace('Z', '+00:00'), '%Y-%m-%dT%H:%M:%S+00:00')
                                except Exception as ts_err:
                                    logging.warning(f"Could not parse ts '{timestamp_str}' (line {line_num}) in blob {blob.name}: {ts_err}. Skip.")
                                    continue
                            cursor.execute("""INSERT OR IGNORE INTO feedback_logs (id, timestamp, user_id, user_email, session_id, feedback_type, content, source_blob_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                           (feedback_id, timestamp_dt, user_id, user_email, session_id, feedback_type, content, blob.name))
                            if cursor.rowcount > 0: new_records_count += 1
                        except json.JSONDecodeError as json_err: logging.warning(f"Invalid JSON (line {line_num}) in blob {blob.name}: {line[:100]}... - Error: {json_err}")
                        except Exception as parse_err: logging.error(f"Error parsing record (line {line_num}) from blob {blob.name}: {line[:100]}... - Error: {parse_err}")
                except Exception as blob_err:
                    logging.error(f"Error processing blob {blob.name}: {blob_err}")
                    error_message = f"Error processing blob {blob.name}: {blob_err}"
        conn.commit()
        logging.info(f"Azure Blob data fetch complete. Processed {processed_files_count} relevant files. Added {new_records_count} new records.")
    except Exception as e:
        logging.error(f"Failed during Azure fetch task: {e}")
        error_message = f"Failed during Azure fetch task: {e}"
    finally:
        if conn: conn.close(); logging.debug("Fetch task database connection closed.")
    return error_message

# --- Flask Routes ---

# --- Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # !! IMPORTANT: Replace ADMIN_PASSWORD_HASH with your actual generated hash !!
        # In production, load username and hash from environment variables.
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username # Optional: store username if needed later
            flash('Login successful!', 'success')
            # Redirect to the page the user was trying to access, or index
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html'), 401 # Unauthorized status

    # If GET request, just show the login form
    # If already logged in, redirect to index
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('login.html')
# --- End Login Route ---

# --- Logout Route ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
# --- End Logout Route ---


@app.route('/')
@login_required # <-- PROTECTED ROUTE
def index():
    """Main route to display the feedback data, handles sorting and searching."""
    # ... (index function logic remains the same) ...
    db = None; feedback_data = []; fetch_error = None
    search_term = request.args.get('search', '').strip()
    global last_fetch_error
    if last_fetch_error:
        fetch_error = f"Last background fetch failed: {last_fetch_error}"; last_fetch_error = None
    try:
        db = get_db(); cursor = db.cursor()
        sort_by = request.args.get('sort_by', 'timestamp')
        order = request.args.get('order', 'desc').lower()
        allowed_sort_columns = ['id', 'timestamp', 'user_id', 'user_email', 'session_id', 'feedback_type']
        if sort_by not in allowed_sort_columns: sort_by = 'timestamp'
        if order not in ['asc', 'desc']: order = 'desc'
        base_query = "SELECT id, strftime('%Y-%m-%d %H:%M:%S UTC', timestamp) as timestamp, user_id, user_email, session_id, feedback_type, content, source_blob_path FROM feedback_logs"
        params = []; where_clauses = []
        if search_term:
            search_columns = ['id', 'user_id', 'user_email', 'session_id', 'feedback_type', 'content', 'source_blob_path']
            search_pattern = f"%{search_term}%"
            for col in search_columns: where_clauses.append(f"{col} LIKE ?"); params.append(search_pattern)
            sql_where = " WHERE (" + " OR ".join(where_clauses) + ")"; base_query += sql_where
        order_clause = f" ORDER BY {sort_by} {order.upper()}"; query = base_query + order_clause
        logging.debug(f"Executing query: {query}"); logging.debug(f"With params: {params}")
        cursor.execute(query, params)
        feedback_data = cursor.fetchall()
    except sqlite3.Error as db_err:
        logging.error(f"Database query error on index page: {db_err}"); db_error_msg = f"Database error: {db_err}"
        fetch_error = f"{fetch_error}\n{db_error_msg}" if fetch_error else db_error_msg; feedback_data = []
    except Exception as e:
        logging.error(f"Unexpected error on index page: {e}"); general_error_msg = f"Unexpected error: {e}"
        fetch_error = f"{fetch_error}\n{general_error_msg}" if fetch_error else general_error_msg; feedback_data = []
    return render_template('index.html', feedback_data=feedback_data, error=fetch_error, search_term=search_term)


@app.route('/about')
@login_required # <-- PROTECTED ROUTE
def about():
    """Renders the about page."""
    return render_template('about.html')

# --- Scheduler Setup ---
# ... (scheduler setup and scheduled_task function remain the same) ...
scheduler = BackgroundScheduler(daemon=True, timezone='UTC')
last_fetch_error = None
def scheduled_task():
    global last_fetch_error; logging.info("Scheduler triggered: Running scheduled Azure fetch task.")
    with app.app_context():
         try:
            last_fetch_error = fetch_data_from_azure()
            if last_fetch_error: logging.warning(f"Scheduled fetch task completed with error: {last_fetch_error}")
            else: logging.info("Scheduled fetch task completed successfully.")
         except Exception as e: logging.error(f"Exception in scheduled_task wrapper: {e}", exc_info=True); last_fetch_error = f"Exception in scheduler wrapper: {e}"


# --- Initialization ---
init_db()
scheduler.add_job( scheduled_task, 'interval', minutes=CHECK_INTERVAL_MINUTES, id='azure_fetch_job', next_run_time=datetime.utcnow(), misfire_grace_time=60)
scheduler.start()
logging.info(f"Scheduler started. Will check Azure every {CHECK_INTERVAL_MINUTES} minutes, starting now.")
import atexit
atexit.register(lambda: scheduler.shutdown())

# --- Main Execution Block ---
if __name__ == '__main__':
    is_direct_run = os.environ.get('WERKZEUG_RUN_MAIN') != 'true'
    is_gunicorn = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')
    if is_direct_run and not is_gunicorn:
         logging.info(f"Starting Flask development server on {FLASK_HOST}:{FLASK_PORT}")
         app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
