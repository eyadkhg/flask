from flask import Flask, request, jsonify, send_file
import os
import io
import uuid
from rembg import remove
from PIL import Image
import tempfile

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/rembg_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Background Removal API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            .endpoint {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            code {
                background-color: #eee;
                padding: 2px 5px;
                border-radius: 3px;
            }
            .try-it {
                margin-top: 30px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            input[type=file] {
                margin: 10px 0;
            }
            #result {
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Background Removal API</h1>
        <p>This API allows you to remove backgrounds from images using the rembg library.</p>
        
        <div class="endpoint">
            <h2>Health Check</h2>
            <p><strong>Endpoint:</strong> <code>/health</code></p>
            <p><strong>Method:</strong> GET</p>
            <p><strong>Description:</strong> Check if the API is running</p>
            <p><strong>Example:</strong> <code>curl -X GET https://eyadomii.pythonanywhere.com/health</code></p>
        </div>
        
        <div class="endpoint">
            <h2>Remove Background</h2>
            <p><strong>Endpoint:</strong> <code>/remove-bg</code></p>
            <p><strong>Method:</strong> POST</p>
            <p><strong>Description:</strong> Upload an image and get back a version with the background removed</p>
            <p><strong>Parameters:</strong> <code>file</code> - The image file to process (supported formats: PNG, JPG, JPEG)</p>
            <p><strong>Example:</strong> <code>curl -X POST -F "file=@/path/to/your/image.jpg" https://eyadomii.pythonanywhere.com/remove-bg -o output.png</code></p>
        </div>
        
        <div class="try-it">
            <h2>Try it now</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="imageFile" name="file" accept="image/png, image/jpeg">
                <button type="submit">Remove Background</button>
            </form>
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('imageFile');
                const resultDiv = document.getElementById('result');
                
                if (!fileInput.files.length) {
                    resultDiv.innerHTML = '<p style="color: red;">Please select an image file</p>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                resultDiv.innerHTML = '<p>Processing...</p>';
                
                fetch('/remove-bg', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = URL.createObjectURL(blob);
                    resultDiv.innerHTML = `
                        <h3>Result:</h3>
                        <img src="${url}" style="max-width: 100%;">
                        <p><a href="${url}" download="image_no_bg.png">Download Image</a></p>
                    `;
                })
                .catch(error => {
                    resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                });
            });
        </script>
    </body>
    </html>
    '''

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "rembg-api"})

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        unique_filename = str(uuid.uuid4())
        
        try:
            # Read the image
            input_image = Image.open(file.stream)
            
            # Process the image with rembg
            output_image = remove(input_image)
            
            # Save to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            output_image.save(temp_file.name)
            temp_file.close()
            
            # Return the processed image
            return send_file(temp_file.name, mimetype='image/png', as_attachment=True, 
                            download_name=f"{unique_filename}.png")
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
