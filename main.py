
class VUI:
    """
        A class for visual user interface. Recommended to use default parameters.
    """
    def __init__(self, icons_dir="icons/", window_size=(525, 700, 3), vui_part=20, max_count=15):
        """
            icons_dir: directory to use icons from.
            window_size: size of an vui window. Recommended to use equal of final window.
            vui_part: How much % of rows from top will be used to stack icons?
        
        """
        self.idir = icons_dir
        self.window = np.zeros(window_size).astype(np.uint8)
        self.size = window_size
        self.vui_part = int(vui_part/100 * self.size[0])
        self.dd_part = (self.vui_part, int(50/100 * self.size[0]))
        
        self.modes = [fname.split(".")[0] for fname in os.listdir(self.idir)]
        self.icon_size = (int(self.size[1]/len(self.modes)), self.vui_part) # c, r
        
        self.current_icons = []
        self.anim_scale = 0.5
        self.anim_color = [5, 15, 2]
        self.prev_mode = "move"
        self.current_mode = "move"
        self.running_mode = None 
        self.hover=None
        
        self.mode_count = 1
        self.max_count = max_count
        self.color_count = 1
        self.max_color = 5
        
        self.current_pointer = (100, 100)
        self.canvas_pointer = None
        
        self.draw_color = (0, 0, 255)
        self.previous_color = (0, 0, 255)
        self.current_color = (0, 0, 255)
        self.pointer_color = (100, 200, 200)
        self.point = (10, -3)
        self.colors=None
        
        self.icons = self.prepare_icons()
        self.get_window()
        
    def prepare_icons(self):
        """
            A method to prepare icons on initial frame.
            Method sets 4 new attributes.
            cols: List to store (y1, y2) of icon.
            icon_position: Dictionary to store (y1, y2) as key and corresponding image as value
            current_icons: A dictionary initialized with initial icons. Changed on every frame when cursor lies above it.
            mode_pos: Mode as key and its icon's (y1, y2) as value.
        """
        icons = []
        cols = np.linspace(0, self.size[1]-1, len(self.modes)+1).astype(np.int64)
        cols = [(cols[i], cols[i+1]) for i in range(len(cols)-1)]
        
        icon_pos = {}
        mode_pos = {}
        for i, image_name in enumerate(os.listdir(self.idir)):
            img = cv2.imread(self.idir+image_name)
            img = cv2.resize(img, (cols[i][1]-cols[i][0], self.vui_part))
            icon_pos[cols[i]] = img
            mode_pos[self.modes[i]] = cols[i]
        self.cols = cols   
        self.icon_position = icon_pos
        self.current_icons = icon_pos
        self.mode_pos = mode_pos
        
    def set_colors(self, col=None, new_colors=None):
        """
            A method to set colors when pointer lies above color icon.
            Initially used subset of {Red, Green, Blue}
            col:- column where current pointer lies.
            new_colors:- If to use other colors.
            
            Method returns list of available colors on dropdown menu. 
            Changes the draw color, pointer color upon condition meet.
        """
        # earlier pointer was clipped within the vui
        pointer = self.canvas_pointer
        pointer = (pointer[1], self.vui_part+ pointer[0])
        if new_colors is None:
            r = np.array([0, 0, 255])
            g = np.array([0, 255, 0])
            b = np.array([255, 0, 0])
            colors = [r, g, b]
            colors_new = [colors[i]+colors[i+1] for i in range(len(colors)-1)]
            colors.extend(colors_new)
            self.colors = colors
        else:
            self.colors = new_colors
        rows = np.linspace(self.dd_part[0], self.dd_part[1], len(self.colors)+1).astype(np.int64)
        rows = [(rows[i], rows[i+1]) for i in range(len(rows)-1)]
        self.color_pos = {}
        for row, color in zip(rows, colors):
            self.color_pos[row] = color
            if row[0]<=pointer[1]<row[1] and col[0]<=pointer[0]<col[1]:
                self.current_color = (color.tolist())
                if self.current_color == self.previous_color:
                    self.color_count+=1
                else:
                    self.previous_color=self.current_color
                    self.color_count = 1
                if self.color_count>=self.max_color:
                    self.draw_color=self.current_color
                self.pointer_color = (np.abs(np.array([200, 200, 100])-color).tolist())
            self.current_window[row[0]:row[1], col[0]:col[1]] = color
        
        return self.colors  
    def get_window(self):
        """
            A method to return a VUI window upon called. Sets pointer on VUI canvas.
        """
        self.current_window = np.zeros_like(self.window).astype(np.uint8)
        for col, img in self.current_icons.items():
            self.current_window[:self.vui_part, col[0]:col[1]] = img
        if self.running_mode == "color":
            self.set_colors(col=self.cols[self.modes.index("color")])
        if self.current_pointer is not None and self.current_pointer[0]>0:
            cv2.circle(self.current_window, (self.current_pointer[1], self.current_pointer[0]), self.point[0], self.pointer_color, self.point[1])
        
        return self.current_window
    def update_vui(self, pointer=(100, 100), cpointer=(10, 100)):
        """
            A method to update the entire VUI properties and state.
            pointer: Current pointer on VUI part.
            cpointer: Current pointer on Canvas.
            
            cpointer is useful when working with color mode.
        """
        self.current_pointer = pointer
        self.canvas_pointer = cpointer
        #print(pointer, canvas_pointer)
        current_icons = {}
        self.hover=None
        if pointer[0]<=self.vui_part:
            for col, mode in zip(self.cols, self.modes):
                icon = self.icon_position[col].copy()
                ishape = icon.shape
                
                #print(mode)
                if col[0]<pointer[1]<=col[1]:
                    # pointer is above this icon now animate it.
                    self.current_mode = mode
                    zeros_icon = np.zeros_like(icon).astype(np.uint8)
                    
                    f = self.anim_scale*self.mode_count
                    r = int(ishape[0] * f)
                    c = int(ishape[1] * f)
                    icon = cv2.resize(icon, (c, r))
                    if f > 1:
                        rd = int((r - ishape[0])/2)
                        cd = int((c - ishape[1])/2)
                        
                        zeros_icon[:, :] = icon[rd:ishape[0]+rd, cd:ishape[1]+cd] 
                    else:
                        rd = int((ishape[0] - r)/2)
                        cd = int((ishape[1] - c)/2)
                        rdd, cdd = 0, 0
                        if ishape[0]-rd-rd > r:
                            rdd=1
                        if ishape[1]-cd-cd > c:
                            cdd=1
                        #print(icon.shape, ishape, rd, abs(r-rd), cd, abs(c-cd))
                        zeros_icon[rd:ishape[0]-rd-rdd, cd:ishape[1]-cd-cdd] = icon[::] 
                            
                    current_icons[col] = zeros_icon.astype(np.uint8) + np.uint8(np.array(self.anim_color)*self.mode_count)
                    
                    
                    if self.prev_mode == self.current_mode:
                        self.mode_count += 1
                    else:
                        self.prev_mode = self.current_mode
                        self.mode_count = 1
                    if self.mode_count >= self.max_count:
                        self.running_mode = self.current_mode
                        self.mode_count = 1
                        self.hover = True
                        
                else:
                    current_icons[col] = icon
                
            self.current_icons = current_icons
        else:
            self.mode_count = 1
                    
        return self.get_window()
                
            
        
                  
# vui = VUI()
# #show(vui.window)
# vui.update_vui()
# vui.update_vui()
# vui.update_vui(pointer=(200, 100))
# vui.update_vui(pointer=(200, 100))

class Canvas:
    def __init__(self, window_size=(525, 700, 3), draw_color=(100, 100, 100), 
                 pointer_color=(0, 0, 0), bg_color=(25, 25, 25), mode="move", 
                 point=(10, -3), vui=None, ssize=(300, 50, 3)):
        """
            A method to initialize canvas.
            window_size: size of a canvas window.
            draw_color: drawing color in RGB.
            pointer_color: pointer color in RGB.
            bg_color: background color in RGB.
            mode: running mode.
            point: tuple of (pointer radius, thickness)
            vui: VUI object.
            ssize: Slider's size.
        
        """
        self.size=window_size
        self.draw_color=draw_color
        self.pointer_color = pointer_color
        self.bg_color = bg_color
        self.window = np.zeros(self.size, dtype=np.uint8)
        self.canvas= self.window.copy()+bg_color
        self.mode = mode
        self.pointer = None
        self.point = point
        self.current_window = self.window+self.canvas
        self.vui = vui
        self.ssize = ssize
        self.sregion = ()
        
    def slider(self, size=(300, 30, 3), spoint=50, scolor=(100, 55, 100)):
        """
            A method to change the pointer size by moving a slider.
            size: size of slider region.
            spoint: slider point, generally row position of pointer.
            scolor: slider color
        """
        swidth=10
        #swidth=int(5/50*spoint)
        #swidth = np.clip(swidth, 5, spoint)
        swindow=np.zeros(self.size).astype(np.uint8)
        swindow[:self.ssize[0], 0:self.ssize[1]] += np.uint8([255, 255, 255])  
        r1 = np.clip(spoint-swidth, swidth, self.ssize[0]-swidth)
        r2 = np.clip(spoint+swidth, swidth, self.ssize[0]-swidth)
        spoint = int(10/50 * spoint)
        #print(r1, r2, spoint)
        
        
        swindow[r1:r2, :self.ssize[1]] = scolor
        self.point=(spoint, self.point[1])
        #cv2.imshow("slider", swindow.astype(np.uint8))
        return swindow.astype(np.uint8)   
    def clear(self):
        self.window = np.zeros(self.size, dtype=np.uint8)
        self.canvas= self.window.copy()+self.bg_color
    def update_window(self, mode, pointer=(400, 100)):
        """
            mode: running mode
            pointer: where is pointer now?
        """
        self.mode = mode
        self.vui.mode=mode
        self.pointer = pointer
        self.draw_color=self.vui.draw_color
        self.pointer_color = self.vui.pointer_color
        #self.pointer = (np.clip(self.vui.vui_part, pointer[0], self.size[0]), pointer[1])
        #print("c", self.draw_color)
        swindow = np.zeros(self.size).astype(np.uint8)
        #print(pointer)
        if 0<pointer[0]<self.ssize[0] and 0<pointer[1]<self.ssize[1]:
            swindow=self.slider(spoint=pointer[0])
            self.mode = "move"
            #self.pointer = (pointer[0], pointer[1]+self.ssize[1])
            #self.pointer_color = self.bg_color
        if self.mode == "draw":
            cv2.circle(self.canvas, (self.pointer[1], self.pointer[0]), self.point[0], self.draw_color, self.point[1])
            self.current_window = self.window+self.canvas+swindow
            cv2.circle(self.current_window, (self.pointer[1], self.pointer[0]), self.point[0], self.pointer_color, self.point[1])
            
        elif self.mode == "erase":
            cv2.circle(self.canvas, (self.pointer[1], self.pointer[0]), self.point[0], self.bg_color, self.point[1])
            self.current_window = self.window+self.canvas+swindow
            cv2.circle(self.current_window, (self.pointer[1], self.pointer[0]), self.point[0], self.pointer_color, self.point[1])
            
        else:
            self.current_window = self.window+self.canvas+swindow
            cv2.circle(self.current_window, (self.pointer[1], self.pointer[0]), self.point[0], self.pointer_color, self.point[1])
            
        #show(self.canvas)
        #show(self.current_window)
        return self.current_window
    
class ContourWriting:
    """
        A class to bind all other classes uses.
    """
    def __init__(self, count_mode=10, avg_frames=100, 
                 rois={"droi":[200, 400, 430, 681],
                       "mroi":[80, 10, 150, 225], 
                       "vroi":[100, 400, 200, 681]}, 
                 icons_dir="icons/", aweight=0.5):
        """
            rois: types of ROIS(draw, move, vui)
        
        """
        self.aweight = aweight
        self.avg_frames=avg_frames
        self.roi_boxes = rois
        self.roi_averages = {key:None for key in rois.keys()}
        self.roi_grays = {key:None for key in rois.keys()}
        self.roi_masks = {key:None for key in rois.keys()}
        self.roi_pointer = {key:None for key in rois.keys()}
        self.roi_counts = {key:None for key in rois.keys()}
        self.size = (525, 700)
        self.set_pointer()
        self.vui = VUI()
        self.canvas_shape = (self.size[0]-self.vui.vui_part, self.size[1], 3) 
    
        self.canvas = Canvas(window_size=self.canvas_shape, vui=self.vui, bg_color=[255, 255, 255])
        self.running_mode = self.vui.running_mode
        
        self.force_modes=None
        self.fcount_mode=count_mode
        self.fcurrent_count=0
        self.fprev_mode = "move"
        self.check_force_mode()
        
        
    def set_pointer(self):
        for rname, pointer in self.roi_pointer.items():
            top, right, bottom, left = self.roi_boxes[rname]
            self.roi_pointer[rname] = (int((left+right)/2), int((top+bottom)/2))
    def running_average(self):
        for rname, roi in self.roi_averages.items():
            gimg = self.roi_grays[rname]
            if roi is None:
                roi = gimg.copy().astype("float")
            else:
                cv2.accumulateWeighted(gimg, roi, self.aweight)
            self.roi_averages[rname] = roi
    def set_grays(self, gray_frame):
        for rname, box in self.roi_boxes.items():
            top, right, bottom, left = box
            gray_roi = gray_frame[top:bottom, right:left]
            #gray_roi = cv2.bilateralFilter(gray_roi, 9, 15, 15)
            gray_roi=cv2.GaussianBlur(gray_roi, (7, 7), 0)
            self.roi_grays[rname] = gray_roi
            
    def make_rectangles(self, clone):
        cv2.putText(clone, f"Curr. Mode: {self.running_mode}", (self.roi_boxes["vroi"][1], self.roi_boxes["vroi"][0]-20),
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)           
        # make rectangle for everything, add text on middle of it
        for rname, box in self.roi_boxes.items():
            top, right, bottom, left = box
            mid = int((top+bottom)/2), int((left+right)/2) 
            if rname == "droi":
                cv2.rectangle(clone, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(clone, rname, (mid[1], mid[0]),
                                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
            if rname == "mroi":
                
                cv2.rectangle(clone, (left, top), (int((left + right)/3), bottom), (0, 255, 0), 2)
                cv2.rectangle(clone, (int((left + right)/3), top), (2*int((left + right)/3), bottom), (0, 255, 0), 2)
                cv2.rectangle(clone, (2*int((left + right)/3), top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(clone, str("Mv"), (int((right)/1), int((top+bottom)/2)),
                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(clone, str("Dr"), (int((left + right)/3), int((top+bottom)/2)),
                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(clone, str("Er"), (2*int((left + right)/3), int((top+bottom)/2)),
                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if rname == "vroi":
                gb_indices = int((left-right)/len(self.vui.modes))
                gb_indices = np.arange(right, left, gb_indices)
                gb_indices[-1] = gb_indices[-1]+1
                for i in range(len(gb_indices)-1):
                    _gleft = gb_indices[i]
                    _gright = gb_indices[i+1]
                    cv2.rectangle(clone, (_gleft, top), (_gright, bottom), (255, 0, 255), 3)
                    cv2.putText(clone, self.vui.modes[i][:2], (_gleft+2, int((top+bottom)/2)),
                                                       cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 255), 2)
        return clone
    
    def find_contours(self, clone, threshold=10):
        self.roi_counts = {key:None for key in self.roi_counts.keys()}
        for rname, ravg in self.roi_averages.items():
            # abs diff betn img and bg
            top, right, bottom, left = self.roi_boxes[rname]
            diff = cv2.absdiff(ravg.astype("uint8"), self.roi_grays[rname])    
            _, th = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
            (cnts, _) = cv2.findContours(th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            m = (-1, -1)
            if len(cnts)!=0:
                max_cnt = max(cnts, key=cv2.contourArea)
                cv2.drawContours(clone, [max_cnt+(right,top)], -1, (0, 0, 255))   
                sshape = max_cnt.shape
                new_segmented = max_cnt.reshape(sshape[0], sshape[-1])
                m = new_segmented.min(axis=0)
                cv2.circle(clone, (right+m[0], top+m[1]), 15, self.vui.pointer_color, -3)
                self.roi_counts[rname] = len(max_cnt)
                # translate m of this roi to window shape
                #if len(max_cnt)>10:    

                if rname!="mroi":
                    pshape = self.size
                    if rname=="vroi":
                        pshape = (self.vui.vui_part, self.vui.size[1])
                    if rname=="droi":
                        # make it self.canvas.shape
                        #pshape = (self.canvas_shape[0], self.canvas_shape[1]-self.canvas.ssize[1]) 
                        pshape=self.canvas_shape
                    h = bottom - top
                    l = left - right


                    m = (int((m[0]/l)*pshape[1]), int((m[1]/h)*pshape[0]))    
                else:
                    m = (right+m[0], top+m[1])
        
                self.roi_pointer[rname]=(m[1], m[0])
                
        return clone    
    
    def get_window(self, canvas, vui):
        final_window = vui.copy()
        canvas_cpy = canvas.copy()
        vshape = vui.shape
        cshape = canvas.shape
        #print(self.running_mode)
        if self.running_mode == "color":
            # get part where color lies and make those part of canvas_bg black
            cp = self.vui.mode_pos[self.running_mode]
            canvas[:self.vui.dd_part[1]-self.vui.vui_part, cp[0]:cp[1]] = vui[self.vui.vui_part:self.vui.dd_part[1], cp[0]:cp[1]]
            
            #show(canvas)
        #else:#
        final_window[self.vui.vui_part:, :] = canvas
        cp = self.roi_pointer["droi"]
        cp = (cp[1], cp[0]+self.vui.vui_part)
        point = self.canvas.point
        cv2.circle(final_window,  cp, point[0], self.canvas.pointer_color, point[1])
        return final_window
    
    def check_force_mode(self):
        top, right, bottom, left = self.roi_boxes["mroi"]
        if self.force_modes is None:
            x=np.linspace(right, left, 4).astype(np.int64)
            x=[(x[i],x[i+1]) for i in range(len(x)-1)]
            force_modes = ["move", "draw", "erase"]
            force_modes = {x[i]:force_modes[i] for i in range(len(x))}
            #print(force_modes)
            self.force_modes = force_modes
        elif self.roi_pointer["mroi"][0]>0:
            mpointer = self.roi_pointer["mroi"]
            
            for col, mode in self.force_modes.items():
                
                if col[0]<=mpointer[1]<col[1]:
                    #print(col, mpointer)
                    if self.fprev_mode==mode:
                        self.fcurrent_count+=1
                    else:
                        self.fcurrent_count=0
                        self.fprev_mode=mode
                    if self.fcurrent_count>=self.fcount_mode:
                        #print("f ", mode)
                        #self.fcurrent_count=0
                        
                        return mode
    def detector(self):
        img = self.canvas.canvas.astype(np.uint8)
        op = pytesseract.image_to_string(img, lang="eng", nice="1")
        print("Detected: ", op)
    def perform_mode(self):
        if self.running_mode=="clear":
            self.canvas.clear()
            self.running_mode="move"
        if self.running_mode=="restart":
            self.take_average =True
            self.num_frames=0
            self.running_mode="move"
            self.canvas.clear()
        if self.running_mode=="save":
            #cv2.imshow("canvas", self.canvas.canvas.astype(np.uint8))
            cv2.imwrite("canvas.png", self.canvas.canvas.astype(np.uint8))
            #cv2.destroyWindow("canvas")
            self.running_mode="move"
        if self.running_mode=="exit":
            self.key=27
        if self.running_mode=="detect":
            self.running_mode="move"
            self.detector()
    def main(self):
        cam = cv2.VideoCapture(0) 
        self.num_frames = 0
        self.take_average=True
        while True:
            (ret, frame) = cam.read()
            if ret:
                self.key = cv2.waitKey(1) & 0xFF
                frame = imutils.resize(frame, width=self.size[1])
                frame = cv2.flip(frame, 1)
                clone = frame.copy()
                gray = cv2.cvtColor(clone, cv2.COLOR_BGR2GRAY)
                self.set_grays(gray)
                self.size = frame.shape
                
                # if to take average and num frames on average taking is lesser than 
                if self.num_frames<self.avg_frames and self.take_average==True:
                    self.running_average()
                    cv2.putText(clone, str(self.num_frames), (self.roi_boxes["mroi"][1], self.roi_boxes["mroi"][0]-5),
                                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1)
                    self.num_frames+=1
                else:
                    self.take_average=False
                    clone = self.find_contours(clone)
                    fmode = self.check_force_mode() 
                    #vui = self.vui.get_window()
                    vui = self.vui.update_vui(pointer=self.roi_pointer["vroi"], cpointer=self.roi_pointer["droi"])
                    if self.vui.hover is not None:
                        self.running_mode = self.vui.running_mode   
                    if  self.roi_counts["mroi"] is not None:
                        if self.roi_counts["vroi"] is not None:
                            if self.roi_counts["mroi"]-5 > self.roi_counts["vroi"] and fmode is not None:
                                self.running_mode = fmode
                            else:
                                self.running_mode = self.vui.running_mode       
                        else:
                            self.running_mode = fmode
                    self.perform_mode()
                    self.vui.running_mode=self.running_mode
                    canvas = self.canvas.update_window(mode=self.running_mode, 
                                                       pointer=self.roi_pointer["droi"]).astype(np.uint8)
                    final_window = self.get_window(canvas=canvas, vui=vui)
                    cv2.imshow("CW", final_window)
                    
                    self.roi_pointer["vroi"] = (-1, -1)
                    
                clone = self.make_rectangles(clone)
                cv2.imshow("Feed", clone)
                if self.key==27:
                    break
        cam.release()
        cv2.destroyAllWindows()

gw = ContourWriting(avg_frames=150, aweight=0.5)
gw.main()
