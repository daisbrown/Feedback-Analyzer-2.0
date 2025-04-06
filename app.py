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
FLASK_HOST = '0 build ...` or `docker run ...`. Your currently running `feedback-app-instance` container will continue to run using the *old* image based on the code *before* you made these latest modifications.

The changes will exist safely in your Git history and on GitHub, but they won't affect the live application until you explicitly decide to pull those changes, rebuild the Docker image, and run a new container based on that updated image.

---

Here are the updated files with the minimal changes for better Azure Web App compatibility (persistent sessions, 1 worker):

**1. `app.py` (Complete File - Updated for Azure Web App Minimal Changes)**

*(Only change is adding `app.config['SESSION_FILE_DIR'] = '/home/flask_session'`)

```python
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
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH") # Load from env, no fallback needed if set

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Session Configuration ---
# IMPORTANT: Load from env var in production.
app.0.0.0'

# --- Authentication Configuration ---
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", None) # Rely on env var

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Session Configuration ---
# IMPORTANT: Load SECRET_KEY from environment variable.
app.config['SECRET_KEY'] = os.environ..config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
# --- CHANGE FOR AZURE WEB APP PERSISTENCE ---
# Store session files in the persistent /home directory
app.config['SESSION_FILE_DIR'] = '/home/flask_session'
# --- END CHANGE ---
Session(app) # Initialize the session extension
# --- End Session Configuration ---


# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):get('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    logging.error("FATAL: FLASK_SECRET_KEY environment variable not set.")
    # Optionally, raise an exception or exit if the key is missing in a real deployment
    # raise ValueError("FLASK_
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return fSECRET_KEY is required for session management.")
    app.config['SECRET_KEY'] = 'dev-unsafe-fallback-key' # Unsafe fallback for dev(*args, **kwargs)
    return decorated_function
# --- End only

app.config['SESSION_TYPE'] = 'filesystem'
# Login Required Decorator ---


# --- Database Setup ---
# ... (get *** CHANGE FOR AZURE WEB APP PERSISTENCE ***
# Use the persistent /home directory_db, close_db, init_db functions remain the same) ... in Azure Web Apps
app.config['SESSION_FILE_DIR'] = '/
def get_db():
    """Opens a new database connection if therehome/flask_session'
# Make sure the directory exists (might be needed on is none yet for the current application context."""
    if 'db' not first run or if mapping changes)
if not os.path.exists(app. in g:
        try:
            g.db = sqlite3.config['SESSION_FILE_DIR']):
    try:
        os.makedirs(appconnect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECL.config['SESSION_FILE_DIR'])
        logging.info(f"Created sessionTYPES)
            g.db.row_factory = sqlite3.Row directory: {app.config['SESSION_FILE_DIR']}")
    except # Return rows as dictionary-like objects
            logging.debug("Database connection opened OSError as e:
        logging.error(f"Could not create session directory.")
        except sqlite3.Error as e:
            logging.error {app.config['SESSION_FILE_DIR']}: {e}")
#(f"Error connecting to database {DATABASE_FILE}: {e}")
 *** END CHANGE ***
Session(app)
# --- End Session Configuration ---

            raise # Re-raise the exception to handle it upstream if necessary
    # --- Check if essential Auth config is missing ---
if not ADMIN_PASSWORD_return g.db

@app.teardown_appcontext
defHASH:
     logging.warning("Warning: ADMIN_PASSWORD_HASH environment variable close_db(error):
    """Closes the database again at the not set. Login will likely fail.")

# --- Login Required Decorator ---
def end of the request."""
    db = g.pop('db', None login_required(f):
    @wraps(f)
    )
    if db is not None:
        db.close()
def decorated_function(*args, **kwargs):
        if not session.        logging.debug("Database connection closed.")
    if error:
        get('logged_in'):
            flash('Please log in to access thislogging.error(f"Error during request teardown: {error}")

 page.', 'warning')
            return redirect(url_for('login',def init_db():
    """Initializes the database schema, adding the next=request.url))
        return f(*args, **kwargs)
    return decorated_function
# --- End Login Required Decorator ---


 source_blob_path column if needed."""
    logging.info(f# --- Database Setup ---
# ... (get_db, close_db"Attempting to initialize/update database schema in '{DATABASE_FILE}'..."), init_db functions remain the same) ...
def get_db():
    conn = None # Initialize conn
    try:
        conn =
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
             sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursorg.db = sqlite3.connect(DATABASE_FILE, detect_types()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_logs (
                id TEXT PRIMARY KEY, timestamp TIMESTAMP, user_id TEXT=sqlite3.PARSE_DECLTYPES)
            g.db.row, user_email TEXT,
                session_id TEXT, feedback_type TEXT,_factory = sqlite3.Row
            logging.debug("Database connection opened content TEXT,
                _fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, source.")
        except sqlite3.Error as e:
            logging.error_blob_path TEXT
            )""")
        logging.info("CREATE(f"Error connecting to database {DATABASE_FILE}: {e}")
 TABLE IF NOT EXISTS executed.")
        try:
            cursor.execute("            raise
    return g.db

@app.teardown_ALTER TABLE feedback_logs ADD COLUMN source_blob_path TEXT")
            appcontext
def close_db(error):
    """Closes thelogging.info("Successfully added 'source_blob_path' column.")
 database again at the end of the request."""
    db = g.pop        except sqlite3.OperationalError as e:
            if "duplicate column('db', None)
    if db is not None: db.close(); name" in str(e).lower():
                logging.info("'source logging.debug("Database connection closed.")
    if error: logging.error(f"Error during request teardown: {error}")

def init_db():
    """Initializes the database schema, adding the source_blob_blob_path' column already exists.")
            else: raise e
_path column if needed."""
    logging.info(f"Attempting        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback_ to initialize/update database schema in '{DATABASE_FILE}'...")
    connlogs (timestamp)")
        conn.commit()
        logging.info(" = None
    try:
        conn = sqlite3.connect(DATABASE_FILE);Database initialization/update check complete.")
    except sqlite3.Error as e cursor = conn.cursor()
        cursor.execute(""" CREATE TABLE IF NOT EXISTS feedback_logs ( id TEXT PRIMARY KEY, timestamp TIMESTAMP, user_id TEXT,: logging.error(f"Failed to initialize/update database schema: {e}") user_email TEXT, session_id TEXT, feedback_type TEXT, content TEXT,
    finally:
        if conn: conn.close()


# --- Azure Blob Interaction ---
# ... (fetch_data_from_azure function _fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, source_blob_path TEXT remains the same) ...
def fetch_data_from_azure():
 ) """)
        logging.info("CREATE TABLE IF NOT EXISTS executed.")
        try    """Fetches data from Azure Blob Storage and updates the local database."""
: cursor.execute("ALTER TABLE feedback_logs ADD COLUMN source_blob_    if not CONTAINER_SAS_URL:
        logging.error("AZURE_CONTAINER_SAS_URL environment variable is not set.")
        path TEXT"); logging.info("Added 'source_blob_path' columnreturn "AZURE_CONTAINER_SAS_URL not configured" # Return.")
        except sqlite3.OperationalError as e:
            if "duplicate error message

    logging.info("Starting Azure Blob data fetch...")
     column name" in str(e).lower(): logging.info("'source_blob_pathnew_records_count = 0
    processed_files_count = ' column exists.")
            else: raise e
        cursor.execute("CREATE INDEX IF0
    error_message = None
    conn = None # Initialize connection NOT EXISTS idx_timestamp ON feedback_logs (timestamp)")
        conn.commit(); logging.info("Database initialization/update check complete.")
    except sqlite3 variable

    try:
        container_client = ContainerClient.from_.Error as e: logging.error(f"Failed to initialize/update database schema: {e}")
    finally:
        if conn: conn.close()container_url(CONTAINER_SAS_URL)
        conn = sqlite


# --- Azure Blob Interaction ---
# ... (fetch_data_from_azure function remains the same) ...
def fetch_data_from_3.connect(DATABASE_FILE)
        cursor = conn.cursor()azure():
    """Fetches data from Azure Blob Storage and updates the local
        blob_list = container_client.list_blobs()
 database."""
    if not CONTAINER_SAS_URL: logging.error("        for blob in blob_list:
            blob_filename = blob.name.split('/')[-1]
            if blob_filename.startswith("feedback_logAZURE_CONTAINER_SAS_URL env var not set."); return "AZURE_") and blob_filename.endswith(".jsonl"):
                logging._CONTAINER_SAS_URL not configured"
    logging.info("info(f"Processing blob: {blob.name}")
                processed_Starting Azure Blob data fetch...")
    new_records_count = 0; processed_files_count = 0; error_message = None; conn =files_count += 1
                try:
                    blob_client = None
    try:
        container_client = ContainerClient.from_ container_client.get_blob_client(blob)
                    downloader =container_url(CONTAINER_SAS_URL); conn = sqlite3. blob_client.download_blob(max_concurrency=1, encodingconnect(DATABASE_FILE); cursor = conn.cursor()
        blob_='UTF-8', timeout=60)
                    blob_content =list = container_client.list_blobs()
        for blob in blob_list downloader.readall()
                    for line_num, line in enumerate(:
            blob_filename = blob.name.split('/')[-1]blob_content.splitlines(), 1):
                        line = line.
            if blob_filename.startswith("feedback_log_") and blobstrip()
                        if not line: continue
                        try:
                            data = json.loads(line)
                            feedback_id = data.get_filename.endswith(".jsonl"):
                logging.info(f"Processing blob: {blob.name}"); processed_files_count += 1("id"); timestamp_str = data.get("timestamp")
                            user
                try:
                    blob_client = container_client.get__id = data.get("user_id"); user_email = datablob_client(blob)
                    downloader = blob_client.download_blob(.get("user_email")
                            session_id = data.getmax_concurrency=1, encoding='UTF-8', timeout=6("session_id"); feedback_type = data.get("feedback_type0)
                    blob_content = downloader.readall()
                    for line_")
                            content = data.get("content")
                            if not allnum, line in enumerate(blob_content.splitlines(), 1):([feedback_id, timestamp_str]):
                                logging.warning(f
                        line = line.strip();
                        if not line: continue
                        "Skipping record (line {line_num}) due to missing id/try:
                            data = json.loads(line)
                            feedback_ts in blob {blob.name}: {line[:100]}...")id=data.get("id"); timestamp_str=data.get("timestamp");
                                continue
                            try: timestamp_dt = datetime.fromisoformat user_id=data.get("user_id"); user_email=(timestamp_str.replace('Z', '+00:00'))data.get("user_email"); session_id=data.get("
                            except ValueError:
                                try: timestamp_dt = datetime.strptimesession_id"); feedback_type=data.get("feedback_type");(timestamp_str.replace('Z', '+00:00'), content=data.get("content")
                            if not all([feedback_ '%Y-%m-%dT%H:%M:%S+00:id, timestamp_str]): logging.warning(f"Skip line {line_num00')
                                except Exception as ts_err:
                                    logging.warning(f"Could not parse ts '{timestamp_str}' (line} missing id/ts in {blob.name}: {line[:100]}..."); {line_num}) in blob {blob.name}: {ts_err continue
                            try: timestamp_dt = datetime.fromisoformat(timestamp}. Skip.")
                                    continue
                            cursor.execute("""INSERT OR IG_str.replace('Z', '+00:00'))
                            except ValueError:
                                try: timestamp_dt = datetime.strptime(timestampNORE INTO feedback_logs (id, timestamp, user_id, user__str.replace('Z', '+00:00'), '%Yemail, session_id, feedback_type, content, source_blob_-%m-%dT%H:%M:%S+00:00path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                           (feedback_id')
                                except Exception as ts_err: logging.warning(f", timestamp_dt, user_id, user_email, session_id, feedback_type, content, blob.name))
                            if cursor.Could not parse ts '{timestamp_str}' line {line_num} in {rowcount > 0: new_records_count += 1
                        blob.name}: {ts_err}. Skip."); continue
                            cursor.except json.JSONDecodeError as json_err: logging.warning(fexecute("""INSERT OR IGNORE INTO feedback_logs (id, timestamp, user"Invalid JSON (line {line_num}) in blob {blob.name_id, user_email, session_id, feedback_type, content}: {line[:100]}... - Error: {json_err, source_blob_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)}")
                        except Exception as parse_err: logging.error(f"Error parsing record (line {line_num}) from blob {blob.name""", (feedback_id, timestamp_dt, user_id, user_}: {line[:100]}... - Error: {parse_erremail, session_id, feedback_type, content, blob.name))}")
                except Exception as blob_err:
                    logging.error(
                            if cursor.rowcount > 0: new_records_countf"Error processing blob {blob.name}: {blob_err}")
 += 1
                        except json.JSONDecodeError as json_err:                    error_message = f"Error processing blob {blob.name}: { logging.warning(f"Invalid JSON line {line_num} in {blobblob_err}"
        conn.commit()
        logging.info(f"Azure.name}: {line[:100]}... Err: {json_err}")
                        except Exception as parse_err: logging.error(f Blob data fetch complete. Processed {processed_files_count} relevant files"Error parsing record line {line_num} from {blob.name}: {line[:. Added {new_records_count} new records.")
    except Exception100]}... Err: {parse_err}")
                except Exception as e:
        logging.error(f"Failed during Azure fetch task as blob_err: logging.error(f"Error processing blob {blob: {e}")
        error_message = f"Failed during Azure fetch.name}: {blob_err}"); error_message = f"Error processing task: {e}"
    finally:
        if conn: conn. {blob.name}: {blob_err}"
        conn.commit();close(); logging.debug("Fetch task database connection closed.")
    return error logging.info(f"Azure fetch complete. Processed {processed_files_message

# --- Flask Routes ---

# --- Login Route ---
@app_count} relevant files. Added {new_records_count} new records.route('/login', methods=['GET', 'POST'])
def login():.")
    except Exception as e: logging.error(f"Failed Azure
    if request.method == 'POST':
        username = request.form. fetch task: {e}"); error_message = f"Failed Azure fetch task: {get('username')
        password = request.form.get('password')e}"
    finally:
        if conn: conn.close(); logging
        if not ADMIN_PASSWORD_HASH: # Check if hash is loaded
            flash('Authentication is not configured correctly.', 'danger')
            return render_template('login.debug("Fetch task db conn closed.")
    return error_message

# --- Flask.html'), 500

        if username == ADMIN_USERNAME and Routes ---

# --- Login Route ---
@app.route('/login', methods=['GET check_password_hash(ADMIN_PASSWORD_HASH, password):
            ', 'POST'])
def login():
    if request.method == 'session['logged_in'] = True
            session['username'] = usernamePOST':
        username = request.form.get('username')
         # Optional: store username if needed later
            flash('Login successful!', 'password = request.form.get('password')
        if not ADMIN_success')
            next_page = request.args.get('next')PASSWORD_HASH:
            flash('Application authentication is not configured correctly.', 'danger')
            return render_template('login.html'), 500 # Internal Server Error

            return redirect(next_page or url_for('index'))
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH        else:
            flash('Invalid username or password.', 'danger')
, password):
            session['logged_in'] = True
            session            return render_template('login.html'), 401 # Unauthorized status
['username'] = username
            flash('Login successful!', 'success')
    if session.get('logged_in'): return redirect(url_for('index'))            next_page = request.args.get('next')
            return
    return render_template('login.html')
# --- End Login redirect(next_page or url_for('index'))
        else: Route ---

# --- Logout Route ---
@app.route('/logout')
            flash('Invalid username or password.', 'danger')
            return render_template('login.html'), 401
    if session.get('
def logout():
    session.pop('logged_in', None)logged_in'): return redirect(url_for('index'))
    return
    session.pop('username', None)
    flash('You have render_template('login.html')
# --- End Login Route ---

 been logged out.', 'info')
    return redirect(url_for('# --- Logout Route ---
@app.route('/logout')
def logoutlogin'))
# --- End Logout Route ---


@app.route('/')
@login_():
    session.pop('logged_in', None); session.pop('username', None)
    flash('You have been logged out.', 'required # <-- PROTECTED ROUTE
def index():
    # ... (index functioninfo')
    return redirect(url_for('login'))
# --- logic remains the same) ...
    db = None; feedback_data = End Logout Route ---

@app.route('/')
@login_required # []; fetch_error = None
    search_term = request.args.get('search', '').strip()
    global last_fetch_error
 <-- PROTECTED ROUTE
def index():
    # ... (index function    if last_fetch_error:
        fetch_error = f"Last background fetch failed: {last_fetch_error}"; last_fetch_ logic remains the same) ...
    db = None; feedback_data = []; fetch_error = None; search_term = request.args.get('searcherror = None
    try:
        db = get_db(); cursor', '').strip()
    global last_fetch_error
    if last_ = db.cursor()
        sort_by = request.args.get('sort_by', 'timestamp')
        order = request.args.fetch_error: fetch_error = f"Last fetch failed: {last_fetch_error}"; last_fetch_error = None
    try:get('order', 'desc').lower()
        allowed_sort_columns = ['id', 'timestamp', 'user_id', 'user_email
        db = get_db(); cursor = db.cursor(); sort_by =', 'session_id', 'feedback_type']
        if sort_ request.args.get('sort_by', 'timestamp'); order = request.args.get('order', 'desc').lower()
        allowed_by not in allowed_sort_columns: sort_by = 'timestamp'
        if order not in ['asc', 'desc']: order = 'descsort_columns = ['id', 'timestamp', 'user_id', ''
        base_query = "SELECT id, strftime('%Y-%user_email', 'session_id', 'feedback_type']
        if sort_by not in allowed_sort_columns: sort_by = 'timestampm-%d %H:%M:%S UTC', timestamp) as timestamp, user_id, user_email, session_id, feedback_type,'
        if order not in ['asc', 'desc']: order = ' content, source_blob_path FROM feedback_logs"
        params = []; where_desc'
        base_query = "SELECT id, strftime('%Yclauses = []
        if search_term:
            search_columns-%m-%d %H:%M:%S UTC', timestamp) as timestamp = ['id', 'user_id', 'user_email', 'session, user_id, user_email, session_id, feedback_type_id', 'feedback_type', 'content', 'source_blob_path']
            search_pattern = f"%{search_term}%", content, source_blob_path FROM feedback_logs"
        params
            for col in search_columns: where_clauses.append( = []; where_clauses = []
        if search_term:
f"{col} LIKE ?"); params.append(search_pattern)
            search_columns = ['id', 'user_id', 'user_            sql_where = " WHERE (" + " OR ".join(where_clauses) + ")"; base_query += sql_where
        order_clause = femail', 'session_id', 'feedback_type', 'content', 'source_blob_path']; search_pattern = f"%{search_term}%"" ORDER BY {sort_by} {order.upper()}"; query = base_query + order_clause
        logging.debug(f"Executing query: {query}"); logging.debug(f"With params: {params
            for col in search_columns: where_clauses.append(}")
        cursor.execute(query, params)
        feedback_dataf"{col} LIKE ?"); params.append(search_pattern)
 = cursor.fetchall()
    except sqlite3.Error as db_err            base_query += " WHERE (" + " OR ".join(where_clauses):
        logging.error(f"Database query error on index page: + ")"
        query = base_query + f" ORDER BY {sort_by} {db_err}"); db_error_msg = f"Database error: {db_err}"
        fetch_error = f"{fetch_error}\ {order.upper()}"
        logging.debug(f"Query: {query},n{db_error_msg}" if fetch_error else db_error Params: {params}"); cursor.execute(query, params); feedback_data = cursor_msg; feedback_data = []
    except Exception as e:
.fetchall()
    except sqlite3.Error as db_err: logging        logging.error(f"Unexpected error on index page: {e}");.error(f"DB query error: {db_err}"); db_ general_error_msg = f"Unexpected error: {e}"
        error_msg = f"Database error: {db_err}"; fetch_error = ffetch_error = f"{fetch_error}\n{general_error_msg}" if fetch_error else general_error_msg; feedback_data"{fetch_error}\n{db_error_msg}" if fetch_error else db = []
    return render_template('index.html', feedback_data=feedback_data, error=fetch_error, search_term=search_error_msg; feedback_data = []
    except Exception as e_term)


@app.route('/about')
@login_required: logging.error(f"Unexpected index error: {e}"); general_error_msg # <-- PROTECTED ROUTE
def about():
    return render_template(' = f"Unexpected error: {e}"; fetch_error = f"{fetchabout.html')

# --- Scheduler Setup ---
# ... (scheduler setup_error}\n{general_error_msg}" if fetch_error else and scheduled_task function remain the same) ...
scheduler = BackgroundScheduler( general_error_msg; feedback_data = []
    return render_daemon=True, timezone='UTC')
last_fetch_error = None
def scheduled_task():
    global last_fetch_error; loggingtemplate('index.html', feedback_data=feedback_data, error=fetch_error, search_term=search_term)


@app.route.info("Scheduler triggered: Running scheduled Azure fetch task.")
    with app('/about')
@login_required # <-- PROTECTED ROUTE
def about.app_context():
         try:
            last_fetch_error = fetch_():
    return render_template('about.html')

# --- Schedulerdata_from_azure()
            if last_fetch_error: logging.warning(f"Scheduled fetch task completed with error: {last_fetch Setup ---
scheduler = BackgroundScheduler(daemon=True, timezone='UTC')_error}")
            else: logging.info("Scheduled fetch task completed successfully
last_fetch_error = None
def scheduled_task():
    .")
         except Exception as e: logging.error(f"Exception in scheduled_taskglobal last_fetch_error; logging.info("Scheduler trigger: Azure fetch task.")
 wrapper: {e}", exc_info=True); last_fetch_error    with app.app_context():
         try:
            last_fetch_error = fetch_data_from_azure()
            if last_fetch_error: logging.warning(f"Scheduled fetch error: {last_fetch_error}")
            else: logging.info("Scheduled fetch OK.")
         except = f"Exception in scheduler wrapper: {e}"


# --- Initialization ---
init_db()
scheduler.add_job( scheduled_task, Exception as e: logging.error(f"Scheduler wrapper exception: {e}", exc_info=True); last_fetch_error = f"Scheduler wrapper 'interval', minutes=CHECK_INTERVAL_MINUTES, id='azure_ exception: {e}"

# --- Initialization ---
init_db()
scheduler.add_job( scheduled_task, 'interval', minutes=CHECKfetch_job', next_run_time=datetime.utcnow(), misfire_grace_time=60)
scheduler.start()
logging._INTERVAL_MINUTES, id='azure_fetch_job', next_info(f"Scheduler started. Will check Azure every {CHECK_INTERVAL_run_time=datetime.utcnow(), misfire_grace_time=6MINUTES} minutes, starting now.")
import atexit
atexit0)
scheduler.start()
logging.info(f"Scheduler started.register(lambda: scheduler.shutdown())

# --- Main Execution Block ---. Check Azure every {CHECK_INTERVAL_MINUTES} mins.")
import a
if __name__ == '__main__':
    is_direct_runtexit
atexit.register(lambda: scheduler.shutdown())

# = os.environ.get('WERKZEUG_RUN_MAIN') != 'true'
    is_gunicorn = 'gunicorn' in --- Main Execution Block ---
if __name__ == '__main__':
     os.environ.get('SERVER_SOFTWARE', '')
    if is_direct_run and not is_gunicorn:
         # Check for required envis_direct_run = os.environ.get('WERKZEUG vars on direct run for better feedback
         if not all([os.environ_RUN_MAIN') != 'true'
    is_gunicorn =.get('FLASK_SECRET_KEY'), ADMIN_PASSWORD_HASH, 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '') CONTAINER_SAS_URL]):
              logging.error("Missing required environment variables (
    if is_direct_run and not is_gunicorn:
FLASK_SECRET_KEY, ADMIN_PASSWORD_HASH, AZURE_CONTAINER         logging.info(f"Starting Flask dev server on {FLASK_HOST}:{_SAS_URL). Cannot start.")
         else:
              logging.info(FLASK_PORT}")
         # Check for essential config on startup for dev serverf"Starting Flask development server on {FLASK_HOST}:{FLASK_
         if not app.config['SECRET_KEY'] or app.config['SECRETPORT}")
              app.run(host=FLASK_HOST, port_KEY'] == 'fallback-secret-key-CHANGE-ME!':
             logging=FLASK_PORT, debug=False)
