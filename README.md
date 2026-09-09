# CapstoneFinalProject
I made a demo of a delivery robot that delivers supplies to teachers around school. To simplify, I made a line-tracking car with a camera that scans the qr codes that are lined up on the track  which links to a website online that tracks the requested materials of teachers.

## Our Car
We used a car chassis with an arduino board to control the motors and move the car. I also installed a raspberry pi 3B+ with a connected camera module to handle QR code scanning and line-tracking. The line-tracking was conducted by extracting each pixel of every frame and assigning it either a black or a white pixel (thresholding). I then calculated moments to decide which direction the robot should move in (info found here: https://dev.to/jeffliulab/following-line-based-on-centroid-detection-1430).

## Website
This was handled by my friend, here was his description: "Our website is what handles all requests. We used supabase to database every request and connect them to a QR code which redirects the PI to a page with quickly accessible text. We also hosted the website on a free service so that the QR codes would work. We used Gemini Ai to make the UI look better and improve the functionality."
