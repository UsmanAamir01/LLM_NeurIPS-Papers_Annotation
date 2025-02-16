# NeurIPS Papers Scraper & Automatic Annotation Using Large Language Model

This project extracts research paper details from NeurIPS Papers using Python. It handles pagination, website restrictions, and stores data locally or in a database.

## Prerequisites

1. **Install Python**  
   Ensure you have Python (version 3.8 or later) installed. You can download it from the official website:  
   👉 [Download Python](https://www.python.org/downloads/)

   After installation, verify it by running:
   ```bash
   python --version
## Setting Up Gemini API

To use the Gemini API, follow these steps:

1. **Get an API Key**  
   - Visit the [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.  
   - Navigate to the API keys section and generate a new API key.  
   - Copy the generated API key for later use.

2. **Store the API Key Securely**  
   - Create a `.env` file in the project directory and add the following line:
     ```env
     GEMINI_API_KEY=your_api_key_here
     ```
   - Alternatively, you can export it as an environment variable:  
     - **Windows (Command Prompt):**  
       ```cmd
       set GEMINI_API_KEY=your_api_key_here
       ```
     - **Mac/Linux (Terminal):**  
       ```bash
       export GEMINI_API_KEY=your_api_key_here
       ```

3. **Ensure the Script Reads the API Key**  
   The Python script should load the API key from the environment. If not already handled, modify your script like this:
   ```python
   import os
   from dotenv import load_dotenv

   load_dotenv()
   api_key = os.getenv("GEMINI_API_KEY")

## Execution
### Running the Scraper
To execute the web scraper, run:
```bash
python scraper.py
```
This will extract research paper details and save them accordingly.

### Running Auto Annotation
You can run the auto-annotation process using either of the following methods:
1. By clicking the **Categorization** button in `scraper.py`.
2. By directly executing:
   ```bash
   python auto_annotator.py
   ```

## Output
The extracted research paper details will be stored in a structured format, such as a CSV, as per the implementation.

## License
This project is open-source. Feel free to modify and enhance it!
