from manim import *
import numpy as np

class RotationAboutOrigin(Scene):
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

        # Rotation angle (45 degrees or pi/4 radians)
        angle_of_rotation = np.pi / 4

        # Create a rotation matrix
        rotation_matrix = np.array([
            [np.cos(angle_of_rotation), -np.sin(angle_of_rotation), 0],
            [np.sin(angle_of_rotation), np.cos(angle_of_rotation), 0],
            [0, 0, 1]
        ])

        # Apply rotation about the origin
        rotated_triangle = triangle.copy().apply_matrix(rotation_matrix)

        # Label for the original triangle
        original_label = Text("Original Shape", font_size=24).next_to(triangle, DOWN)
        rotation_label = Text("Rotated Shape", font_size=24).next_to(rotated_triangle, DOWN)

        # Display axes and the original triangle
        self.play(Create(axes))
        self.play(Create(triangle))
        self.play(Write(original_label))

        # Rotate the triangle
        self.play(Transform(triangle.copy(), rotated_triangle))
        self.play(FadeOut(original_label), Write(rotation_label))

        # Pause before ending
        self.wait(2)
