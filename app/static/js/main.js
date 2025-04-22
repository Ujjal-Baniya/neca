/**
 * Main JavaScript file for the Service Marketplace application
 */

$(document).ready(function() {
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Service image gallery
    const mainImage = $('#main-service-image');
    $('.service-thumbnail').on('click', function() {
        const imgSrc = $(this).attr('src');
        mainImage.attr('src', imgSrc);
        $('.service-thumbnail').removeClass('active');
        $(this).addClass('active');
    });
    
    // Review image gallery
    $('.review-image').on('click', function() {
        const imgSrc = $(this).attr('src');
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        $('#modalImage').attr('src', imgSrc);
        modal.show();
    });
    
    // Star rating input
    $('.rating-input').on('change', function() {
        const value = $(this).val();
        const stars = $(this).closest('.rating-group').find('.rating-star');
        
        stars.each(function(index) {
            if (index < value) {
                $(this).removeClass('far').addClass('fas');
            } else {
                $(this).removeClass('fas').addClass('far');
            }
        });
    });
    
    // Handle message form submission via AJAX
    $('#message-form').on('submit', function(e) {
        if (typeof socket !== 'undefined') {
            e.preventDefault();
            const form = $(this);
            const content = form.find('textarea[name="content"]').val();
            const recipientId = form.find('input[name="recipient_id"]').val();
            
            // Emit Socket.IO event
            socket.emit('send_message', {
                content: content,
                recipient_id: parseInt(recipientId)
            }, function(response) {
                if (response.success) {
                    // Clear form and show success message
                    form.find('textarea').val('');
                    showAlert('Message sent successfully!', 'success');
                    
                    // If in conversation view, append message to chat
                    if ($('.chat-messages').length) {
                        appendMessage(content, true);
                    }
                } else {
                    showAlert('Error sending message: ' + response.error, 'danger');
                }
            });
        }
    });
    
    // Handle notification marking as read
    $('.mark-notification-read').on('click', function(e) {
        e.preventDefault();
        const btn = $(this);
        const url = btn.data('url');
        
        $.ajax({
            url: url,
            type: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    btn.closest('.notification-item').removeClass('notification-unread');
                    updateNotificationCount();
                }
            }
        });
    });
    
    // Handle mark all notifications as read
    $('#mark-all-notifications-read').on('click', function(e) {
        e.preventDefault();
        const btn = $(this);
        const url = btn.data('url');
        
        $.ajax({
            url: url,
            type: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    $('.notification-item').removeClass('notification-unread');
                    updateNotificationCount();
                }
            }
        });
    });
    
    // Handle service search form
    $('#service-search-form').on('submit', function() {
        // Remove empty fields to keep URL clean
        $(this).find('input, select').each(function() {
            if (!$(this).val()) {
                $(this).prop('disabled', true);
            }
        });
    });
    
    // File input preview
    $('.custom-file-input').on('change', function() {
        const fileCount = this.files.length;
        let fileName = fileCount > 1 
            ? fileCount + ' files selected' 
            : $(this).val().split('\\').pop();
        
        $(this).next('.custom-file-label').html(fileName);
        
        // Show image preview
        if (fileCount > 0 && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').attr('src', e.target.result).show();
            }
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    // Socket.IO connection for real-time features
    if (typeof io !== 'undefined') {
        // Connect to Socket.IO in the conversation page
        if ($('.chat-container').length) {
            const conversationId = $('.chat-container').data('conversation-id');
            
            // Tell server to join this conversation room
            socket.emit('join_conversation', {
                conversation_id: conversationId
            });
            
            // Handle receiving a new message
            socket.on('new_message', function(data) {
                if (data.conversation_id == conversationId) {
                    // Check if the message is from the other user (not self)
                    if (data.sender_id != currentUserId) {
                        appendMessage(data.content, false, data.timestamp);
                        
                        // Mark message as read
                        $.ajax({
                            url: '/messages/mark-read/' + data.message_id,
                            type: 'POST'
                        });
                    }
                }
            });
            
            // Leave the conversation room when leaving the page
            $(window).on('beforeunload', function() {
                socket.emit('leave_conversation', {
                    conversation_id: conversationId
                });
            });
        }
    }
    
    // Scroll to bottom of chat on page load
    if ($('.chat-messages').length) {
        scrollChatToBottom();
    }
});

// Helper Functions

/**
 * Append a message to the chat container
 * @param {string} content - The message content
 * @param {boolean} isSender - Whether the current user is the sender
 * @param {string} timestamp - Optional timestamp string
 */
function appendMessage(content, isSender, timestamp = null) {
    const chatMessages = $('.chat-messages');
    const messageClass = isSender ? 'message-sender' : 'message-receiver';
    const messageDirection = isSender ? 'sender' : 'receiver';
    
    // Create timestamp if not provided
    if (!timestamp) {
        const now = new Date();
        timestamp = now.toISOString();
    }
    
    // Format the timestamp
    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Create the message HTML
    const messageHtml = `
        <div class="message ${messageDirection}">
            <div class="${messageClass}">${content}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    // Append to chat and scroll to bottom
    chatMessages.append(messageHtml);
    scrollChatToBottom();
}

/**
 * Scroll the chat container to the bottom
 */
function scrollChatToBottom() {
    const chatMessages = $('.chat-messages');
    chatMessages.scrollTop(chatMessages[0].scrollHeight);
}

/**
 * Show an alert message
 * @param {string} message - The alert message
 * @param {string} type - Alert type (success, info, warning, danger)
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show mt-3" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    $('#alerts-container').html(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
}

/**
 * Update the notification count in the navbar
 */
function updateNotificationCount() {
    $.ajax({
        url: '/notifications/get-unread-count',
        type: 'GET',
        success: function(response) {
            const count = response.count;
            const badge = $('#notification-count');
            
            if (count > 0) {
                badge.text(count).removeClass('d-none');
            } else {
                badge.text('0').addClass('d-none');
            }
        }
    });
}