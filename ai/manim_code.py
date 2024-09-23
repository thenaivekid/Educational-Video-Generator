from manim import *

class RotationOfTriangle(Scene):
    def construct(self):
        axes = Axes(x_range=[-10, 10, 1], y_range=[-10, 10, 1], width=10, height=10).add_coordinates()
        triangle = Polygon([-3, -1, 0], [-5, -3, 0], [-1, -4, 0], color=BLUE)
        self.play(Write(axes), Write(triangle))
        self.play(Rotate(triangle, angle=PI, about_point=ORIGIN))
        self.wait(2)
        self.play(FadeOut(triangle), FadeOut(axes))
        self.wait(1)