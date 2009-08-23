#!/usr/bin/env python

# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Flowchart'
PLUGIN_AUTHOR = 'Thomas Hansen'
PLUGIN_EMAIL = 'thomas.hansen@gmail.com'


from pymt import *
from pyglet.gl import *

class SVGButton(MTButton):
    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        super(SVGButton,self).__init__(**kwargs)
        filename = kwargs.get('filename')
        self.svg = MTSvg(filename=filename)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glScalef(self.width/self.svg.width, self.height/self.svg.height, 1)
        self.svg.draw()
        glPopMatrix()



class FlowchartObject(MTScatterWidget):
    def __init__(self, **kwargs):
        super(FlowchartObject, self).__init__(**kwargs)

        self.svg = MTSvg(filename='../flowchart/box.svg')
        self.size = (self.svg.width, self.svg.height)
        self._hide_children = False
        self.hidden_children = []

        self.add_bttn = SVGButton( filename='transport-shuffle.svg', pos=(self.center[0]-15, -15), size=(30,30))
        self.add_bttn.push_handlers(on_press=self.add_new_child)
        self.add_widget(self.add_bttn)

        self.hide_bttn = SVGButton(filename='minus.svg', pos=(0, self.height-20), size=(20,20))
        self.hide_bttn.push_handlers(on_press=self.toggle_children)
        self.add_widget(self.hide_bttn)
        self.hide_bttn2 = SVGButton(filename='plus.svg', pos=(0, self.height-20), size=(20,20))
        self.hide_bttn2.push_handlers(on_press=self.toggle_children)

        self.del_bttn = SVGButton(filename='power.svg', pos=(self.width-20, self.height-20), size=(20,20))
        self.del_bttn.push_handlers(on_press=self.remove)
        self.add_widget(self.del_bttn)

    def hide_children(self):
        self.hide_bttn.label = "+"
        for c in self.children:
            if isinstance(c, FlowchartObject):
                self.hidden_children.append(c)
        for c in self.hidden_children:
            self.remove_widget(c)
        self._hide_children = True

    def show_children(self):
        self.hide_bttn.label = "-"
        for c in self.hidden_children:
                self.add_widget(c)
        self.hidden_children = []
        self._hide_children = False

    def toggle_children(self, touchID, x, y):
        if self._hide_children:
            self.show_children()
            self.remove_widget(self.hide_bttn2)
            self.add_widget(self.hide_bttn)
        else:
            self.hide_children()
            self.remove_widget(self.hide_bttn)
            self.add_widget(self.hide_bttn2)

    def add_new_child(self, touchID, x,y):
        child = FlowchartObject(translation=(x-20,y-20), scale = 0.5)
        child.on_touch_down([], touchID, x,y)
        self.add_widget(child)


    def remove(self, touchID, x,y):
        self.parent.remove_widget(self)


    def draw_connection(self, child):
            x1,y1 = self.center  #from here
            x2,y2 = child.to_parent(*child.center) #to here
            angle = Vector.angle(Vector(0,1), Vector(x1-x2,y1-y2))
            offset = Vector.rotate(Vector(20,0),-angle)
            drawPolygon((x1-offset.x,y1-offset.y,x1+offset.x,y1+offset.y,x2,y2))

    def draw_connections(self):
        offset = Vector(0,0)
        for child in self.children:
            if  isinstance(child, FlowchartObject):
                glColor4f(1,1,1,0.5)
                self.draw_connection(child)
        for child in self.hidden_children:
            if  isinstance(child, FlowchartObject):
                glColor4f(1,0.5,0.5,0.1)
                self.draw_connection(child)

    def draw(self):
        self.draw_connections()
        self.svg.draw()


def pymt_plugin_activate(root, ctx):
    ctx.plane = MTScatterPlane()
    ctx.plane.add_widget(FlowchartObject())
    root.add_widget(ctx.plane)

def pymt_plugin_deactivate(root, ctx):
    root.remove_widget(ctx.plane)

if __name__ == '__main__':
    w = MTWindow()
    ctx = MTContext()
    pymt_plugin_activate(w, ctx)
    runTouchApp()
    pymt_plugin_deactivate(w, ctx)