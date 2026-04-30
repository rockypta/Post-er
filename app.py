import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import os
import time
import threading
import concurrent.futures # For ThreadPoolExecutor
import tempfile # For temporary files
import math # For calculating part sizes

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
        self.method_combobox.grid(row=0, column=0, padx=2, pady=2, sticky="w") # Reduced padding
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
        self.content_frame.grid(row=1, column=1, rowspan=2, columnspan=5, padx=2, pady=2, sticky="nsew")

        # Request Headers
        self.headers_text = tk.Text(self.content_frame, height=10, background="#4A6572", foreground="white", insertbackground="white")
        self.headers_text.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        self.headers_text.bind("<Tab>", self._on_header_text_tab)

        # Body for POST
        self.body_text = tk.Text(self.content_frame, height=10, background="#4A6572", foreground="white", insertbackground="white")
        self.body_text.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        self.body_text.bind("<Tab>", self._on_body_text_tab)
        self.body_text.bind("<Shift-Tab>", self._on_body_text_tab)

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Initially show headers
        self.show_headers()

        # File Upload
        ttk.Label(self.root, text="File:").grid(row=3, column=0, padx=2, pady=2, sticky="w")
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.root, textvariable=self.file_path_var, state="readonly")
        self.file_entry.grid(row=3, column=1, columnspan=3, padx=2, pady=2, sticky="ew")
        self.browse_button = ttk.Button(self.root, text="Browse", command=self.select_file, width=10)
        self.browse_button.grid(row=3, column=4, padx=2, pady=2, sticky="e")
        self.clear_file_button = ttk.Button(self.root, text="Clear", command=self.clear_file, width=10)
        self.clear_file_button.grid(row=3, column=5, padx=2, pady=2, sticky="e")
        self.file_data = None # To store the content of the selected file

        # Certificate
        ttk.Label(self.root, text="Cert:").grid(row=4, column=0, padx=2, pady=2, sticky="w")
        self.cert_path_var = tk.StringVar()
        self.cert_entry = ttk.Entry(self.root, textvariable=self.cert_path_var, state="readonly")
        self.cert_entry.grid(row=4, column=1, columnspan=3, padx=2, pady=2, sticky="ew")
        self.browse_cert_button = ttk.Button(self.root, text="Browse", command=self.select_cert, width=10)
        self.browse_cert_button.grid(row=4, column=4, padx=2, pady=2, sticky="e")
        self.clear_cert_button = ttk.Button(self.root, text="Clear", command=self.clear_cert, width=10)
        self.clear_cert_button.grid(row=4, column=5, padx=2, pady=2, sticky="e")

        # CA Certificate
        ttk.Label(self.root, text="CA Cert:").grid(row=5, column=0, padx=2, pady=2, sticky="w")
        self.ca_cert_path_var = tk.StringVar()
        self.ca_cert_entry = ttk.Entry(self.root, textvariable=self.ca_cert_path_var, state="readonly")
        self.ca_cert_entry.grid(row=5, column=1, columnspan=3, padx=2, pady=2, sticky="ew")
        self.browse_ca_cert_button = ttk.Button(self.root, text="Browse", command=self.select_ca_cert, width=10)
        self.browse_ca_cert_button.grid(row=5, column=4, padx=2, pady=2, sticky="e")
        self.clear_ca_cert_button = ttk.Button(self.root, text="Clear", command=self.clear_ca_cert, width=10)
        self.clear_ca_cert_button.grid(row=5, column=5, padx=2, pady=2, sticky="e")

        # Bind <Return> to the root window to trigger send_request globally
        self.root.bind("<Return>", self.send_request_wrapper)

        # Response
        ttk.Label(self.root, text="Response:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.status_var = tk.StringVar(value="Status: N/A")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.grid(row=6, column=1, padx=5, pady=5, sticky="w") # columnspan reduced
        self.data_info_var = tk.StringVar(value="Sent: 0B, Recv: 0B")
        self.data_info_label = ttk.Label(self.root, textvariable=self.data_info_var)
        self.data_info_label.grid(row=6, column=2, columnspan=2, padx=5, pady=5, sticky="w") # Adjusted column and columnspan
        self.download_speed_var = tk.StringVar(value="Speed: N/A")
        self.download_speed_label = ttk.Label(self.root, textvariable=self.download_speed_var)
        self.download_speed_label.grid(row=6, column=4, columnspan=2, padx=5, pady=5, sticky="e") # New label
        self.response_text = tk.Text(self.root, height=20, background="#4A6572", foreground="white", insertbackground="white")
        self.response_text.grid(row=7, column=0, columnspan=6, padx=5, pady=5, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=0) # Browse button column, no weight
        self.root.grid_columnconfigure(5, weight=0) # Clear button column, no weight
        self.root.grid_rowconfigure(1, weight=1) # New: for headers/body buttons and content frame
        self.root.grid_rowconfigure(2, weight=1) # New: for headers/body buttons and content frame
        self.root.grid_rowconfigure(7, weight=1) # Response text area
        
        self.request_thread = None
        self.cancel_flag = threading.Event()
        
        # Set initial focus to the URL entry
        self.url_entry.focus_set()

    NUM_DOWNLOAD_PARTS = 8 # Number of concurrent parts for multipart download

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

    def select_ca_cert(self):
        ca_cert_path = filedialog.askopenfilename()
        if ca_cert_path:
            self.ca_cert_path_var.set(ca_cert_path)

    def clear_ca_cert(self):
        self.ca_cert_path_var.set("")

    def _format_bytes(self, bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val}B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.2f}KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.2f}MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f}GB"

    def send_request_wrapper(self, event=None):
        focused_widget = self.root.focus_get()
        if focused_widget != self.headers_text and focused_widget != self.body_text:
            self.send_request()

    def send_request(self):
        if self.request_thread and self.request_thread.is_alive():
            # If a request is already running, this click is to cancel it
            self.cancel_request()
        else:
            # Start a new request in a separate thread
            self.cancel_flag.clear() # Clear any previous cancellation flag
            self.send_button.config(text="Cancel", command=self.cancel_request)
            self.request_thread = threading.Thread(target=self._execute_request)
            self.request_thread.start()

    def cancel_request(self):
        self.cancel_flag.set() # Signal the worker thread to stop
        self.response_text.insert(tk.END, "\nRequest cancelled by user.\n")
        self.status_var.set("Status: Cancelled")
        self.download_speed_var.set("Speed: N/A")
        self.data_info_var.set("Sent: 0B, Recv: 0B")
        # Reset button immediately, as thread might take a moment to actually stop
        self._request_finished() 

    def _request_finished(self):
        # This method is called when the request thread finishes or is cancelled
        self.send_button.config(text="Send", command=self.send_request)
        self.request_thread = None # Clear the thread reference

    def _execute_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        cert_path = self.cert_path_var.get()
        
        # Clear response area and reset status/speed in the main thread
        self.root.after(0, lambda: self.response_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.status_var.set("Status: Sending..."))
        self.root.after(0, lambda: self.data_info_var.set("Sent: 0B, Recv: 0B"))
        self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
        self.root.after(0, lambda: self.root.update_idletasks())

        if not url:
            self.root.after(0, lambda: self.response_text.insert(tk.END, "Error: URL cannot be empty.\n"))
            self.root.after(0, lambda: self.status_var.set("Status: Error"))
            self.root.after(0, self._request_finished)
            return

        headers = {}
        header_lines = self.headers_text.get(1.0, tk.END).strip().split('\n')
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        # Add a default User-Agent if not already provided, to mimic browser behavior
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

        request_body_size = 0
        request_header_size = sum(len(k) + len(v) + 4 for k, v in headers.items()) + 2 # +4 for ': ' and '\r\n', +2 for final '\r\n'

        schemes_to_try = []
        if not url.startswith("http://") and not url.startswith("https://"):
            schemes_to_try = ["http://", "https://"]
            
        full_url = url
        response = None
        error_message = ""

        for scheme in ["", *schemes_to_try]:
            if self.cancel_flag.is_set(): # Check for cancellation before making request
                self.root.after(0, lambda: self.response_text.insert(tk.END, "\nRequest aborted before sending.\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Aborted"))
                self.root.after(0, self._request_finished)
                return

            try:
                full_url = scheme + url
                kwargs = {'headers': headers, 'stream': True} # Use stream for potential large file downloads
                ca_cert_path = self.ca_cert_path_var.get()
                if cert_path:
                    kwargs['cert'] = cert_path
                
                if ca_cert_path:
                    kwargs['verify'] = ca_cert_path
                else:
                    kwargs['verify'] = True # Default to True if no CA cert is provided

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
                self.root.after(0, lambda: self.response_text.insert(tk.END, error_message))
                self.root.after(0, lambda: self.status_var.set("Status: SSL Error"))
                self.root.after(0, self._request_finished)
                return
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {e}\n"
                if schemes_to_try and (scheme == schemes_to_try[-1] or not schemes_to_try):
                    self.root.after(0, lambda: self.response_text.insert(tk.END, error_message))
                    self.root.after(0, lambda: self.status_var.set("Status: Request Error"))
                    self.root.after(0, self._request_finished)
                    return
                continue
        
        if response is None:
            self.root.after(0, lambda: self.response_text.insert(tk.END, error_message if error_message else "Unknown error occurred.\n"))
            self.root.after(0, lambda: self.status_var.set("Status: Error"))
            self.root.after(0, self._request_finished)
            return

        # --- File Download Logic ---
        is_file_download = False
        filename = None

        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition and 'attachment' in content_disposition:
            # Try to extract filename from Content-Disposition
            try:
                filename = content_disposition.split('filename=')[1].strip('"\'')
                is_file_download = True
            except IndexError:
                pass # Fallback to content-type or URL

        if not is_file_download:
            content_type = response.headers.get('Content-Type', '').lower()
            # Heuristic: if not text/html or application/json, assume it's a file
            if 'text/html' not in content_type and 'application/json' not in content_type and 'text/plain' not in content_type:
                is_file_download = True
                # Generate filename from URL if not already found
                if not filename:
                    filename = os.path.basename(url.split('?')[0]) # Remove query params
                    if not filename or '.' not in filename: # If no clear filename, use a generic one
                        import datetime # Import datetime here as it's only needed for this specific case
                        filename = "downloaded_file" + ('.' + content_type.split('/')[-1] if '/' in content_type else '')
                        if filename == "downloaded_file": # Still generic, add a timestamp
                            filename = f"downloaded_file_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        if is_file_download and filename:
            download_dir = filedialog.askdirectory(initialdir=os.getcwd(), title="Select folder to save file")
            if not download_dir: # User cancelled the dialog
                self.root.after(0, lambda: self.response_text.insert(tk.END, "File download cancelled by user.\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Download Cancelled"))
                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed
                response.close()
                self.root.after(0, self._request_finished)
                return

            try:
                download_path = os.path.join(download_dir, filename)
                total_size = int(response.headers.get('content-length', 0))
                bytes_received = 0
                start_time = time.time()

                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancel_flag.is_set(): # Check for cancellation during download
                            self.root.after(0, lambda: self.response_text.insert(tk.END, "\nFile download cancelled.\n"))
                            self.root.after(0, lambda: self.status_var.set("Status: Download Cancelled"))
                            self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
                            response.close()
                            self.root.after(0, self._request_finished)
                            return
                        f.write(chunk)
                        bytes_received += len(chunk)
                        
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = bytes_received / elapsed_time # bytes per second
                            self.root.after(0, lambda s=speed: self.download_speed_var.set(f"Speed: {self._format_bytes(s)}/s"))
                        
                        # Update Recv count
                        self.root.after(0, lambda br=bytes_received: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(br)}"))
                        # self.root.after(0, lambda: self.root.update_idletasks()) # update_idletasks is expensive, only call if necessary

                self.root.after(0, lambda: self.response_text.insert(tk.END, f"File downloaded successfully to: {download_path}\n"))
                self.root.after(0, lambda: self.status_var.set(f"Status: Downloaded ({response.status_code})"))
                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed after completion
            except Exception as e:
                self.root.after(0, lambda e=e: self.response_text.insert(tk.END, f"Error downloading file: {e}\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Download Error"))
                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed on error
            finally:
                response.close() # Close the stream
            
            # Final update for data info after download
            response_header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 2
            response_body_size = os.path.getsize(download_path) if os.path.exists(download_path) else 0
            self.root.after(0, lambda rbs=response_body_size: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(rbs)}"))
            self.root.after(0, self._request_finished)
            return # Exit after file download

        # Calculate response size for non-file responses
        response_header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 2
        response_body_size = len(response.content)
        
        self.root.after(0, lambda: self.status_var.set(f"Status: {response.status_code}"))
        self.root.after(0, lambda: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(response_body_size)}"))
        self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed for non-file responses

        self.root.after(0, lambda: self.response_text.insert(tk.END, f"Status Code: {response.status_code}\n"))
        self.root.after(0, lambda: self.response_text.insert(tk.END, "Response Headers:\n"))
        self.root.after(0, lambda: [self.response_text.insert(tk.END, f"  {key}: {value}\n") for key, value in response.headers.items()])
        self.root.after(0, lambda: self.response_text.insert(tk.END, "\nBody:\n"))
        try:
            self.root.after(0, lambda: self.response_text.insert(tk.END, json.dumps(response.json(), indent=2)))
        except json.JSONDecodeError:
            self.root.after(0, lambda: self.response_text.insert(tk.END, response.text))
        finally:
            self.root.after(0, self._request_finished)


    def _download_file_multipart(self, url, headers, download_path, total_size, request_header_size, request_body_size, verify_ssl):
        self.root.after(0, lambda: self.status_var.set("Status: Downloading (Multipart)..."))
        self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))

        part_size = math.ceil(total_size / self.NUM_DOWNLOAD_PARTS)
        temp_files = []
        bytes_received_total = 0
        start_time = time.time()
        
        # Use a lock for updating shared progress variables
        progress_lock = threading.Lock()

        def download_part(part_num, start_byte, end_byte):
            nonlocal bytes_received_total
            if self.cancel_flag.is_set():
                return False # Indicate cancellation

            part_headers = headers.copy()
            part_headers['Range'] = f'bytes={start_byte}-{end_byte}'
            
            temp_file_path = f"{download_path}.part{part_num:03d}"
            temp_files.append(temp_file_path)

            try:
                part_response = requests.get(url, headers=part_headers, stream=True, verify=verify_ssl)
                part_response.raise_for_status() # Raise an exception for bad status codes

                bytes_received_part = 0
                with open(temp_file_path, 'wb') as f:
                    for chunk in part_response.iter_content(chunk_size=8192):
                        if self.cancel_flag.is_set():
                            part_response.close()
                            return False # Indicate cancellation
                        f.write(chunk)
                        bytes_received_part += len(chunk)
                        
                        with progress_lock:
                            bytes_received_total += len(chunk)
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = bytes_received_total / elapsed_time
                                self.root.after(0, lambda s=speed: self.download_speed_var.set(f"Speed: {self._format_bytes(s)}/s"))
                            self.root.after(0, lambda br=bytes_received_total: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(br)}"))
                part_response.close()
                return True # Indicate success
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda e=e: self.response_text.insert(tk.END, f"\nError downloading part {part_num}: {e}\n"))
                # Signal cancellation for other threads if one fails
                self.cancel_flag.set()
                return False
            except Exception as e:
                self.root.after(0, lambda e=e: self.response_text.insert(tk.END, f"\nUnexpected error downloading part {part_num}: {e}\n"))
                self.cancel_flag.set()
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.NUM_DOWNLOAD_PARTS) as executor:
            futures = []
            for i in range(self.NUM_DOWNLOAD_PARTS):
                start_byte = i * part_size
                end_byte = min(total_size - 1, start_byte + part_size - 1)
                if start_byte > end_byte: # Handle cases where total_size is smaller than NUM_DOWNLOAD_PARTS
                    break
                futures.append(executor.submit(download_part, i, start_byte, end_byte))
            
            # Wait for all parts to complete or for cancellation
            all_parts_successful = True
            for future in concurrent.futures.as_completed(futures):
                if not future.result(): # If any part failed or was cancelled
                    all_parts_successful = False
                    break
            
            if self.cancel_flag.is_set():
                self.root.after(0, lambda: self.response_text.insert(tk.END, "\nFile download cancelled.\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Download Cancelled"))
                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
                all_parts_successful = False # Ensure cleanup happens

        if not all_parts_successful:
            # Clean up any partially downloaded temp files
            for tf in temp_files:
                if os.path.exists(tf):
                    os.remove(tf)
            return False

        # Merge parts
        try:
            with open(download_path, 'wb') as outfile:
                for i in range(len(futures)): # Iterate based on number of parts submitted
                    part_file = f"{download_path}.part{i:03d}"
                    if os.path.exists(part_file):
                        with open(part_file, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(part_file) # Clean up temp file
            self.root.after(0, lambda: self.response_text.insert(tk.END, f"File downloaded successfully to: {download_path}\n"))
            self.root.after(0, lambda: self.status_var.set(f"Status: Downloaded (Multipart)"))
            self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
            return True
        except Exception as e:
            self.root.after(0, lambda e=e: self.response_text.insert(tk.END, f"Error merging file parts: {e}\n"))
            self.root.after(0, lambda: self.status_var.set("Status: Merge Error"))
            self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
            return False

    def _execute_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        cert_path = self.cert_path_var.get()
        
        # Clear response area and reset status/speed in the main thread
        self.root.after(0, lambda: self.response_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.status_var.set("Status: Sending..."))
        self.root.after(0, lambda: self.data_info_var.set("Sent: 0B, Recv: 0B"))
        self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
        self.root.after(0, lambda: self.root.update_idletasks())

        if not url:
            self.root.after(0, lambda: self.response_text.insert(tk.END, "Error: URL cannot be empty.\n"))
            self.root.after(0, lambda: self.status_var.set("Status: Error"))
            self.root.after(0, self._request_finished)
            return

        headers = {}
        header_lines = self.headers_text.get(1.0, tk.END).strip().split('\n')
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        # Add a default User-Agent if not already provided, to mimic browser behavior
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

        request_body_size = 0
        request_header_size = sum(len(k) + len(v) + 4 for k, v in headers.items()) + 2 # +4 for ': ' and '\r\n', +2 for final '\r\n'

        schemes_to_try = []
        if not url.startswith("http://") and not url.startswith("https://"):
            schemes_to_try = ["http://", "https://"]
            
        full_url = url
        response = None
        error_message = ""

        for scheme in ["", *schemes_to_try]:
            if self.cancel_flag.is_set(): # Check for cancellation before making request
                self.root.after(0, lambda: self.response_text.insert(tk.END, "\nRequest aborted before sending.\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Aborted"))
                self.root.after(0, self._request_finished)
                return

            try:
                full_url = scheme + url
                kwargs = {'headers': headers, 'stream': True} # Use stream for potential large file downloads
                ca_cert_path = self.ca_cert_path_var.get()
                if cert_path:
                    kwargs['cert'] = cert_path
                
                if ca_cert_path:
                    kwargs['verify'] = ca_cert_path
                else:
                    kwargs['verify'] = True # Default to True if no CA cert is provided
                
                verify_ssl = kwargs['verify'] # Store the verify argument for multipart download

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
                self.root.after(0, lambda: self.response_text.insert(tk.END, error_message))
                self.root.after(0, lambda: self.status_var.set("Status: SSL Error"))
                self.root.after(0, self._request_finished)
                return
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {e}\n"
                if schemes_to_try and (scheme == schemes_to_try[-1] or not schemes_to_try):
                    self.root.after(0, lambda: self.response_text.insert(tk.END, error_message))
                    self.root.after(0, lambda: self.status_var.set("Status: Request Error"))
                    self.root.after(0, self._request_finished)
                    return
                continue
        
        if response is None:
            self.root.after(0, lambda: self.response_text.insert(tk.END, error_message if error_message else "Unknown error occurred.\n"))
            self.root.after(0, lambda: self.status_var.set("Status: Error"))
            self.root.after(0, self._request_finished)
            return

        # --- File Download Logic ---
        is_file_download = False
        filename = None

        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition and 'attachment' in content_disposition:
            # Try to extract filename from Content-Disposition
            try:
                filename = content_disposition.split('filename=')[1].strip('"\'')
                is_file_download = True
            except IndexError:
                pass # Fallback to content-type or URL

        if not is_file_download:
            content_type = response.headers.get('Content-Type', '').lower()
            # Heuristic: if not text/html or application/json, assume it's a file
            if 'text/html' not in content_type and 'application/json' not in content_type and 'text/plain' not in content_type:
                is_file_download = True
                # Generate filename from URL if not already found
                if not filename:
                    filename = os.path.basename(url.split('?')[0]) # Remove query params
                    if not filename or '.' not in filename: # If no clear filename, use a generic one
                        import datetime # Import datetime here as it's only needed for this specific case
                        filename = "downloaded_file" + ('.' + content_type.split('/')[-1] if '/' in content_type else '')
                        if filename == "downloaded_file": # Still generic, add a timestamp
                            filename = f"downloaded_file_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        if is_file_download and filename:
            download_dir = filedialog.askdirectory(initialdir=os.getcwd(), title="Select folder to save file")
            if not download_dir: # User cancelled the dialog
                self.root.after(0, lambda: self.response_text.insert(tk.END, "File download cancelled by user.\n"))
                self.root.after(0, lambda: self.status_var.set("Status: Download Cancelled"))
                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed
                response.close()
                self.root.after(0, self._request_finished)
                return

            download_path = os.path.join(download_dir, filename)
            total_size = int(response.headers.get('content-length', 0))
            accept_ranges = response.headers.get('Accept-Ranges', '').lower()

            # Check if multipart download is possible and beneficial
            if total_size > 0 and accept_ranges == 'bytes':
                response.close() # Close the initial response, as we'll make new requests for parts
                multipart_success = self._download_file_multipart(full_url, headers, download_path, total_size, request_header_size, request_body_size, verify_ssl)
                if multipart_success:
                    # Final update for data info after download
                    response_header_size = sum(len(k) + len(v) + 4 for k, v in headers.items()) + 2 # Re-estimate headers for multipart
                    response_body_size = os.path.getsize(download_path) if os.path.exists(download_path) else 0
                    self.root.after(0, lambda rbs=response_body_size: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(rbs)}"))
                self.root.after(0, self._request_finished)
                return # Exit after file download attempt
            else:
                # Fallback to single-part download if multipart is not supported or not beneficial
                self.root.after(0, lambda: self.response_text.insert(tk.END, "Multipart download not supported or not applicable. Falling back to single-part.\n"))
                try:
                    bytes_received = 0
                    start_time = time.time()

                    with open(download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.cancel_flag.is_set(): # Check for cancellation during download
                                self.root.after(0, lambda: self.response_text.insert(tk.END, "\nFile download cancelled.\n"))
                                self.root.after(0, lambda: self.status_var.set("Status: Download Cancelled"))
                                self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A"))
                                response.close()
                                self.root.after(0, self._request_finished)
                                return
                            f.write(chunk)
                            bytes_received += len(chunk)
                            
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = bytes_received / elapsed_time # bytes per second
                                self.root.after(0, lambda s=speed: self.download_speed_var.set(f"Speed: {self._format_bytes(s)}/s"))
                            
                            # Update Recv count
                            self.root.after(0, lambda br=bytes_received: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(br)}"))

                    self.root.after(0, lambda: self.response_text.insert(tk.END, f"File downloaded successfully to: {download_path}\n"))
                    self.root.after(0, lambda: self.status_var.set(f"Status: Downloaded ({response.status_code})"))
                    self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed after completion
                except Exception as e:
                    self.root.after(0, lambda e=e: self.response_text.insert(tk.END, f"Error downloading file: {e}\n"))
                    self.root.after(0, lambda: self.status_var.set("Status: Download Error"))
                    self.root.after(0, lambda: self.download_speed_var.set("Speed: N/A")) # Reset speed on error
                finally:
                    response.close() # Close the stream
                
                # Final update for data info after download
                response_header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 2
                response_body_size = os.path.getsize(download_path) if os.path.exists(download_path) else 0
                self.root.after(0, lambda rbs=response_body_size: self.data_info_var.set(f"Sent: {request_header_size + request_body_size}B, Recv: {self._format_bytes(rbs)}"))
                self.root.after(0, self._request_finished)
                return # Exit after file download


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="white")
    app = PostmanApp(root)
    root.mainloop()
