import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json

class PostmanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Post-er")
        self.root.configure(bg="#34495E") # Muted dark blue background

        # Configure ttk styles for muted dark blue background
        style = ttk.Style()
        style.theme_use('clam') # Use a theme that allows background customization
        style.configure("TLabel", background="#34495E", foreground="white")
        style.configure("TCombobox", fieldbackground="#4A6572", background="#34495E", foreground="white", selectbackground="#4A6572", selectforeground="white", font=('Arial', 10))
        style.map("TCombobox", fieldbackground=[("readonly", "#4A6572")])
        style.configure("TEntry", fieldbackground="#4A6572", foreground="white", insertbackground="white", font=('Arial', 10))
        style.map("TEntry", fieldbackground=[("readonly", "#4A6572")])
        style.configure("TButton", background="#4A6572", foreground="white", font=('Arial', 10, 'bold'), borderwidth=0) # Removed border for a flatter look
        style.map("TButton", background=[('active', '#5C7B8C'), ('pressed', '#5C7B8C'), ('!pressed', '#4A6572')]) # Active/pressed state color
        style.configure("Text", background="#4A6572", foreground="white", insertbackground="white") # For tk.Text widgets
        style.configure("TFrame", background="#34495E") # For ttk.Frame

        # Method
        self.method_var = tk.StringVar(value="GET")
        self.method_combobox = ttk.Combobox(self.root, textvariable=self.method_var, values=("GET", "POST"), state="readonly", width=6)
        self.method_combobox.grid(row=0, column=0, padx=5, pady=2, sticky="w") # Reduced padding
        self.method_combobox.set("GET") # Set initial value

        # URL
        self.url_entry = ttk.Entry(self.root)
        self.url_entry.grid(row=0, column=1, columnspan=4, padx=2, pady=2, sticky="ew") # Reduced padding

        # Send Button
        self.send_button = ttk.Button(self.root, text="Send", command=self.send_request)
        self.send_button.grid(row=0, column=5, padx=2, pady=2, sticky="ew") # Reduced padding

        # Headers/Body Buttons
        self.headers_button = ttk.Button(self.root, text="Headers", command=self.show_headers, width=10)
        self.headers_button.grid(row=1, column=0, padx=2, pady=2, sticky="ew") # Reduced padding
        self.body_button = ttk.Button(self.root, text="Body", command=self.show_body, width=10)
        self.body_button.grid(row=2, column=0, padx=2, pady=2, sticky="ew") # Reduced padding

        # Content Frame for Headers and Body
        self.content_frame = ttk.Frame(self.root, style="TFrame")
        self.content_frame.grid(row=1, column=1, rowspan=2, columnspan=5, padx=5, pady=5, sticky="nsew")

        # Request Headers
        self.headers_text = tk.Text(self.content_frame, height=10, background="#4A6572", foreground="white", insertbackground="white")
        self.headers_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.headers_text.bind("<Tab>", self._on_header_text_tab)

        # Body for POST
        self.body_text = tk.Text(self.content_frame, height=10, background="#4A6572", foreground="white", insertbackground="white")
        self.body_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.body_text.bind("<Tab>", self._on_body_text_tab)
        self.body_text.bind("<Shift-Tab>", self._on_body_text_tab)

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Initially show headers
        self.show_headers()

        # File Upload
        ttk.Label(self.root, text="File:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.root, textvariable=self.file_path_var, state="readonly")
        self.file_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.browse_button = ttk.Button(self.root, text="Browse", command=self.select_file, width=10)
        self.browse_button.grid(row=3, column=4, padx=5, pady=5, sticky="e")
        self.clear_file_button = ttk.Button(self.root, text="Clear", command=self.clear_file, width=10)
        self.clear_file_button.grid(row=3, column=5, padx=5, pady=5, sticky="e")
        self.file_data = None # To store the content of the selected file

        # Certificate
        ttk.Label(self.root, text="Cert:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.cert_path_var = tk.StringVar()
        self.cert_entry = ttk.Entry(self.root, textvariable=self.cert_path_var, state="readonly")
        self.cert_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.browse_cert_button = ttk.Button(self.root, text="Browse", command=self.select_cert, width=10)
        self.browse_cert_button.grid(row=4, column=4, padx=5, pady=5, sticky="e")
        self.clear_cert_button = ttk.Button(self.root, text="Clear", command=self.clear_cert, width=10)
        self.clear_cert_button.grid(row=4, column=5, padx=5, pady=5, sticky="e")

        # Bind <Return> to the root window to trigger send_request globally
        self.root.bind("<Return>", self.send_request_wrapper)

        # Response
        ttk.Label(self.root, text="Response:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.status_var = tk.StringVar(value="Status: N/A")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        self.data_info_var = tk.StringVar(value="Sent: 0B, Recv: 0B")
        self.data_info_label = ttk.Label(self.root, textvariable=self.data_info_var)
        self.data_info_label.grid(row=5, column=3, columnspan=3, padx=5, pady=5, sticky="e")
        self.response_text = tk.Text(self.root, height=20, background="#4A6572", foreground="white", insertbackground="white")
        self.response_text.grid(row=6, column=0, columnspan=6, padx=5, pady=5, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=1)
        self.root.grid_columnconfigure(5, weight=0) # Send button column, no weight
        self.root.grid_rowconfigure(1, weight=1) # New: for headers/body buttons and content frame
        self.root.grid_rowconfigure(2, weight=1) # New: for headers/body buttons and content frame
        self.root.grid_rowconfigure(6, weight=1) # Response text area
        
        # Set initial focus to the URL entry
        self.url_entry.focus_set()

    def show_headers(self):
        self.headers_text.grid()
        self.body_text.grid_remove()
        self.headers_button.state(['pressed'])
        self.body_button.state(['!pressed'])

    def show_body(self):
        self.body_text.grid()
        self.headers_text.grid_remove()
        self.body_button.state(['pressed'])
        self.headers_button.state(['!pressed'])

    def _on_header_text_tab(self, event):
        self.body_text.focus_set()
        return "break"

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

    def send_request_wrapper(self, event=None):
        focused_widget = self.root.focus_get()
        if focused_widget != self.headers_text and focused_widget != self.body_text:
            self.send_request()

    def send_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        cert_path = self.cert_path_var.get()
        self.response_text.delete(1.0, tk.END)
        self.status_var.set("Status: Sending...")
        self.data_info_var.set("Sent: 0B, Recv: 0B")
        self.root.update_idletasks() # Update UI to show "Sending..."

        if not url:
            self.response_text.insert(tk.END, "Error: URL cannot be empty.\n")
            self.status_var.set("Status: Error")
            return

        headers = {}
        header_lines = self.headers_text.get(1.0, tk.END).strip().split('\n')
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        request_body_size = 0
        request_header_size = sum(len(k) + len(v) + 4 for k, v in headers.items()) + 2 # +4 for ': ' and '\r\n', +2 for final '\r\n'

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
                        request_body_size = len(self.file_data)
                        response = requests.post(full_url, data=self.file_data, **kwargs)
                    else:
                        body_content = self.body_text.get(1.0, tk.END).strip()
                        if body_content:
                            try:
                                body = json.loads(body_content)
                                request_body_size = len(json.dumps(body).encode('utf-8'))
                                response = requests.post(full_url, json=body, **kwargs)
                            except json.JSONDecodeError:
                                # If not valid JSON, send as plain text
                                request_body_size = len(body_content.encode('utf-8'))
                                response = requests.post(full_url, data=body_content, **kwargs)
                        else:
                            response = requests.post(full_url, **kwargs)
                break # If successful, break the loop
            except requests.exceptions.MissingSchema:
                error_message = f"Error: Missing URL scheme. Tried {full_url}\n"
                continue
            except requests.exceptions.SSLError as e:
                error_message = f"SSL Error: {e}\n"
                self.response_text.insert(tk.END, error_message)
                self.status_var.set("Status: SSL Error")
                return
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {e}\n"
                if schemes_to_try and (scheme == schemes_to_try[-1] or not schemes_to_try):
                    self.response_text.insert(tk.END, error_message)
                    self.status_var.set("Status: Request Error")
                    return
                continue
        
        if response is None:
            self.response_text.insert(tk.END, error_message if error_message else "Unknown error occurred.\n")
            self.status_var.set("Status: Error")
            return

        # Calculate response size
        response_header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 2
        response_body_size = len(response.content)
        
        self.status_var.set(f"Status: {response.status_code}")
        self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {response_header_size + response_body_size}B")

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
