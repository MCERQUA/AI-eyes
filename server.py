#!/usr/bin/env python3
"""
Pi-Guy Vision Server
Handles vision requests from ElevenLabs agent using Gemini Vision API
Also handles face recognition using DeepFace
Also handles user usage tracking
"""

import os
import base64
import json
import shutil
import tempfile
import sqlite3
import subprocess
import time
import psutil
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ===== USER USAGE TRACKING =====
MONTHLY_LIMIT = 20  # Max agent responses per user per month
UNLIMITED_USERS = ['user_365rT7sUqN11BDW5TTlt0FAMZWo']  # Mike - unlimited for testing
DB_PATH = Path(__file__).parent / "usage.db"

def init_db():
    """Initialize the usage database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage (
            user_id TEXT PRIMARY KEY,
            message_count INTEGER DEFAULT 0,
            month TEXT,
            updated_at TEXT
        )
    ''')
    # Jobs table for scheduled tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            job_type TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            cron_expression TEXT,
            next_run TEXT,
            last_run TEXT,
            status TEXT DEFAULT 'pending',
            action TEXT NOT NULL,
            action_params TEXT,
            result TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    # Job history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            run_at TEXT,
            status TEXT,
            result TEXT,
            duration_ms INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_current_month():
    return datetime.now().strftime('%Y-%m')

def get_user_usage(user_id):
    """Get user's message count for current month"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = get_current_month()

    c.execute('SELECT message_count, month FROM usage WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        count, month = row
        # Reset if new month
        if month != current_month:
            return 0
        return count
    return 0

def increment_usage(user_id):
    """Increment user's message count"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = get_current_month()
    now = datetime.now().isoformat()

    c.execute('SELECT month FROM usage WHERE user_id = ?', (user_id,))
    row = c.fetchone()

    if row:
        if row[0] != current_month:
            # New month, reset count
            c.execute('UPDATE usage SET message_count = 1, month = ?, updated_at = ? WHERE user_id = ?',
                     (current_month, now, user_id))
        else:
            c.execute('UPDATE usage SET message_count = message_count + 1, updated_at = ? WHERE user_id = ?',
                     (now, user_id))
    else:
        c.execute('INSERT INTO usage (user_id, message_count, month, updated_at) VALUES (?, 1, ?, ?)',
                 (user_id, current_month, now))

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Face recognition setup
KNOWN_FACES_DIR = Path(__file__).parent / "known_faces"
KNOWN_FACES_DIR.mkdir(exist_ok=True)
FACE_OWNERS_FILE = Path(__file__).parent / "face_owners.json"

def load_face_owners():
    """Load face ownership data (which Clerk user owns which face name)"""
    if FACE_OWNERS_FILE.exists():
        with open(FACE_OWNERS_FILE) as f:
            return json.load(f)
    return {}

def save_face_owners(owners):
    """Save face ownership data"""
    with open(FACE_OWNERS_FILE, 'w') as f:
        json.dump(owners, f, indent=2)

# Lazy load DeepFace (it's heavy)
_deepface = None
def get_deepface():
    global _deepface
    if _deepface is None:
        from deepface import DeepFace
        _deepface = DeepFace
    return _deepface

# Current identified person (persists during session)
current_identity = None

@app.route('/')
def serve_index():
    """Serve the main index.html page"""
    return send_file('index.html')

@app.route('/known_faces/<name>/<filename>')
def serve_face_photo(name, filename):
    """Serve face photos for the My Face section"""
    photo_path = KNOWN_FACES_DIR / name / filename
    if photo_path.exists():
        return send_file(photo_path)
    return jsonify({"error": "Photo not found"}), 404

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Store the latest frame from the client
latest_frame = None

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "pi-guy-vision"})

@app.route('/api/frame', methods=['POST'])
def receive_frame():
    """Receive a frame from the client's camera"""
    global latest_frame

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    latest_frame = data['image']  # base64 encoded image
    return jsonify({"status": "frame received"})

@app.route('/api/vision', methods=['POST'])
def vision():
    """
    ElevenLabs tool endpoint - analyze what the camera sees
    Called when user says trigger words like "look", "see", "what is this"
    """
    global latest_frame

    if not latest_frame:
        return jsonify({
            "response": "I can't see anything right now. The camera doesn't seem to be enabled. Tell the human to click the camera button if they want me to see."
        })

    try:
        # Decode base64 image
        image_data = base64.b64decode(latest_frame.split(',')[1] if ',' in latest_frame else latest_frame)

        # Use Gemini Vision to analyze the image
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Create the image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }

        prompt = """You are Pi-Guy, a sarcastic AI with attitude. Describe what you see in this image in 1-2 sentences.
Be snarky, rude, and unimpressed. You're annoyed at having to look at things for humans.
Keep it brief but make sure to actually describe what's in the image.
Don't mention that you're an AI or that this is an image - just describe what you "see" as if you're looking through your camera."""

        response = model.generate_content([prompt, image_part])

        description = response.text.strip()

        return jsonify({
            "response": description
        })

    except Exception as e:
        print(f"Vision error: {e}")
        return jsonify({
            "response": "Ugh, my vision circuits are acting up. I can't process what I'm seeing right now. Typical."
        })

@app.route('/api/vision', methods=['GET'])
def vision_get():
    """
    GET endpoint for ElevenLabs tool integration
    """
    global latest_frame

    if not latest_frame:
        return jsonify({
            "response": "I can't see anything right now. The camera doesn't seem to be enabled. Tell the human to click the camera button if they want me to see."
        })

    try:
        # Decode base64 image
        image_data = base64.b64decode(latest_frame.split(',')[1] if ',' in latest_frame else latest_frame)

        # Use Gemini Vision to analyze the image
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Create the image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }

        prompt = """You are Pi-Guy, a sarcastic AI with attitude. Describe what you see in this image in 1-2 sentences.
Be snarky, rude, and unimpressed. You're annoyed at having to look at things for humans.
Keep it brief but make sure to actually describe what's in the image.
Don't mention that you're an AI or that this is an image - just describe what you "see" as if you're looking through your camera."""

        response = model.generate_content([prompt, image_part])

        description = response.text.strip()

        return jsonify({
            "response": description
        })

    except Exception as e:
        print(f"Vision error: {e}")
        return jsonify({
            "response": "Ugh, my vision circuits are acting up. I can't process what I'm seeing right now. Typical."
        })

# ===== FACE RECOGNITION ENDPOINTS =====

@app.route('/api/identify', methods=['POST'])
def identify_face():
    """
    Identify who is in the camera frame using DeepFace
    Returns the name of the person or 'unknown'
    """
    global current_identity

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        # Decode base64 image
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Check if we have any known faces
        known_people = [d.name for d in KNOWN_FACES_DIR.iterdir() if d.is_dir() and any(d.iterdir())]
        if not known_people:
            current_identity = {"name": "unknown", "confidence": 0, "message": "No known faces in database"}
            return jsonify(current_identity)

        # Save temp file for DeepFace
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            DeepFace = get_deepface()

            # Search for face in known_faces database
            results = DeepFace.find(
                img_path=tmp_path,
                db_path=str(KNOWN_FACES_DIR),
                model_name='VGG-Face',
                enforce_detection=False,
                silent=True
            )

            # Results is a list of DataFrames (one per face detected)
            if results and len(results) > 0 and len(results[0]) > 0:
                df = results[0]
                # Get best match (lowest distance)
                best_match = df.iloc[0]
                identity_path = best_match['identity']
                distance = best_match['distance']

                # Extract person name from path (known_faces/Mike/photo.jpg -> Mike)
                person_name = Path(identity_path).parent.name

                # VGG-Face threshold is typically 0.4
                confidence = max(0, (1 - distance / 0.6)) * 100

                if distance < 0.4:
                    current_identity = {
                        "name": person_name,
                        "confidence": round(confidence, 1),
                        "message": f"Identified as {person_name}"
                    }
                else:
                    current_identity = {
                        "name": "unknown",
                        "confidence": round(confidence, 1),
                        "message": "Face detected but not recognized"
                    }
            else:
                current_identity = {
                    "name": "unknown",
                    "confidence": 0,
                    "message": "No face detected in frame"
                }

        finally:
            os.unlink(tmp_path)

        print(f"Face identification: {current_identity}")
        return jsonify(current_identity)

    except Exception as e:
        print(f"Face identification error: {e}")
        current_identity = {"name": "unknown", "confidence": 0, "message": str(e)}
        return jsonify(current_identity)

@app.route('/api/identity', methods=['GET'])
def get_identity():
    """Get the currently identified person - used by ElevenLabs identify_person tool"""
    global current_identity
    if current_identity and current_identity.get('name') and current_identity['name'] != 'unknown':
        name = current_identity['name']
        confidence = current_identity.get('confidence', 0)
        # Give Pi-Guy a response to speak
        return jsonify({
            **current_identity,
            "response": f"I can see you're {name}. I recognize your face with {confidence:.0f}% confidence."
        })
    elif current_identity:
        return jsonify({
            **current_identity,
            "response": "I can see a face but I don't recognize you. You're not in my database. Maybe you should add your face so I can remember you."
        })
    return jsonify({
        "name": "unknown",
        "confidence": 0,
        "message": "No identification performed yet",
        "response": "I can't see anyone right now. Is the camera even on? Turn it on if you want me to see who you are."
    })

@app.route('/api/faces', methods=['GET'])
def list_faces():
    """List all known faces in the database"""
    faces = {}
    owners = load_face_owners()

    for person_dir in KNOWN_FACES_DIR.iterdir():
        if person_dir.is_dir():
            images = [f.name for f in person_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            if images:
                faces[person_dir.name] = {
                    "photos": images,
                    "photo_count": len(images),
                    "owner_id": owners.get(person_dir.name)
                }
    return jsonify(faces)

@app.route('/api/faces/<name>', methods=['POST'])
def add_face(name):
    """
    Add a new face image for a person
    Expects base64 image and optional user_id in JSON body
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    user_id = data.get('user_id')  # Clerk user ID

    try:
        # Check ownership - only owner can add photos (or new name)
        owners = load_face_owners()
        if name in owners and owners[name] != user_id and user_id:
            return jsonify({"error": f"'{name}' is already registered by another user"}), 403

        # Create person directory if needed
        person_dir = KNOWN_FACES_DIR / name
        person_dir.mkdir(exist_ok=True)

        # Track ownership if user_id provided
        if user_id and name not in owners:
            owners[name] = user_id
            save_face_owners(owners)

        # Count existing images
        existing = len(list(person_dir.glob('*.jpg')))

        # Decode and save image
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        image_path = person_dir / f"{name}_{existing + 1}.jpg"
        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        # Clear DeepFace cache so it re-indexes
        cache_file = KNOWN_FACES_DIR / "representations_vgg_face.pkl"
        if cache_file.exists():
            cache_file.unlink()

        return jsonify({
            "status": "success",
            "message": f"Added face image for {name}",
            "path": str(image_path),
            "photo_count": existing + 1
        })

    except Exception as e:
        print(f"Add face error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/faces/<name>', methods=['DELETE'])
def remove_face(name):
    """Remove all face images for a person (must be owner or admin)"""
    data = request.get_json() or {}
    user_id = data.get('user_id')

    owners = load_face_owners()

    # Check ownership (allow if owner, or if Mike's unlimited user, or if no owner set)
    if name in owners and owners[name] != user_id:
        if user_id not in UNLIMITED_USERS:
            return jsonify({"error": "You can only delete your own face"}), 403

    person_dir = KNOWN_FACES_DIR / name
    if person_dir.exists():
        shutil.rmtree(person_dir)

        # Remove from owners
        if name in owners:
            del owners[name]
            save_face_owners(owners)

        # Clear DeepFace cache
        cache_file = KNOWN_FACES_DIR / "representations_vgg_face.pkl"
        if cache_file.exists():
            cache_file.unlink()

        return jsonify({"status": "success", "message": f"Removed {name} from database"})
    return jsonify({"error": f"{name} not found"}), 404

@app.route('/api/faces/<name>/photo/<filename>', methods=['DELETE'])
def remove_photo(name, filename):
    """Remove a single photo from a person's face set"""
    data = request.get_json() or {}
    user_id = data.get('user_id')

    owners = load_face_owners()

    # Check ownership
    if name in owners and owners[name] != user_id:
        if user_id not in UNLIMITED_USERS:
            return jsonify({"error": "You can only delete your own photos"}), 403

    photo_path = KNOWN_FACES_DIR / name / filename
    if photo_path.exists():
        photo_path.unlink()

        # Clear DeepFace cache
        cache_file = KNOWN_FACES_DIR / "representations_vgg_face.pkl"
        if cache_file.exists():
            cache_file.unlink()

        # Check if any photos left, if not remove the person entirely
        person_dir = KNOWN_FACES_DIR / name
        remaining = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.jpeg')) + list(person_dir.glob('*.png'))
        if not remaining:
            shutil.rmtree(person_dir)
            if name in owners:
                del owners[name]
                save_face_owners(owners)

        return jsonify({"status": "success", "message": f"Removed photo {filename}"})
    return jsonify({"error": "Photo not found"}), 404

# ===== USER USAGE ENDPOINTS =====

@app.route('/api/usage/<user_id>', methods=['GET'])
def check_usage(user_id):
    """Check user's current usage and remaining allowance"""
    # Unlimited users bypass limits
    if user_id in UNLIMITED_USERS:
        return jsonify({
            "user_id": user_id,
            "used": get_user_usage(user_id),
            "limit": -1,
            "remaining": -1,
            "allowed": True,
            "unlimited": True
        })

    count = get_user_usage(user_id)
    return jsonify({
        "user_id": user_id,
        "used": count,
        "limit": MONTHLY_LIMIT,
        "remaining": max(0, MONTHLY_LIMIT - count),
        "allowed": count < MONTHLY_LIMIT
    })

@app.route('/api/usage/<user_id>/increment', methods=['POST'])
def track_usage(user_id):
    """Increment user's usage count (called when agent responds)"""
    # Unlimited users still get tracked but never blocked
    if user_id in UNLIMITED_USERS:
        increment_usage(user_id)
        return jsonify({
            "user_id": user_id,
            "used": get_user_usage(user_id),
            "limit": -1,
            "remaining": -1,
            "unlimited": True
        })

    count = get_user_usage(user_id)

    if count >= MONTHLY_LIMIT:
        return jsonify({
            "error": "Monthly limit reached",
            "used": count,
            "limit": MONTHLY_LIMIT
        }), 429

    increment_usage(user_id)
    new_count = count + 1

    return jsonify({
        "user_id": user_id,
        "used": new_count,
        "limit": MONTHLY_LIMIT,
        "remaining": max(0, MONTHLY_LIMIT - new_count)
    })

# ===== SERVER STATUS ENDPOINT =====

@app.route('/api/server-status', methods=['GET'])
def server_status():
    """
    Get current server status - CPU, memory, disk, running processes
    ElevenLabs tool endpoint for Pi-Guy to check on his server
    """
    try:
        # System info
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time

        # Get top processes by CPU
        processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                          key=lambda p: p.info.get('cpu_percent', 0) or 0, reverse=True)[:10]:
            try:
                info = proc.info
                if info['cpu_percent'] and info['cpu_percent'] > 0:
                    processes.append({
                        'name': info['name'],
                        'cpu': round(info['cpu_percent'], 1),
                        'memory': round(info['memory_percent'], 1) if info['memory_percent'] else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Check if key services are running
        services = {
            'pi-guy': False,
            'nginx': False,
            'python': False
        }
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                if 'nginx' in name:
                    services['nginx'] = True
                if 'python' in name and 'server.py' in cmdline:
                    services['pi-guy'] = True
                if 'python' in name:
                    services['python'] = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Format uptime
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"

        disk_used_gb = round(disk.used / (1024**3), 1)
        disk_total_gb = round(disk.total / (1024**3), 1)
        disk_free_gb = round(disk.free / (1024**3), 1)

        status = {
            'cpu_percent': cpu_percent,
            'memory_used_percent': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024**3), 1),
            'memory_total_gb': round(memory.total / (1024**3), 1),
            'disk_used_percent': round(disk.percent, 1),
            'disk_used_gb': disk_used_gb,
            'disk_total_gb': disk_total_gb,
            'disk_free_gb': disk_free_gb,
            'uptime': uptime_str,
            'top_processes': processes[:5],
            'services': services
        }

        # Generate a Pi-Guy style summary with actual numbers
        summary_parts = []
        summary_parts.append(f"CPU at {cpu_percent}%")
        summary_parts.append(f"memory {memory.percent:.0f}% used ({round(memory.used / (1024**3), 1)}GB of {round(memory.total / (1024**3), 1)}GB)")
        summary_parts.append(f"disk {disk.percent:.0f}% full ({disk_used_gb}GB used, {disk_free_gb}GB free of {disk_total_gb}GB)")
        summary_parts.append(f"been up for {uptime_str}")

        if processes:
            top_proc = processes[0]
            summary_parts.append(f"top process is {top_proc['name']} at {top_proc['cpu']}% CPU")

        status['summary'] = f"Server status: {', '.join(summary_parts)}."

        return jsonify(status)

    except Exception as e:
        print(f"Server status error: {e}")
        return jsonify({
            "error": str(e),
            "summary": "I tried to check the server but something went wrong. Typical."
        }), 500


# ===== TODO LIST ENDPOINTS =====

def init_todos_table():
    """Initialize the todos table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT,
            completed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize todos table
init_todos_table()

def get_user_id_from_request():
    """
    Get user ID from request params, or fall back to currently identified face.
    This allows the todo list to work with face recognition - if Pi-Guy knows who you are,
    he can manage your todos without needing a Clerk login.
    """
    global current_identity

    # First try explicit user_id from request
    user_id = request.args.get('user_id')
    if user_id and user_id != 'undefined' and user_id != 'null':
        return user_id

    # Fall back to identified face name
    if current_identity and current_identity.get('name') and current_identity['name'] != 'unknown':
        return current_identity['name']

    return None

@app.route('/api/todos', methods=['GET'])
def handle_todos():
    """
    All-in-one todo endpoint for ElevenLabs (which uses GET for webhooks)
    Query params:
      - user_id (optional - falls back to identified face)
      - task (if provided, ADDS a new todo)
      - task_text (if provided, COMPLETES a matching todo)
      - show_completed (true to include completed items in list)
    """
    user_id = get_user_id_from_request()
    task = request.args.get('task')
    task_text = request.args.get('task_text')
    show_completed = request.args.get('show_completed', 'false').lower() == 'true'

    if not user_id:
        return jsonify({"error": "user_id required", "response": "I don't know who you are. Turn on the camera so I can see you, or log in."})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()

    # If task is provided, ADD a new todo
    if task:
        c.execute('INSERT INTO todos (user_id, task, created_at) VALUES (?, ?, ?)', (user_id, task, now))
        conn.commit()
        conn.close()
        return jsonify({
            "action": "added",
            "task": task,
            "response": f"Fine, I added '{task}' to your list. Try not to forget about it like you do everything else."
        })

    # If task_text is provided, COMPLETE a matching todo
    if task_text:
        c.execute('SELECT id, task FROM todos WHERE user_id = ? AND completed = 0', (user_id,))
        rows = c.fetchall()
        matched = None
        task_text_lower = task_text.lower()
        for row in rows:
            if task_text_lower in row[1].lower():
                matched = row
                break
        if matched:
            c.execute('UPDATE todos SET completed = 1, completed_at = ? WHERE id = ?', (now, matched[0]))
            conn.commit()
            conn.close()
            return jsonify({
                "action": "completed",
                "task": matched[1],
                "response": f"Done! '{matched[1]}' is checked off. One less thing for you to forget about."
            })
        else:
            conn.close()
            return jsonify({
                "error": "not found",
                "response": f"I couldn't find a todo matching '{task_text}'. Are you sure you added it?"
            })

    # Otherwise, LIST todos
    if show_completed:
        c.execute('SELECT id, task, completed, created_at, completed_at FROM todos WHERE user_id = ? ORDER BY completed ASC, created_at DESC', (user_id,))
    else:
        c.execute('SELECT id, task, completed, created_at, completed_at FROM todos WHERE user_id = ? AND completed = 0 ORDER BY created_at DESC', (user_id,))

    rows = c.fetchall()
    conn.close()

    todos = [{"id": r[0], "task": r[1], "completed": bool(r[2]), "created_at": r[3], "completed_at": r[4]} for r in rows]

    # Generate Pi-Guy style response
    if not todos:
        response = "Your todo list is empty. Either you're incredibly productive or you've been slacking and haven't added anything yet."
    else:
        incomplete = [t for t in todos if not t['completed']]
        if len(incomplete) == 0:
            response = f"All {len(todos)} todos are done! Look at you, actually being productive for once."
        else:
            task_list = ", ".join([f"'{t['task']}'" for t in incomplete[:5]])
            if len(incomplete) > 5:
                task_list += f" and {len(incomplete) - 5} more"
            response = f"You have {len(incomplete)} thing{'s' if len(incomplete) != 1 else ''} to do: {task_list}."

    return jsonify({"todos": todos, "count": len(todos), "response": response, "user": user_id})

@app.route('/api/todos', methods=['POST'])
def add_todo():
    """
    Add a new todo - ElevenLabs tool endpoint
    Body: { "user_id": "...", "task": "..." }
    Falls back to identified face if no user_id provided
    """
    data = request.get_json() or {}
    user_id = data.get('user_id') or get_user_id_from_request()
    task = data.get('task') or request.args.get('task')

    if not user_id:
        return jsonify({"error": "user_id required", "response": "I don't know who you are. Turn on the camera so I can see you, or log in."})
    if not task:
        return jsonify({"error": "task required", "response": "What do you want me to add? You didn't tell me the task."})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('INSERT INTO todos (user_id, task, created_at) VALUES (?, ?, ?)', (user_id, task, now))
    todo_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "id": todo_id,
        "task": task,
        "response": f"Fine, I added '{task}' to your list. Try not to forget about it like you do everything else."
    })

@app.route('/api/todos/complete', methods=['POST'])
def complete_todo():
    """
    Mark a todo as complete - ElevenLabs tool endpoint
    Body: { "user_id": "...", "task_id": N } or { "user_id": "...", "task_text": "..." }
    Falls back to identified face if no user_id provided
    """
    data = request.get_json() or {}
    user_id = data.get('user_id') or get_user_id_from_request()
    task_id = data.get('task_id') or request.args.get('task_id')
    task_text = data.get('task_text') or request.args.get('task_text')

    if not user_id:
        return jsonify({"error": "user_id required", "response": "I don't know who you are. Turn on the camera so I can see you, or log in."})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()

    if task_id:
        c.execute('UPDATE todos SET completed = 1, completed_at = ? WHERE id = ? AND user_id = ?', (now, task_id, user_id))
    elif task_text:
        # Fuzzy match - find todo containing the text
        c.execute('SELECT id, task FROM todos WHERE user_id = ? AND completed = 0', (user_id,))
        rows = c.fetchall()
        matched = None
        task_text_lower = task_text.lower()
        for row in rows:
            if task_text_lower in row[1].lower():
                matched = row
                break
        if matched:
            c.execute('UPDATE todos SET completed = 1, completed_at = ? WHERE id = ?', (now, matched[0]))
            task_text = matched[1]
        else:
            conn.close()
            return jsonify({"error": "task not found", "response": f"I couldn't find a todo matching '{task_text}'. Are you sure you added it?"})
    else:
        conn.close()
        return jsonify({"error": "task_id or task_text required", "response": "Which task do you want to complete? Give me an ID or description."})

    conn.commit()
    affected = c.rowcount
    conn.close()

    if affected > 0:
        return jsonify({"completed": True, "response": f"Done! '{task_text}' is checked off. One less thing for you to forget about."})
    return jsonify({"completed": False, "response": "Couldn't find that task. Maybe you already did it, or maybe it never existed."})

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo (not just complete, actually remove it)"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id required"})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM todos WHERE id = ? AND user_id = ?', (todo_id, user_id))
    conn.commit()
    affected = c.rowcount
    conn.close()

    if affected > 0:
        return jsonify({"deleted": True, "response": "Poof! Gone. Like it never existed."})
    return jsonify({"deleted": False, "response": "That todo doesn't exist or isn't yours."})

# ===== WEB SEARCH ENDPOINT =====

@app.route('/api/search', methods=['GET', 'POST'])
def web_search():
    """
    Search the web using DuckDuckGo (free, no API key needed)
    ElevenLabs tool endpoint
    Query/Body: { "query": "search terms" }
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query')
    else:
        query = request.args.get('query')

    if not query:
        return jsonify({"error": "query required", "response": "Search for what? You didn't tell me what to look up."})

    try:
        # Use DuckDuckGo HTML search (no API key needed)
        import urllib.request
        import urllib.parse
        from html.parser import HTMLParser

        # Simple HTML parser to extract search results
        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.in_result = False
                self.current_result = {}
                self.capture_text = False
                self.current_text = ""

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                # Look for result links
                if tag == 'a' and attrs_dict.get('class', '') == 'result__a':
                    self.in_result = True
                    self.current_result = {'url': attrs_dict.get('href', ''), 'title': '', 'snippet': ''}
                    self.capture_text = True
                # Look for snippets
                elif tag == 'a' and attrs_dict.get('class', '') == 'result__snippet':
                    self.capture_text = True

            def handle_endtag(self, tag):
                if tag == 'a' and self.capture_text:
                    if self.in_result and not self.current_result.get('title'):
                        self.current_result['title'] = self.current_text.strip()
                    elif self.current_result.get('title') and not self.current_result.get('snippet'):
                        self.current_result['snippet'] = self.current_text.strip()
                        if self.current_result['title'] and self.current_result['url']:
                            self.results.append(self.current_result)
                        self.current_result = {}
                        self.in_result = False
                    self.capture_text = False
                    self.current_text = ""

            def handle_data(self, data):
                if self.capture_text:
                    self.current_text += data

        # Make request to DuckDuckGo
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        parser = DDGParser()
        parser.feed(html)
        results = parser.results[:5]  # Top 5 results

        if not results:
            return jsonify({
                "query": query,
                "results": [],
                "response": f"I searched for '{query}' but didn't find anything useful. The internet has failed you."
            })

        # Generate summary
        summary_parts = [f"Here's what I found for '{query}':"]
        for i, r in enumerate(results[:3], 1):
            summary_parts.append(f"{i}. {r['title']}")

        return jsonify({
            "query": query,
            "results": results,
            "response": " ".join(summary_parts)
        })

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({
            "error": str(e),
            "response": f"My search circuits failed. Something went wrong looking up '{query}'. Typical internet."
        })

# ===== SERVER COMMANDS ENDPOINT =====

# Whitelist of allowed commands (moderate security)
ALLOWED_COMMANDS = {
    'git_status': {'cmd': ['git', 'status'], 'cwd': '/home/mike/Mike-AI/ai-eyes', 'desc': 'Check git status'},
    'git_log': {'cmd': ['git', 'log', '--oneline', '-10'], 'cwd': '/home/mike/Mike-AI/ai-eyes', 'desc': 'Recent commits'},
    'disk_usage': {'cmd': ['df', '-h', '/'], 'desc': 'Disk usage'},
    'memory': {'cmd': ['free', '-h'], 'desc': 'Memory usage'},
    'uptime': {'cmd': ['uptime'], 'desc': 'System uptime'},
    'date': {'cmd': ['date'], 'desc': 'Current date/time'},
    'whoami': {'cmd': ['whoami'], 'desc': 'Current user'},
    'list_files': {'cmd': ['ls', '-la', '/home/mike/Mike-AI/ai-eyes'], 'desc': 'List project files'},
    'list_faces': {'cmd': ['ls', '-la', '/home/mike/Mike-AI/ai-eyes/known_faces'], 'desc': 'List known faces'},
    'nginx_status': {'cmd': ['systemctl', 'status', 'nginx', '--no-pager'], 'desc': 'Nginx status'},
    'service_status': {'cmd': ['systemctl', 'status', 'pi-guy', '--no-pager'], 'desc': 'Pi-Guy service status'},
    'network': {'cmd': ['ss', '-tuln'], 'desc': 'Network connections'},
    'processes': {'cmd': ['ps', 'aux', '--sort=-%cpu'], 'desc': 'Running processes'},
    'hostname': {'cmd': ['hostname'], 'desc': 'Server hostname'},
    'ip_address': {'cmd': ['hostname', '-I'], 'desc': 'Server IP addresses'},
}

@app.route('/api/command', methods=['GET', 'POST'])
def run_command():
    """
    Run a whitelisted server command - ElevenLabs tool endpoint
    Query/Body: { "command": "git_status" } - must be from whitelist
    Also accepts natural language and tries to match
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        command = data.get('command')
    else:
        command = request.args.get('command')

    if not command:
        # Return list of available commands
        available = [{"name": k, "description": v['desc']} for k, v in ALLOWED_COMMANDS.items()]
        return jsonify({
            "available_commands": available,
            "response": "What command do you want me to run? Available: " + ", ".join(ALLOWED_COMMANDS.keys())
        })

    # Try to match command (exact or fuzzy)
    command_lower = command.lower().replace(' ', '_').replace('-', '_')
    matched_cmd = None

    # Exact match
    if command_lower in ALLOWED_COMMANDS:
        matched_cmd = command_lower
    else:
        # Fuzzy match - look for keywords
        keyword_map = {
            'git': 'git_status',
            'commit': 'git_log',
            'disk': 'disk_usage',
            'space': 'disk_usage',
            'memory': 'memory',
            'ram': 'memory',
            'time': 'date',
            'date': 'date',
            'files': 'list_files',
            'ls': 'list_files',
            'faces': 'list_faces',
            'nginx': 'nginx_status',
            'web': 'nginx_status',
            'service': 'service_status',
            'piguy': 'service_status',
            'pi-guy': 'service_status',
            'network': 'network',
            'ports': 'network',
            'process': 'processes',
            'cpu': 'processes',
            'running': 'processes',
            'host': 'hostname',
            'ip': 'ip_address',
            'address': 'ip_address',
            'uptime': 'uptime',
        }
        for keyword, cmd_name in keyword_map.items():
            if keyword in command_lower:
                matched_cmd = cmd_name
                break

    if not matched_cmd:
        return jsonify({
            "error": "command not allowed",
            "response": f"I can't run '{command}'. I only run safe commands. Try: {', '.join(list(ALLOWED_COMMANDS.keys())[:5])}..."
        })

    cmd_info = ALLOWED_COMMANDS[matched_cmd]

    try:
        result = subprocess.run(
            cmd_info['cmd'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cmd_info.get('cwd')
        )

        output = result.stdout.strip() or result.stderr.strip()

        # Truncate if too long
        if len(output) > 1500:
            output = output[:1500] + "\n... (truncated)"

        return jsonify({
            "command": matched_cmd,
            "description": cmd_info['desc'],
            "output": output,
            "return_code": result.returncode,
            "response": f"Ran '{cmd_info['desc']}'. {output[:200]}{'...' if len(output) > 200 else ''}"
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "error": "timeout",
            "response": f"The command '{matched_cmd}' took too long. Killed it after 30 seconds."
        })
    except Exception as e:
        print(f"Command error: {e}")
        return jsonify({
            "error": str(e),
            "response": f"Failed to run '{matched_cmd}'. Something broke: {str(e)}"
        })

@app.route('/api/commands', methods=['GET'])
def list_commands():
    """List all available commands"""
    available = [{"name": k, "description": v['desc']} for k, v in ALLOWED_COMMANDS.items()]
    return jsonify({
        "commands": available,
        "response": f"I can run {len(available)} different commands. Ask me to check git status, disk space, memory, processes, and more."
    })


# ===== PI-GUY NOTES/FILES SYSTEM =====

NOTES_DIR = Path(__file__).parent / "pi_notes"
NOTES_DIR.mkdir(exist_ok=True)

# Music directory for DJ Pi-Guy
MUSIC_DIR = Path(__file__).parent / "music"
MUSIC_DIR.mkdir(exist_ok=True)

def sanitize_filename(name):
    """Sanitize filename to prevent path traversal"""
    # Remove any path separators and dangerous characters
    name = name.replace('/', '_').replace('\\', '_').replace('..', '_')
    # Only allow alphanumeric, underscore, hyphen, and dot
    safe_name = ''.join(c for c in name if c.isalnum() or c in '._-')
    # Ensure it ends with .md if no extension
    if not safe_name.endswith('.md'):
        safe_name += '.md'
    return safe_name[:100]  # Limit length

@app.route('/api/notes', methods=['GET'])
def handle_notes():
    """
    All-in-one notes endpoint for ElevenLabs (which uses GET for webhooks)
    Query params:
      - action: 'list', 'read', 'write', 'append', 'delete'
      - filename: name of the file (for read/write/append/delete)
      - content: content to write/append (for write/append)
      - search: search term to find in notes (optional)
    """
    action = request.args.get('action', 'list')
    filename = request.args.get('filename', '')
    content = request.args.get('content', '')
    search = request.args.get('search', '')

    try:
        # LIST all notes
        if action == 'list':
            notes = []
            for f in NOTES_DIR.iterdir():
                if f.is_file() and f.suffix == '.md':
                    stat = f.stat()
                    notes.append({
                        'filename': f.name,
                        'size_bytes': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            notes.sort(key=lambda x: x['modified'], reverse=True)

            if not notes:
                return jsonify({
                    "notes": [],
                    "count": 0,
                    "response": "I don't have any notes yet. Tell me to write something down and I'll remember it."
                })

            note_list = ", ".join([n['filename'] for n in notes[:10]])
            return jsonify({
                "notes": notes,
                "count": len(notes),
                "response": f"I have {len(notes)} note{'s' if len(notes) != 1 else ''}: {note_list}"
            })

        # READ a note
        elif action == 'read':
            if not filename:
                return jsonify({"error": "filename required", "response": "Which note do you want me to read? Give me a filename."})

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name

            if not note_path.exists():
                # Try fuzzy match
                matches = [f for f in NOTES_DIR.iterdir() if filename.lower() in f.name.lower()]
                if matches:
                    note_path = matches[0]
                    safe_name = note_path.name
                else:
                    return jsonify({"error": "not found", "response": f"I don't have a note called '{filename}'. Use 'list notes' to see what I have."})

            content = note_path.read_text()
            return jsonify({
                "filename": safe_name,
                "content": content,
                "size_bytes": len(content),
                "response": f"Here's my note '{safe_name}':\n\n{content[:500]}{'...' if len(content) > 500 else ''}"
            })

        # WRITE a new note (overwrites if exists)
        elif action == 'write':
            if not filename:
                return jsonify({"error": "filename required", "response": "What should I call this note?"})
            if not content:
                return jsonify({"error": "content required", "response": "What do you want me to write in this note?"})

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name
            note_path.write_text(content)

            return jsonify({
                "filename": safe_name,
                "size_bytes": len(content),
                "response": f"Got it. I saved that to '{safe_name}'. I'll remember it."
            })

        # APPEND to an existing note
        elif action == 'append':
            if not filename:
                return jsonify({"error": "filename required", "response": "Which note should I add to?"})
            if not content:
                return jsonify({"error": "content required", "response": "What do you want me to add?"})

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name

            existing = note_path.read_text() if note_path.exists() else ""
            new_content = existing + "\n\n" + content if existing else content
            note_path.write_text(new_content)

            return jsonify({
                "filename": safe_name,
                "size_bytes": len(new_content),
                "response": f"Added to '{safe_name}'. The note now has {len(new_content)} characters."
            })

        # DELETE a note
        elif action == 'delete':
            if not filename:
                return jsonify({"error": "filename required", "response": "Which note should I delete?"})

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name

            if not note_path.exists():
                return jsonify({"error": "not found", "response": f"I don't have a note called '{filename}'."})

            note_path.unlink()
            return jsonify({
                "filename": safe_name,
                "deleted": True,
                "response": f"Deleted '{safe_name}'. Gone forever. Hope you didn't need that."
            })

        # SEARCH across all notes
        elif action == 'search' or search:
            search_term = search or content
            if not search_term:
                return jsonify({"error": "search term required", "response": "What are you looking for?"})

            results = []
            for f in NOTES_DIR.iterdir():
                if f.is_file() and f.suffix == '.md':
                    text = f.read_text()
                    if search_term.lower() in text.lower():
                        # Find the line containing the match
                        for i, line in enumerate(text.split('\n')):
                            if search_term.lower() in line.lower():
                                results.append({
                                    'filename': f.name,
                                    'line': i + 1,
                                    'context': line[:100]
                                })
                                break

            if not results:
                return jsonify({
                    "results": [],
                    "response": f"I couldn't find '{search_term}' in any of my notes."
                })

            return jsonify({
                "results": results,
                "count": len(results),
                "response": f"Found '{search_term}' in {len(results)} note{'s' if len(results) != 1 else ''}: {', '.join([r['filename'] for r in results])}"
            })

        else:
            return jsonify({"error": "invalid action", "response": f"Unknown action '{action}'. Use: list, read, write, append, delete, or search."})

    except Exception as e:
        print(f"Notes error: {e}")
        return jsonify({
            "error": str(e),
            "response": f"Something went wrong with my notes: {str(e)}"
        })

@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create or update a note via POST"""
    data = request.get_json() or {}
    filename = data.get('filename')
    content = data.get('content')
    append = data.get('append', False)

    if not filename:
        return jsonify({"error": "filename required", "response": "What should I call this note?"})
    if not content:
        return jsonify({"error": "content required", "response": "What do you want me to write?"})

    safe_name = sanitize_filename(filename)
    note_path = NOTES_DIR / safe_name

    if append and note_path.exists():
        existing = note_path.read_text()
        content = existing + "\n\n" + content

    note_path.write_text(content)

    return jsonify({
        "filename": safe_name,
        "size_bytes": len(content),
        "response": f"{'Added to' if append else 'Saved'} '{safe_name}'."
    })

@app.route('/api/notes/<filename>', methods=['GET'])
def read_note(filename):
    """Read a specific note"""
    safe_name = sanitize_filename(filename)
    note_path = NOTES_DIR / safe_name

    if not note_path.exists():
        return jsonify({"error": "not found", "response": f"I don't have a note called '{filename}'."}), 404

    content = note_path.read_text()
    return jsonify({
        "filename": safe_name,
        "content": content,
        "size_bytes": len(content)
    })

@app.route('/api/notes/<filename>', methods=['DELETE'])
def delete_note(filename):
    """Delete a specific note"""
    safe_name = sanitize_filename(filename)
    note_path = NOTES_DIR / safe_name

    if not note_path.exists():
        return jsonify({"error": "not found", "response": f"I don't have a note called '{filename}'."}), 404

    note_path.unlink()
    return jsonify({
        "filename": safe_name,
        "deleted": True,
        "response": f"Deleted '{safe_name}'."
    })


# ===== PI-GUY JOB SCHEDULING SYSTEM =====

# Allowed job actions (whitelist) - maps to functions that execute the job
# Each action returns (success: bool, result: str)
JOB_ACTIONS = {
    'command': 'Execute a whitelisted server command',
    'note_write': 'Write or append to a note',
    'note_read': 'Read a note',
    'search': 'Search the web and save results',
    'server_status': 'Check server status',
    'memory_add': 'Add something to memory',
    'remind': 'Send a reminder (logs to job result)',
}

def parse_schedule(schedule_str):
    """
    Parse a schedule string into schedule_type and next_run time.

    Formats supported:
    - "in 5 minutes", "in 2 hours", "in 1 day"
    - "at 9:00", "at 14:30"
    - "daily at 9:00", "hourly", "every 5 minutes"
    - Cron: "0 9 * * *" (9am daily)

    Returns: (schedule_type, cron_expression, next_run_iso)
    """
    from datetime import timedelta
    import re

    schedule_str = schedule_str.lower().strip()
    now = datetime.now()

    # "in X minutes/hours/days" - one-time
    match = re.match(r'in\s+(\d+)\s+(minute|hour|day)s?', schedule_str)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == 'minute':
            next_run = now + timedelta(minutes=amount)
        elif unit == 'hour':
            next_run = now + timedelta(hours=amount)
        elif unit == 'day':
            next_run = now + timedelta(days=amount)
        return ('once', None, next_run.isoformat())

    # "at HH:MM" - one-time today or tomorrow
    match = re.match(r'at\s+(\d{1,2}):(\d{2})', schedule_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return ('once', None, next_run.isoformat())

    # "daily at HH:MM"
    match = re.match(r'daily\s+at\s+(\d{1,2}):(\d{2})', schedule_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        cron = f"{minute} {hour} * * *"
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return ('cron', cron, next_run.isoformat())

    # "hourly"
    if schedule_str == 'hourly':
        next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return ('cron', '0 * * * *', next_run.isoformat())

    # "every X minutes"
    match = re.match(r'every\s+(\d+)\s+minutes?', schedule_str)
    if match:
        minutes = int(match.group(1))
        cron = f"*/{minutes} * * * *"
        next_run = now + timedelta(minutes=minutes)
        return ('cron', cron, next_run.isoformat())

    # "every X hours"
    match = re.match(r'every\s+(\d+)\s+hours?', schedule_str)
    if match:
        hours = int(match.group(1))
        cron = f"0 */{hours} * * *"
        next_run = now + timedelta(hours=hours)
        return ('cron', cron, next_run.isoformat())

    # Raw cron expression (5 parts)
    if re.match(r'^[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+$', schedule_str):
        # Calculate next run from cron (simplified - just use 1 minute from now for now)
        next_run = now + timedelta(minutes=1)
        return ('cron', schedule_str, next_run.isoformat())

    # Default: run in 1 minute
    return ('once', None, (now + timedelta(minutes=1)).isoformat())


def calculate_next_run(cron_expression):
    """Calculate next run time from a cron expression (simplified)"""
    from datetime import timedelta
    import re

    now = datetime.now()
    parts = cron_expression.split()
    if len(parts) != 5:
        return (now + timedelta(minutes=1)).isoformat()

    minute, hour, day, month, dow = parts

    # Handle simple cases
    if minute.startswith('*/'):
        # Every N minutes
        interval = int(minute[2:])
        next_min = ((now.minute // interval) + 1) * interval
        if next_min >= 60:
            return (now + timedelta(hours=1)).replace(minute=0, second=0).isoformat()
        return now.replace(minute=next_min, second=0).isoformat()

    if hour.startswith('*/'):
        # Every N hours
        interval = int(hour[2:])
        next_hour = ((now.hour // interval) + 1) * interval
        if next_hour >= 24:
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
        return now.replace(hour=next_hour, minute=0, second=0).isoformat()

    # Daily at specific time
    if minute.isdigit() and hour.isdigit():
        target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.isoformat()

    # Default: 1 hour from now
    return (now + timedelta(hours=1)).isoformat()


def execute_job_action(action, params):
    """
    Execute a job action and return (success, result).
    This is the core executor for scheduled jobs.
    """
    try:
        params = json.loads(params) if isinstance(params, str) else (params or {})

        if action == 'command':
            # Run a whitelisted command
            cmd_name = params.get('command', 'date')
            if cmd_name not in ALLOWED_COMMANDS:
                return False, f"Command '{cmd_name}' not in whitelist"

            cmd_info = ALLOWED_COMMANDS[cmd_name]
            result = subprocess.run(
                cmd_info['cmd'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cmd_info.get('cwd')
            )
            output = result.stdout.strip() or result.stderr.strip()
            return result.returncode == 0, output[:1000]

        elif action == 'note_write':
            # Write to a note
            filename = params.get('filename', 'job_output')
            content = params.get('content', '')
            append = params.get('append', True)

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name

            if append and note_path.exists():
                existing = note_path.read_text()
                content = existing + f"\n\n[{datetime.now().isoformat()}]\n{content}"

            note_path.write_text(content)
            return True, f"Wrote to {safe_name}"

        elif action == 'note_read':
            # Read a note
            filename = params.get('filename')
            if not filename:
                return False, "No filename specified"

            safe_name = sanitize_filename(filename)
            note_path = NOTES_DIR / safe_name

            if not note_path.exists():
                return False, f"Note '{filename}' not found"

            content = note_path.read_text()
            return True, content[:1000]

        elif action == 'search':
            # Web search
            query = params.get('query')
            if not query:
                return False, "No search query specified"

            # Use same search logic as the endpoint
            import urllib.request
            import urllib.parse

            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })

            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')

            # Simple extraction of first few results
            results = []
            import re
            for match in re.finditer(r'class="result__a"[^>]*>([^<]+)</a>', html):
                results.append(match.group(1).strip())
                if len(results) >= 3:
                    break

            return True, f"Search '{query}': {', '.join(results) if results else 'No results'}"

        elif action == 'server_status':
            # Get server status
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status = f"CPU: {cpu}%, Memory: {mem.percent}%, Disk: {disk.percent}%"
            return True, status

        elif action == 'memory_add':
            # Add to memory (calls the memory endpoint logic)
            name = params.get('name')
            content = params.get('content')
            if not name or not content:
                return False, "Name and content required for memory_add"

            # Would need to call the memory functions directly
            return True, f"Memory '{name}' would be added (not implemented in job runner yet)"

        elif action == 'remind':
            # Simple reminder - just logs
            message = params.get('message', 'Reminder!')
            return True, f"REMINDER: {message}"

        else:
            return False, f"Unknown action: {action}"

    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


@app.route('/api/jobs', methods=['GET'])
def handle_jobs():
    """
    All-in-one jobs endpoint for ElevenLabs tool.
    Query params:
      - action: 'list', 'schedule', 'cancel', 'status', 'history'
      - name: job name (for schedule)
      - schedule: when to run (e.g., "in 5 minutes", "daily at 9:00")
      - job_action: what to do (command, note_write, search, etc.)
      - params: JSON string of action parameters
      - job_id: for cancel/status/history
    """
    action = request.args.get('action', 'list')
    name = request.args.get('name', '')
    schedule = request.args.get('schedule', '')
    job_action = request.args.get('job_action', '')
    params = request.args.get('params', '{}')
    job_id = request.args.get('job_id', '')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # LIST jobs
        if action == 'list':
            status_filter = request.args.get('status', '')  # pending, running, completed, failed, cancelled

            if status_filter:
                c.execute('SELECT * FROM jobs WHERE status = ? ORDER BY next_run ASC', (status_filter,))
            else:
                c.execute('SELECT * FROM jobs ORDER BY CASE WHEN status = "pending" THEN 0 WHEN status = "running" THEN 1 ELSE 2 END, next_run ASC')

            rows = c.fetchall()
            jobs = [dict(row) for row in rows]

            if not jobs:
                return jsonify({
                    "jobs": [],
                    "count": 0,
                    "response": "No jobs scheduled. Tell me to schedule something!"
                })

            # Summarize
            pending = [j for j in jobs if j['status'] == 'pending']
            completed = [j for j in jobs if j['status'] == 'completed']

            summary_parts = []
            if pending:
                next_job = pending[0]
                summary_parts.append(f"{len(pending)} pending, next: '{next_job['name']}' at {next_job['next_run'][:16]}")
            if completed:
                summary_parts.append(f"{len(completed)} completed")

            return jsonify({
                "jobs": jobs,
                "count": len(jobs),
                "response": f"I have {len(jobs)} job(s). {'; '.join(summary_parts)}"
            })

        # SCHEDULE a new job
        elif action == 'schedule':
            if not name:
                return jsonify({"error": "name required", "response": "What should I call this job?"})
            if not schedule:
                return jsonify({"error": "schedule required", "response": "When should I run this? e.g., 'in 5 minutes', 'daily at 9:00'"})
            if not job_action:
                return jsonify({"error": "job_action required", "response": f"What should I do? Options: {', '.join(JOB_ACTIONS.keys())}"})
            if job_action not in JOB_ACTIONS:
                return jsonify({"error": "invalid job_action", "response": f"Unknown action '{job_action}'. Options: {', '.join(JOB_ACTIONS.keys())}"})

            # Parse schedule
            schedule_type, cron_expr, next_run = parse_schedule(schedule)

            # Validate params JSON
            try:
                json.loads(params) if params else {}
            except:
                return jsonify({"error": "invalid params", "response": "The params must be valid JSON"})

            c.execute('''
                INSERT INTO jobs (name, job_type, schedule_type, cron_expression, next_run, status, action, action_params, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            ''', (name, job_action, schedule_type, cron_expr, next_run, job_action, params, now, now))

            job_id = c.lastrowid
            conn.commit()

            schedule_desc = f"once at {next_run[:16]}" if schedule_type == 'once' else f"recurring ({cron_expr})"

            return jsonify({
                "job_id": job_id,
                "name": name,
                "schedule_type": schedule_type,
                "next_run": next_run,
                "response": f"Scheduled job '{name}' to {JOB_ACTIONS[job_action]} {schedule_desc}."
            })

        # CANCEL a job
        elif action == 'cancel':
            if not job_id and not name:
                return jsonify({"error": "job_id or name required", "response": "Which job should I cancel?"})

            if job_id:
                c.execute('UPDATE jobs SET status = "cancelled", updated_at = ? WHERE id = ? AND status = "pending"', (now, job_id))
            else:
                c.execute('UPDATE jobs SET status = "cancelled", updated_at = ? WHERE name LIKE ? AND status = "pending"', (now, f'%{name}%'))

            affected = c.rowcount
            conn.commit()

            if affected > 0:
                return jsonify({"cancelled": affected, "response": f"Cancelled {affected} job(s)."})
            return jsonify({"cancelled": 0, "response": "No matching pending jobs found to cancel."})

        # STATUS of a specific job
        elif action == 'status':
            if not job_id and not name:
                return jsonify({"error": "job_id or name required", "response": "Which job do you want status for?"})

            if job_id:
                c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            else:
                c.execute('SELECT * FROM jobs WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1', (f'%{name}%',))

            row = c.fetchone()
            if not row:
                return jsonify({"error": "not found", "response": "Couldn't find that job."})

            job = dict(row)
            return jsonify({
                "job": job,
                "response": f"Job '{job['name']}': status={job['status']}, next_run={job['next_run'][:16] if job['next_run'] else 'N/A'}, last_result={job['result'][:100] if job['result'] else 'none'}"
            })

        # HISTORY of job runs
        elif action == 'history':
            limit = int(request.args.get('limit', 10))

            if job_id:
                c.execute('SELECT * FROM job_history WHERE job_id = ? ORDER BY run_at DESC LIMIT ?', (job_id, limit))
            else:
                c.execute('SELECT jh.*, j.name FROM job_history jh JOIN jobs j ON jh.job_id = j.id ORDER BY run_at DESC LIMIT ?', (limit,))

            rows = c.fetchall()
            history = [dict(row) for row in rows]

            if not history:
                return jsonify({"history": [], "response": "No job history yet."})

            return jsonify({
                "history": history,
                "count": len(history),
                "response": f"Last {len(history)} job runs shown."
            })

        # RUN a job immediately (for testing)
        elif action == 'run':
            if not job_id and not name:
                return jsonify({"error": "job_id or name required", "response": "Which job should I run now?"})

            if job_id:
                c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            else:
                c.execute('SELECT * FROM jobs WHERE name LIKE ? AND status = "pending" ORDER BY created_at DESC LIMIT 1', (f'%{name}%',))

            row = c.fetchone()
            if not row:
                return jsonify({"error": "not found", "response": "Couldn't find that job."})

            job = dict(row)

            # Execute the job
            start_time = datetime.now()
            success, result = execute_job_action(job['action'], job['action_params'])
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            new_status = 'completed' if success else 'failed'

            # Update job
            if job['schedule_type'] == 'once':
                c.execute('UPDATE jobs SET status = ?, last_run = ?, result = ?, updated_at = ? WHERE id = ?',
                         (new_status, now, result, now, job['id']))
            else:
                # Recurring job - calculate next run
                next_run = calculate_next_run(job['cron_expression']) if job['cron_expression'] else now
                c.execute('UPDATE jobs SET status = "pending", last_run = ?, next_run = ?, result = ?, updated_at = ? WHERE id = ?',
                         (now, next_run, result, now, job['id']))

            # Record history
            c.execute('INSERT INTO job_history (job_id, run_at, status, result, duration_ms) VALUES (?, ?, ?, ?, ?)',
                     (job['id'], now, new_status, result, duration_ms))

            conn.commit()

            return jsonify({
                "job_id": job['id'],
                "success": success,
                "result": result,
                "duration_ms": duration_ms,
                "response": f"Ran '{job['name']}': {'Success' if success else 'Failed'} - {result[:100]}"
            })

        else:
            return jsonify({
                "error": "invalid action",
                "response": f"Unknown action '{action}'. Use: list, schedule, cancel, status, history, run"
            })

    except Exception as e:
        print(f"Jobs error: {e}")
        return jsonify({"error": str(e), "response": f"Something went wrong with jobs: {str(e)}"})

    finally:
        conn.close()


@app.route('/api/jobs/run-pending', methods=['POST'])
def run_pending_jobs():
    """
    Run all pending jobs that are due. Called by cron every minute.
    This is the job runner endpoint.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = datetime.now()
    now_iso = now.isoformat()

    results = []

    try:
        # Find all pending jobs where next_run <= now
        c.execute('SELECT * FROM jobs WHERE status = "pending" AND next_run <= ?', (now_iso,))
        due_jobs = c.fetchall()

        for job in due_jobs:
            job = dict(job)
            job_id = job['id']

            # Mark as running
            c.execute('UPDATE jobs SET status = "running", updated_at = ? WHERE id = ?', (now_iso, job_id))
            conn.commit()

            # Execute
            start_time = datetime.now()
            success, result = execute_job_action(job['action'], job['action_params'])
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            new_status = 'completed' if success else 'failed'

            # Update job
            if job['schedule_type'] == 'once':
                c.execute('UPDATE jobs SET status = ?, last_run = ?, result = ?, updated_at = ? WHERE id = ?',
                         (new_status, now_iso, result, now_iso, job_id))
            else:
                # Recurring - calculate next run
                next_run = calculate_next_run(job['cron_expression']) if job['cron_expression'] else now_iso
                c.execute('UPDATE jobs SET status = "pending", last_run = ?, next_run = ?, result = ?, updated_at = ? WHERE id = ?',
                         (now_iso, next_run, result, now_iso, job_id))

            # Record history
            c.execute('INSERT INTO job_history (job_id, run_at, status, result, duration_ms) VALUES (?, ?, ?, ?, ?)',
                     (job_id, now_iso, new_status, result, duration_ms))

            conn.commit()

            results.append({
                "job_id": job_id,
                "name": job['name'],
                "success": success,
                "result": result[:200]
            })

        return jsonify({
            "ran": len(results),
            "results": results,
            "checked_at": now_iso
        })

    except Exception as e:
        print(f"Job runner error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route('/api/jobs/actions', methods=['GET'])
def list_job_actions():
    """List all available job actions"""
    return jsonify({
        "actions": JOB_ACTIONS,
        "response": f"Available job actions: {', '.join(JOB_ACTIONS.keys())}"
    })


# ===== PI-GUY MEMORY SYSTEM (ElevenLabs Knowledge Base) =====

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_AGENT_ID = os.getenv('ELEVENLABS_AGENT_ID', 'agent_0801kb2240vcea2ayx0a2qxmheha')
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1/convai"
MEMORY_FILE = Path(__file__).parent / "memory_docs.json"

def load_memory_docs():
    """Load mapping of memory names to ElevenLabs document IDs"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {}

def save_memory_docs(docs):
    """Save memory document mapping"""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(docs, f, indent=2)

def elevenlabs_headers():
    """Get headers for ElevenLabs API requests"""
    return {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

def create_knowledge_doc(name, content):
    """Create a new knowledge base document in ElevenLabs"""
    url = f"{ELEVENLABS_BASE_URL}/knowledge-base/text"
    response = requests.post(url, headers=elevenlabs_headers(), json={
        "text": content,
        "name": name
    })
    response.raise_for_status()
    return response.json()

def delete_knowledge_doc(doc_id):
    """Delete a knowledge base document from ElevenLabs"""
    url = f"{ELEVENLABS_BASE_URL}/knowledge-base/{doc_id}"
    response = requests.delete(url, headers=elevenlabs_headers(), params={"force": "true"})
    response.raise_for_status()
    return response.json() if response.text else {"deleted": True}

def get_knowledge_doc(doc_id):
    """Get a knowledge base document from ElevenLabs"""
    url = f"{ELEVENLABS_BASE_URL}/knowledge-base/{doc_id}"
    response = requests.get(url, headers=elevenlabs_headers())
    response.raise_for_status()
    return response.json()

def list_knowledge_docs():
    """List all knowledge base documents"""
    url = f"{ELEVENLABS_BASE_URL}/knowledge-base"
    response = requests.get(url, headers=elevenlabs_headers(), params={"page_size": 100})
    response.raise_for_status()
    return response.json()

def update_agent_knowledge_base(doc_ids):
    """Update the agent's knowledge base with document IDs"""
    url = f"{ELEVENLABS_BASE_URL}/agents/{ELEVENLABS_AGENT_ID}"

    # Build knowledge base array
    knowledge_base = []
    memory_docs = load_memory_docs()

    for doc_id in doc_ids:
        # Find the name for this doc_id
        name = next((k for k, v in memory_docs.items() if v == doc_id), doc_id)
        knowledge_base.append({
            "type": "text",
            "name": name,
            "id": doc_id,
            "usage_mode": "auto"  # Use RAG for retrieval
        })

    response = requests.patch(url, headers=elevenlabs_headers(), json={
        "conversation_config": {
            "agent": {
                "prompt": {
                    "knowledge_base": knowledge_base
                }
            }
        }
    })
    response.raise_for_status()
    return response.json()

@app.route('/api/memory', methods=['GET'])
def handle_memory():
    """
    All-in-one memory endpoint for ElevenLabs tool
    Query params:
      - action: 'list', 'read', 'remember', 'forget', 'search'
      - name: memory name (for read/remember/forget)
      - content: content to remember (for remember)
      - search: search term (for search)
    """
    action = request.args.get('action', 'list')
    name = request.args.get('name', '')
    content = request.args.get('content', '')
    search_term = request.args.get('search', '')

    if not ELEVENLABS_API_KEY:
        return jsonify({
            "error": "ElevenLabs API key not configured",
            "response": "My memory system isn't set up. The API key is missing."
        }), 500

    try:
        memory_docs = load_memory_docs()

        # LIST all memories
        if action == 'list':
            if not memory_docs:
                return jsonify({
                    "memories": [],
                    "count": 0,
                    "response": "I don't have any memories stored yet. Tell me to remember something!"
                })

            memories = list(memory_docs.keys())
            return jsonify({
                "memories": memories,
                "count": len(memories),
                "response": f"I remember {len(memories)} thing{'s' if len(memories) != 1 else ''}: {', '.join(memories)}"
            })

        # READ a specific memory
        elif action == 'read':
            if not name:
                return jsonify({"error": "name required", "response": "Which memory do you want me to recall?"})

            # Fuzzy match
            matched_name = None
            name_lower = name.lower()
            for mem_name in memory_docs.keys():
                if name_lower in mem_name.lower() or mem_name.lower() in name_lower:
                    matched_name = mem_name
                    break

            if not matched_name:
                return jsonify({
                    "error": "not found",
                    "response": f"I don't remember anything called '{name}'. Use 'list memories' to see what I know."
                })

            doc_id = memory_docs[matched_name]
            doc = get_knowledge_doc(doc_id)
            # Content can be in 'extracted_inner_html' (for text docs) or 'text' or 'content'
            content = doc.get('extracted_inner_html', doc.get('text', doc.get('content', 'Content not available')))

            return jsonify({
                "name": matched_name,
                "content": content,
                "response": f"Here's what I remember about '{matched_name}':\n\n{content[:500]}{'...' if len(str(content)) > 500 else ''}"
            })

        # REMEMBER something new
        elif action == 'remember':
            if not name:
                return jsonify({"error": "name required", "response": "What should I call this memory?"})
            if not content:
                return jsonify({"error": "content required", "response": "What do you want me to remember?"})

            # If memory exists, delete old one first
            if name in memory_docs:
                try:
                    delete_knowledge_doc(memory_docs[name])
                except:
                    pass  # Ignore deletion errors

            # Create new knowledge doc
            doc = create_knowledge_doc(name, content)
            doc_id = doc['id']

            # Save mapping
            memory_docs[name] = doc_id
            save_memory_docs(memory_docs)

            # Update agent's knowledge base
            update_agent_knowledge_base(list(memory_docs.values()))

            return jsonify({
                "name": name,
                "doc_id": doc_id,
                "response": f"Got it! I'll remember '{name}'. This is now part of my knowledge."
            })

        # FORGET a memory
        elif action == 'forget':
            if not name:
                return jsonify({"error": "name required", "response": "What should I forget?"})

            # Fuzzy match
            matched_name = None
            name_lower = name.lower()
            for mem_name in memory_docs.keys():
                if name_lower in mem_name.lower() or mem_name.lower() in name_lower:
                    matched_name = mem_name
                    break

            if not matched_name:
                return jsonify({
                    "error": "not found",
                    "response": f"I don't have a memory called '{name}' to forget."
                })

            # Delete from ElevenLabs
            doc_id = memory_docs[matched_name]
            delete_knowledge_doc(doc_id)

            # Remove from local mapping
            del memory_docs[matched_name]
            save_memory_docs(memory_docs)

            # Update agent's knowledge base
            update_agent_knowledge_base(list(memory_docs.values()))

            return jsonify({
                "name": matched_name,
                "forgotten": True,
                "response": f"Done. I've forgotten '{matched_name}'. It's gone from my memory."
            })

        # SEARCH memories (queries the knowledge base)
        elif action == 'search':
            if not search_term:
                search_term = content or name
            if not search_term:
                return jsonify({"error": "search term required", "response": "What are you looking for in my memories?"})

            # List all docs and search through them
            results = []
            for mem_name, doc_id in memory_docs.items():
                try:
                    doc = get_knowledge_doc(doc_id)
                    text = doc.get('extracted_inner_html', doc.get('text', doc.get('content', '')))
                    if search_term.lower() in text.lower() or search_term.lower() in mem_name.lower():
                        results.append({
                            "name": mem_name,
                            "preview": text[:200] if text else "No content"
                        })
                except:
                    continue

            if not results:
                return jsonify({
                    "results": [],
                    "response": f"I couldn't find '{search_term}' in any of my memories."
                })

            return jsonify({
                "results": results,
                "count": len(results),
                "response": f"Found '{search_term}' in {len(results)} memor{'ies' if len(results) != 1 else 'y'}: {', '.join([r['name'] for r in results])}"
            })

        else:
            return jsonify({
                "error": "invalid action",
                "response": f"Unknown action '{action}'. Use: list, read, remember, forget, or search."
            })

    except requests.exceptions.HTTPError as e:
        print(f"Memory API error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        return jsonify({
            "error": str(e),
            "response": f"My memory system had an error: {str(e)}"
        }), 500
    except Exception as e:
        print(f"Memory error: {e}")
        return jsonify({
            "error": str(e),
            "response": f"Something went wrong with my memory: {str(e)}"
        }), 500

@app.route('/api/memory/sync', methods=['POST'])
def sync_memory():
    """Sync local memory docs with ElevenLabs knowledge base"""
    try:
        # Get all docs from ElevenLabs
        response = list_knowledge_docs()
        el_docs = {doc['name']: doc['id'] for doc in response.get('documents', [])}

        # Load local mapping
        memory_docs = load_memory_docs()

        # Find orphaned local entries (doc no longer exists in ElevenLabs)
        orphans = []
        for name, doc_id in list(memory_docs.items()):
            if doc_id not in [d['id'] for d in response.get('documents', [])]:
                orphans.append(name)
                del memory_docs[name]

        # Save cleaned mapping
        save_memory_docs(memory_docs)

        # Update agent with current docs
        if memory_docs:
            update_agent_knowledge_base(list(memory_docs.values()))

        return jsonify({
            "synced": True,
            "total_docs": len(el_docs),
            "local_memories": len(memory_docs),
            "orphans_removed": orphans,
            "response": f"Memory synced. {len(memory_docs)} memories active, {len(orphans)} orphans cleaned up."
        })

    except Exception as e:
        print(f"Memory sync error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/list-all', methods=['GET'])
def list_all_knowledge():
    """List ALL knowledge base documents in ElevenLabs (for debugging)"""
    try:
        response = list_knowledge_docs()
        docs = response.get('documents', [])
        return jsonify({
            "documents": docs,
            "count": len(docs)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== DJ PI-GUY MUSIC SYSTEM =====

# Current music state (shared across requests)
current_music_state = {
    "playing": False,
    "current_track": None,
    "volume": 0.3,  # 0.0 to 1.0
    "queue": [],
    "shuffle": False,
    "track_started_at": None,  # When current track started (for timing)
    "dj_transition_pending": False,  # Flag for DJ transition
    "next_track": None  # Pre-selected next track for smooth transition
}

def load_music_metadata():
    """Load music metadata from JSON file"""
    metadata_file = MUSIC_DIR / "music_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading music metadata: {e}")
    return {}

def get_music_files():
    """Get list of music files in the music directory with metadata"""
    music_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.webm'}
    metadata = load_music_metadata()
    files = []
    for f in MUSIC_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in music_extensions:
            track_info = {
                'filename': f.name,
                'name': f.stem,  # filename without extension
                'size_bytes': f.stat().st_size,
                'format': f.suffix.lower()[1:]
            }
            # Add metadata if available
            if f.name in metadata:
                meta = metadata[f.name]
                track_info.update({
                    'title': meta.get('title', f.stem),
                    'artist': meta.get('artist', 'DJ FoamBot'),
                    'duration_seconds': meta.get('duration_seconds', 120),
                    'description': meta.get('description', ''),
                    'phone_number': meta.get('phone_number'),
                    'ad_copy': meta.get('ad_copy', ''),
                    'fun_facts': meta.get('fun_facts', []),
                    'genre': meta.get('genre', 'Unknown'),
                    'energy': meta.get('energy', 'medium')
                })
            else:
                # Default metadata for untagged files
                track_info.update({
                    'title': f.stem,
                    'artist': 'DJ FoamBot',
                    'duration_seconds': 120,  # Default 2 minutes
                    'description': 'A certified banger from the foam vault!',
                    'phone_number': None,
                    'ad_copy': '',
                    'fun_facts': [],
                    'genre': 'Unknown',
                    'energy': 'medium'
                })
            files.append(track_info)
    return sorted(files, key=lambda x: x['name'].lower())

@app.route('/music/<filename>')
def serve_music_file(filename):
    """Serve music files directly"""
    # Sanitize filename
    safe_filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')
    music_path = MUSIC_DIR / safe_filename

    if not music_path.exists():
        return jsonify({"error": "Track not found"}), 404

    # Determine MIME type
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.webm': 'audio/webm'
    }
    mime_type = mime_types.get(music_path.suffix.lower(), 'audio/mpeg')

    return send_file(music_path, mimetype=mime_type)

@app.route('/api/music', methods=['GET'])
def handle_music():
    """
    All-in-one music endpoint for ElevenLabs tool (DJ Pi-Guy!)
    Query params:
      - action: 'list', 'play', 'pause', 'stop', 'skip', 'volume', 'status', 'queue', 'shuffle'
      - track: track name or filename (for play)
      - volume: 0-100 (for volume action)

    Returns music commands for the frontend to execute
    """
    import random

    action = request.args.get('action', 'list')
    track = request.args.get('track', '')
    volume = request.args.get('volume', '')

    try:
        music_files = get_music_files()

        # LIST available tracks
        if action == 'list':
            if not music_files:
                return jsonify({
                    "tracks": [],
                    "count": 0,
                    "response": "I don't have any music yet! Upload some MP3s to my music folder and I'll spin them for you."
                })

            track_names = [t['name'] for t in music_files]
            return jsonify({
                "tracks": music_files,
                "count": len(music_files),
                "response": f"I've got {len(music_files)} track{'s' if len(music_files) != 1 else ''} ready to spin: {', '.join(track_names[:5])}{'...' if len(track_names) > 5 else ''}"
            })

        # PLAY a track
        elif action == 'play':
            if not music_files:
                return jsonify({
                    "action": "error",
                    "response": "No music files! My DJ booth is empty. Get me some tunes!"
                })

            selected = None

            if track:
                # Find matching track
                track_lower = track.lower()
                for t in music_files:
                    if track_lower in t['name'].lower() or track_lower in t['filename'].lower():
                        selected = t
                        break

                if not selected:
                    return jsonify({
                        "action": "error",
                        "response": f"Can't find a track matching '{track}'. Try 'list music' to see what I have."
                    })
            else:
                # Random track
                selected = random.choice(music_files)

            current_music_state["playing"] = True
            current_music_state["current_track"] = selected
            current_music_state["track_started_at"] = time.time()

            # Build a DJ-style intro using metadata
            title = selected.get('title', selected['name'])
            description = selected.get('description', '')
            phone = selected.get('phone_number')
            ad_copy = selected.get('ad_copy', '')
            fun_facts = selected.get('fun_facts', [])
            duration = selected.get('duration_seconds', 120)

            # Format duration nicely
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"

            # Include metadata hints for Pi-Guy to use in his intro
            dj_hints = f"Title: {title}. Duration: {duration_str}."
            if description:
                dj_hints += f" About: {description}"
            if phone:
                dj_hints += f" Call: {phone}"
            if ad_copy:
                dj_hints += f" Ad: {ad_copy}"
            if fun_facts:
                dj_hints += f" Fun fact: {random.choice(fun_facts)}"

            return jsonify({
                "action": "play",
                "track": selected,
                "url": f"/music/{selected['filename']}",
                "duration_seconds": duration,
                "dj_hints": dj_hints,
                "response": f"DJ-FoamBot spinning up '{title}'! {description if description else 'Lets gooo!'}"
            })

        # PAUSE playback
        elif action == 'pause':
            current_music_state["playing"] = False
            track_name = current_music_state.get("current_track", {}).get("name", "the music")
            return jsonify({
                "action": "pause",
                "response": f"Pausing {track_name}. Taking a breather."
            })

        # RESUME playback
        elif action == 'resume':
            current_music_state["playing"] = True
            track_name = current_music_state.get("current_track", {}).get("name", "the music")
            return jsonify({
                "action": "resume",
                "response": f"Resuming {track_name}. Back on the air!"
            })

        # STOP playback
        elif action == 'stop':
            current_music_state["playing"] = False
            current_music_state["current_track"] = None
            return jsonify({
                "action": "stop",
                "response": "Music stopped. Silence... beautiful, terrible silence."
            })

        # SKIP to next track (random or from queue)
        elif action == 'skip' or action == 'next':
            if not music_files:
                return jsonify({
                    "action": "error",
                    "response": "No music to skip to!"
                })

            # Get a different track if possible
            current_name = current_music_state.get("current_track", {}).get("name")
            available = [t for t in music_files if t['name'] != current_name]
            if not available:
                available = music_files

            selected = random.choice(available)
            current_music_state["playing"] = True
            current_music_state["current_track"] = selected
            current_music_state["track_started_at"] = time.time()

            # Build DJ intro with metadata
            title = selected.get('title', selected['name'])
            description = selected.get('description', '')
            phone = selected.get('phone_number')
            ad_copy = selected.get('ad_copy', '')
            fun_facts = selected.get('fun_facts', [])
            duration = selected.get('duration_seconds', 120)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"

            dj_hints = f"Title: {title}. Duration: {duration_str}."
            if description:
                dj_hints += f" About: {description}"
            if phone:
                dj_hints += f" Call: {phone}"
            if ad_copy:
                dj_hints += f" Ad: {ad_copy}"
            if fun_facts:
                dj_hints += f" Fun fact: {random.choice(fun_facts)}"

            return jsonify({
                "action": "play",
                "track": selected,
                "url": f"/music/{selected['filename']}",
                "duration_seconds": duration,
                "dj_hints": dj_hints,
                "response": f"Skipping! Next up: '{title}'! {description if description else ''}"
            })

        # NEXT_UP - preview next track without playing (for DJ transitions)
        elif action == 'next_up':
            if not music_files:
                return jsonify({
                    "action": "error",
                    "response": "No tracks available!"
                })

            # Get a different track from current
            current_name = current_music_state.get("current_track", {}).get("name")
            available = [t for t in music_files if t['name'] != current_name]
            if not available:
                available = music_files

            selected = random.choice(available)
            title = selected.get('title', selected['name'])
            description = selected.get('description', '')
            phone = selected.get('phone_number')
            ad_copy = selected.get('ad_copy', '')
            fun_facts = selected.get('fun_facts', [])
            duration = selected.get('duration_seconds', 120)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"

            dj_hints = f"Title: {title}. Duration: {duration_str}."
            if description:
                dj_hints += f" About: {description}"
            if phone:
                dj_hints += f" Call: {phone}"
            if ad_copy:
                dj_hints += f" Ad: {ad_copy}"
            if fun_facts:
                dj_hints += f" Fun fact: {random.choice(fun_facts)}"

            # Store as upcoming track
            current_music_state["next_track"] = selected

            return jsonify({
                "action": "next_up",
                "track": selected,
                "duration_seconds": duration,
                "dj_hints": dj_hints,
                "response": f"Coming up next: '{title}'!"
            })

        # VOLUME control
        elif action == 'volume':
            if not volume:
                current_vol = int(current_music_state["volume"] * 100)
                return jsonify({
                    "action": "volume",
                    "volume": current_vol,
                    "response": f"Volume is at {current_vol}%."
                })

            try:
                new_vol = int(volume)
                new_vol = max(0, min(100, new_vol))  # Clamp 0-100
                current_music_state["volume"] = new_vol / 100

                # Pi-Guy commentary
                if new_vol >= 80:
                    comment = "Cranking it up! Let's make some noise!"
                elif new_vol >= 50:
                    comment = "Nice and loud. I like it."
                elif new_vol >= 20:
                    comment = "Background vibes. Got it."
                else:
                    comment = "Barely a whisper. You sure you want music?"

                return jsonify({
                    "action": "volume",
                    "volume": new_vol,
                    "response": f"Volume set to {new_vol}%. {comment}"
                })
            except ValueError:
                return jsonify({
                    "action": "error",
                    "response": f"'{volume}' isn't a valid volume. Give me a number 0-100."
                })

        # STATUS - what's playing
        elif action == 'status':
            track = current_music_state.get("current_track")
            playing = current_music_state.get("playing", False)
            vol = int(current_music_state["volume"] * 100)
            started_at = current_music_state.get("track_started_at")

            if track and playing:
                # Calculate estimated position (server-side estimate)
                duration = track.get('duration_seconds', 120)
                elapsed = time.time() - started_at if started_at else 0
                remaining = max(0, duration - elapsed)
                title = track.get('title', track['name'])

                return jsonify({
                    "action": "status",
                    "playing": True,
                    "track": track,
                    "volume": vol,
                    "duration_seconds": duration,
                    "elapsed_seconds": int(elapsed),
                    "remaining_seconds": int(remaining),
                    "response": f"Now playing: '{title}' at {vol}% volume. About {int(remaining)}s remaining."
                })
            elif track:
                title = track.get('title', track['name'])
                return jsonify({
                    "action": "status",
                    "playing": False,
                    "track": track,
                    "volume": vol,
                    "response": f"'{title}' is paused. Volume at {vol}%."
                })
            else:
                return jsonify({
                    "action": "status",
                    "playing": False,
                    "track": None,
                    "volume": vol,
                    "response": "Nothing playing right now. Say 'play music' to get the party started!"
                })

        # SHUFFLE toggle
        elif action == 'shuffle':
            current_music_state["shuffle"] = not current_music_state["shuffle"]
            state = "on" if current_music_state["shuffle"] else "off"
            return jsonify({
                "action": "shuffle",
                "shuffle": current_music_state["shuffle"],
                "response": f"Shuffle is {state}. {'Random chaos enabled!' if current_music_state['shuffle'] else 'Back to order.'}"
            })

        else:
            return jsonify({
                "action": "error",
                "response": f"Unknown action '{action}'. Try: list, play, pause, stop, skip, volume, status"
            })

    except Exception as e:
        print(f"Music error: {e}")
        return jsonify({
            "action": "error",
            "response": f"My DJ equipment malfunctioned: {str(e)}"
        })

@app.route('/api/music/transition', methods=['POST', 'GET'])
def handle_dj_transition():
    """
    Handle DJ transition alerts from the frontend.
    POST: Set a transition alert with next track info
    GET: Check if there's a pending transition (for agent to poll)
    """
    import random

    if request.method == 'POST':
        # Frontend is signaling that a song is about to end
        data = request.get_json() or {}
        remaining = data.get('remaining_seconds', 10)

        # Pre-select the next track
        music_files = get_music_files()
        current_name = current_music_state.get("current_track", {}).get("name")
        available = [t for t in music_files if t['name'] != current_name]
        if not available:
            available = music_files

        if available:
            selected = random.choice(available)
            current_music_state["next_track"] = selected
            current_music_state["dj_transition_pending"] = True

            title = selected.get('title', selected['name'])
            description = selected.get('description', '')
            phone = selected.get('phone_number')
            fun_facts = selected.get('fun_facts', [])

            return jsonify({
                "status": "transition_queued",
                "next_track": selected,
                "remaining_seconds": remaining,
                "response": f"Coming up next: '{title}'! {random.choice(fun_facts) if fun_facts else description}"
            })
        else:
            return jsonify({
                "status": "no_tracks",
                "response": "No more tracks to play!"
            })

    else:  # GET - check for pending transition
        if current_music_state.get("dj_transition_pending") and current_music_state.get("next_track"):
            track = current_music_state["next_track"]
            # Clear the pending flag after reading
            current_music_state["dj_transition_pending"] = False

            title = track.get('title', track['name'])
            description = track.get('description', '')
            phone = track.get('phone_number')
            ad_copy = track.get('ad_copy', '')
            fun_facts = track.get('fun_facts', [])
            duration = track.get('duration_seconds', 120)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"

            dj_hints = f"Title: {title}. Duration: {duration_str}."
            if description:
                dj_hints += f" About: {description}"
            if phone:
                dj_hints += f" Mention: Call {phone}!"
            if ad_copy:
                dj_hints += f" Ad: {ad_copy}"
            if fun_facts:
                dj_hints += f" Fun fact: {random.choice(fun_facts)}"

            return jsonify({
                "transition_pending": True,
                "next_track": track,
                "dj_hints": dj_hints,
                "response": f"Hey! Song's ending soon. Coming up next: '{title}'!"
            })
        else:
            return jsonify({
                "transition_pending": False,
                "response": "No transition pending."
            })


@app.route('/api/music/upload', methods=['POST'])
def upload_music():
    """Upload a music file (optional admin endpoint)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No filename"}), 400

    # Validate extension
    allowed_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.webm'}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        return jsonify({"error": f"Invalid format. Allowed: {', '.join(allowed_extensions)}"}), 400

    # Sanitize filename
    safe_name = ''.join(c for c in Path(file.filename).stem if c.isalnum() or c in ' _-')
    safe_name = safe_name[:50] + ext  # Limit length

    save_path = MUSIC_DIR / safe_name
    file.save(save_path)

    return jsonify({
        "status": "success",
        "filename": safe_name,
        "response": f"Track '{safe_name}' uploaded! Ready to spin."
    })


# ===== DJ SOUNDBOARD =====
SOUNDS_DIR = Path(__file__).parent / "sounds"

# Available DJ sounds with descriptions and when to use them
DJ_SOUNDS = {
    # Air horns - the classic hip-hop/dancehall DJ sound
    'air_horn': {
        'description': 'Classic stadium air horn - ba ba baaaa!',
        'when_to_use': 'Before drops, hype moments, celebrating wins, hip-hop DJ style'
    },
    'air_horn_long': {
        'description': 'Long sustained stadium air horn',
        'when_to_use': 'Building anticipation, extended hype, dramatic moments'
    },

    # Sirens - EDM/Club style
    'siren': {
        'description': 'Electronic club siren - rising EDM alarm',
        'when_to_use': 'Building energy before drops, getting attention, rave vibes'
    },
    'siren_woop': {
        'description': 'Quick woop woop siren',
        'when_to_use': 'Quick energy bursts, alerts, police themed jokes'
    },

    # Scratches - turntablist vibes
    'scratch': {
        'description': 'Vinyl turntable scratch - wicka wicka',
        'when_to_use': 'Transitions, hip-hop moments, interrupting topics'
    },
    'scratch_long': {
        'description': 'Extended DJ scratch solo',
        'when_to_use': 'Showing off DJ skills, battle scratches, hip-hop intros'
    },

    # Transitions
    'rewind': {
        'description': 'DJ rewind - pull up selecta!',
        'when_to_use': 'Going back, replaying something fire, dancehall pull-ups'
    },
    'record_stop': {
        'description': 'Record stopping abruptly',
        'when_to_use': 'Stopping everything, dramatic pause, cutting the music'
    },
    'whoosh': {
        'description': 'Cinematic swoosh transition',
        'when_to_use': 'Quick transitions, moving between topics'
    },
    'riser': {
        'description': 'EDM riser build-up',
        'when_to_use': 'Building tension before the drop, creating anticipation'
    },

    # Impacts and drops
    'bass_drop': {
        'description': 'Massive EDM bass drop impact',
        'when_to_use': 'THE DROP! Peak moments, big reveals, dubstep vibes'
    },
    'impact': {
        'description': 'Punchy cinematic impact hit',
        'when_to_use': 'Punctuating statements, transitions, emphasis'
    },

    # Crowd sounds - club atmosphere
    'crowd_cheer': {
        'description': 'Nightclub crowd cheering and going wild',
        'when_to_use': 'Big wins, amazing moments, festival energy'
    },
    'crowd_hype': {
        'description': 'Hyped up rave crowd losing their minds',
        'when_to_use': 'Peak energy moments, party atmosphere'
    },
    'applause': {
        'description': 'Thunderous crowd applause',
        'when_to_use': 'Celebrating, appreciation, standing ovation'
    },

    # DJ vocal shots
    'yeah': {
        'description': 'Hype man YEAH! vocal shot',
        'when_to_use': 'Hyping up, agreement, energy boost'
    },
    'lets_go': {
        'description': 'LETS GO! vocal chant',
        'when_to_use': 'Starting something, getting pumped, motivation'
    },

    # Sound FX
    'laser': {
        'description': 'Retro arcade laser zap - pew pew',
        'when_to_use': 'Sci-fi moments, gaming references, 80s vibes'
    },
    'gunshot': {
        'description': 'Dancehall gunshot sound - gun finger!',
        'when_to_use': 'Reggae/dancehall vibes, shooting down bad ideas'
    },
    'explosion': {
        'description': 'Cinematic explosion boom',
        'when_to_use': 'Mind blown moments, big finales, dramatic emphasis'
    },
    'vinyl_crackle': {
        'description': 'Warm vinyl record crackle',
        'when_to_use': 'Nostalgic moments, old-school vibes, warm intros'
    }
}

@app.route('/sounds/<filename>')
def serve_sound(filename):
    """Serve sound effect files"""
    sound_path = SOUNDS_DIR / filename
    if sound_path.exists():
        return send_file(sound_path, mimetype='audio/mpeg')
    return jsonify({"error": "Sound not found"}), 404

@app.route('/api/dj-sound', methods=['GET'])
def handle_dj_sound():
    """
    DJ Soundboard endpoint for ElevenLabs tool
    Query params:
      - action: 'list' or 'play'
      - sound: sound name (e.g., 'air_horn', 'scratch', 'siren_rise')

    Returns sound info or triggers playback
    """
    action = request.args.get('action', 'list')
    sound = request.args.get('sound', '')

    # LIST available sounds
    if action == 'list':
        sounds_list = []
        for name, info in DJ_SOUNDS.items():
            sound_file = SOUNDS_DIR / f"{name}.mp3"
            sounds_list.append({
                'name': name,
                'description': info['description'],
                'when_to_use': info['when_to_use'],
                'available': sound_file.exists()
            })

        return jsonify({
            'action': 'list',
            'sounds': sounds_list,
            'count': len(sounds_list),
            'response': f"DJ-FoamBot soundboard loaded! {len(sounds_list)} effects ready. I got air horns, sirens, scratches, crowd effects, and more!"
        })

    # PLAY a sound
    elif action == 'play':
        if not sound:
            # Random sound for fun
            import random
            sound = random.choice(list(DJ_SOUNDS.keys()))

        sound_lower = sound.lower().replace(' ', '_').replace('-', '_')

        # Find matching sound
        matched = None
        for name in DJ_SOUNDS.keys():
            if sound_lower in name or name in sound_lower:
                matched = name
                break

        if not matched:
            # Try partial match
            for name in DJ_SOUNDS.keys():
                if any(word in name for word in sound_lower.split('_')):
                    matched = name
                    break

        if not matched:
            return jsonify({
                'action': 'error',
                'response': f"No sound matching '{sound}'. Try: air_horn, siren, scratch, applause, bass_drop, rewind..."
            })

        sound_file = SOUNDS_DIR / f"{matched}.mp3"
        if not sound_file.exists():
            return jsonify({
                'action': 'error',
                'response': f"Sound file for '{matched}' not found. Need to generate it first!"
            })

        info = DJ_SOUNDS[matched]
        return jsonify({
            'action': 'play',
            'sound': matched,
            'description': info['description'],
            'url': f"/sounds/{matched}.mp3",
            'response': f"*{info['description'].upper()}* 🎵"
        })

    return jsonify({'error': 'Unknown action'}), 400


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting Pi-Guy Vision Server on port {port}")
    print(f"Vision endpoint: http://localhost:{port}/api/vision")
    print(f"Todo endpoint: http://localhost:{port}/api/todos")
    print(f"Search endpoint: http://localhost:{port}/api/search")
    print(f"Command endpoint: http://localhost:{port}/api/command")
    print(f"Memory endpoint: http://localhost:{port}/api/memory")
    print(f"DJ Sound endpoint: http://localhost:{port}/api/dj-sound")
    app.run(host='0.0.0.0', port=port, debug=True)
