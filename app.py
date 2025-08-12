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

        # Send Button
        self.send_button = ttk.Button(self.root, text="Send", command=self.send_request)
        self.send_button.grid(row=3, column=1, pady=10)

        # Response
        ttk.Label(self.root, text="Response:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.response_text = tk.Text(self.root, height=20, width=80)
        self.response_text.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(5, weight=1)


    def send_request(self):
        url = self.url_entry.get()
        method = self.method_var.get()
        self.response_text.delete(1.0, tk.END)

        if not url:
            messagebox.showerror("Error", "URL cannot be empty.")
            return
        
        if not url.startswith("http://") and not url.startswith("https://"):
            messagebox.showerror("Error", "URL must start with http:// or https://")
            return

        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                body_content = self.body_text.get(1.0, tk.END).strip()
                if body_content:
                    try:
                        body = json.loads(body_content)
                        response = requests.post(url, json=body)
                    except json.JSONDecodeError:
                        messagebox.showerror("Error", "Invalid JSON in request body.")
                        return
                else:
                    response = requests.post(url)
            
            self.response_text.insert(tk.END, f"Status Code: {response.status_code}\n")
            self.response_text.insert(tk.END, "Headers:\n")
            for key, value in response.headers.items():
                self.response_text.insert(tk.END, f"  {key}: {value}\n")
            self.response_text.insert(tk.END, "\nBody:\n")
            try:
                self.response_text.insert(tk.END, json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                self.response_text.insert(tk.END, response.text)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Request Error", f"An error occurred: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PostmanApp(root)
    root.mainloop()
