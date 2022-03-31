# People finding security camera system

## what it is
I already had a few IP cameras around the house and covering our backyard.  I also ran motion software to only record events that may be of interest.  This worked fine for indoors, but outdoors was a real problem.  We live in an area with lots of wildlife, and wind, both of which would cause motion detection to trigger.  This meant that there was lots of footage recorded, but too much of it had no real interest, which also meant it never got watched.  

## Idea
I already had a linux server running for other purposes, so it made sense to make the system a little smarter.  This idea runs off three docker containers.  The first aggregates all the video sources and checks for motion.  This sends video frames with a tag indicating if motion exists between frames.  The recognition engine will not run unless the input image is tagged with motion, which saves a lot of energy.  

The second container is running a recognition engine, this was trivial to set up with cvlib.  Performance was decent for this purpose anyways.  The server running this had a GTX 1080 which could process up to 24 full HD frames per second with the YOLO CNN algorithm.  For five cameras this means each is checked four times per second at least, so that works fine.  

The last container is a recorder.  This keeps a buffer of thirty seconds so that when a recognition event occurs we also have a record of the moments leading up to the observation.  

Lastly, there are also optional desktop apps which tie into the system and display video feeds, or act as alarms.  These are implemented in PyQt and don't require a dockerized container and GPU.  They are very simply implemented, with a QLabel acting as a display device.  This is very basic, but it worked.  

## Facial recognition
For the first implementation I had planned to use facial recognition to disarm the system.  This was also very easy to set up with python's facial recognition module.  This actually worked, but having both algorithms work from the same cameras was a problem.  the detection was very efficient, even at a distance.  Facial recognition didn't work well unless the target was very close to the camera.  This meant that disarming the system required either a lengthy walk, or more cameras placed in more strategic locations.  At the time I didn't want either of these, so this idea needs work.  

