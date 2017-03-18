#!/usr/bin/env python
from error_calc import *
from auto_master import *
from threading import Thread
from threading import Timer
import rospy
from math import sqrt
import time

def getDistance_((x1,y1),(x2,y2)):
    dx = x2-x1
    dy = y2-y1
    return sqrt(dx**2 + dy**2)

class ErrorSmoothie:
    def __init__(self, automaster):
        self.am = automaster
        
        self.reset()
        
        
    def reset(self):
        self.current_camera = -1
        self.switch_camera_to = True
        
        self.one_tag_cc = False
        
        self.last_front_point_nc = None
        self.last_front_point_cc = None
        
        self.last_error = 0
        
        self.error_diff = 0
    
    def errorSmooth(self):
        
        iterations = (SMOOTHING_TIME/SMOOTHING_DT)
        de = self.error_diff / iterations
        
        for i in range(int(iterations)):
            self.error_diff -= de
            time.sleep(SMOOTHING_DT)
        self.error_diff = 0
        
    def setSwitchCameraTO(self):
        print "sup"
        self.switch_camera_to = True
    
        
    def gvPositionsHandler(self, data):
        print "---"
        print "got pos"
        p1 = (data.p1.x, data.p1.y)
        p2 = (data.p2.x, data.p2.y)
        tagid1 = data.tagid1
        tagid2 = data.tagid2
        cameraid = data.cameraid
        
        
        if self.current_camera == -1:
            print "first camera"
            self.current_camera = cameraid
        
        
        if self.current_camera == cameraid:
            print "current camera"
            
            if p2 == (0,0) and tagid2 == 0: #one tag
                print "one tag"
                
                if tagid1 == 1: #only back tag
                    print "only back tag"
                    #maybe use normal error here
                    self.one_tag_cc = True
                
                else: # only front tag
                    print "only front tag"
                    if self.last_front_point_cc == None or getDistance_(p1, self.last_front_point_cc) < 2:
                        if self.last_front_point_cc == None:
                            print "no last front point cc"
                        else:
                            print "last fron tpoint too close"
                        la = p1
                    else:
                        print "getting direction from last front point"
                        d = getDirection(self.last_front_point_cc, p1)
                        self.am.latest_direction = d
                        la = getLookAheadPoint(p1,d,LOOKAHEAD)
                    
                    error, dist = self.am.error_calc.calculateError(la)
                    print "error no smooth", error
                    self.last_error = error
                    error = error - self.error_diff
                    
                    
                    self.last_front_point_cc = p1
                    
                    
                    self.am.latest_point = p1
                    self.am.latest_position_update = rospy.get_time()
                    print "dist", dist
                    print "processed error", error
                    self.am.processError(error, dist)
                    
                    
            
            else: #two tags
                print "two tags"
                
                if tagid1 !=1:
                    tp = p1
                    p1 = p2
                    p2 = tp
                
                direction = getDirection(p1,p2)
                lookAheadPoint = getLookAheadPoint(p2, direction, LOOKAHEAD)
                
                error,dist = self.am.error_calc.calculateError(lookAheadPoint)
                self.last_error = error
                
                print "error, no smooth", error
                
                error = error - self.error_diff
                
                self.latest_front_point_cc = p2
                
                self.am.latest_point = p2
                self.am.latest_direction = direction
                self.am.latest_position_update = rospy.get_time()
                
                print "dist", dist
                print "processed error", error
                self.am.processError(error, dist)
        
        else:
            print "new camera"
            if not self.switch_camera_to: #just switched cameras, old camera not interesting
                print "cant switch camera yet bro"
                return
            
            if p2 == (0,0) and tagid2 == 0: #one tag
                print "one tag"
                if tagid1 == 1: #only back tag
                    print "only back tag"
                    pass
                else: #only front tag
                    print "only front tag"
                    if self.one_tag_cc:
                        print "self.one_tag_cc = true"
                        print "switching to camera " + str(cameraid)
                        if self.last_front_point_nc == None or getDistance_(self.last_front_point_nc, p1) < 2:
                            if self.last_front_point_nc == None:
                                print "no last front point nc"
                            else:
                                print "last front point too close"
                            la = p1
                        else:
                            print "getting dir from last front point, nc"
                            dd = getDirection(self.last_front_point_nc, p1)
                            self.am.latest_direction = dd
                            la = getLookAheadPoint(p1, dd, LOOKAHEAD)
                        
                        
                        error, dist = self.am.error_calc.calculateError(la)
                        
                        print "new error", error
                        self.error_diff = error - self.last_error
                        print "error_diff", self.error_diff
                        self.last_error = error
                        
                        
                        self.current_camera = cameraid
                        
                        self.last_front_point_cc = p1
                        self.last_front_point_nc = None
                        self.one_tag_cc = False
                        
                        self.switch_camera_to = False
                        
                        
                        Thread(target = self.errorSmooth).start()
                        Timer(10.0, self.setSwitchCameraTO).start()
                        #start 2 timers/threads
                        
                        self.am.latest_point = p1
                        self.am.latest_position_update = rospy.get_time()
                        
                        
                        error = error - self.error_diff
                        
                        print "dist", dist
                        print "processed error", error
                        self.am.processError(error, dist)
                        
                    else:
                        print "self.one_tag_cc = false"
                        self.last_front_point_nc = p1
                        
                    
            else: #two tags
                
                
                print "two tags"
                
                print "switching to camera " + str(cameraid)
                if tagid1 !=1:
                    tp = p1
                    p1 = p2
                    p2 = tp
                
                direction = getDirection(p1,p2)
                lookAheadPoint = getLookAheadPoint(p2, direction, LOOKAHEAD)
                
                error,dist = self.am.error_calc.calculateError(lookAheadPoint)
                
                
                print "new error", error
                
                self.error_diff = error - self.last_error
                
                print "error_diff", self.error_diff
                
                self.current_camera = cameraid
                
                self.last_front_point_cc = p2
                self.last_fron_point_nc = None
                self.one_tag_cc = False
                
                self.switch_camera_to = False
                
                
                Thread(target = self.errorSmooth).start()
                Timer(10.0, self.setSwitchCameraTO).start()
                
                self.am.latest_point = p2
                self.am.latest_direction = direction
                self.am.latest_position_update = rospy.get_time()
                
                
                error = error - self.error_diff
                
                print "processed error", error
                self.am.processError(error, dist)
                
                
            
                    
