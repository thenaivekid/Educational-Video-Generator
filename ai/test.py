from moviepy.editor import VideoFileClip

def extract_thumbnail(video_path: str, thumbnail_path: str):
    """Extract the first frame from the video and save it as a thumbnail image."""
    try:
        # Load the video file
        video = VideoFileClip(video_path)

        # Get the first frame
        first_frame = video.get_frame(0)  # Get the frame at time 0 seconds

        # Save the first frame as an image
        first_frame_image = f"{thumbnail_path}.png"
        video.save_frame(first_frame_image, t=0)  # Save the frame as an image

        print(f"Thumbnail saved as: {first_frame_image}")
        return first_frame_image
    except Exception as e:
        print(f"Error extracting thumbnail: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    video_path = r".\media\videos\generate_manim\480p15\Video.mp4"  # Replace with your video path
    thumbnail_path = "./"  # Replace with your desired thumbnail path
    extract_thumbnail(video_path, thumbnail_path)