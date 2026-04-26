"""GUI components for StringShare application."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional


class StringShareWindow(tk.Tk):
    """Main window for displaying and copying strings."""

    def __init__(self, text: str, on_close: Optional[Callable[[], None]] = None):
        """
        Initialize the StringShare window.

        Args:
            text: The text to display and copy
            on_close: Optional callback when window closes
        """
        super().__init__()
        self.title("StringShare")
        self.geometry("300x200")
        self._text_content = text
        self._on_close_callback = on_close
        self._copied = False

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        self.label = tk.Label(self, text=self._text_content, wraplength=250)
        self.label.pack(pady=20)

        self.button = tk.Button(self, text="Copy", command=self._copy_to_clipboard)
        self.button.pack(pady=10)

    def _copy_to_clipboard(self) -> None:
        """Copy the displayed text to clipboard and show feedback."""
        self.clipboard_clear()
        self.clipboard_append(self._text_content)
        self.update()

        self.button.config(text="Copied!")
        self._copied = True
        self.after(1000, self._reset_button)

    def _reset_button(self) -> None:
        """Reset button text after copy feedback."""
        if self._copied:
            self.button.config(text="Copy")
            self._copied = False

    def _on_window_close(self) -> None:
        """Handle window close event."""
        if self._on_close_callback:
            self._on_close_callback()
        self.destroy()


class PeerSelectionWindow(tk.Tk):
    """Window for selecting peers to send strings to."""

    def __init__(
        self,
        peers: Dict[str, str],
        on_send: Optional[Callable[[List[str]], None]] = None,
    ):
        """
        Initialize the peer selection window.

        Args:
            peers: Dictionary mapping peer names to IP addresses
            on_send: Callback when send is clicked with list of selected peer IPs
        """
        super().__init__()
        self.title("StringShare - Select Peers")
        self.geometry("350x400+100+100")
        self._peers = peers
        self._on_send_callback = on_send

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Title label
        title_label = tk.Label(
            self, text="Select peers to send to:", font=("Arial", 10, "bold")
        )
        title_label.pack(pady=10)

        # Frame for listbox and scrollbar
        list_frame = tk.Frame(self)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=scrollbar.set,
            font=("Arial", 9),
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Populate listbox with peers
        for peer_name, ip in self._peers.items():
            self.listbox.insert(tk.END, f"{peer_name} ({ip})")

        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10, fill=tk.X, padx=10)

        send_button = tk.Button(button_frame, text="Send", command=self._on_send)
        send_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def _on_send(self) -> None:
        """Handle send button click."""
        selected_indices = self.listbox.curselection()
        if selected_indices:
            selected_ips = [list(self._peers.values())[i] for i in selected_indices]
            if self._on_send_callback:
                self._on_send_callback(selected_ips)
        self.destroy()

