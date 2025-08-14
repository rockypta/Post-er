import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json

class PostmanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Post-er")

        # Configure ttk styles for white background
        style = ttk.Style()
        style.configure("TLabel", background="white")
        style.configure("TCombobox", fieldbackground="white", background="white", selectbackground="white", selectforeground="black")
        style.map("TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("TEntry", fieldbackground="white")
        style.map("TEntry", fieldbackground=[("readonly", "white")])

        # Method
        self.method_var = tk.StringVar(value="GET")
        self.method_combobox = ttk.Combobox(self.root, textvariable=self.method_var, values=("GET", "POST"), state="readonly", width=6)
        self.method_combobox.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.method_combobox.set("GET") # Set initial value

        # URL
        self.url_entry = ttk.Entry(self.root)
        self.url_entry.grid(row=0, column=1, columnspan=4, padx=5, pady=5, sticky="ew")

        # Request Headers
        self.headers_label = ttk.Label(self.root, text="Headers:")
        self.headers_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.headers_text = tk.Text(self.root, height=5)
        self.headers_text.grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky="ew")

        # Body for POST
        self.body_label = ttk.Label(self.root, text="Body:")
        self.body_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.body_text = tk.Text(self.root, height=10)
        self.body_text.grid(row=2, column=1, columnspan=4, padx=5, pady=5, sticky="ew")
        self.body_text.bind("<Tab>", self._on_body_text_tab)
        self.body_text.bind("<Shift-Tab>", self._on_body_text_tab)

        # File Upload
        ttk.Label(self.root, text="File:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.root, textvariable=self.file_path_var, width=60, state="readonly")
        self.file_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = ttk.Button(self.root, text="Browse", command=self.select_file)
        self.browse_button.grid(row=3, column=2, padx=5, pady=5)
        self.clear_file_button = ttk.Button(self.root, text="Clear", command=self.clear_file)
        self.clear_file_button.grid(row=3, column=3, padx=5, pady=5)
        self.file_data = None # To store the content of the selected file

        # Certificate
        ttk.Label(self.root, text="Cert:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.cert_path_var = tk.StringVar()
        self.cert_entry = ttk.Entry(self.root, textvariable=self.cert_path_var, width=60, state="readonly")
        self.cert_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.browse_cert_button = ttk.Button(self.root, text="Browse", command=self.select_cert)
        self.browse_cert_button.grid(row=4, column=2, padx=5, pady=5)
        self.clear_cert_button = ttk.Button(self.root, text="Clear", command=self.clear_cert)
        self.clear_cert_button.grid(row=4, column=3, padx=5, pady=5)

        # Send Button
        self.send_button = ttk.Button(self.root, text="Send", command=self.send_request)
        self.send_button.grid(row=5, column=4, padx=5, pady=10)

        # Bind <Return> to the root window to trigger send_request globally
        self.root.bind("<Return>", lambda event: self.send_request())

        # Response
        ttk.Label(self.root, text="Response:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.response_text = tk.Text(self.root, height=20)
        self.response_text.grid(row=7, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=3)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(7, weight=1)
        
        # Set initial focus to the URL entry
        self.url_entry.focus_set()

    def _on_body_text_tab(self, event):
        if event.state & 0x1:  # Check for Shift key (state 0x1)
            self.url_entry.focus_set()
        else:
            self.send_button.focus_set()
        return "break"

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_var.set(file_path)
            try:
                with open(file_path, 'rb') as f:
                    self.file_data = f.read()
            except Exception as e:
                messagebox.showerror("File Error", f"Could not read file: {e}")
                self.file_path_var.set("")
                self.file_data = None

    def clear_file(self):
        self.file_path_var.set("")
        self.file_data = None

    def select_cert(self):
        cert_path = filedialog.askopenfilename()
        if cert_path:
            self.cert_path_var.set(cert_path)

    def clear_cert(self):
        self.cert_path_var.set("")

    def send_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        cert_path = self.cert_path_var.get()
        self.response_text.delete(1.0, tk.END)

        if not url:
            self.response_text.insert(tk.END, "Error: URL cannot be empty.\n")
            return

        headers = {}
        header_lines = self.headers_text.get(1.0, tk.END).strip().split('\n')
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        schemes_to_try = []
        if not url.startswith("http://") and not url.startswith("https://"):
            schemes_to_try = ["http://", "https://"]
            
        full_url = url
        response = None
        error_message = ""

        for scheme in ["", *schemes_to_try]:
            try:
                full_url = scheme + url
                kwargs = {'headers': headers}
                if cert_path:
                    kwargs['cert'] = cert_path
                    kwargs['verify'] = True # Ensure verification

                if method == "GET":
                    response = requests.get(full_url, **kwargs)
                elif method == "POST":
                    if self.file_data:
                        response = requests.post(full_url, data=self.file_data, **kwargs)
                    else:
                        body_content = self.body_text.get(1.0, tk.END).strip()
                        if body_content:
                            try:
                                body = json.loads(body_content)
                                response = requests.post(full_url, json=body, **kwargs)
                            except json.JSONDecodeError:
                                # If not valid JSON, send as plain text
                                response = requests.post(full_url, data=body_content, **kwargs)
                        else:
                            response = requests.post(full_url, **kwargs)
                break # If successful, break the loop
            except requests.exceptions.MissingSchema:
                # This means the scheme was missing, try the next one
                error_message = f"Error: Missing URL scheme. Tried {full_url}\n"
                continue
            except requests.exceptions.SSLError as e:
                error_message = f"SSL Error: {e}\n"
                self.response_text.insert(tk.END, error_message)
                return
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {e}\n"
                if schemes_to_try and (scheme == schemes_to_try[-1] or not schemes_to_try): # Last attempt or no schemes to try
                    self.response_text.insert(tk.END, error_message)
                    return
                continue
        
        if response is None:
            self.response_text.insert(tk.END, error_message if error_message else "Unknown error occurred.\n")
            return

        self.response_text.insert(tk.END, f"Status Code: {response.status_code}\n")
        self.response_text.insert(tk.END, "Response Headers:\n")
        for key, value in response.headers.items():
            self.response_text.insert(tk.END, f"  {key}: {value}\n")
        self.response_text.insert(tk.END, "\nBody:\n")
        try:
            self.response_text.insert(tk.END, json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            self.response_text.insert(tk.END, response.text)


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="white")
    app = PostmanApp(root)
    root.mainloop()
