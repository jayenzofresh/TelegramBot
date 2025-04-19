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

class ForwardingHistory:
    def __init__(self):
        self.history = []
        self.deleted_messages = []

    def add_entry(self, source_group: str, target_group: str, message_id: int, timestamp: str) -> None:
        self.history.append({
            "source_group": source_group,
            "target_group": target_group,
            "message_id": message_id,
            "timestamp": timestamp,
        })

    def add_deleted_message(self, group: str, message_id: int, timestamp: str) -> None:
        self.deleted_messages.append({
            "group": group,
            "message_id": message_id,
            "timestamp": timestamp,
        })

    def get_history(self) -> list:
        return self.history

    def get_deleted_messages(self) -> list:
        return self.deleted_messages

class ForwardingStatistics:
    def __init__(self):
        self.statistics = defaultdict(int)
        self.deletion_statistics = defaultdict(int)

    def increment(self, group_id: int) -> None:
        self.statistics[group_id] += 1

    def increment_deletion(self, group_id: int) -> None:
        self.deletion_statistics[group_id] += 1

    def get_statistics(self) -> dict:
        return {
            "forwarded": self.statistics,
            "deleted": self.deletion_statistics
        }

class UserManagement:
    def __init__(self):
        self.users = set()

    def add_user(self, user_id: int) -> None:
        self.users.add(user_id)
        logging.info(f"User {user_id} added to the list")

    def remove_user(self, user_id: int) -> None:
        self.users.discard(user_id)
        logging.info(f"User {user_id} removed from the list")

    def get_users(self) -> list:
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

    def start(self) -> None:
        layout = [
            [sg.Text("Phone Number:"), sg.Input(key="-PHONE-", size=(30, 1))],
            [sg.Button("Send Verification Code", key="-SEND_CODE-")],
            [sg.Text("Verification Code:"), sg.Input(key="-CODE-", size=(30, 1))],
            [sg.Button("Login", key="-LOGIN-")],
            [sg.Text("Source Group:"), sg.Combo([], key="-SOURCE_GROUP-", size=(30, 1))],
            [sg.Button("Refresh Groups", key="-REFRESH_GROUPS-")],
            [sg.Button("Forward Messages to Groups", key="-FORWARD_MESSAGES-")],
            [sg.Button("Delete Forwarded Messages", key="-DELETE_FORWARDED-")],
            [sg.Button("View Forwarding History", key="-VIEW_HISTORY-")],
            [sg.Button("View Deletion History", key="-VIEW_DELETIONS-")],
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
            elif event == "-FORWARD_MESSAGES-":
                asyncio.create_task(self.forward_messages_to_groups())
            elif event == "-DELETE_FORWARDED-":
                asyncio.create_task(self.delete_forwarded_messages())
            elif event == "-VIEW_HISTORY-":
                self.view_forwarding_history()
            elif event == "-VIEW_DELETIONS-":
                self.view_deletion_history()

        self.window.close()

    async def send_verification_code(self, phone: str) -> None:
        if not phone or not phone.startswith("+"):
            self.log_message("Please enter a valid phone number starting with +.")
            return
        try:
            self.client = TelegramClient(
                StringSession(),
                API_ID,
                API_HASH,
                device_model="TelegramBot",
                system_version="1.0",
                app_version="1.0"
            )
            await self.client.connect()
            if await self.client.is_user_authorized():
                self.log_message("Already authorized!")
                return
            await self.client.send_code_request(phone)
            self.log_message("Verification code sent.")
        except Exception as e:
            self.log_message(f"Error sending verification code: {e}")

    async def login(self, phone: str, code: str) -> None:
        if not code.strip():
            self.log_message("Please enter a valid verification code.")
            return
        try:
            await self.client.sign_in(phone, code)
            self.log_message("Login successful.")
            await self.refresh_groups()
        except Exception as e:
            self.log_message(f"Error during login: {e}")

    async def refresh_groups(self) -> None:
        try:
            self.groups_with_topics = []
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or (dialog.is_channel and dialog.megagroup):
                    self.groups_with_topics.append((dialog, []))
            self.update_groups()
            self.log_message("Groups refreshed successfully.")
        except Exception as e:
            self.log_message(f"Error refreshing groups: {e}")

    def update_groups(self) -> None:
        self.window["-SOURCE_GROUP-"].update(values=[group.title for group, _ in self.groups_with_topics])

    async def forward_messages_to_groups(self) -> None:
        await self.refresh_groups()

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
            source_group_obj = next(group for group, _ in self.groups_with_topics if group.title == source_group)
            target_group_objs = [group for group, _ in self.groups_with_topics if group.title in target_groups]

            if not target_group_objs:
                self.log_message("No valid target groups selected.")
                return

            handler_key = f"{source_group_obj.id}_to_{'_'.join([str(tg.id) for tg in target_group_objs])}"
            if handler_key in self.active_handlers:
                self.log_message("Handler for this forwarding configuration is already active.")
                return

            @self.client.on(events.NewMessage(chats=source_group_obj.id))
            async def handler(event):
                for target_group in target_group_objs:
                    try:
                        await asyncio.sleep(2)  # Rate limiting
                        await self.client.forward_messages(target_group.id, event.message)
                        self.forwarding_statistics.increment(target_group.id)
                        self.forwarding_history.add_entry(
                            source_group_obj.title,
                            target_group.title,
                            event.message.id,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        self.log_message(f"Message forwarded from {source_group_obj.title} to {target_group.title}")
                    except Exception as e:
                        self.log_message(f"Error forwarding message to {target_group.title}: {e}")

            self.active_handlers.add(handler_key)
            self.log_message(f"Forwarding messages from {source_group_obj.title} to {[tg.title for tg in target_group_objs]}")
        except Exception as e:
            self.log_message(f"Error setting up forwarding: {e}")

    async def delete_forwarded_messages(self) -> None:
        await self.refresh_groups()

        group_titles = [group.title for group, _ in self.groups_with_topics]
        layout = [
            [sg.Text("Select groups to delete forwarded messages from (hold Ctrl for multiple):")],
            [sg.Listbox(values=group_titles, size=(50, 10), key="-GROUPS-", select_mode="multiple")],
            [sg.Button("Confirm", key="-CONFIRM-"), sg.Button("Cancel", key="-CANCEL-")]
        ]

        delete_window = sg.Window("Select Groups", layout)

        try:
            while True:
                event, values = delete_window.read()
                if event in (sg.WINDOW_CLOSED, "-CANCEL-"):
                    break
                elif event == "-CONFIRM-":
                    selected = values["-GROUPS-"]
                    if not selected:
                        sg.popup("Please select at least one group.")
                        continue

                    selected_groups = [
                        group for group, _ in self.groups_with_topics 
                        if group.title in selected
                    ]

                    for group in selected_groups:
                        try:
                            async for message in self.client.iter_messages(group.id):
                                if message.forward is not None:
                                    await message.delete()
                                    self.forwarding_statistics.increment_deletion(group.id)
                                    self.forwarding_history.add_deleted_message(
                                        group.title,
                                        message.id,
                                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    )
                                    self.log_message(f"Deleted forwarded message {message.id} from {group.title}")
                            
                            self.log_message(f"Completed deletion of forwarded messages in {group.title}")
                        except Exception as e:
                            self.log_message(f"Error deleting messages in {group.title}: {e}")
                    break
        finally:
            delete_window.close()

    def view_forwarding_history(self) -> None:
        history = self.forwarding_history.get_history()
        if not history:
            sg.popup("Forwarding History", "No messages have been forwarded yet.")
            return
        history_str = "\n".join(
            [f"{entry['timestamp']}: Message {entry['message_id']} from {entry['source_group']} to {entry['target_group']}"
             for entry in history]
        )
        sg.popup("Forwarding History", history_str, scrollable=True)

    def view_deletion_history(self) -> None:
        deleted = self.forwarding_history.get_deleted_messages()
        if not deleted:
            sg.popup("Deletion History", "No messages have been deleted yet.")
            return
        history_str = "\n".join(
            [f"{entry['timestamp']}: Deleted message {entry['message_id']} from {entry['group']}"
             for entry in deleted]
        )
        sg.popup("Deletion History", history_str, scrollable=True)

    def log_message(self, message: str, max_lines: int = 100) -> None:
        current_log = self.window["-LOG-"].get()
        log_lines = current_log.splitlines()
        log_lines.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}")
        if len(log_lines) > max_lines:
            log_lines = log_lines[-max_lines:]
        self.window["-LOG-"].update("\n".join(log_lines))

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    gui = TelegramBotGUI()
    gui.start()