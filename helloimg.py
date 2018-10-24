import cv2

image = cv2.imread("MyImage.png")

if image is not None :
    cv2.imshow("image", image)
    cv2.waitKey()

else :
    print("Empty image")