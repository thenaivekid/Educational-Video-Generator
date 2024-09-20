from manim import *

class ReflectionScene(Scene):
    def construct(self):
        # Create the axes
        axes = Axes(
            x_range=[-7, 7, 1],
            y_range=[-5, 5, 1],
            axis_config={"color": BLUE}
        )

        # Create a triangle in the first quadrant
        triangle = Polygon(
            [1, 1, 0],  # First point
            [2, 3, 0],  # Second point
            [3, 1, 0],  # Third point
            color=GREEN
        )

        # Reflect the triangle across the y-axis by changing the sign of x-coordinates
        reflected_triangle = Polygon(
            [-1, 1, 0],  # Reflected first point
            [-2, 3, 0],  # Reflected second point
            [-3, 1, 0],  # Reflected third point
            color=RED
        )

        # Label for the original triangle
        original_label = Text("Original Shape", font_size=24).next_to(triangle, DOWN)

        # Display axes and the original triangle
        self.play(Create(axes))
        self.play(Create(triangle))
        self.play(Write(original_label))

        # Reflect the triangle (remove the original label after transformation)
        self.play(Transform(triangle.copy(), reflected_triangle))
        self.play(FadeOut(original_label))  # Remove the original label after reflection

        # Pause before ending
        self.wait(2)
