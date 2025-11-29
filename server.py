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
import psutil
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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting Pi-Guy Vision Server on port {port}")
    print(f"Vision endpoint: http://localhost:{port}/api/vision")
    print(f"Todo endpoint: http://localhost:{port}/api/todos")
    print(f"Search endpoint: http://localhost:{port}/api/search")
    print(f"Command endpoint: http://localhost:{port}/api/command")
    app.run(host='0.0.0.0', port=port, debug=True)
