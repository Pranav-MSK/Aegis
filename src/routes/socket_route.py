
# from threading import Lock
# from functools import wraps
# from flask_socketio import SocketIO, emit

# from src.config import socketio
# from src.utils import _collect_metrics

# thread = None
# thread_lock = Lock()

# def background_thread():
#     """Background thread that sends system metrics to clients"""
#     while True:
#         try:
#             metrics = _collect_metrics()
#             if metrics:
#                 socketio.emit('system_metrics', metrics)
#             socketio.sleep(1)  # Update every second
#         except Exception as e:
#             print(f"Error in background thread: {str(e)}")
#             socketio.sleep(5)  # Wait longer if there's an error

# @socketio.on('connect')
# def handle_connect():
#     """Handle client connection"""
#     global thread
#     with thread_lock:
#         if thread is None:
#             thread = socketio.start_background_task(background_thread)
#     emit('connect_response', {'status': 'connected'})

# @socketio.on('disconnect')
# def handle_disconnect():
#     """Handle client disconnection"""
#     print('Client disconnected')

# @socketio.on('request_metrics')
# def handle_metrics_request():
#     """Handle individual metrics request"""
#     try:
#         metrics = _collect_metrics()
#         if metrics:
#             emit('system_metrics', metrics)
#         else:
#             emit('error', {'message': 'Failed to collect metrics'})
#     except Exception as e:
#         emit('error', {
#             'message': 'An error occurred while fetching the system information',
#             'details': str(e)
#         })

# # Error handling for the socket
# @socketio.on_error()
# def error_handler(e):
#     """Handle socket errors"""
#     print(f'Socket error: {str(e)}')
#     emit('error', {
#         'message': 'An error occurred in the socket connection',
#         'details': str(e)
#     })