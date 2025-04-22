"""Message views."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room

from app.extensions import db, socketio
from app.forms.message import MessageForm
from app.models.message import Message, Conversation
from app.models.user import User
from app.models.notification import Notification

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/')
@login_required
def index():
    """View message inbox."""
    # Get conversations for current user
    conversations = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) | (Conversation.user2_id == current_user.id))
    ).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('messages/index.html', conversations=conversations)

@messages_bp.route('/conversation/<int:conversation_id>')
@login_required
def conversation(conversation_id):
    """View a conversation."""
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Ensure user is part of the conversation
    if not conversation.has_user(current_user.id):
        abort(403)
    
    # Get the other user in the conversation
    other_user = conversation.get_other_user(current_user.id)
    
    # Get messages for this conversation
    page = request.args.get('page', 1, type=int)
    messages = conversation.messages.order_by(Message.created_at.desc()) \
        .paginate(page=page, per_page=current_app.config['MESSAGES_PER_PAGE'])
    
    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        conversation_id=conversation_id,
        recipient_id=current_user.id,
        read=False
    ).all()
    
    for message in unread_messages:
        message.mark_as_read()
    
    # Create message form
    form = MessageForm()
    form.recipient_id.data = other_user.id
    
    return render_template('messages/conversation.html',
                          conversation=conversation,
                          other_user=other_user,
                          messages=messages,
                          form=form)

@messages_bp.route('/send', methods=['POST'])
@login_required
def send():
    """Send a new message."""
    form = MessageForm()
    
    if form.validate_on_submit():
        recipient_id = int(form.recipient_id.data)
        recipient = User.query.get_or_404(recipient_id)
        
        # Get or create conversation
        conversation = Conversation.get_or_create(current_user.id, recipient_id)
        
        # Create message
        message = Message(
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            conversation_id=conversation.id
        )
        
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = message.created_at
        
        db.session.commit()
        
        # Create notification for recipient
        notification_content = f"New message from {current_user.username}"
        Notification.create(
            user_id=recipient_id,
            type='message',
            content=notification_content,
            related_id=message.id
        )
        
        # Emit Socket.IO event
        socketio.emit('new_message', {
            'conversation_id': conversation.id,
            'message_id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': message.content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.username
        }, room=f'user_{recipient_id}')
        
        # If coming from conversation view, redirect back
        if request.referrer and f'/conversation/{conversation.id}' in request.referrer:
            return redirect(url_for('messages.conversation', conversation_id=conversation.id))
        
        # Otherwise redirect to inbox
        flash('Message sent!', 'success')
        return redirect(url_for('messages.index'))
    
    # Handle form errors
    flash('Error sending message. Please try again.', 'danger')
    return redirect(url_for('messages.index'))

@messages_bp.route('/new/<int:recipient_id>', methods=['GET', 'POST'])
@login_required
def new(recipient_id):
    """Start a new conversation with a user."""
    recipient = User.query.get_or_404(recipient_id)
    
    # Check if conversation already exists
    existing_conversation = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == recipient_id)) |
        ((Conversation.user1_id == recipient_id) & (Conversation.user2_id == current_user.id))
    ).first()
    
    if existing_conversation:
        return redirect(url_for('messages.conversation', conversation_id=existing_conversation.id))
    
    # Create message form
    form = MessageForm()
    form.recipient_id.data = recipient_id
    
    if form.validate_on_submit():
        # Create conversation
        conversation = Conversation(user1_id=current_user.id, user2_id=recipient_id)
        db.session.add(conversation)
        db.session.commit()
        
        # Create message
        message = Message(
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            conversation_id=conversation.id
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Create notification for recipient
        notification_content = f"New message from {current_user.username}"
        Notification.create(
            user_id=recipient_id,
            type='message',
            content=notification_content,
            related_id=message.id
        )
        
        # Emit Socket.IO event
        socketio.emit('new_message', {
            'conversation_id': conversation.id,
            'message_id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': message.content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.username
        }, room=f'user_{recipient_id}')
        
        flash('Message sent!', 'success')
        return redirect(url_for('messages.conversation', conversation_id=conversation.id))
    
    return render_template('messages/new.html', form=form, recipient=recipient)

@messages_bp.route('/mark-read/<int:message_id>', methods=['POST'])
@login_required
def mark_read(message_id):
    """Mark a message as read."""
    message = Message.query.get_or_404(message_id)
    
    # Ensure user is the recipient
    if message.recipient_id != current_user.id:
        abort(403)
    
    message.mark_as_read()
    
    return jsonify({'success': True})

def register_socketio_handlers(socketio_instance):
    """Register Socket.IO event handlers."""
    
    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection."""
        if current_user.is_authenticated:
            # Join a room specific to this user
            join_room(f'user_{current_user.id}')
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        if current_user.is_authenticated:
            # Leave the user-specific room
            leave_room(f'user_{current_user.id}')
    
    @socketio_instance.on('join_conversation')
    def handle_join_conversation(data):
        """Handle client joining a conversation."""
        conversation_id = data.get('conversation_id')
        
        if not conversation_id or not current_user.is_authenticated:
            return
        
        # Verify user is part of the conversation
        conversation = Conversation.query.get(conversation_id)
        if not conversation or not conversation.has_user(current_user.id):
            return
        
        # Join a room for this conversation
        join_room(f'conversation_{conversation_id}')
    
    @socketio_instance.on('leave_conversation')
    def handle_leave_conversation(data):
        """Handle client leaving a conversation."""
        conversation_id = data.get('conversation_id')
        
        if not conversation_id or not current_user.is_authenticated:
            return
        
        # Leave the conversation room
        leave_room(f'conversation_{conversation_id}')
    
    @socketio_instance.on('send_message')
    def handle_send_message(data):
        """Handle sending a message via Socket.IO."""
        if not current_user.is_authenticated:
            return {'error': 'Authentication required'}
        
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        
        if not recipient_id or not content or not content.strip():
            return {'error': 'Invalid message'}
        
        recipient = User.query.get(recipient_id)
        if not recipient:
            return {'error': 'Recipient not found'}
        
        # Get or create conversation
        conversation = Conversation.get_or_create(current_user.id, recipient_id)
        
        # Create message
        message = Message(
            content=content,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            conversation_id=conversation.id
        )
        
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = message.created_at
        
        db.session.commit()
        
        # Create notification for recipient
        notification_content = f"New message from {current_user.username}"
        Notification.create(
            user_id=recipient_id,
            type='message',
            content=notification_content,
            related_id=message.id
        )
        
        # Emit to the recipient's room
        emit('new_message', {
            'conversation_id': conversation.id,
            'message_id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': message.content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.username
        }, room=f'user_{recipient_id}')
        
        # Also emit to the conversation room
        emit('new_message', {
            'conversation_id': conversation.id,
            'message_id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': message.content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.username
        }, room=f'conversation_{conversation.id}')
        
        return {
            'success': True,
            'message_id': message.id,
            'conversation_id': conversation.id
        }