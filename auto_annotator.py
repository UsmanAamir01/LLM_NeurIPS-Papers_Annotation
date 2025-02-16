import os
import time
import csv
import google.generativeai as genai
from PyPDF2 import PdfReader
from datetime import datetime
import itertools
import signal  
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# --- Configuration ---
PDF_FOLDER_PATH = r'D:\Semester 6\Data Science\python-scraping\scraped_pdfs'
LABELS = [
    "Machine Learning",
    "Deep Learning",
    "Computer Vision",
    "Natural Language Processing",
    "Reinforcement Learning",
    "Optimization",
    "Data Science",
    "Artificial Intelligence",
    "Robotics",
]
GENERIC_LABELS_PROMPT = ", ".join(LABELS)
GEMINI_API_KEYS = [
    os.getenv("GOOGLE_API_KEY"),
    os.getenv("GOOGLE_API_KEY2"),
    os.getenv("GOOGLE_API_KEY3")
]
MODEL_NAME = "gemini-1.5-flash"
CSV_OUTPUT_FILE = r'D:\Semester 6\Data Science\python-scraping\python_metadata.csv'
API_TIMEOUT_SECONDS = 90

# Filter out any None keys
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
if not GEMINI_API_KEYS:
    print("Error: No Gemini API keys found. Please set up at least one API key.")
    sys.exit(1)

print(f"DEBUG: Loaded {len(GEMINI_API_KEYS)} Gemini API keys.")

# Create a cycling iterator for API keys
api_key_cycle = itertools.cycle(GEMINI_API_KEYS)

pdf_categories_global = {}
csv_header_written = False

def extract_abstract_from_pdf(pdf_path):
    """Extracts only the abstract from a PDF file.
       Assumes that the abstract starts with a line containing 'Abstract' and ends with an empty line."""
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

    #Extract the abstract section
    abstract = ""
    lower_text = text.lower()
    if "abstract" in lower_text:
        lines = text.split("\n")
        capturing = False
        for line in lines:
            if "abstract" in line.lower():
                capturing = True
                continue
            if capturing:
                if line.strip() == "":
                    break
                abstract += line.strip() + " "
    return abstract.strip() if abstract else "Abstract Not Found"

def categorize_pdf_with_gemini(paper_title, paper_abstract, labels_prompt=GENERIC_LABELS_PROMPT):
    """Categorizes a research paper using its title and abstract.
       Implements API key rotation and retry logic."""
    if not paper_title and not paper_abstract:
        return "No Text Extracted"

    prompt_content = f"""
Instructions: You are an expert research paper classifier.
You are provided with a research paper's title and abstract.
Based on the content, classify the paper into one of the following categories:
{labels_prompt}.
If the paper does not clearly belong to any of these categories, reply with "Other".
IMPORTANT: Respond ONLY with the category name.

Research Paper Title:
{paper_title}

Research Paper Abstract:
{paper_abstract}

Category:
"""
    max_retries_per_key = 3
    api_error_delay = 60
    api_keys_tried_count = 0
    keys_exhausted_delay_occurred = False

    while api_keys_tried_count < len(GEMINI_API_KEYS) * max_retries_per_key:
        try:
            current_api_key = next(api_key_cycle)
            genai.configure(api_key=current_api_key)
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(prompt_content) 
            gemini_output = response.text.strip()

            if gemini_output.lower() not in [label.lower() for label in LABELS + ["Other"]]:
                print(f"Warning: Gemini returned unexpected label: '{gemini_output}'.")
                return "Uncategorized"
            return gemini_output

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str:
                delay = api_error_delay
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                key_index = GEMINI_API_KEYS.index(current_api_key) if current_api_key in GEMINI_API_KEYS else 'N/A'
                print(f"{timestamp} - Gemini API error (Key index: {key_index}): 429 Rate Limit Exceeded (Attempt {api_keys_tried_count % max_retries_per_key + 1}/{max_retries_per_key}).")
                api_keys_tried_count += 1
                if api_keys_tried_count >= len(GEMINI_API_KEYS) * max_retries_per_key and not keys_exhausted_delay_occurred:
                    print(f"{timestamp} - All keys rate limited. Waiting for {delay} seconds before retrying...")
                    time.sleep(delay)
                    keys_exhausted_delay_occurred = True
                continue
            elif "deadline" in error_str:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                key_index = GEMINI_API_KEYS.index(current_api_key) if current_api_key in GEMINI_API_KEYS else 'N/A'
                print(f"{timestamp} - Gemini API Timeout (Key index: {key_index}).")
                api_keys_tried_count += 1
                continue
            else:
                print(f"Gemini API error: {e}")
                return "API Error"

    timestamp_fail = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp_fail} - Max API retries reached. Categorization failed.")
    return "API Error (Retries Exhausted)"

def save_category_to_csv_append(pdf_name, category, csv_filename, write_header=False):
    """Appends a PDF's category to the CSV file. Writes header only if needed."""
    file_exists = os.path.exists(csv_filename)
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        if write_header or not file_exists:
            print("DEBUG: Writing CSV header...")
            csv_writer.writerow(['PDF Name', 'Category'])
        print(f"DEBUG: Writing row: PDF Name='{pdf_name}', Category='{category}'")
        csv_writer.writerow([pdf_name, category])
    print(f"Saved category for '{pdf_name}' to {csv_filename}")

# --- GUI Class Definition ---

class PDFCategorizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Categorizer")
        # Increase width of the window (set width to 1200 pixels, height to 600 pixels)
        self.geometry("1200x600")
        self.configure(bg="#2C3E50")

        self.pdf_folder = tk.StringVar(value=PDF_FOLDER_PATH)
        self.metadata = {}  # Dictionary: {pdf_filename: category}
        self.csv_header_written = False
        # New variable to choose CSV mode: "append" or "new"
        self.csv_mode = tk.StringVar(value="append")
        # Entry variable for new CSV filename (only used if csv_mode=="new")
        self.new_csv_filename = tk.StringVar(value="")

        # Will store the CSV file name to use
        self.current_csv_filename = CSV_OUTPUT_FILE

        self.create_widgets()

    def create_widgets(self):
        # Top frame for folder selection and CSV mode options
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="PDF Folder:", background="#2C3E50", foreground="#ECF0F1", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.folder_entry = ttk.Entry(top_frame, textvariable=self.pdf_folder, width=60, font=("Helvetica", 12))
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Browse...", command=self.browse_folder, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Start Categorization", command=self.start_categorization, width=20).pack(side=tk.LEFT, padx=5)

        csv_option_frame = ttk.Frame(self, padding=10)
        csv_option_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(csv_option_frame, text="CSV Mode:", background="#2C3E50", foreground="#ECF0F1", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(csv_option_frame, text="Append to Existing CSV", variable=self.csv_mode, value="append", command=self.toggle_csv_entry).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(csv_option_frame, text="Create New CSV", variable=self.csv_mode, value="new", command=self.toggle_csv_entry).pack(side=tk.LEFT, padx=5)
        self.csv_entry = ttk.Entry(csv_option_frame, textvariable=self.new_csv_filename, width=40, font=("Helvetica", 12))
        self.csv_entry.pack_forget()

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("PDF Name", "Category")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=300)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Log area
        log_frame = ttk.LabelFrame(self, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, font=("Helvetica", 12))
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.style_widgets()

    def toggle_csv_entry(self):
        if self.csv_mode.get() == "new":
            self.csv_entry.pack(side=tk.LEFT, padx=5)
        else:
            self.csv_entry.pack_forget()

    def style_widgets(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Colors
        primary = "#3498db"    
        secondary = "#2980b9" 
        bg_color = "#2C3E50"  
        accent = "#e67e22"    
        text_color = "#ECF0F1" 

        style.configure("TLabel", background=bg_color, foreground=text_color, font=("Helvetica", 12))
        style.configure("Header.TLabel", background=bg_color, foreground=primary, font=("Helvetica", 26, "bold"))

        style.configure("TButton", background=primary, foreground="white", font=("Helvetica", 12, "bold"), padding=8)
        style.map("TButton",
                  background=[("active", secondary)],
                  foreground=[("active", "white")])
        style.configure("TEntry", fieldbackground="white", foreground="black", font=("Helvetica", 12))
        style.configure("TCombobox", fieldbackground="white", foreground="black", font=("Helvetica", 12))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.pdf_folder.get())
        if folder_selected:
            self.pdf_folder.set(folder_selected)

    def log(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        self.log_area.insert(tk.END, timestamp + message + "\n")
        self.log_area.see(tk.END)

    def get_csv_filename(self):
        """Returns the CSV filename based on the CSV mode.
           If 'append', returns the pre-configured CSV_OUTPUT_FILE.
           If 'new', returns the name entered by the user or a timestamped default."""
        if self.csv_mode.get() == "append":
            return CSV_OUTPUT_FILE
        else:
            new_name = self.new_csv_filename.get().strip()
            if new_name:
                # Ensure the new file name ends with .csv
                if not new_name.lower().endswith(".csv"):
                    new_name += ".csv"
                return new_name
            else:
                base, ext = os.path.splitext(CSV_OUTPUT_FILE)
                new_filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                return new_filename

    def start_categorization(self):
        folder = self.pdf_folder.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid PDF folder.")
            return

        self.current_csv_filename = self.get_csv_filename()
        self.csv_header_written = False

        self.tree.delete(*self.tree.get_children())
        self.log_area.delete("1.0", tk.END)
        self.metadata = {}
        self.progress_var.set(0)

        threading.Thread(target=self.process_folder, args=(folder,), daemon=True).start()

    def process_folder(self, folder_path):
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        total = len(pdf_files)
        if total == 0:
            self.log("No PDF files found in the selected folder.")
            return

        for idx, filename in enumerate(pdf_files, start=1):
            pdf_path = os.path.join(folder_path, filename)
            self.log(f"Processing: {filename}")
            abstract = extract_abstract_from_pdf(pdf_path)
            if abstract:
                title = os.path.splitext(filename)[0]
                category = categorize_pdf_with_gemini(title, abstract)
            else:
                category = "Text Extraction Failed"
            self.metadata[filename] = category
            self.log(f"  - Category: {category}")
            # Append result to CSV using the current CSV filename
            save_category_to_csv_append(filename, category, self.current_csv_filename, write_header=not self.csv_header_written)
            if not self.csv_header_written:
                self.csv_header_written = True
            self.tree.insert("", tk.END, values=(filename, category))
            progress_percent = (idx / total) * 100
            self.progress_var.set(progress_percent)
            time.sleep(1) 

        self.log("Categorization complete.")

def signal_handler(sig, frame):
    print("\nScript interrupted by user. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    app = PDFCategorizerGUI()
    app.mainloop()
