try:
    from multiprocessing import Process, Queue, Pipe
    import numpy as np
    import signal
    import cv2
    import time
    import os
    from mss import mss
except ImportError as e:
    print("[+] Some required modules were not found.")
    print("[+] Installing required modules with pip")
    os.system("pip install -r requirements.txt")
    print("[+] Required modules were installed.\n")
    print("[+] Restarting the program")
    os.system("python3 scope.py")


def get_screen_size():
    with mss() as sct:
        monitor = sct.monitors[1]
        return monitor['width'], monitor['height']


def grab_screen_region(region, frame_queue):
    sct = mss()
    while True:
        sct_img = sct.grab(region)
        img = np.array(sct_img)
        if(frame_queue.qsize() < 60):
            frame_queue.put(img)


def display_img(frame_queue, Connection_1, Connection_2):
    fps = 0
    prev_frame_time = 0
    new_frame_time = 0
    Pid1 = Connection_1.recv()
    Pid2 = Connection_2.recv()
    print("[+] Frame Grab Process ID:".ljust(37), Pid1)
    print("[+] Frame Queue Counter Process ID:".ljust(37), Pid2)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # out = cv2.VideoWriter('output.avi', fourcc, 60.0, (zoomed_width, zoomed_width))
    while True:
        new_frame_time = time.time()
        sct_img = frame_queue.get()
        sct_img = cv2.resize(sct_img, (zoomed_width, zoomed_width))
        cv2.circle(sct_img, (scope_width, scope_width),
                   int(scope_width/15), color, thickness)
        sct_img = cv2.putText(sct_img, "FPS: "+str(fps), origin, font,
                              fontScale, color, thickness, cv2.LINE_AA)
        cv2.imshow('CS:GO Scope', sct_img)
        # im = np.flip(sct_img[:, :, :3], 2)  # 1
        # im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        # out.write(im)
        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            cv2.destroyAllWindows()
            # out.release()
            os.kill(Pid1, 9)
            os.kill(Pid2, 9)
            return
        fps = int(1/(new_frame_time-prev_frame_time))
        prev_frame_time = new_frame_time


def frame_queue_size(frame_queue):
    while True:
        frames_in_queue = frame_queue.qsize()
        print("[+] Frames in Queue:".ljust(37), frames_in_queue, end="\r")
        time.sleep(1)


screen_width, screen_height = get_screen_size()
scope_width = 300
zoom_factor = 2
zoomed_width = scope_width * zoom_factor
horizontal_mid = int((screen_width-scope_width)/2)
vertical_mid = int((screen_height-scope_width)/2)
bounding_box = {'top': vertical_mid,
                'left': horizontal_mid, 'width': scope_width, 'height': scope_width}
color = (0, 255, 0)
thickness = 1
origin = (5, 26)
fontScale = 0.6
font = cv2.FONT_HERSHEY_SIMPLEX
frame_queue = Queue()

if __name__ == '__main__':
    Connection_1, Connection_2 = Pipe()
    print("[+] Starting Program".ljust(37))
    print("[+] Press 'q' to quit".ljust(37))
    print("[+] Screen Resolution:".ljust(37), screen_width, "x", screen_width)
    grab_process = Process(target=grab_screen_region, args=(
        bounding_box, frame_queue,))
    frame_queue_process = Process(target=frame_queue_size, args=(frame_queue,))
    grab_process.start()
    frame_queue_process.start()
    Connection_1.send(grab_process.pid)
    Connection_2.send(frame_queue_process.pid)
    display_process = Process(target=display_img, args=(
        frame_queue,  Connection_1, Connection_2,))
    display_process.start()
    grab_process.join()
    display_process.join()
    frame_queue_process.join()
    print("[+] Program Terminated".ljust(37))
