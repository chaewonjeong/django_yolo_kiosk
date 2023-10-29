from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators import gzip
from django.http import StreamingHttpResponse, HttpResponseServerError
import cv2
import threading


def home(request):
    context = {}
    return render(request, "home.html", context)
@gzip.gzip_page
def live_cam(request):
    try:
        cam =VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type='multipart/x-mixed-replace;boundary=frame')
    except HttpResponseServerError:
        print("error")
        pass
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n\r\n')





def start_detect(request):
    data = {'message': '뷰가 실행되었습니다.'}
    return JsonResponse(data)



def result(request):
    context = {
    }
    return render(request, "result.html", context)