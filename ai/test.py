from moviepy.editor import VideoFileClip, AudioFileClip

def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """Add audio to the video, trimming or silencing as necessary."""
    try:
        # Load the video and audio files
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # Set the audio to the video
        video = video.set_audio(audio)

        # Check lengths and adjust
        if audio.duration < video.duration:
            # If audio is shorter, keep the video length
            final_video = video.set_duration(audio.duration)
        else:
            # If video is shorter, keep the video length and silence the rest
            final_video = video.set_duration(video.duration)

        # Write the final video to a file
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')

        print(f"Video with audio saved as: {output_path}")
    except Exception as e:
        print(f"Error adding audio to video: {str(e)}")

# Example usage
if __name__ == "__main__":
    output_file = "different_shapes_like_star_circle_etc_colorful_1726919096.mp4"
    generic_path = f"media/videos/manim_code/480p15/{output_file}"  # Path to the video
    audio_path = "temp_math_audio.mp3"  # Path to the audio file
    output_path = f"math_vid_final.mp4"  # Output path for the final video

    add_audio_to_video(generic_path, audio_path, output_path)