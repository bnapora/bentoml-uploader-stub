import numpy as np
from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
from pathlib import Path

import bentoml
from bentoml.io import NumpyNdarray, Image, Multipart, JSON, Text, File

from PIL.Image import Image as PILImage

from bentoml_extensions.io_descriptors.wsi_file import WSIFile

bento_model = bentoml.sklearn.get("iris_clf:latest")
iris_clf_runner = bento_model.to_runner()

svc = bentoml.Service("image_upload_test", runners=[iris_clf_runner])




@svc.api(input=Image(), output=JSON())
def save_image(f: PILImage): #
    # image_name = image.name if image.name.strip() != "" else "Image.tiff"
    image_name = 'Test.' + f.format

    save_folder = Path(f"./tmp/save_image/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/{datetime.now().microsecond}")
    save_folder.mkdir(parents=True, exist_ok=True)
   
    image_path = save_folder / image_name
    f.save(image_path)
        
    return {'method':'save_image'}

@svc.api(input=Multipart(image=WSIFile(), meta=JSON()), output=JSON())
def save_wsi(image, meta:JSON):
    image_name = image.name if image.name.strip() != "" else "Image.tiff"

    save_folder = Path(f"./tmp/save_wsi/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/{datetime.now().microsecond}")
    save_folder.mkdir(parents=True, exist_ok=True)
   
    image_path = save_folder / image_name
    with open(str(image_path), "wb") as outfile:
        outfile.write(image._wrapped._file.raw.readall())
        
    return {'method':'save_wsi'}

flask_app = Flask(__name__)
svc.mount_wsgi_app(flask_app)


@flask_app.route("/metadata")
def metadata():
    return {"name": bento_model.tag.name, "version": bento_model.tag.version}


# For demo purpose, here's an identical inference endpoint implemented via FastAPI
@flask_app.route("/predict_flask", methods=["POST"])
def predict():
    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        input_arr = np.array(request.json, dtype=float)
        return jsonify(iris_clf_runner.predict.run(input_arr).tolist())
    else:
        return "Content-Type not supported!"
