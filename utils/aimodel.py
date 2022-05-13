import os
import sys
import glob
import cv2

from utils import darknet

class AiModel():
    def __init__(self, config, weight, meta):
        self.digitList = []

        # YOLO model
        self.network = None
        self.class_names = None
        self.darknet_image  = None
        self.model_size = None

        # Path
        self.yoloConfig = None
        self.yoloWeight = None
        self.yoloMeta = None

        # Initial class
        self.startUp(config, weight, meta)

    def startUp(self, config, weight, meta):
        """Preload setting and model."""
        CWD_PATH = os.getcwd()
        self.yoloConfig = config
        self.yoloWeight = weight
        self.yoloMeta = meta

        # Load model
        self.network, self.class_names, self.darknet_image = self.get_yolo_model(
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
        self.network, self.class_names, class_colors = darknet.load_network(configPath,  metaPath, weightPath, batch_size=1)
        # self.network = darknet.load_net_custom(configPath.encode(
        #     "ascii"), weightPath.encode("ascii"), 0, 1)  # batch size = 1
        # self.class_names = darknet.load_meta(metaPath.encode("ascii"))

        # Create an image of darknet.
        self.model_size = (
            darknet.network_width(self.network), 
            darknet.network_height(self.network)
        )
        self.darknet_image = darknet.make_image(darknet.network_width(self.network), 
            darknet.network_height(self.network), 3)
        return self.network, self.class_names, self.darknet_image

    def convert_to_num(self, detections, isDebug=False):
        """Convert list to number."""
        isNegative = False
        num = 0.0
        category_list = [cate[0] for cate in detections]
        
        # Calculate how many ditigs in this image.
        digit = len(category_list) - 1
        if '10' in category_list:
            digit = category_list.index('10') - 1
            category_list.remove('10')
        if '11' in category_list:
            category_list.remove('11')
            digit -= 1
            isNegative = True
        
        # Calculate number.
        for category in category_list:
            if (category != '10') or (category != '11'):
                num += int(category) * 10 ** digit
                digit -= 1

        if isDebug:
            print('Number: {}'.format(num))
            for detection in detections:
                print('Class: {:2d}  Score:{:.4f} || '.format(
                    int(detection[0]), float(detection[1])), end='')
            print('\n')
        return round(num, 3)

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
                        detection[0] +
                        " [" + str(round(float(detection[1]), 2)) + "]",
                        (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        [0, 255, 0], 2)
        return img

    def detectROI(self, imgList, isDebug=False):
        """Detect ROI from HMI."""
        detections = []
        for img in imgList:
            # Resize image before YOLO.
            resized_img = cv2.resize(img, 
                (darknet.network_width(self.network), 
                darknet.network_height(self.network)), 
                interpolation=cv2.INTER_LINEAR)
            
            # Convert to the type of darknet image.
            darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

            # Detect bbox
            detections = darknet.detect_image(self.network, self.class_names, self.darknet_image, thresh=0.5)
            # sort by x -> y.
            # detections.sort(key=lambda x: x[2][1])  # sorted by Y axis
            # detections = self.sortCoordinate(detections, darknet.network_width(self.network), darknet.network_height(self.network))

            if isDebug:
                outputImg = self.cvDrawBoxes(detections, resized_img)
                cv2.namedWindow('Debug', cv2.WINDOW_NORMAL)
                cv2.imshow('Debug', outputImg)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        return detections
    
    def detectDigit(self, img, isDebug=False):
        """Detect digit."""
        # Resize image before YOLO.
        resized_img = cv2.resize(img, 
            (darknet.network_width(self.network), 
            darknet.network_height(self.network)), 
            interpolation=cv2.INTER_LINEAR)
        
        # Convert to the type of darknet image.
        darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

        # Detect bbox
        detections = darknet.detect_image(self.network, self.class_names, self.darknet_image, thresh=0.7)
        # detections = darknet.detect_image(
        #     self.network, self.class_names, self.darknet_image, thresh=0.7)
        detections.sort(key=lambda x: x[2][0])  # sorted by X axis

        # Convert detected list to number.
        num = self.convert_to_num(detections, isDebug)

        if isDebug:
            print('Num: {}'.format(num))
            outputImg = self.cvDrawBoxes(detections, resized_img)
            cv2.namedWindow('Debug', cv2.WINDOW_NORMAL)
            cv2.imshow('Debug', outputImg)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return num

    def detectImages(self, imgList, isDebug=False):
        """Detect image from image list."""
        for img in imgList:
            # Resize image before YOLO.
            resized_img = cv2.resize(img, 
                (darknet.network_width(self.network), 
                darknet.network_height(self.network)), 
                interpolation=cv2.INTER_LINEAR)
            
            # Convert to the type of darknet image.
            darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

            # Detect bbox
            detections = darknet.detect_image(
                self.network, self.class_names, self.darknet_image, thresh=0.25)
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
            (darknet.network_width(self.network), 
            darknet.network_height(self.network)), 
            interpolation=cv2.INTER_LINEAR)

        # Convert to the type of darknet image.
        darknet.copy_image_from_bytes(self.darknet_image, resized_img.tobytes())

        # Detect bbox
        detections = darknet.detect_image(self.network, self.class_names, 
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

    def sortCoordinate(self, detections, width, height):
        sortList = []
        unSortList = [detections[0]]     # Append first list.

        for index in range(1, len(detections)):
            # Get diff of y
            diffY = detections[index][2][1] - detections[index - 1][2][1]

            if diffY < 10:
                # Append to unSortList
                unSortList.append(detections[index])
            else:
                # Sort unSortList by x then extend to sortList.
                unSortList.sort(key=lambda k: k[2][0])
                sortList.extend(unSortList)
                unSortList = [detections[index]]

                # Append last list
                if index == len(detections) - 1:
                    sortList.append(detections[index])
        return sortList
