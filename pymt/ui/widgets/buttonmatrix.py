from __future__ import with_statement
__all__ = ['MTButtonMatrix']

from pyglet.gl import *
from ...graphx import set_color, drawRectangle
from ..factory import MTWidgetFactory
from widget import MTWidget

class MTButtonMatrix(MTWidget):
    '''ButtonMatrix is a lightweight Grid of buttons/tiles
      collide_point returns which matrix element was hit
      draw_tile(i,j) draws the  tile @ matrix position (i,j)
    '''

    def __init__(self,**kwargs):
        kwargs.setdefault('matrix_size', (3,3))
        super(MTButtonMatrix, self).__init__(**kwargs)
        self.matrix_size = kwargs.get('matrix_size')
        self.matrix = [[0 for i in range(self.matrix_size[0])] for j in range(self.matrix_size[1])]
        self.border = 5
        self.matrix_size = kwargs.get('matrix_size')


    def draw_tile(self, i, j):
        if self.matrix[i][j] == 0:
            set_color(1,1,0,1)
        if self.matrix[i][j] == 'down':
            set_color(0,0,1,1)

        with gx_matrix:
            glTranslatef(self.width/self.matrix_size[0]*i, self.height/self.matrix_size[1]*j,0)
            s =  (self.width/self.matrix_size[0]-self.border,self.height/self.matrix_size[1]-self.border)
            drawRectangle(size=s)


    def draw(self):
        for i in range (self.matrix_size[0]):
            for j in range (self.matrix_size[1]):
                self.draw_tile(i,j)


    def collide_point(self, x, y):
        i = x/(self.width/self.matrix_size[0])
        j = y/(self.height/self.matrix_size[1])
        return (i,j)

    def on_touch_down(self, touches, touchID, x, y):
        i,j = self.collide_point(x,y)
        if self.matrix[i][j] == 'down':
            self.matrix[i][j] = 0
        else:
            self.matrix[i][j] = 'down'

MTWidgetFactory.register('MTButtonMatrix', MTButtonMatrix)
