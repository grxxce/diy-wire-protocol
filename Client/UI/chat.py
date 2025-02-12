import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
class ChatUI:
    def __init__(self, root, callbacks, username, all_users):
        self.root = root
        self.username = username
        self.all_users = all_users

        self.chat_histories = {}  # Format: {username: [{'sender': str, 'message': str, 'timestamp': str}]}
        self.new_messages = {}
        self.selected_recipient = None
        
        # Store callbacks
        self.send_message_callback = callbacks.get('send_message')
        self.get_inbox_callback = callbacks.get('get_inbox')
        self.save_settings_callback = callbacks.get('save_settings')
        self.delete_account_callback = callbacks.get('delete_account')
        
        # Configure the window
        self.root.title(f"Chat - {username}")
        self.root.geometry("1000x700")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        self.style.configure('TEntry', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 11))
        
        self.create_widgets()
        self._refresh_inbox()  # Load initial inbox

        self.update_search_results(
            [user for user in all_users if user != username]
        )

        self.delete_message_callback = callbacks.get('delete_message')
        
        # Create context menu
        self.message_menu = tk.Menu(root, tearoff=0)
        self.message_menu.add_command(label="Delete Message", command=self._delete_selected_message)
        
        # Bind right-click to messages in inbox
        self.chat_display.bind("<Button-3>", self._show_message_menu)
        self.chat_display.tag_bind("message", "<Button-3>", self._show_message_menu)
        
        # Track messages in chat display
        self.displayed_messages = []
    
    def _show_message_menu(self, event):
        """Show context menu for chat messages."""
        try:
            # Get clicked position
            clicked_pos = self.chat_display.index(f"@{event.x},{event.y}")
            
            # Find which message was clicked
            clicked_message = None
            for msg in self.displayed_messages:
                if (self.chat_display.compare(msg['start'], '<=', clicked_pos) and
                    self.chat_display.compare(msg['end'], '>=', clicked_pos)):
                    clicked_message = msg
                    break
            
            if clicked_message:
                # Store currently selected message
                self.selected_message = clicked_message
                # Show menu
                self.message_menu.post(event.x_root, event.y_root)
                
        except Exception as e:
            print(f"Error showing message menu: {e}")

    def create_widgets(self):
        # Main container with two columns
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Column (Search, Inbox, Settings)
        self.left_column = ttk.Frame(self.main_frame, width=250)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.left_column.pack_propagate(False)  # Maintain width
        
        # Create search panel (top of left column)
        self.create_search_panel()
        
        # Create inbox panel (middle of left column)
        self.create_inbox_panel()
        
        # Create settings panel (bottom of left column)
        self.create_settings_panel()
        
        # Right Column (Chat Area)
        self.create_chat_panel()
        
    def create_search_panel(self):
        """Create the search panel at the top of left column"""
        self.search_frame = ttk.LabelFrame(self.left_column, text="Search Users", padding="5")
        self.search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Search input
        self.search_var = tk.StringVar()
        # Fix: Change 'w' to 'write' and use trace_add instead of trace
        self.search_var.trace_add('write', self._on_search_change)
        
        self.search_input = ttk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            font=('Arial', 11)
        )
        self.search_input.pack(fill=tk.X, pady=(0, 5))
        
        # Search results
        self.search_results = tk.Listbox(
            self.search_frame,
            height=6,
            font=('Arial', 11),
            selectmode=tk.SINGLE
        )
        self.search_results.pack(fill=tk.X)
        self.search_results.bind('<<ListboxSelect>>', self._on_user_select)
    
    def create_inbox_panel(self):
        """Create the inbox panel below search panel"""
        self.inbox_frame = ttk.LabelFrame(self.left_column, text="Inbox", padding="5")
        self.inbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Inbox list
        self.inbox_list = tk.Listbox(
            self.inbox_frame,
            selectmode=tk.SINGLE,
            font=('Arial', 11)
        )
        self.inbox_list.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.inbox_list.bind('<<ListboxSelect>>', self._on_inbox_select)
        
        # Refresh button
        ttk.Button(
            self.inbox_frame,
            text="Refresh Inbox",
            command=self._refresh_inbox
        ).pack(fill=tk.X)
    
    def create_chat_panel(self):
        """Create the chat panel (right side)"""
        self.chat_frame = ttk.LabelFrame(self.main_frame, text="Select a conversation", padding="5")
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=('Arial', 11),
            state='disabled'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure tags for message styling
        self.chat_display.tag_configure(
            'sent',
            justify='right',
            foreground='#0084ff'
        )
        self.chat_display.tag_configure(
            'received',
            justify='left',
            foreground='#000000'
        )

        # Message input area
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.pack(fill=tk.X)
        
        self.message_input = ttk.Entry(
            self.input_frame,
            font=('Arial', 11)
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_input.bind('<Return>', lambda e: self._handle_send())
        
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self._handle_send
        )
        self.send_button.pack(side=tk.RIGHT)

    def _start_chat_with_user(self, username):
        """Start or switch to chat with selected user"""
        self.selected_recipient = username
        self.chat_frame.configure(text=f"Chat with {username}")
        
        # Initialize chat history for new users
        if username not in self.chat_histories:
            self.chat_histories[username] = []
            self.new_messages[username] = []
        # Display chat history
        self._display_chat_history(username)
        self._refresh_inbox()
    
    def _display_chat_history(self, username):
        """Display the chat history for a specific user"""
        self.chat_display.configure(state='normal')
        self.chat_display.delete(1.0, tk.END)
        
        # Display each message in the history
        for msg in self.chat_histories[username]:
            if msg['sender'] == self.username:
                self._format_sent_message(msg['message'], msg['timestamp'])
            else:
                self._format_received_message(msg['sender'], msg['message'], msg['timestamp'])
        
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)
    
    def display_message(self, from_user, message):
        """Updates chat history (but does not display messages)"""
        print("display_message: ", from_user, message)
        timestamp = datetime.now().strftime('%H:%M')
        
        # Store message in chat history
        if from_user not in self.chat_histories:
            print("from_user not in chat_histories")
            self.chat_histories[from_user] = []
        
        if from_user not in self.new_messages:
            self.new_messages[from_user] = []

        self.chat_histories[from_user].append({
            'sender': from_user,
            'message': message,
            'timestamp': timestamp
        })
        self.new_messages[from_user].append({
            'sender': from_user,
            'message': message,
            'timestamp': timestamp
        })

        print("chat_histories", self.chat_histories)

        self.display_stored_messages()
        self._refresh_inbox()

    def display_sent_message(self, message):
        """Display a sent message in the chat area."""
        self.chat_display.configure(state='normal')
        
        # Add timestamp
        timestamp = datetime.now().strftime('%H:%M')
        
        # Format and insert the message
        self.chat_display.insert(tk.END, f"{timestamp} You: ", 'sent')
        self.chat_display.insert(tk.END, f"{message}\n", 'sent')
        
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)  # Auto-scroll to bottom

    def _handle_send(self):
        """Handle sending a message"""
        if not hasattr(self, 'selected_recipient') or not self.selected_recipient:
            messagebox.showwarning("Warning", "Please select a user to chat with first.")
            return
            
        message = self.message_input.get().strip()
        if message:
            # Send message through callback
            self.send_message_callback(self.selected_recipient, message)
            
            # Store and display sent message
            timestamp = datetime.now().strftime('%H:%M')
            
            # Add to chat history
            if self.selected_recipient not in self.chat_histories:
                self.chat_histories[self.selected_recipient] = []
                
            self.chat_histories[self.selected_recipient].append({
                'sender': self.username,
                'message': message,
                'timestamp': timestamp
            })
            
            # Display sent message
            self.chat_display.configure(state='normal')
            self._format_sent_message(message, timestamp)
            self.chat_display.configure(state='disabled')
            self.chat_display.see(tk.END)
            
            # Clear input
            self.message_input.delete(0, tk.END)
    
    def _format_received_message(self, sender, message, timestamp):
        """Format and insert received message with tags."""
        start_pos = self.chat_display.index("end-1c")
        
        self.chat_display.insert(tk.END, f"{sender} ({timestamp}): ", "sender")
        self.chat_display.insert(tk.END, f"{message}\n", "message")
        
        end_pos = self.chat_display.index("end-1c")
        
        # Store message data with its position
        self.displayed_messages.append({
            'start': start_pos,
            'end': end_pos,
            'sender': sender,
            'message': message,
            'timestamp': timestamp
        })

    def _format_sent_message(self, message, timestamp):
        """Format and insert sent message with tags."""
        start_pos = self.chat_display.index("end-1c")
        
        self.chat_display.insert(tk.END, f"You ({timestamp}): ", "sender")
        self.chat_display.insert(tk.END, f"{message}\n", "message")
        
        end_pos = self.chat_display.index("end-1c")
        
        # Store message data with its position
        self.displayed_messages.append({
            'start': start_pos,
            'end': end_pos,
            'sender': self.username,
            'message': message,
            'timestamp': timestamp
        })


    
    def _on_search_change(self, *args):
        """Handle search input changes"""
        search_text = self.search_var.get().strip().lower()  # Convert to lowercase for case-insensitive search
        
        if search_text:
            # Filter users whose names contain the search text
            results = [
                user for user in self.all_users 
                if search_text in user.lower() and user != self.username
            ]
        else:
            # Show all users except current user when search is empty
            results = [user for user in self.all_users if user != self.username]
            
        self.update_search_results(results)
    
    def _on_user_select(self, event):
        """Handle user selection from search results"""
        print("SELECTED USER DETECTED")
        selection = self.search_results.curselection()
        if selection:
            self.selected_recipient = self.search_results.get(selection[0])
            self.chat_display.configure(state='normal')
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.configure(state='disabled')
            self.chat_frame.configure(text=f"Chat with {self.selected_recipient}")
            self.display_stored_messages()
    
    def display_stored_messages(self):
        """Display all stored messages for the selected recipient."""
        print(f"Displaying stored messages for recipient: {self.selected_recipient}")
        
        if not self.selected_recipient:
            print("No recipient selected, cannot display messages")
            return
            
        if self.selected_recipient not in self.chat_histories:
            print(f"No chat history for {self.selected_recipient}")
            return
            
        # Clear current display
        self.chat_display.configure(state='normal')
        self.chat_display.delete(1.0, tk.END)
        
        # Display all messages in chronological order
        for msg in self.chat_histories[self.selected_recipient]:
            sender = msg['sender']
            message = msg['message']
            timestamp = msg['timestamp']
            
            if sender == self.username:
                self._format_sent_message(message, timestamp)
            else:
                self._format_received_message(sender, message, timestamp)
        
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)
        
        print(f"Finished displaying {len(self.chat_histories[self.selected_recipient])} messages")

    
    def _on_inbox_select(self, event):
        """Handle inbox conversation selection"""
        # selection = self.inbox_list.curselection()
        # print("selection:", selection)
        # if not selection:
        #     return
            
        # # Get selected message data
        # selected_index = selection[0]
        # selected_message = self.new_messages[selected_index]
        # sender = selected_message['sender']
        # message = selected_message['message']
        # timestamp = selected_message['timestamp']
        
        # print(f"Selected message from {sender}: {message}")
        
        # # Remove this specific message from new_messages
        # if sender in self.new_messages:
        #     # Find and remove the specific message
        #     self.new_messages[sender] = [
        #         msg for msg in self.new_messages[sender]
        #         if not (msg['message'] == message and 
        #                msg['timestamp'] == timestamp)
        #     ]
            
        #     # If no more messages from this sender, remove the sender
        #     if not self.new_messages[sender]:
        #         del self.new_messages[sender]
        
        # # Add message to chat history
        # if sender not in self.chat_histories:
        #     self.chat_histories[sender] = []
        # self.chat_histories[sender].append({
        #     'sender': sender,
        #     'message': message,
        #     'timestamp': timestamp
        # })
        
        # # Set as selected recipient and display chat
        # self.selected_recipient = sender
        # self.chat_frame.configure(text=f"Chat with {sender}")
        # self.display_stored_messages()
        
        # # Refresh inbox to update display
        # self._refresh_inbox()
    
    def _refresh_inbox(self):
        """Refresh inbox conversations"""
        print("new MESSAGES TO POP:", self.new_messages)
        
        self.inbox_list.delete(0, tk.END)
        
        # Get all messages sorted by timestamp
        all_messages = []
        for sender, messages in self.new_messages.items():
            for msg in messages:
                all_messages.append({
                    'sender': sender,
                    'message': msg['message'],
                    'timestamp': msg['timestamp'],
                    'preview': f"{sender}: {msg['message'][:30]}..."  # Message preview
                })
        
        # Sort by timestamp (newest first)
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take most recent 50 messages
        recent_messages = all_messages[:50]
        
        # Update inbox display
        for msg in recent_messages:
            self.inbox_list.insert(tk.END, msg['preview'])
            # Store full message data in the listbox
            self.inbox_list.message_data = recent_messages
            
        print(f"Updated inbox with {len(recent_messages)} messages")
    
    def update_search_results(self, users):
        """Update the search results listbox"""
        self.search_results.delete(0, tk.END)
        for user in users:
            self.search_results.insert(tk.END, user)


    def create_settings_panel(self):
        """Create the settings panel at the bottom of left column"""
        self.settings_frame = ttk.LabelFrame(self.left_column, text="Settings", padding="5")
        self.settings_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Message history limit setting
        history_frame = ttk.Frame(self.settings_frame)
        history_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(
            history_frame,
            text="Messages to show:",
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
        
        self.history_var = tk.StringVar(value="50")  # Default value
        history_spinbox = ttk.Spinbox(
            history_frame,
            from_=10,
            to=200,
            width=5,
            textvariable=self.history_var,
            command=self._on_history_change
        )
        history_spinbox.pack(side=tk.RIGHT)
        
        # Save Settings Button
        ttk.Button(
            self.settings_frame,
            text="Save Settings",
            command=self._save_settings
        ).pack(fill=tk.X, pady=(0, 5))
        
        # Separator
        ttk.Separator(self.settings_frame).pack(fill=tk.X, pady=5)
        
        # Danger Zone
        danger_frame = ttk.LabelFrame(self.settings_frame, text="Danger Zone", padding="5")
        danger_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Delete Account Button
        delete_button = ttk.Button(
            danger_frame,
            text="Delete Account",
            style='Danger.TButton',
            command=self._confirm_delete_account
        )
        delete_button.pack(fill=tk.X)
        
        # Configure danger button style
        self.style.configure('Danger.TButton', 
                           foreground='red',
                           font=('Arial', 11, 'bold'))
    
    def _on_history_change(self):
        """Handle message history limit change"""
        try:
            value = int(self.history_var.get())
            if value < 10:
                self.history_var.set("10")
            elif value > 200:
                self.history_var.set("200")
        except ValueError:
            self.history_var.set("50")  # Reset to default if invalid
    
    def _save_settings(self):
        """Save user settings"""
        try:
            history_limit = int(self.history_var.get())
            # Call callback to save settings
            if hasattr(self, 'save_settings_callback'):
                self.save_settings_callback({
                    'message_history_limit': history_limit
                })
            messagebox.showinfo("Success", "Settings saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Invalid settings values")
    
    def _delete_selected_message(self):
        """Delete the selected message."""
        if not hasattr(self, 'selected_message'):
            return
            
        msg = self.selected_message
        
        # Confirm deletion
        if messagebox.askyesno("Delete Message", 
                             f"Delete this message from {msg['sender']}?"):
            
            # Call delete callback
            if self.delete_message_callback:
                delete_request = {
                    'sender': msg['sender'],
                    'message': msg['message'],
                    'timestamp': msg['timestamp']
                }
                self.delete_message_callback(delete_request)
            
            # Remove from chat history
            if self.selected_recipient in self.chat_histories:
                self.chat_histories[self.selected_recipient] = [
                    m for m in self.chat_histories[self.selected_recipient]
                    if not (m['message'] == msg['message'] and 
                           m['timestamp'] == msg['timestamp'])
                ]
            
            # Refresh chat display
            self.display_stored_messages()

    def _confirm_delete_account(self):
        """Show confirmation dialog before deleting account"""
        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete your account?\n"
                             "This action cannot be undone!",
                             icon='warning'):
            if hasattr(self, 'delete_account_callback'):
                self.delete_account_callback()