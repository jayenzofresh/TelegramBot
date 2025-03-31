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
import PySimpleGUI as sg
from config import API_ID, API_HASH
from datetime import datetime, timedelta
import joblib

# Load pre-trained spam detection model and vectorizer
try:
    spam_model = joblib.load('spam_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')
except Exception as e:
    logging.error(f"Error loading spam detection model or vectorizer: {e}")
    spam_model = None
    vectorizer = None


# Helper Functions
async def get_user_groups_with_topics(client):
    """
    Retrieves a list of groups and channels with topics that the user is a part of.
    """
    groups_with_topics = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group_topics = []  # Replace with logic to retrieve group topics
                groups_with_topics.append((dialog, group_topics))
            elif dialog.is_channel and dialog.megagroup:
                channel_topics = []  # Replace with logic to retrieve channel topics
                groups_with_topics.append((dialog, channel_topics))
    except Exception as e:
        logging.error(f"Error retrieving groups: {e}")
    return groups_with_topics


async def auto_reply(client, event, reply_message):
    """
    Automatically replies to messages with a predefined message.
    """
    try:
        await client.send_message(event.sender_id, reply_message)
        logging.info(f"Auto-reply sent to user {event.sender_id}")
    except Exception as e:
        logging.error(f"Error sending auto-reply to user {event.sender_id}: {e}")


async def detect_spam(message):
    """
    Detects spam messages using a Naive Bayes classifier.
    """
    if not spam_model or not vectorizer:
        logging.error("Spam detection model or vectorizer is not loaded.")
        return False
    try:
        message_vector = vectorizer.transform([message])
        is_spam = spam_model.predict(message_vector)[0]
        return is_spam
    except Exception as e:
        logging.error(f"Error during spam detection: {e}")
        return False


async def schedule_message(client, user_id, message, send_time):
    """
    Sends a message to a user at a scheduled time.
    """
    delay = (send_time - datetime.now()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await client.send_message(user_id, message)


class ForwardingHistory:
    def __init__(self):
        self.history = []

    def add_entry(self, source_group, target_group, message_id, timestamp):
        self.history.append({
            "source_group": source_group,
            "target_group": target_group,
            "message_id": message_id,
            "timestamp": timestamp,
        })

    def get_history(self):
        return self.history


class ForwardingStatistics:
    def __init__(self):
        self.statistics = defaultdict(int)

    def increment(self, group_id):
        self.statistics[group_id] += 1

    def get_statistics(self):
        return self.statistics


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


class TelegramBotGUI:
    def __init__(self):
        self.client = None
        self.queue = Queue()
        self.rate_limits = defaultdict(int)
        self.active_handlers = set()
        self.groups_with_topics = []
        self.user_management = UserManagement()
        self.forwarding_history = ForwardingHistory()
        self.forwarding_statistics = ForwardingStatistics()

    def start(self):
        layout = [
            [sg.Text("Phone Number:"), sg.Input(key="-PHONE-", size=(30, 1))],
            [sg.Button("Send Verification Code", key="-SEND_CODE-")],
            [sg.Text("Verification Code:"), sg.Input(key="-CODE-", size=(30, 1))],
            [sg.Button("Login", key="-LOGIN-")],
            [sg.Text("Source Group:"), sg.Combo([], key="-SOURCE_GROUP-", size=(30, 1))],
            [sg.Button("Refresh Groups", key="-REFRESH_GROUPS-")],
            [sg.Button("Schedule Message", key="-SCHEDULE_MESSAGE-")],
            [sg.Button("View Forwarding History", key="-VIEW_HISTORY-")],
            [sg.Button("Forward Messages to Groups", key="-FORWARD_MESSAGES-")],
            [sg.Multiline(size=(60, 10), key="-LOG-", disabled=True)],
        ]

        self.window = sg.Window("Telegram Bot", layout, finalize=True)

        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            elif event == "-SEND_CODE-":
                asyncio.create_task(self.send_verification_code(values["-PHONE-"]))
            elif event == "-LOGIN-":
                asyncio.create_task(self.login(values["-PHONE-"], values["-CODE-"]))
            elif event == "-REFRESH_GROUPS-":
                asyncio.create_task(self.refresh_groups())
            elif event == "-SCHEDULE_MESSAGE-":
                asyncio.create_task(self.schedule_message())
            elif event == "-VIEW_HISTORY-":
                self.view_forwarding_history()
            elif event == "-VIEW_STATS-":
                self.view_forwarding_statistics()
            elif event == "-FORWARD_MESSAGES-":
                asyncio.create_task(self.forward_messages_to_groups())

        self.window.close()

    async def send_verification_code(self, phone):
        if not phone or not phone.startswith("+"):
            self.log_message("Please enter a valid phone number starting with +.")
            return
        try:
            self.client = TelegramClient(StringSession(), API_ID, API_HASH)
            await self.client.connect()
            await self.client.send_code_request(phone)
            self.log_message("Verification code sent.")
        except Exception as e:
            self.log_message(f"Error sending verification code: {e}")

    async def login(self, phone, code):
        if not code.strip():
            self.log_message("Please enter a valid verification code.")
            return
        try:
            await self.client.sign_in(phone, code)
            self.log_message("Login successful.")
        except Exception as e:
            self.log_message(f"Error during login: {e}")

    async def refresh_groups(self):
        try:
            self.groups_with_topics = await get_user_groups_with_topics(self.client)
            self.update_groups()
            self.log_message("Groups refreshed successfully.")
        except Exception as e:
            self.log_message(f"Error refreshing groups: {e}")

    def update_groups(self):
        self.window["-SOURCE_GROUP-"].update([group.title for group, _ in self.groups_with_topics])

    async def schedule_message(self):
        user_id = sg.popup_get_text("Enter user ID:")
        message = sg.popup_get_text("Enter your message:")
        send_time = sg.popup_get_text("Enter send time (YYYY-MM-DD HH:MM:SS):")
        if not user_id or not message or not send_time:
            self.log_message("Invalid input for scheduling message.")
            return
        try:
            send_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.log_message("Invalid date/time format. Please use YYYY-MM-DD HH:MM:SS.")
            return

        try:
            await schedule_message(self.client, int(user_id), message, send_time)
            self.log_message(f"Message scheduled for user {user_id} at {send_time}")
        except Exception as e:
            self.log_message(f"Error scheduling message: {e}")

    def view_forwarding_history(self):
        history = self.forwarding_history.get_history()
        history_str = "\n".join(
            [f"{entry['timestamp']}: Message {entry['message_id']} from {entry['source_group']} to {entry['target_group']}" for entry in history]
        )
        sg.popup("Forwarding History", history_str)

    def view_forwarding_statistics(self):
        stats = self.forwarding_statistics.get_statistics()
        if not stats:
            sg.popup("Forwarding Statistics", "No statistics available.")
            return
        stats_str = "\n".join([f"Group {group_id}: {count} messages forwarded" for group_id, count in stats.items()])
        sg.popup("Forwarding Statistics", stats_str)

    async def forward_messages_to_groups(self):
        """
        Configures forwarding messages from a source group to multiple target groups.
        """
        # Refresh and fetch the list of groups the user is a member of
        await self.refresh_groups()

        # Display all groups in a Listbox for source group selection
        source_group_titles = [group.title for group, _ in self.groups_with_topics]
        source_group_layout = [
            [sg.Text("Select the source group:")],
            [sg.Listbox(values=source_group_titles, size=(50, 10), key="-SOURCE_GROUP-", select_mode="single")],
            [sg.Button("Confirm Source Group", key="-CONFIRM_SOURCE_GROUP-"), sg.Button("Cancel", key="-CANCEL-")]
        ]
        source_group_window = sg.Window("Select Source Group", source_group_layout)

        source_group = None
        while True:
            event, values = source_group_window.read()
            if event in (sg.WINDOW_CLOSED, "-CANCEL-"):
                source_group_window.close()
                return
            elif event == "-CONFIRM_SOURCE_GROUP-":
                selected = values["-SOURCE_GROUP-"]
                if selected:
                    source_group = selected[0]
                    source_group_window.close()
                    break
                else:
                    sg.popup("Please select a source group.")

        # Display all groups in a Listbox for target group selection
        target_group_layout = [
            [sg.Text("Select the target groups (hold Ctrl to select multiple):")],
            [sg.Listbox(values=source_group_titles, size=(50, 10), key="-TARGET_GROUPS-", select_mode="multiple")],
            [sg.Button("Confirm Target Groups", key="-CONFIRM_TARGET_GROUPS-"), sg.Button("Cancel", key="-CANCEL-")]
        ]
        target_group_window = sg.Window("Select Target Groups", target_group_layout)

        target_groups = None
        while True:
            event, values = target_group_window.read()
            if event in (sg.WINDOW_CLOSED, "-CANCEL-"):
                target_group_window.close()
                return
            elif event == "-CONFIRM_TARGET_GROUPS-":
                selected = values["-TARGET_GROUPS-"]
                if selected:
                    target_groups = selected
                    target_group_window.close()
                    break
                else:
                    sg.popup("Please select at least one target group.")

        try:
            # Map group titles to their corresponding group objects
            source_group_obj = next(group for group, _ in self.groups_with_topics if group.title == source_group)
            target_group_objs = [
                group for group, _ in self.groups_with_topics if group.title in target_groups
            ]

            if not target_group_objs:
                self.log_message("No valid target groups selected.")
                return

            # Set up the forwarding handler
            handler_key = f"{source_group_obj.id}_to_{'_'.join([str(tg.id) for tg in target_group_objs])}"
            if handler_key in self.active_handlers:
                self.log_message("Handler for this forwarding configuration is already active.")
                return

            @self.client.on(events.NewMessage(chats=source_group_obj.id))
            async def handler(event):
                for target_group in target_group_objs:
                    try:
                        # Forward the message to each target group
                        await self.client.forward_messages(target_group.id, event.message)
                        self.forwarding_statistics.increment(target_group.id)
                        self.forwarding_history.add_entry(
                            source_group_obj.title, target_group.title, event.message.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        self.log_message(f"Message forwarded from {source_group_obj.title} to {target_group.title}")
                    except Exception as e:
                        self.log_message(f"Error forwarding message to {target_group.title}: {e}")

            self.active_handlers.add(handler_key)

            self.log_message(f"Forwarding messages from {source_group_obj.title} to {[tg.title for tg in target_group_objs]}")
        except Exception as e:
            self.log_message(f"Error setting up forwarding: {e}")

    def log_message(self, message, max_lines=100):
        current_log = self.window["-LOG-"].get()
        log_lines = current_log.splitlines()
        log_lines.append(message)
        if len(log_lines) > max_lines:
            log_lines = log_lines[-max_lines:]
        self.window["-LOG-"].update("\n".join(log_lines))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gui = TelegramBotGUI()
    gui.start()
