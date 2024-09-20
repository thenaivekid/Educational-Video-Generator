from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from typing import List

def assemble_video(scene_images: List[str], audio_files: List[str], output_filename: str = "educational_video.mp4", images_per_audio: int = 5):
    """Assemble the video using multiple audio files, distributing multiple images per audio clip."""
    clips = []
    
    # Ensure that the number of images matches the expected number based on audio files and images_per_audio
    if len(scene_images) != len(audio_files) * images_per_audio:
        raise ValueError(f"The number of scene images ({len(scene_images)}) does not match {len(audio_files) * images_per_audio} expected images for {images_per_audio} per audio file.")

    image_index = 0

    for audio_file in audio_files:
        # Load the audio clip
        audio_clip = AudioFileClip(audio_file)

        # Calculate the duration for each image based on the audio duration
        image_duration = audio_clip.duration / images_per_audio

        for _ in range(images_per_audio):
            # Calculate the start and end time for this image portion of the audio
            start_time = (image_index % images_per_audio) * image_duration
            end_time = start_time + image_duration

            # Load the corresponding image
            image_clip = ImageClip(scene_images[image_index]).set_duration(image_duration)

            # Set the corresponding portion of the audio (only the segment of the audio for each image)
            image_clip = image_clip.set_audio(audio_clip.subclip(start_time, end_time))

            # Append the image clip to the list of clips
            clips.append(image_clip)

            # Move to the next image
            image_index += 1

    # Concatenate all clips into a single video
    final_video = concatenate_videoclips(clips, method="compose")

    # Write the final video to a file
    final_video.write_videofile(output_filename, fps=1)

    print(f"Video assembled and saved as: {output_filename}")

# Example usage
if __name__ == "__main__":
    # Use images from temp_img_0.png to temp_img_9.png
    scene_images = [f"temp_img_{i}.png" for i in range(10)]  # 10 images

    # Use both audio files
    audio_files = ["temp_audio_0.mp3", "temp_audio_1.mp3"]  # 2 audio files

    # Assemble the video with 5 images per audio
    assemble_video(scene_images, audio_files, images_per_audio=5)
