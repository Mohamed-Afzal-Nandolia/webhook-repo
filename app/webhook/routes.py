from flask import Blueprint, json, request, current_app, send_file
from app.extensions import mongo
from datetime import datetime
from bson.objectid import ObjectId
import io

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

def parse_github_payload(payload):
    """
    Parse GitHub webhook payload and extract required fields.
    """
    event_type = request.headers.get('X-GitHub-Event', 'unknown').lower()
    
    # Determine action type and extract fields based on event type
    if event_type == 'push':
        action = 'PUSH'
        author = payload.get('pusher', {}).get('name', 'Unknown')
        to_branch = payload.get('ref', '').split('/')[-1]
        from_branch = ''
        timestamp = payload.get('head_commit', {}).get('timestamp', datetime.utcnow().isoformat() + 'Z')
    
    elif event_type == 'pull_request':
        pr_action = payload.get('action', 'opened').upper()
        action = 'PULL_REQUEST'
        author = payload.get('pull_request', {}).get('user', {}).get('login', 'Unknown')
        from_branch = payload.get('pull_request', {}).get('head', {}).get('ref', '')
        to_branch = payload.get('pull_request', {}).get('base', {}).get('ref', '')
        timestamp = payload.get('pull_request', {}).get('created_at', datetime.utcnow().isoformat() + 'Z')
    
    else:
        # Default fallback
        action = 'PUSH'
        author = payload.get('pusher', {}).get('name', 'Unknown')
        to_branch = payload.get('ref', '').split('/')[-1] if payload.get('ref') else ''
        from_branch = ''
        timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Get request ID (use GitHub event ID)
    request_id = request.headers.get('X-GitHub-Delivery', str(ObjectId()))
    
    return {
        'request_id': request_id,
        'author': author,
        'action': action,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'pr_action': pr_action if event_type == 'pull_request' else '',
        'timestamp': timestamp
    }

@webhook.route('/receiver', methods=["POST"])
def receiver():
    """
    GitHub webhook receiver endpoint.
    Receives webhook payload and stores it in MongoDB.
    """
    try:
        payload = request.get_json()
        
        if not payload:
            return {'error': 'No payload received'}, 400
        
        # Parse the payload
        data = parse_github_payload(payload)
        
        # Insert into MongoDB
        result = mongo.db.webhooks.insert_one({
            'request_id': data['request_id'],
            'author': data['author'],
            'action': data['action'],
            'from_branch': data['from_branch'],
            'to_branch': data['to_branch'],
            'timestamp': data['timestamp'],
            'created_at': datetime.utcnow()
        })
        
        return {
            'status': 'success',
            'id': str(result.inserted_id),
            'message': 'Webhook received and stored'
        }, 200
    
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }, 500

@webhook.route('/events', methods=["GET"])
def get_events():
    """
    GET endpoint to retrieve all stored webhook events.
    Used by UI to poll for updates.
    """
    try:
        # Get all events sorted by timestamp in descending order
        events = list(mongo.db.webhooks.find().sort('created_at', -1).limit(50))
        
        # Convert ObjectId to string for JSON serialization
        for event in events:
            event['_id'] = str(event['_id'])
        
        return {
            'status': 'success',
            'count': len(events),
            'events': events
        }, 200
    
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }, 500

@webhook.route('/', methods=["GET"])
def index():
    """
    Serve the main UI page.
    """
    try:
        with open('static/index.html', 'r') as f:
            return f.read(), 200
    except:
        return '<h1>Webhook Receiver Active</h1><p>Access /webhook/events for data</p>', 200
