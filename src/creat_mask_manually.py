import cv2
import numpy as np
from shapely.geometry import Polygon, Point
import os

# a list of points that will be used to create the mask
points = []

def create_mask(image_path):
    image = cv2.imread(image_path) 
    original_width = image.shape[1] # save the original width of the image
    image = resized_image(image, 1080) # resize the image to a width of 1080 because the original image is too big for my screen
    
    cv2.imshow("image", image)
    # mouse_callback function will be called when the user clicks on the image
    cv2.setMouseCallback("image", mouse_callback)
    cv2.waitKey(0)

    mask = create_mask_from_points(points, image.shape[:2]) 
    mask = resized_image(mask, original_width)
    points.clear()

    return mask

def create_mask_from_points(points, image_size):
    # create a polygon from the points
    polygon = Polygon(points)
    mask = np.zeros(image_size, dtype=np.uint8)

    for y in range(image_size[1]):
        for x in range(image_size[0]):
            if polygon.contains(Point(x, y)):
                mask[y, x] = 1
    return mask
    
# this function will be called when the user clicks on the image
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(points)

def resized_image(image,desired_width):
    aspect_ratio = image.shape[1] / image.shape[0]
    desired_height = int(desired_width / aspect_ratio)
    resized_image = cv2.resize(image, (desired_width, desired_height))
    return resized_image


if __name__ == "__main__":
    directory_path = 'C:/Users/avish/OneDrive/Desktop/data_set4/Sets/Set_0/images'
    save_path = f"{directory_path}/masks"
    save_path_see = f"{directory_path}/masks_see"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    if not os.path.exists(save_path_see):
        os.makedirs(save_path_see)
    counter = 0
    for file in os.listdir(directory_path):
        if file.endswith(".png") or file.endswith(".jpg"):
            counter += 1
            image_path = os.path.join(directory_path, file)
            file_number = os.path.splitext(file)[0].replace("image", "")
            mask = create_mask(image_path)
            cv2.imwrite(os.path.join(save_path, f"mask{file_number}.png"), mask)
            cv2.imwrite(os.path.join(save_path_see, f"mask{file_number}.png"), mask*255)
            print("mask saved for image", file_number)
    
    
    