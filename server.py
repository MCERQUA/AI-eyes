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
    """Get the currently identified person"""
    global current_identity
    if current_identity:
        return jsonify(current_identity)
    return jsonify({"name": "unknown", "confidence": 0, "message": "No identification performed yet"})

@app.route('/api/faces', methods=['GET'])
def list_faces():
    """List all known faces in the database"""
    faces = {}
    for person_dir in KNOWN_FACES_DIR.iterdir():
        if person_dir.is_dir():
            images = [f.name for f in person_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            if images:
                faces[person_dir.name] = images
    return jsonify(faces)

@app.route('/api/faces/<name>', methods=['POST'])
def add_face(name):
    """
    Add a new face image for a person
    Expects base64 image in JSON body
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400

    try:
        # Create person directory if needed
        person_dir = KNOWN_FACES_DIR / name
        person_dir.mkdir(exist_ok=True)

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
            "path": str(image_path)
        })

    except Exception as e:
        print(f"Add face error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/faces/<name>', methods=['DELETE'])
def remove_face(name):
    """Remove all face images for a person"""
    person_dir = KNOWN_FACES_DIR / name
    if person_dir.exists():
        shutil.rmtree(person_dir)

        # Clear DeepFace cache
        cache_file = KNOWN_FACES_DIR / "representations_vgg_face.pkl"
        if cache_file.exists():
            cache_file.unlink()

        return jsonify({"status": "success", "message": f"Removed {name} from database"})
    return jsonify({"error": f"{name} not found"}), 404

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting Pi-Guy Vision Server on port {port}")
    print(f"Vision endpoint: http://localhost:{port}/api/vision")
    app.run(host='0.0.0.0', port=port, debug=True)
