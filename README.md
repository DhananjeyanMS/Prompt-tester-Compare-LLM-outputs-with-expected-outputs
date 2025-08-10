# Gemini Output Verification Tool

A Flask-based web application that **tests Gemini model outputs** against pre-defined expected outputs.  
It supports optional **system prompts**, configurable generation parameters, and provides a **side-by-side diff** of mismatches.

---

## 📌 Features

- Upload:
  - **System Prompt** (`.txt`) — optional
  - **Input Messages** (`.txt`)
  - **Expected Outputs** (`.txt`)
- Runs each input through Google Gemini API
- Compares **actual output** vs **expected output**
- Shows:
  - ✅ Match status
  - ⚠ Mismatch with highlighted differences
- Adjustable parameters:
  - Temperature
  - Top P
  - Top K
- Predefined Gemini models:
  - `gemini-1.5-flash-latest`
  - `gemini-2.0-flash-001`
  - `gemini-2.5-flash`
- Web interface with:
  - `templates/index.html`
  - `static/style.css`

---

## 📂 Project Structure

```

project/
├── app.py                # Main Flask app
├── templates/
│   └── index.html         # HTML UI
├── static/
│   └── style.css          # Styling
├── uploads/               # Uploaded files (auto-created)
└── .env                   # Environment variables

````

---

## 🔧 Installation

1. **Clone the repository**  

2. **Install dependencies**

3. **Create `.env` file**

   ```
   GEMINI_API_KEY=your_api_key_here
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

5. **Open in browser**

   ```
   http://127.0.0.1:8080
   ```

---

## 🖥️ Usage

1. **Enter your Gemini API key** in the form (or store in `.env`).
2. Select a **Gemini model**.
3. Upload:

   * System Message (`.txt`) — optional
   * One or more Input Message files (`.txt`)
   * Corresponding Expected Output files (`.txt`)
4. Adjust `temperature`, `top_p`, and `top_k` (optional).
5. Submit and view:

   * Input
   * Expected Output
   * Actual Output
   * Status (Match/Mismatch)
   * Diff view with highlights

---

## 🗂 Allowed File Types

* `.txt` only
* Number of input files **must match** number of expected output files

---

## ⚠️ Notes

* This app runs in **debug mode** — do **not** use in production without changes.
* Ensure your Gemini API key has quota for multiple requests.
* Diff legend:

  * 🟩 Added lines
  * 🟥 Removed lines
  * ℹ Intra-line changes

---

