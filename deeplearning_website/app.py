from flask import Flask,render_template,request,url_for,redirect
from werkzeug.utils import redirect, secure_filename
import os
import sqlite3
import cv2
import torch
from torchvision import transforms 

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'jpg','JPG','jpeg','JPEG'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    split = filename.split('.')
    if split[-1] in ALLOWED_EXTENSIONS:
        return True 
    return False

@app.route("/",methods=['GET','POST'])
def new_post():
    #return render_template("index.html",usernames=user_list,captions=media_list,images=image_list,my_index=numberOfPosts)
    return render_template("newpost.html")

def classify_image(image):
    prediction = animal_model(image)
    image_name = class_names[prediction.argmax().item()]
    probability = torch.exp(torch.tensor(prediction[0][0].item())) if torch.exp(torch.tensor(prediction[0][0].item())) > torch.exp(torch.tensor(prediction[0][1].item())) else torch.exp(torch.tensor(prediction[0][1].item()))
    probability = round(probability.item()*100,2)
    print('Probability ',probability)
    print('Image ',image_name)
    return (probability,image_name)

@app.route('/my_post',methods=['POST'])
def my_post():
    if request.method == 'POST':
        print(request.form.get('caption'))
        print(request.form.get('uname'))
        
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('uploaded_image',filename=filename,username=request.form.get('uname'),caption=request.form.get('caption')))
    return 'hello'

# Transformation to be done on image
test_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406],std=[0.229,0.224,0.225])
])

# Class names
class_names = ['Cat','Dog']
# Loading in model
device = torch.device("cpu")
animal_model = torch.jit.load('cat_dog_torchScript_model.pt').to(device)

@app.route('/uploads/<filename>/<username>/<caption>')
def uploaded_image(filename,username,caption):
    # Read in image
    image = cv2.imread('static/'+filename)
    img_saved = image.copy()
    # Resizing
    image = cv2.resize(image,(224,224))
    # Converting to RGB
    image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

    # Convert OpenCV image to pytorch to tensor format. Transform image and reshape for model
    image = test_transform(image)
    image = image.view(1,3,224,224)

    # Classifying image
    prob,image_name = classify_image(image)

    os.remove('static/'+filename)

    # insert into sql cat or dog table
    with sqlite3.connect('socialMedia.db') as conn:
        c = conn.cursor()
        if image_name == 'Cat':
            c.execute("INSERT INTO catpics VALUES (?,?,?)",(username,filename,caption))
            cv2.imwrite(f'static/cats/{filename}',img_saved)
        else:
            c.execute("INSERT INTO dogpics VALUES (?,?,?)",(username,filename,caption))
            cv2.imwrite(f'static/dogs/{filename}',img_saved)

        conn.commit()
    conn.close()

    return render_template("newpost.html",probability=prob,animal=image_name)

@app.route("/dogs")
def dog_posts():
    # Grabbing all entries from dog table
    with sqlite3.connect('socialMedia.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM dogpics")
        dog_entries = c.fetchall()
    conn.close() 
    
    my_index = len(dog_entries)
    print(dog_entries)

    usernames = []
    images = []
    captions = []

    for i in range(len(dog_entries)):
        usernames.append(dog_entries[i][0])
        images.append('static/dogs/'+dog_entries[i][1])
        captions.append(dog_entries[i][2])

    return render_template("dogs.html",usernames=usernames,images=images,captions=captions,my_index=my_index)

@app.route("/cats")
def cat_posts():
    # Grabbing all entries from dog table
    with sqlite3.connect('socialMedia.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM catpics")
        cat_entries = c.fetchall()
    conn.close() 
    
    my_index = len(cat_entries)
    print(cat_entries)

    usernames = []
    images = []
    captions = []

    for i in range(len(cat_entries)):
        usernames.append(cat_entries[i][0])
        images.append('static/cats/'+cat_entries[i][1])
        captions.append(cat_entries[i][2])

    return render_template("cats.html",usernames=usernames,images=images,captions=captions,my_index=my_index)