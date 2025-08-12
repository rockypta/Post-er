import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json

class PostmanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Postman")

        # URL
        ttk.Label(self.root, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(self.root, width=80)
        self.url_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Method
        self.method_var = tk.StringVar(value="GET")
        ttk.Radiobutton(self.root, text="GET", variable=self.method_var, value="GET").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(self.root, text="POST", variable=self.method_var, value="POST").grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # Body for POST
        self.body_label = ttk.Label(self.root, text="Body (JSON):")
        self.body_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.body_text = tk.Text(self.root, height=10, width=80)
        self.body_text.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.body_text.bind("<Tab>", self._on_body_text_tab)
        self.body_text.bind("<Shift-Tab>", self._on_body_text_tab)

        # Send Button
        self.send_button = ttk.Button(self.root, text="Send", command=self.send_request)
        self.send_button.grid(row=3, column=1, pady=10)
        self.send_button.bind("<Return>", lambda event: self.send_request())

        # Response
        ttk.Label(self.root, text="Response:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.response_text = tk.Text(self.root, height=20, width=80)
        self.response_text.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(5, weight=1)
        
        # Set initial focus to the URL entry
        self.url_entry.focus_set()

    def _on_body_text_tab(self, event):
        if event.state & 0x1:  # Check for Shift key (state 0x1)
            self.url_entry.focus_set()
        else:
            self.send_button.focus_set()
        return "break"

    def send_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        self.response_text.delete(1.0, tk.END)

        if not url:
            self.response_text.insert(tk.END, "Error: URL cannot be empty.\n")
            return

        schemes_to_try = []
        if not url.startswith("http://") and not url.startswith("https://"):
            schemes_to_try = ["http://", "https://"]
            
        full_url = url
        response = None
        error_message = ""

        for scheme in ["", *schemes_to_try]:
            try:
                full_url = scheme + url
                if method == "GET":
                    response = requests.get(full_url)
                elif method == "POST":
                    body_content = self.body_text.get(1.0, tk.END).strip()
                    if body_content:
                        try:
                            body = json.loads(body_content)
                            response = requests.post(full_url, json=body)
                        except json.JSONDecodeError:
                            self.response_text.insert(tk.END, "Error: Invalid JSON in request body.\n")
                            return
                            return
                    else:
                        response = requests.post(full_url)
                break # If successful, break the loop
            except requests.exceptions.MissingSchema:
                # This means the scheme was missing, try the next one
                error_message = f"Error: Missing URL scheme. Tried {full_url}\n"
                continue
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {e}\n"
                if scheme == schemes_to_try[-1] or not schemes_to_try: # Last attempt or no schemes to try
                    self.response_text.insert(tk.END, error_message)
                    return
                continue
        
        if response is None:
            self.response_text.insert(tk.END, error_message if error_message else "Unknown error occurred.\n")
            return

        self.response_text.insert(tk.END, f"Status Code: {response.status_code}\n")
        self.response_text.insert(tk.END, "Headers:\n")
        for key, value in response.headers.items():
            self.response_text.insert(tk.END, f"  {key}: {value}\n")
        self.response_text.insert(tk.END, "\nBody:\n")
        try:
            self.response_text.insert(tk.END, json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            self.response_text.insert(tk.END, response.text)


if __name__ == "__main__":
    root = tk.Tk()
    app = PostmanApp(root)
    root.mainloop()
