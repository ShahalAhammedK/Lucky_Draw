import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
import random
import os
import json # Import json for saving/loading entries
from datetime import timedelta

# Create the Flask application instance
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set a secret key for flashing messages

# Configure session to be permanent and set a lifetime (optional, but good for persistence)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # Set a longer lifetime for testing
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Recommended for security and compatibility
app.config['SESSION_COOKIE_SECURE'] = False # Use True in production with HTTPS. Render uses HTTPS by default.

# Define the folder to store uploaded files and persistent entries
UPLOAD_FOLDER = 'uploads'
if not os.path.isdir(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ENTRIES_FILE = os.path.join(UPLOAD_FOLDER, 'entries.json') # Path to store entries

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page with the file upload form."""
    # Clear session data when returning to the index page to allow a fresh start
    session.pop('entries', None) 
    return render_template('index.html', winner=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle the file upload and perform the lucky draw."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        try:
            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(file)

            # Assuming the first column contains the names/entries
            if df.empty:
                flash('The Excel file is empty.')
                return redirect(url_for('index'))
                
            entries = df.iloc[:, 0].dropna().tolist()

            if not entries:
                flash('No valid entries found in the first column.')
                return redirect(url_for('index'))
            
            # Store entries in session for re-draw functionality
            session['entries'] = entries
            session.modified = True # Mark session as modified to ensure it's saved

            # Also save entries to a JSON file for persistence across server restarts
            with open(ENTRIES_FILE, 'w') as f:
                json.dump(entries, f)
            
            # Select a random winner from the list of entries
            winner = random.choice(entries)
            
            # Render the template again, this time with the winner
            return render_template('index.html', winner=winner)

        except Exception as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('index'))

    else:
        flash('Invalid file type. Please upload an .xlsx or .xls file.')
        return redirect(url_for('index'))

@app.route('/redraw', methods=['POST'])
def redraw():
    """Perform a re-draw using the previously uploaded entries, loading from file if session is empty."""
    entries = session.get('entries') # Try to get entries from session

    if not entries: # If not in session, try to load from file
        try:
            if os.path.exists(ENTRIES_FILE):
                with open(ENTRIES_FILE, 'r') as f:
                    entries = json.load(f)
                session['entries'] = entries # Store in session for future redraws
                session.modified = True
            else:
                flash('No entries found for re-draw. Please upload an Excel file first.')
                return render_template('index.html', winner=None) 
        except json.JSONDecodeError:
            flash('Error reading saved entries file. Please upload an Excel file again.')
            return render_template('index.html', winner=None)
        except Exception as e:
            flash(f'An error occurred while loading entries: {e}. Please upload an Excel file again.')
            return render_template('index.html', winner=None)

    if not entries: # Final check if entries are still empty after trying session and file
        flash('No valid entries found for re-draw. Please upload an Excel file first.')
        return render_template('index.html', winner=None)
    
    # Ensure a new random choice is made each time
    winner = random.choice(entries)
    
    return render_template('index.html', winner=winner)

if __name__ == '__main__':
    # Run the app in debug mode
    app.run(debug=True)
