from flask import Flask
import os
from flask import request
from flask import flash
from flask import redirect
from werkzeug.utils import secure_filename
import ipfshttpclient
from flask_cors import CORS
from flask import session, g, jsonify

SECRET_KEY = os.urandom(24)

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'files')
ALLOWED_EXTENSIONS = set(['html'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and True
           # filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return """
        <html>
            <head>
                <title> upload </title>
            </head>
            <body>
                <script>
                    const upload = (ip) => {
                        const form = document.getElementById('upload-form');
                        form.submit(); 
                    }
                </script>
                <form id='upload-form' method="post" enctype="multipart/form-data">
                    <input type='file' name='file' /><br>
                    <button onclick="upload(this)">Upload</button>
                </form>
            </body>
        </html>
        """

    elif request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('no selected file')
            print('no selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ipfs = add_to_ipfs(filename)
            url = f'http://localhost:8080/ipfs/{ipfs["Hash"]}'
            return redirect(f'http://localhost:8000/single.html?src={url}&type=video/webm');

        print(file)
        print(allowed_file(file.filename))
        return 'adf'
    
@app.route('/uploaded_file/<filename>')
def uploaded_file(filename):
    return 'fadf' + filename


def add_to_ipfs(file):
    client = ipfshttpclient.connect('/ip4/0.0.0.0/tcp/5001/http')    
    return client.add(os.path.join(UPLOAD_FOLDER, file))


SEQIT = None

@app.route('/v1/<hash>')
def v1(hash):
    with open('video.webm', 'rb') as f:
        vid = f.read()

    import base64
    og = base64.b64encode(vid).decode()
    import nucy
    SEQ = nucy.Seq(og)
    SEQIT = SEQ.start()
    itr = SEQIT
    cipher = base64.b64encode(next(SEQIT)).decode()
    with open(os.path.join(UPLOAD_FOLDER, hash + '-v1'), 'w') as f:
        f.write(cipher)
   
    fs = add_to_ipfs(hash + '-v1')
    link = f'http://localhost:8080/ipfs/{fs["Hash"]}'
    plain = next(itr).decode()
    with open(os.path.join(UPLOAD_FOLDER, hash + '-v2'), 'w') as f:
        f.write(plain)
   
    fs = add_to_ipfs(hash + '-v2')
    link2 = f'http://localhost:8080/ipfs/{fs["Hash"]}'

    return jsonify([link, link2])

@app.route('/v2/<hash>')
def v2(hash):

    return link

@app.route('/test')
def test():
    with open('video.webm', 'rb') as f:
        vid = f.read()

    import base64
    og = base64.b64encode(vid).decode()
    import nucy
    SEQ = nucy.Seq(og)
    it = SEQ.start()
    cipher = base64.b64encode(next(it)).decode()
    plain = next(it).decode()
    print(og[:10], cipher[:10], plain[:10])
    return f"""
    <html>
        <head>
            <title>video testing</title>
        </head>
        <body>
            <video controls>
                <source src="data:video/webm;base64,{og}" />
            </video>
            <video controls>
                <source src="data:video/webm;base64,{cipher}" />
            </video>
            <video controls>
                <source src="data:video/webm;base64,{plain}" />
            </video>
        </body>
    </html>
    """

if __name__ == '__main__':
    print('...')
    print(add_to_ipfs('account.html'))
    app.run(debug=True, host='0.0.0.0')
