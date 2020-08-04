import os
import sys
import glob
import cv2

from utils import darknet

class AiModel():
    def __init__(self):
        self.digitList = []

        # YOLO model
        self.netMain = None
        self.metaMain = None
        self.darknet_image  = None

        # Path
        self.yoloConfig = None
        self.yoloWeight = None
        self.yoloMeta = None

        # Initial class
        self.startUp()

    def startUp(self):
        """Preload setting and model."""
        CWD_PATH = os.getcwd()
        # Get path.
        self.yoloConfig = os.path.join(CWD_PATH, 'model', 'yolov4-first_hmi.cfg')
        self.yoloWeight = os.path.join(CWD_PATH, 'model', 'yolov4-first_hmi_best.weights')
        self.yoloMeta = os.path.join(CWD_PATH, 'model', 'first_hmi.data')

        # Load model
        self.netMain, self.metaMain, self.darknet_image = self.get_yolo_model(
            self.yoloConfig, self.yoloWeight, self.yoloMeta)

    def get_yolo_model(self, configPath, weightPath, metaPath):
        """Get yolo model."""
        # Exceptions handling: path exist
        if not os.path.exists(configPath):
            raise ValueError("Invalid config path `" +
                            os.path.abspath(configPath) + "`")
        if not os.path.exists(weightPath):
            raise ValueError("Invalid weight path `" +
                            os.path.abspath(weightPath)+"`")
        if not os.path.exists(metaPath):
            raise ValueError("Invalid data file path `" +
                            os.path.abspath(metaPath)+"`")

        # Load YOLO model & class names on first run.\
        self.netMain = darknet.load_net_custom(configPath.encode(
            "ascii"), weightPath.encode("ascii"), 0, 1)  # batch size = 1
        self.metaMain = darknet.load_meta(metaPath.encode("ascii"))

        # Create an image of darknet.
        self.darknet_image = darknet.make_image(darknet.network_width(self.netMain), 
            darknet.network_height(self.netMain), 3)
        return self.netMain, self.metaMain, self.darknet_image

    def convert_to_num(self, detections, isDebug=False):
        """Convert list to number."""
        isNegative = False
        num = 0.0
        category_list = [cate[0] for cate in detections]
        
        # Calculate how many ditigs in this image.
        digit = len(category_list) - 1
        if b'10' in category_list:
            digit = category_list.index(b'10') - 1
            category_list.remove(b'10')
        if b'11' in category_list:
            category_list.remove(b'11')
            digit -= 1
            isNegative = True
        
        # Calculate number.
        for category in category_list:
            if (category != b'10') or (category != b'11'):
                num += int(category) * 10 ** digit
                digit -= 1

        if isDebug:
            print('Number: {}'.format(num))
            for detection in detections:
                print('Class: {:2d}  Score:{:.4f} || '.format(
                    int(detection[0]), detection[1]), end='')
            print('\n')
        return num

    def convertBack(self, x, y, w, h):
        """Convert back to the original coordinates of cv2.rectangle."""
        xmin = int(round(x - (w / 2)))
        xmax = int(round(x + (w / 2)))
        ymin = int(round(y - (h / 2)))
        ymax = int(round(y + (h / 2)))
        return xmin, ymin, xmax, ymax

    def cvDrawBoxes(self, detections, img):
        """Draw bbox on the image."""
        for detection in detections:
            x, y, w, h = detection[2][0],\
                detection[2][1],\
                detection[2][2],\
                detection[2][3]
            xmin, ymin, xmax, ymax = self.convertBack(
                float(x), float(y), float(w), float(h))
            pt1 = (xmin, ymin)
            pt2 = (xmax, ymax)
            cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
            cv2.putText(img,
                        detection[0].decode() +
                        " [" + str(round(detection[1] * 100, 2)) + "]",
                        (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        [0, 255, 0], 2)
        return img

    def detectImages(self, imgList, isDebug=False):
        """Detect image from image list."""
        for img in imgList:
            # Resize image before YOLO.
            resized_img = cv2.resize(img, 
                (darknet.network_width(self.netMain), 
                darknet.network_height(self.netMain)), 
                interpolation=cv2.INTER_LINEAR)
            
            # Convert to the type of darknet image.
            darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

            # Detect bbox
            detections = darknet.detect_image(
                self.netMain, self.metaMain, self.darknet_image, thresh=0.25)
            detections.sort(key=lambda x: x[2][0])  # sorted by X axis

            # Convert detected list to number.
            num = self.convert_to_num(detections, isDebug)
            self.digitList.append(num)

            if isDebug:
                outputImg = self.cvDrawBoxes(detections, resized_img)
                cv2.nameWindow('Debug', cv2.WINDOW_NORMAL)
                cv2.imshow('Debug', outputImg)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        return self.digitList

    def detectImage(self, img, isDebug=False):
        """Detect image from single image."""
        # Resize image before YOLO.
        resized_img = cv2.resize(img, 
            (darknet.network_width(self.netMain), 
            darknet.network_height(self.netMain)), 
            interpolation=cv2.INTER_LINEAR)

        # Convert to the type of darknet image.
        darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

        # Detect bbox
        detections = darknet.detect_image(self.netMain, self.metaMain, 
            self.darknet_image, thresh=0.25)
        detections.sort(key=lambda x: x[2][0])  # sorted by X axis

        # Convert detected list to number.
        num = self.convert_to_num(detections, isDebug)
        # self.digitList.append(num)

        if isDebug:
            outputImg = self.cvDrawBoxes(detections, resized_img)
            cv2.namedWindow('Debug', cv2.WINDOW_NORMAL)
            cv2.imshow('Debug', outputImg)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return num