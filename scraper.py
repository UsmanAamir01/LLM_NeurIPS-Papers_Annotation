import sys
sys.path.append(r"E:\SEMESTER\Python scrapper\Packages")
import threading
import ssl
from pathlib import Path
import aiofiles
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import random
import os
import csv
import asyncio
import aiohttp
from tkinter import ttk, scrolledtext, messagebox, filedialog
import tkinter as tk
import subprocess 

class NeurIPSScraper(tk.Tk):
    
    PRIMARY_COLOR = '#E74C3C'   
    SECONDARY_COLOR = '#C0392B'  
    BACKGROUND_COLOR = '#2C3E50' 
    ACCENT_COLOR = '#27AE60'     
    TEXT_COLOR = '#ECF0F1'       

    def __init__(self):
        super().__init__()
        self.title("NeurIPS Paper Scraper")
        self.configure(bg=self.BACKGROUND_COLOR)
        self.state('zoomed')
        self.metadata_list = []
        self.create_styles()
        self.initialize_gui()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        #styling
        style.configure('TFrame', background=self.BACKGROUND_COLOR)
        style.configure('TLabelFrame', background=self.BACKGROUND_COLOR,
                        foreground=self.TEXT_COLOR, font=('Helvetica', 12, 'bold'))
        style.configure('TLabel', background=self.BACKGROUND_COLOR,
                        foreground=self.TEXT_COLOR, font=('Helvetica', 12))
        style.configure('Header.TLabel', font=('Helvetica', 26, 'bold'),
                        foreground='white')
        style.configure('TEntry', fieldbackground='white', foreground='black')
        style.configure('TButton', 
                        background=self.PRIMARY_COLOR, 
                        foreground='white', 
                        font=('Helvetica', 14, 'bold'),
                        borderwidth=0, 
                        focusthickness=3, 
                        padding=(10, 6))  
        style.map('TButton',
                  background=[('active', self.SECONDARY_COLOR)],
                  foreground=[('active', 'white')])

        style.configure('TCombobox', fieldbackground='white', foreground='black', font=('Helvetica', 12))
        style.configure("Treeview",
                        background="white",
                        foreground="black",
                        fieldbackground="white",
                        font=('Helvetica', 12))
        style.configure("Treeview.Heading",
                        background=self.PRIMARY_COLOR,
                        foreground="white",
                        font=('Helvetica', 12, 'bold'))

    def initialize_gui(self):
       
       #Styling and Color Scheme
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=20, pady=(20, 10))
        title_label = ttk.Label(header_frame, text="NeurIPS Paper Scraper", style='Header.TLabel')
        title_label.pack(anchor='center')
        
        sidebar_frame = ttk.Frame(self)
        sidebar_frame.grid(row=1, column=0, sticky='nsw', padx=(20,10), pady=10)
        sidebar_frame.columnconfigure(0, weight=1)
        
        options_frame = ttk.LabelFrame(sidebar_frame, text="Options", padding=10)
        options_frame.grid(row=0, column=0, sticky='new', pady=(0, 20))
        
        current_year = time.localtime().tm_year
        years = list(range(1990, current_year + 1))
        
        # Start Year
        year_frame = ttk.Frame(options_frame)
        year_frame.pack(fill=tk.X, pady=5)
        ttk.Label(year_frame, text="Start Year:").pack(side=tk.LEFT, padx=5)
        self.start_year = ttk.Combobox(year_frame, values=years, width=8, state='readonly', font=('Helvetica', 12))
        self.start_year.set("2018")
        self.start_year.pack(side=tk.LEFT, padx=5)
        
        # End Year
        year_frame2 = ttk.Frame(options_frame)
        year_frame2.pack(fill=tk.X, pady=5)
        ttk.Label(year_frame2, text="End Year:").pack(side=tk.LEFT, padx=5)
        self.end_year = ttk.Combobox(year_frame2, values=years, width=8, state='readonly', font=('Helvetica', 12))
        self.end_year.set("2024")
        self.end_year.pack(side=tk.LEFT, padx=5)
        
        # Download Folder with Browse button 
        dir_frame = ttk.Frame(options_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="Download Folder:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.download_dir = ttk.Entry(dir_frame, font=('Helvetica', 12))
        self.download_dir.insert(0, "Scrapped_PDFs")
        self.download_dir.grid(row=0, column=1, padx=5, sticky=tk.EW)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).grid(row=0, column=2, padx=5, sticky=tk.E)
        dir_frame.columnconfigure(1, weight=1)
        
        buttons_frame = ttk.Frame(options_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.scrape_button = ttk.Button(buttons_frame, text="Scrape Metadata", command=self.scrape_metadata)
        self.scrape_button.pack(fill=tk.X, pady=5)
        
        self.download_button = ttk.Button(buttons_frame, text="Download PDFs", command=self.download_pdfs)
        self.download_button.pack(fill=tk.X, pady=5)
        
        self.categorize_button = ttk.Button(buttons_frame, text="Categorization", command=self.open_categorization)
        self.categorize_button.pack(fill=tk.X, pady=5)
        
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=1, sticky='nsew', padx=(10,20), pady=10)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Creating table
        columns = ("Title", "Authors", "Year", "PDF Link")
        self.tree = ttk.Treeview(content_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Title":
                self.tree.column(col, width=300)
            elif col == "Authors":
                self.tree.column(col, width=200)
            elif col == "Year":
                self.tree.column(col, width=70)
            else:
                self.tree.column(col, width=200)
                
        # Adding scrollbars
        vsb = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(content_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        footer_frame = ttk.Frame(self)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=20, pady=(10,20))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(footer_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0,5))
        
        # Log area below progress bar
        self.log_area = scrolledtext.ScrolledText(footer_frame, height=8, bg='white',
                                                   fg='black', font=('Helvetica', 12))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=os.getcwd(), title="Select PDF Download Directory")
        if directory:
            self.download_dir.delete(0, tk.END)
            self.download_dir.insert(0, directory)

    def log(self, message: str):
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)

    async def download_pdf(self, session: aiohttp.ClientSession, pdf_url: str, destination_path: str) -> bool:
        headers = {'User-Agent': random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        ])}
        try:
            async with session.get(pdf_url, headers=headers) as response:
                if response.status == 200:
                    async with aiofiles.open(destination_path, 'wb') as f:
                        await f.write(await response.read())
                    return True
                self.log(f"Failed to download {pdf_url}: HTTP {response.status}")
                return False
        except Exception as e:
            self.log(f"Error downloading {pdf_url}: {str(e)}")
            return False

    async def scrape_year(self, session: aiohttp.ClientSession, year: int) -> List[Dict]:
        if year < 2019:
            base_url = f"https://papers.nips.cc/paper/{year}"
            pdf_base = f"https://papers.nips.cc/paper_files/paper/{year}/file"
        else:
            base_url = f"https://proceedings.neurips.cc/paper/{year}"
            pdf_base = f"https://proceedings.neurips.cc/paper/{year}/file"

        headers = {'User-Agent': random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        ])}
        papers = []
        try:
            async with session.get(base_url, headers=headers) as response:
                if response.status != 200:
                    self.log(f"Failed to fetch year {year}: HTTP {response.status}")
                    return papers

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                paper_links = soup.select("a[title='paper title']")

                for paper_link in paper_links:
                    try:
                        title = paper_link.text.strip()
                        authors_tag = paper_link.find_next('i')
                        authors = authors_tag.text.strip() if authors_tag else ""
                        abstract_url = paper_link.get('href', '')
                        if 'Abstract' in abstract_url:
                            paper_hash = abstract_url.split('/')[-1].replace('-Abstract.html', '')
                            pdf_link = f"{pdf_base}/{paper_hash}-Paper.pdf"
                            papers.append({
                                'title': title,
                                'authors': authors,
                                'year': str(year),
                                'pdf_link': pdf_link
                            })
                    except Exception as e:
                        self.log(f"Error processing paper: {str(e)}")
                self.log(f"Year {year}: {len(papers)} papers saved in metadata.")
        except Exception as e:
            self.log(f"Error scraping year {year}: {str(e)}")
        return papers

    async def scrape_metadata_async(self):
        start_year = int(self.start_year.get())
        end_year = int(self.end_year.get())
        timeout = aiohttp.ClientTimeout(total=60)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = [self.scrape_year(session, year) for year in range(start_year, end_year + 1)]
            results = await asyncio.gather(*tasks)
            all_papers = []
            for papers in results:
                all_papers.extend(papers)
            csv_path = Path('python_metadata.csv')
            if not csv_path.exists():
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['title', 'authors', 'year', 'pdf_link'])
                    writer.writeheader()
                    writer.writerows(all_papers)
            return all_papers

    async def download_pdfs_async(self):
        download_dir = Path(self.download_dir.get())
        download_dir.mkdir(exist_ok=True)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            total = len(self.metadata_list)
            for i, paper in enumerate(self.metadata_list, 1):
                title = ''.join(c if c.isalnum() else '_' for c in paper['title'])
                path = download_dir / f"{title}_{paper['year']}.pdf"
                self.log(f"Downloading: {title}")
                success = await self.download_pdf(session, paper['pdf_link'], str(path))
                self.log(f"{'Downloaded' if success else 'Failed to download'}: {title}")
                progress = (i / total) * 100
                self.progress_var.set(progress)

    def scrape_metadata(self):
        self.scrape_button.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        self.progress_var.set(0)
        def run_scrape():
            start_time = time.time()
            papers = asyncio.run(self.scrape_metadata_async())
            elapsed_time = time.time() - start_time
            self.after(0, self.finish_scrape, papers, elapsed_time)
        threading.Thread(target=run_scrape, daemon=True).start()

    def finish_scrape(self, papers, elapsed_time):
        self.metadata_list = papers
        for paper in papers:
            self.tree.insert('', tk.END, values=(paper['title'], paper['authors'], paper['year'], paper['pdf_link']))
        self.scrape_button.config(state=tk.NORMAL)
        messagebox.showinfo("Scraping Complete",
                            f"Scraped {len(papers)} papers\nTotal time: {elapsed_time:.2f} seconds")

    def download_pdfs(self):
        self.download_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        def run_download():
            if not self.metadata_list:
                csv_path = Path('python_metadata.csv')
                if csv_path.exists():
                    self.log("Loading metadata from existing CSV...")
                    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        papers = list(reader)
                    self.metadata_list = papers
                    for paper in papers:
                        self.tree.insert('', tk.END, values=(paper['title'], paper['authors'], paper['year'], paper['pdf_link']))
                else:
                    self.log("No metadata found. Scraping metadata now...")
                    start_time = time.time()
                    papers = asyncio.run(self.scrape_metadata_async())
                    elapsed_time = time.time() - start_time
                    self.after(0, self.finish_scrape, papers, elapsed_time)
            asyncio.run(self.download_pdfs_async())
            self.after(0, self.finish_download)
        threading.Thread(target=run_download, daemon=True).start()

    def finish_download(self):
        self.download_button.config(state=tk.NORMAL)
        messagebox.showinfo("Download Complete", "PDF Download Complete")
        
    def open_categorization(self):
        try:
            subprocess.Popen(["python", "auto_annotator.py"])
            self.log("Launched auto_annotator.py for categorization.")
        except Exception as e:
            self.log(f"Failed to launch auto_annotator.py: {e}")

if __name__ == "__main__":
    app = NeurIPSScraper()
    app.mainloop()
