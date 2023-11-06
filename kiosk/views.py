import uuid
import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators import gzip
from django.http import StreamingHttpResponse, HttpResponseServerError
from django.conf import settings
import cv2
import numpy as np
import base64
import threading
from django.core.cache import cache
import ultralytics
from ultralytics import YOLO
from .models import Product

from uuid import uuid4
from django.utils import timezone




def home(request):
    context = {}
    return render(request, "home.html", context)
@gzip.gzip_page
def live_cam(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type='multipart/x-mixed-replace;boundary=frame')
    except HttpResponseServerError:
        print("error")
        pass
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        if image is not None:
            _, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()
        else:
            return None

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n\r\n')



def load_yolo():
    model = cache.get("cached_model")

    if model is None:
        try:
            model = YOLO('/Users/jeongchaewon/workspace_local/Dev/django_yolo_kiosk/kiosk/static/models/best.pt')
            cache.set("cached_model", model)
        except Exception as e:
            return None
    return model

def save_image(image_data, file_path):
    with open(file_path, 'wb') as f:
        f.write(image_data)


def make_result_images(results):
    for r in results:
        image = r.plot()
        _, jpeg = cv2.imencode('.jpg', image)
        jpeg = jpeg.tobytes()
        result_img = base64.b64encode(jpeg).decode('utf-8')
        return result_img

def make_cropped_images(results, uuid):
    result = results

    folder_path = '/Users/jeongchaewon/workspace_local/Dev/django_yolo_kiosk/media/result'
    path = os.path.join(folder_path, uuid)

    for r in result:
        r.save_crop(path)

    # subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    class_folders = [f.name for f in os.scandir(path) if f.is_dir()]
    result_dict = {}


    for class_folder in class_folders:
        class_name = class_folder
        class_path = os.path.join(path, class_folder)
        class_images = []

        for filename in os.listdir(class_path):
            if filename.endswith('.jpg'):
                crp_img_path = os.path.join(class_path, filename)
                crp_img = cv2.imread(crp_img_path, cv2.IMREAD_COLOR)
                _, jpeg = cv2.imencode('.jpg', crp_img)
                jpeg = jpeg.tobytes()
                cropped_img = base64.b64encode(jpeg).decode('utf-8')
                class_images.append(cropped_img)
        result_dict[class_name] = class_images
        print(class_name)

    return result_dict


def get_price(result_dict):
    return_dict = {}

    for class_name in result_dict.keys():
        products = Product.objects.filter(class_id=class_name)
        for product in products:
            product_info = {"product_name": product.name, "price": product.price}
            return_dict[class_name] = product_info
    return return_dict

# start_detect 함수 수정
def start_detect(request):
    cam = VideoCamera()
    frame = cam.get_frame()
    new_uuid = str(uuid.uuid4())

    folder_path = os.path.join(settings.MEDIA_ROOT, 'result', new_uuid)
    os.makedirs(folder_path)

    if frame is not None:
        image = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)

        image_file_path = "/Users/jeongchaewon/workspace_local/Dev/django_yolo_kiosk/media/tmp/captured_image.jpg"
        cv2.imwrite(image_file_path, image)

        model = load_yolo()
        results = model(image_file_path)

        # result를 받아 값을 반환하는 각종 처리함수
        result_img = make_result_images(results)
        result_crop_imgs = make_cropped_images(results, new_uuid)
        name_and_price = get_price(result_crop_imgs)

        # TODO
        # result_crop_imgs의 딕셔너리값을 받아와서 다음 모델에 넘겨서 소분류까지 진행

        #TODO
        #크롭된 객체들을 데이터베이스에서 찾아서 가격 책정
        # price = {}
        # price = get_price(result_crop_imgs)





        captured_img = base64.b64encode(frame).decode('utf-8')
        context = {"captured_img": captured_img, "yolo_result": results, 'result_img': result_img, 'result_crop_imgs': result_crop_imgs, 'name_and_price': name_and_price}
        return render(request, "result.html", context)
    else:
        # 프레임이 None이면 오류 페이지를 반환하거나 다른 처리를 수행할 수 있음
        return HttpResponseServerError("프레임을 캡처할 수 없습니다.")






def result(request):
    context = {
    }
    return render(request, "result.html", context)