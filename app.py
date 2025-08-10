import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import difflib # Import difflib for comparison

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey_for_flash_messages'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

GEMINI_MODELS = [
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash-001", 
    "gemini-2.5-flash"

    # Add other models you might want to test
]

def generate_diff_html(text1, text2):
    """Generates HTML with highlighted differences between two texts."""
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(keepends=True), text2.splitlines(keepends=True)))
    
    html_diff = []
    for line in diff:
        if line.startswith('+ '):
            html_diff.append(f'<span class="diff-added">{line}</span>')
        elif line.startswith('- '):
            html_diff.append(f'<span class="diff-removed">{line}</span>')
        elif line.startswith('? '):
            # This line indicates intra-line changes, we'll just show it for context
            html_diff.append(f'<span class="diff-info">{line}</span>')
        else:
            html_diff.append(f'<span>{line}</span>')
    return '<pre>' + ''.join(html_diff) + '</pre>'


@app.route('/', methods=['GET', 'POST'])
def index():
    results_table_data = [] 
    selected_model = request.form.get('gemini_model', "gemini-pro") 

    if request.method == 'POST':
        api_key = request.form.get('api_key')
        selected_model = request.form.get('gemini_model') 

        if not api_key:
            flash('Please set your Gemini API Key.', 'error')
            return redirect(request.url)

        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            flash(f"Error configuring Gemini API: {e}", 'error')
            return redirect(request.url)

        system_message = None
        if 'system_message_file' in request.files:
            system_file = request.files['system_message_file']
            if system_file and allowed_file(system_file.filename):
                filename = secure_filename(system_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                system_file.save(filepath)
                with open(filepath, 'r', encoding='utf-8') as f:
                    system_message = f.read()
            elif system_file.filename != '':
                flash('Invalid file type for system message. Only .txt allowed.', 'error')
                return redirect(request.url)

        # Process input and expected output files
        input_files_list = request.files.getlist('input_message_files')
        expected_output_files_list = request.files.getlist('expected_output_files')

        if not input_files_list:
            flash('Please upload at least one input message file.', 'error')
            return redirect(request.url)
        
        if len(input_files_list) != len(expected_output_files_list):
            flash('The number of input files must match the number of expected output files.', 'error')
            return redirect(request.url)

        # Read file contents and store them paired
        paired_files_content = []
        for i in range(len(input_files_list)):
            input_file = input_files_list[i]
            expected_output_file = expected_output_files_list[i]

            if not (input_file and allowed_file(input_file.filename) and
                    expected_output_file and allowed_file(expected_output_file.filename)):
                flash('Invalid file type detected. Only .txt files are allowed for all inputs and expected outputs.', 'error')
                return redirect(request.url)
            
            # Save and read input file
            input_filename = secure_filename(input_file.filename)
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            input_file.save(input_filepath)
            with open(input_filepath, 'r', encoding='utf-8') as f:
                input_text = f.read()

            # Save and read expected output file
            expected_output_filename = secure_filename(expected_output_file.filename)
            expected_output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], expected_output_filename)
            expected_output_file.save(expected_output_filepath)
            with open(expected_output_filepath, 'r', encoding='utf-8') as f:
                expected_output_text = f.read()
            
            paired_files_content.append({
                "input_text": input_text,
                "expected_output_text": expected_output_text
            })

        try:
            temperature = float(request.form.get('temperature', 0))
            top_p = float(request.form.get('top_p', 0.95))
            top_k = int(request.form.get('top_k', 64))
        except ValueError:
            flash('Invalid value for temperature, top_p, or top_k. Please enter numbers.', 'error')
            return redirect(request.url)

        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": 8192,
        }

        try:
            model = genai.GenerativeModel(model_name=selected_model)
        except Exception as e:
            flash(f"Error initializing Gemini model '{selected_model}': {e}", 'error')
            return redirect(request.url)

        for pair in paired_files_content:
            input_content = pair["input_text"]
            expected_output_content = pair["expected_output_text"]
            actual_output_content = ""
            diff_html = ""
            status = "Error" # Default status

            try:
                current_chat_history = []
                if system_message:
                    current_chat_history.append({"role": "user", "parts": [system_message]})
                    current_chat_history.append({"role": "model", "parts": ["Understood."]}) 
                
                chat = model.start_chat(history=current_chat_history)
                response = chat.send_message(input_content, generation_config=generation_config)
                actual_output_content = response.text

                # Compare actual and expected output
                if actual_output_content.strip() == expected_output_content.strip():
                    status = "Match"
                    diff_html = '<span class="diff-match">Outputs Match!</span>'
                else:
                    status = "Mismatch"
                    diff_html = generate_diff_html(expected_output_content, actual_output_content)

            except Exception as e:
                flash(f"Error processing input: '{input_content[:50]}...' - {e}", 'error')
                actual_output_content = f"Error: {e}"
                diff_html = '<span class="diff-error">Error during generation or comparison.</span>'
            
            results_table_data.append({
                "input_content": input_content,
                "expected_output_content": expected_output_content,
                "actual_output_content": actual_output_content,
                "diff_html": diff_html,
                "status": status
            })

    return render_template('index.html', 
                           results_table_data=results_table_data, 
                           gemini_models=GEMINI_MODELS, 
                           selected_model=selected_model)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
