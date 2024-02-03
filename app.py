from flask import Flask, render_template, request, jsonify
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from PIL import Image
import io

app = Flask(__name__)

model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

max_length = 20
num_beams = 8
gen_kwargs = {"max_length": max_length, "num_beams": num_beams}

def predict_step(image):
    try:
        i_image = Image.open(io.BytesIO(image))
        if i_image.mode != "RGB":
            i_image = i_image.convert(mode="RGB")

        pixel_values = feature_extractor(images=i_image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)

        # Create an attention mask to handle padding
        attention_mask = torch.ones(pixel_values.shape[:2], device=device)

        output_ids = model.generate(pixel_values, attention_mask=attention_mask, **gen_kwargs)
        preds = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]

        return preds
    except Exception as e:
        print("Error processing image:", e)
        return None

@app.route('/')
@app.route('/home')
def intro():
    return render_template('intro.html')

@app.route('/index')
def index():
    return render_template('layout.html')


@app.route('/imageInput')
def imageInput():
    return render_template('imageInput.html')

@app.route('/imgLinkInput')
def button2():
    return render_template('imgLinkInput.html')

@app.route('/videoInput')
def button3():
    return render_template('videoInput.html')


@app.route('/generate_description', methods=['POST'])
def generate_description():
    try:
        # Ensure 'image' is present in the request files
        if 'image' not in request.files:
            raise ValueError("No image file provided")

        image_data = request.files['image'].read()
        description = predict_step(image_data)

        if description is not None:
            return jsonify({'description': description})
        else:
            return jsonify({'error': 'Failed to generate description'})
    except Exception as e:
        print("Error in generate_description:", e)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)