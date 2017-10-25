from math import sin, cos, pi

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def value(self):
        return (self.x, self.y)

class Circle(object):
    def __init__(self, r=1, n=50):
        self.points = [Point(cos(2*pi/n*x)*r, sin(2*pi/n*x)*r).value() for x in range(0,n+1)]

    def segments(self):
        return [(v, w) for v, w in zip(self.points, self.points[1:])]

if __name__ == "__main__":
    circle = Circle(50, 20)
    print(circle.segments())
