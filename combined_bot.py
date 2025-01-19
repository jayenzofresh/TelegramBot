import os
import sys
import asyncio
import json
import logging
from collections import defaultdict
from queue import Queue
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError
from telethon.sessions import StringSession
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QListWidget, QListWidgetItem, QInputDialog, QTextEdit, QSystemTrayIcon, QMenu, QAction
)
from PyQt6.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPalette, QColor
from config import API_ID, API_HASH
from datetime import datetime, timedelta

# Helper Functions
async def get_user_groups_with_topics(client):
    """
    Retrieves a list of groups and channels with topics that the user is a part of.

    Args:
        client (TelegramClient): The Telegram client to use.

    Returns:
        list: A list of tuples containing the group or channel and its topics.
    """
    groups_with_topics = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                # Get group topics
                group_topics = await client.get_participants(dialog.entity)
                groups_with_topics.append((dialog, group_topics))
            elif dialog.is_channel and dialog.megagroup:
                # Get channel topics
                topics = await client.get_participants(dialog.entity)
                channel_topics = []
                for topic in topics:
                    channel_topics.append(topic)
                groups_with_topics.append((dialog, channel_topics))
    except Exception as e:
        logging.error(f"Error retrieving groups: {e}")
    return groups_with_topics

async def auto_reply(client, event, reply_message):
    """
    Automatically replies to messages with a predefined message.

    Args:
        client (TelegramClient): The Telegram client to use.
        event (NewMessage.Event): The event containing the message.
        reply_message (str): The message to reply with.
    """
    try:
        await client.send_message(event.sender_id, reply_message)
        logging.info(f"Auto-reply sent to user {event.sender_id}")
    except Exception as e:
        logging.error(f"Error sending auto-reply to user {event.sender_id}: {e}")

async def translate_message(message, target_language):
    """
    Translates a message to the specified language.

    Args:
        message (str): The message to translate.
        target_language (str): The target language code (e.g., 'en' for English).

    Returns:
        str: The translated message.
    """
    from googletrans import Translator

    translator = Translator()
    translated = translator.translate(message, dest=target_language)
    translated_message = translated.text
    return translated_message

async def forward_media(client, event, target_groups):
    """
    Forwards media messages to target groups.

    Args:
        client (TelegramClient): The Telegram client to use.
        event (NewMessage.Event): The event containing the media message.
        for group_id in target_groups:
            await client.forward_messages(group_id, event.message)
            logging.info(f"Media forwarded to group {group_id}")
        for group_id in target_groups:
            await client.send_file(group_id, event.message.media)
            logging.info(f"Media forwarded to group {group_id}")
    except Exception as e:
        logging.error(f"Error forwarding media to group {group_id}: {e}")

async def schedule_broadcast(client, message, target_groups, send_time):
    """
    Schedules a broadcast message to be sent to multiple groups at a specified time.

    Args:
        client (TelegramClient): The Telegram client to use.
        message (str): The message to broadcast.
        target_groups (list): A list of target group IDs.
        send_time (datetime): The time to send the broadcast.
    """
    delay = (send_time - datetime.utcnow()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    try:
        for group_id in target_groups:
            await client.send_message(group_id, message)
            logging.info(f"Broadcast message sent to group {group_id} at {send_time}")
    except Exception as e:
        logging.error(f"Error sending broadcast message to group {group_id}: {e}")

async def view_user_analytics(client):
    """
    Retrieves and displays user analytics.

    Args:
        client (TelegramClient): The Telegram client to use.
    """
    # Placeholder for user analytics logic
    analytics = "User analytics data"
    logging.info("User analytics viewed")
    return analytics

async def manage_custom_commands(client, command, response):
    """
    Manages custom commands by adding or updating them.

    Args:
        client (TelegramClient): The Telegram client to use.
        command (str): The custom command.
        response (str): The response to the custom command.
    """
    # Implement custom commands management logic
    try:
        # Assuming you have a dictionary to store commands
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Load pre-trained spam detection model and vectorizer
spam_model = joblib.load('spam_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

async def detect_spam(message):
    """
    Detects spam messages using a Naive Bayes classifier.

    Args:
        message (str): The message to check for spam.

    Returns:
        bool: True if the message is spam, False otherwise.
    """
    message_vector = vectorizer.transform([message])
    is_spam = spam_model.predict(message_vector)[0]
    return is_spam
    Returns:
        bool: True if the message is spam, False otherwise.
    """
    # Placeholder for spam detection logic
    is_spam = "spam" in message.lower()
    return is_spam

async def manage_message_templates(client, template_name, template_content):
    """
    Manages message templates by adding or updating them.

    Args:
        client (TelegramClient): The Telegram client to use.
        template_name (str): The name of the template.
        template_content (str): The content of the template.
    """
    # Placeholder for message templates management logic
    logging.info(f"Message template '{template_name}' managed with content '{template_content}'")

class ForwardingHistory:
    def __init__(self):
        self.history = []

    def add_entry(self, source_group, target_group, message_id, timestamp):
        self.history.append({
            "source_group": source_group,
            "target_group": target_group,
            "message_id": message_id,
            "timestamp": timestamp
        })
        logging.info(f"Message {message_id} forwarded from {source_group} to {target_group} at {timestamp}")

    def get_history(self):
        return self.history

class ForwardingStatistics:
    def __init__(self):
async def forward_message(client, source_group, target_groups_with_topics, selected_users, delay, queue, rate_limits, filters, history, stats):
    """
    Forwards messages from a source group to target groups with topics while respecting Telegram's rate limits.

    Args:
        client (TelegramClient): The Telegram client to use.
        source_group (int): The ID of the source group.
        target_groups_with_topics (list): A list of tuples containing the target group or channel and its topics.
        selected_users (list): A list of user IDs to forward messages from.
        delay (int): The delay between forwarding messages.
        queue (Queue): A queue to manage message forwarding.
        rate_limits (defaultdict): A dictionary to track rate limits for each group.
        filters (dict): A dictionary of filters for forwarding messages.
        history (ForwardingHistory): An instance to track forwarding history.
        stats (ForwardingStatistics): An instance to track forwarding statistics.
    """
    async def handler(event):
        if event.sender_id == (await client.get_me()).id or event.sender_id in selected_users:
            if filters.get("keywords") and not any(keyword in event.message.message for keyword in filters["keywords"]):
                return
            if filters.get("user_ids") and event.sender_id not in filters["user_ids"]:
                return

            for target_group, topics in target_groups_with_topics:
                if rate_limits[target_group.id] > 0:
                    await asyncio.sleep(rate_limits[target_group.id])
                try:
                    if topics:
                        for topic in topics:
                            await client.send_message(target_group.id, event.message, topic=topic.id)
                            history.add_entry(source_group, target_group.id, event.message.id, datetime.now())
                            stats.increment(target_group.id)
                    else:
                        await client.send_message(target_group, event.message)
                        history.add_entry(source_group, target_group.id, event.message.id, datetime.now())
                        stats.increment(target_group.id)
                    if delay > 0:
                        await asyncio.sleep(delay)
                except FloodWaitError as e:
                    logging.error(f"Flood wait error for group {target_group.id}: Waiting for {e.seconds} seconds")
                    rate_limits[target_group.id] = e.seconds
                    await asyncio.sleep(e.seconds)
                except RPCError as e:
                    logging.error(f"RPC error for group {target_group.id}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error for group {target_group.id}: {e}")

    try:
        client.add_event_handler(handler, events.NewMessage(chats=[source_group]))
    except Exception as e:
        logging.error(f"Error adding event handler: {e}")
                    logging.error(f"RPC error for group {target_group.id}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error for group {target_group.id}: {e}")

    try:
        client.add_event_handler(handler, events.NewMessage(chats=[source_group]))
    except Exception as e:
        logging.error(f"Error adding event handler: {e}")

async def get_premium_users(client):
    """
    Retrieves a list of premium users.

    Args:
        client (TelegramClient): The Telegram client to use.

    Returns:
        list: A list of premium user IDs.
    """
    premium_users = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.entity.is_premium:
                premium_users.append(dialog.entity.id)
    except Exception as e:
        logging.error(f"Error retrieving premium users: {e}")
    return premium_users

async def send_premium_message(client, message):
    """
    Sends a message to all premium users.

    Args:
        client (TelegramClient): The Telegram client to use.
        message (str): The message to send.
    """
    premium_users = await get_premium_users(client)
    for user_id in premium_users:
        try:
            await client.send_message(user_id, message)
        except Exception as e:
            logging.error(f"Error sending message to premium user {user_id}: {e}")

async def schedule_message(client, user_id, message, send_time):
    """
    Schedules a message to be sent at a specific time.

    Args:
        client (TelegramClient): The Telegram client to use.
        user_id (int): The ID of the user to send the message to.
        message (str): The message to send.
        send_time (datetime): The time to send the message.
    """
    delay = (send_time - datetime.utcnow()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    try:
        await client.send_message(user_id, message)
        logging.info(f"Scheduled message sent to user {user_id} at {send_time}")
    except Exception as e:
        logging.error(f"Error sending scheduled message to user {user_id}: {e}")

class UserManagement:
    def __init__(self):
        self.users = set()

    def add_user(self, user_id):
        self.users.add(user_id)
        logging.info(f"User {user_id} added to the list")

    def remove_user(self, user_id):
        self.users.discard(user_id)
        logging.info(f"User {user_id} removed from the list")

    def get_users(self):
        return list(self.users)

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Login")
        self.setGeometry(100, 100, 300, 200)

        self.layout = QVBoxLayout()
        self.phone_label = QLabel("Phone Number:")
        self.layout.addWidget(self.phone_label)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g., +123456789")
        self.layout.addWidget(self.phone_input)

        self.send_code_button = QPushButton("Send Verification Code")
        self.send_code_button.clicked.connect(self.send_verification_code)
        self.layout.addWidget(self.send_code_button)

        self.code_label = QLabel("Verification Code:")
        self.layout.addWidget(self.code_label)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter the verification code")
        self.layout.addWidget(self.code_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.start_login)
        self.layout.addWidget(self.login_button)

        self.limit_label = QLabel("User Limit:")
        self.layout.addWidget(self.limit_label)

        self.limit_input = QLineEdit()
        self.limit_input.setText("50")  # Default value
        self.layout.addWidget(self.limit_input)

        self.setLayout(self.layout)

        self.client = None
        self.thread_pool = QThreadPool()
        self.login_worker = None
        self.phone_sent = False

    def send_verification_code(self):
        """Send the verification code to the user's phone number."""
        phone = self.phone_input.text()
        if not phone or not phone.startswith("+"):
            QMessageBox.warning(self, "Error", "Please enter a valid phone number starting with +.")
            return
        try:
            logging.info("Sending verification code to phone number: %s", phone)
            self.client = TelegramClient(StringSession(), API_ID, API_HASH)
            await self.client.connect()
            await self.client.send_code_request(phone)
            self.phone_sent = True
            self.send_code_button.setEnabled(False)
            self.code_input.setEnabled(True)
            self.login_button.setEnabled(True)
        except Exception as e:
            logging.error(f"Error sending verification code: {e}")
            QMessageBox.critical(self, "Error", "Failed to send verification code. Please try again.")

    def start_login(self):
        """Start the login process."""
        if not self.phone_sent:
            QMessageBox.warning(self, "Error", "Please send the verification code first.")
            return
        code = self.code_input.text()
        if not code.strip():
            QMessageBox.warning(self, "Error", "Please enter a valid verification code.")
            return
        logging.info("Starting login process for phone number: %s", self.phone_input.text())
        login_runnable = LoginRunnable(self.phone_input.text(), code)
        login_runnable.success.connect(self.open_main_window)
        login_runnable.error.connect(self.show_error)
        self.thread_pool.start(login_runnable)

    def open_main_window(self, client):
        """Open the main application window."""
        self.client = client
        self.main_window = MainWindow(self.client, int(self.limit_input.text()))
        self.main_window.show()
        self.close()

    def show_error(self, message):
        """Display an error message."""
        logging.error("Error occurred: %s", message)
        QMessageBox.critical(self, "Error", message)

class MainWindow(QWidget):
    def __init__(self, client, limit):
        super().__init__()
        self.client = client
        self.limit = limit
        self.user_management = UserManagement()
        self.forwarding_history = ForwardingHistory()
        self.forwarding_statistics = ForwardingStatistics()
        self.setWindowTitle("Telegram Bot")
        self.setGeometry(100, 100, 600, 700)

        self.layout = QVBoxLayout()

        self.source_label = QLabel("Source Group:")
        self.layout.addWidget(self.source_label)

        self.source_selector = QComboBox()
        self.layout.addWidget(self.source_selector)

        self.target_label = QLabel("Target Groups and Topics:")
        self.layout.addWidget(self.target_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search groups or topics...")
        self.search_bar.textChanged.connect(self.filter_groups)
        self.layout.addWidget(self.search_bar)

        self.target_list = QListWidget()
        self.target_list.setSelectionMode(QListWidget.MultiSelection)
        self.layout.addWidget(self.target_list)

        self.refresh_button = QPushButton("Refresh Groups")
        self.refresh_button.clicked.connect(self.start_refresh_groups)
        self.layout.addWidget(self.refresh_button)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.layout.addWidget(self.log_viewer)

        self.start_button = QPushButton("Start Forwarding")
        self.start_button.clicked.connect(self.start_forwarding)
        self.layout.addWidget(self.start_button)

        self.schedule_button = QPushButton("Schedule Message")
        self.schedule_button.clicked.connect(self.schedule_message)
        self.layout.addWidget(self.schedule_button)

        self.add_user_button = QPushButton("Add User")
        self.add_user_button.clicked.connect(self.add_user)
        self.layout.addWidget(self.add_user_button)

        self.remove_user_button = QPushButton("Remove User")
        self.remove_user_button.clicked.connect(self.remove_user)
        self.layout.addWidget(self.remove_user_button)

        self.view_history_button = QPushButton("View Forwarding History")
        self.view_history_button.clicked.connect(self.view_forwarding_history)
        self.layout.addWidget(self.view_history_button)

        self.view_stats_button = QPushButton("View Forwarding Statistics")
        self.view_stats_button.clicked.connect(self.view_forwarding_statistics)
        self.layout.addWidget(self.view_stats_button)

        self.auto_reply_button = QPushButton("Enable Auto-Reply")
        self.auto_reply_button.clicked.connect(self.enable_auto_reply)
        self.layout.addWidget(self.auto_reply_button)

        self.translate_button = QPushButton("Enable Message Translation")
        self.translate_button.clicked.connect(self.enable_message_translation)
        self.layout.addWidget(self.translate_button)

        self.media_forwarding_button = QPushButton("Enable Media Forwarding")
        self.media_forwarding_button.clicked.connect(self.enable_media_forwarding)
        self.layout.addWidget(self.media_forwarding_button)

        self.broadcast_button = QPushButton("Schedule Broadcast")
        self.broadcast_button.clicked.connect(self.schedule_broadcast)
        self.layout.addWidget(self.broadcast_button)

        self.analytics_button = QPushButton("View User Analytics")
        self.analytics_button.clicked.connect(self.view_user_analytics)
        self.layout.addWidget(self.analytics_button)

        self.custom_commands_button = QPushButton("Manage Custom Commands")
        self.custom_commands_button.clicked.connect(self.manage_custom_commands)
        self.layout.addWidget(self.custom_commands_button)

        self.spam_detection_button = QPushButton("Enable Spam Detection")
        self.spam_detection_button.clicked.connect(self.enable_spam_detection)
        self.layout.addWidget(self.spam_detection_button)

        self.message_templates_button = QPushButton("Manage Message Templates")
        self.message_templates_button.clicked.connect(self.manage_message_templates)
        self.layout.addWidget(self.message_templates_button)

        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        self.tray_icon.setToolTip("Telegram Bot")

        tray_menu = QMenu()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.setLayout(self.layout)
        self.queue = Queue()
        self.rate_limits = defaultdict(int)
        self.groups_with_topics = []

        self.apply_dark_theme()

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(palette)

    def log_message(self, message):
        self.log_viewer.append(message)
        self.tray_icon.showMessage("Telegram Bot", message, QSystemTrayIcon.Information)

    def start_refresh_groups(self):
        async def refresh():
            try:
                self.groups_with_topics = await get_user_groups_with_topics(self.client)
                self.update_groups(self.groups_with_topics)
                self.log_message("Groups refreshed successfully.")
            except Exception as e:
                self.log_message(f"Error refreshing groups: {e}")

        asyncio.run(refresh())

    def update_groups(self, groups_with_topics):
        self.source_selector.clear()
        self.target_list.clear()

        for group, topics in groups_with_topics:
            self.source_selector.addItem(group.title, group.id)
            if topics:
                for topic in topics:
                    item = QListWidgetItem(f"{group.title} - {topic.title}")
                    item.setData(Qt.UserRole, group.id)
                    self.target_list.addItem(item)
            else:
                item = QListWidgetItem(group.title)
                item.setData(Qt.UserRole, group.id)
                self.target_list.addItem(item)

    def filter_groups(self):
        search_text = self.search_bar.text().lower()
        self.target_list.clear()

        for group, topics in self.groups_with_topics:
            if search_text in group.title.lower():
                if topics:
                    for topic in topics:
                        if search_text in topic.title.lower():
                            item = QListWidgetItem(f"{group.title} - {topic.title}")
                            item.setData(Qt.UserRole, group.id)
                            self.target_list.addItem(item)
                else:
                    item = QListWidgetItem(group.title)
                    item.setData(Qt.UserRole, group.id)
                    self.target_list.addItem(item)

    def start_forwarding(self):
        source_group_id = self.source_selector.currentData()
        if source_group_id is None:
            QMessageBox.warning(self, "Error", "Please select a valid source group.")
            return

        selected_items = self.target_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select at least one target group.")
            return
        for item in selected_items:
            group_id = item.data(Qt.UserRole)
            group = await self.client.get_entity(group_id)
            topics = await self.client.get_participants(group)
            target_groups_with_topics.append((group, topics))
            topics = asyncio.run(self.client.get_participants(group))
            target_groups_with_topics.append((group, topics))

        selected_users = []  # Add logic to select specific users if needed
        delay, ok = QInputDialog.getInt(self, "Set Delay", "Enter delay in seconds between messages:", 0, 0, 60)
        if not ok:
            return

        filters = {
            "keywords": ["important", "urgent"],  # Example keywords
            "user_ids": [123456789, 987654321]  # Example user IDs
        }

        try:
            asyncio.run(forward_message(self.client, source_group_id, target_groups_with_topics, selected_users, delay, self.queue, self.rate_limits, filters, self.forwarding_history, self.forwarding_statistics))
            self.log_message("Forwarding started successfully.")
        except Exception as e:
            logging.error(f"Error starting forwarding: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start forwarding messages: {e}")

    def schedule_message(self):
        user_id, ok = QInputDialog.getInt(self, "Schedule Message", "Enter user ID:")
        if not ok:
            return
        message, ok = QInputDialog.getText(self, "Schedule Message", "Enter your message:")
        if not ok or not message:
            return
        send_time, ok = QInputDialog.getText(self, "Schedule Message", "Enter send time (YYYY-MM-DD HH:MM:SS):")
        if not ok or not send_time:
            return
        try:
            send_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S")
            await schedule_message(self.client, user_id, message, send_time)
            self.log_message(f"Message scheduled for user {user_id} at {send_time}")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid date/time format. Please use YYYY-MM-DD HH:MM:SS.")

    def add_user(self):
        user_id, ok = QInputDialog.getInt(self, "Add User", "Enter user ID:")
        if ok:
            self.user_management.add_user(user_id)
            self.log_message(f"User {user_id} added.")

    def remove_user(self):
        user_id, ok = QInputDialog.getInt(self, "Remove User", "Enter user ID:")
        if ok:
            self.user_management.remove_user(user_id)
            self.log_message(f"User {user_id} removed.")

    def view_forwarding_history(self):
        history = self.forwarding_history.get_history()
        history_str = "\n".join([f"{entry['timestamp']}: Message {entry['message_id']} from {entry['source_group']} to {entry['target_group']}" for entry in history])
        QMessageBox.information(self, "Forwarding History", history_str)

    def view_forwarding_statistics(self):
        stats = self.forwarding_statistics.get_statistics()
        stats_str = "\n".join([f"Group {group_id}: {count} messages forwarded" for group_id, count in stats.items()])
        QMessageBox.information(self, "Forwarding Statistics", stats_str)

    def send_message(self):
        message = "Hello, world!"
        asyncio.run(self.send_message_async(message))

    async def send_message_async(self, message):
        await self.client.send_message(await self.client.get_me().id, message)

    def send_premium_message(self):
        message, ok = QInputDialog.getText(self, "Send Premium Message", "Enter your message:")
        if ok and message:
            async def send_message():
                try:
                    await send_premium_message(self.client, message)
                    QMessageBox.information(self, "Success", "Message sent to premium users.")
                except Exception as e:
                    logging.error(f"Error sending premium message: {e}")
                    QMessageBox.critical(self, "Error", "Failed to send message to premium users.")
            asyncio.create_task(send_message())

    def enable_message_translation(self):
        target_language, ok = QInputDialog.getText(self, "Enable Message Translation", "Enter target language code (e.g., 'en' for English):")
        if ok and target_language:
            async def translation_handler(event):
                translated_message = await translate_message(event.message.message, target_language)
                await self.client.send_message(event.sender_id, translated_message)
            self.client.add_event_handler(translation_handler, events.NewMessage)
            self.log_message("Message translation enabled.")

    def enable_media_forwarding(self):
        target_groups, ok = QInputDialog.getText(self, "Enable Media Forwarding", "Enter target group IDs (comma-separated):")
        if ok and target_groups:
            target_group_ids = [int(group_id.strip()) for group_id in target_groups.split(",")]
            async def media_forwarding_handler(event):
                if event.message.media:
                    await forward_media(self.client, event, target_group_ids)
            self.client.add_event_handler(media_forwarding_handler, events.NewMessage)
            self.log_message("Media forwarding enabled.")

    def schedule_broadcast(self):
        message, ok = QInputDialog.getText(self, "Schedule Broadcast", "Enter broadcast message:")
        if not ok or not message:
            return
        target_groups, ok = QInputDialog.getText(self, "Schedule Broadcast", "Enter target group IDs (comma-separated):")
        if not ok or not target_groups:
            return
        send_time, ok = QInputDialog.getText(self, "Schedule Broadcast", "Enter send time (YYYY-MM-DD HH:MM:SS):")
        if not ok or not send_time:
            return
        try:
            await schedule_broadcast(self.client, message, target_group_ids, send_time)
            send_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S")
            asyncio.run(schedule_broadcast(self.client, message, target_group_ids, send_time))
            self.log_message(f"Broadcast scheduled for {send_time}")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid date/time format. Please use YYYY-MM-DD HH:MM:SS.")



    async def manage_custom_commands(self):
        command, ok = QInputDialog.getText(self, "Manage Custom Commands", "Enter custom command:")
        if not ok or not command:
            return
        response, ok = QInputDialog.getText(self, "Manage Custom Commands", "Enter response for the command:")
        if not ok or not response:
            return
        await manage_custom_commands(self.client, command, response)
        self.log_message(f"Custom command '{command}' managed.")

    def enable_spam_detection(self):
        async def spam_detection_handler(event):
            if await detect_spam(event.message.message):
                await event.message.delete()
                logging.info(f"Spam message from user {event.sender_id} deleted.")
        self.client.add_event_handler(spam_detection_handler, events.NewMessage)
        self.log_message("Spam detection enabled.")

    

class LoginRunnable(QRunnable):
    success = pyqtSignal(TelegramClient)
    error = pyqtSignal(str)

    def __init__(self, phone, code):
        super().__init__()
        self.phone = phone
        self.code = code

    def run(self):
        asyncio.run(self.async_run())

    async def async_run(self):
        try:
            login_worker = LoginWorker(self.phone, self.code)
            await login_worker.async_run()
            self.success.emit(login_worker.client)
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            self.error.emit(str(e))

class LoginWorker(QObject):
    success = pyqtSignal(TelegramClient)
    error = pyqtSignal(str)

    def __init__(self, phone, code):
        super().__init__()
        self.phone = phone
        self.code = code
        try:
            self.client = TelegramClient(StringSession(), API_ID, API_HASH)
        except Exception as e:
            logging.error(f"Error initializing TelegramClient: {e}")
            self.client = None

    async def async_run(self):
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(self.phone)
                if self.code.strip():
                    await self.client.sign_in(self.phone, self.code)
            self.save_session()
            self.success.emit(self.client)
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            self.error.emit(str(e))
        finally:
            await self.client.disconnect()

    def save_session(self):
        session_data = {"session": self.client.session.save()}
        try:
            with open("session.json", "w") as f:
                json.dump(session_data, f)
        except IOError as e:
            logging.error(f"Error saving session to file: {e}")

class RefreshWorker(QRunnable):
    groups_with_topics = pyqtSignal(list)
class RefreshWorker(QRunnable):
    groups_with_topics = pyqtSignal(list)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        asyncio.run(self.refresh_groups())

    async def refresh_groups(self):
        try:
            groups = await get_user_groups_with_topics(self.client)
            self.groups_with_topics.emit(groups)
        except Exception as e:
            logging.error(f"Error occurred: {e}")
    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    window = MainWindow(client, 50)
    window.show()
    sys.exit(app.exec())
```