import os
import subprocess
 
def play_audio(file_path, gain=1.0):
    """
    使用 mpg123 播放音频文件，并调整音量。
 
    Args:
        file_path (str): 音频文件的路径。
        gain (float): 音量增益 (默认为 1.0).
    """
    try:
        command = ["mpg123",  file_path]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"播放音频时出错: {e}")
 
if __name__ == "__main__":
    # for file_name in os.listdir("/home/myb/guide_dog/audio_file"):
    #     audio_file = "/home/myb/guide_dog/audio_file/" + file_name
    #     play_audio(audio_file)  # 尝试 gain=2.0 或更大的值
    play_audio("/home/myb/Exhibition_Hall/guide_dog/audio_file/test.mp3")


# import simpleaudio as sa
 
# def play_audio(filename):
#     try:
#         wave_obj = sa.WaveObject.from_wave_file(filename)
#         play_obj = wave_obj.play()
#         play_obj.wait_done()  # 等待播放完成
#     except Exception as e:
#         print(f"Error playing audio file: {e}")
 
# if __name__ == "__main__":
#     audio_file = "/home/myb/guide_dog/audio_file/start_xy.wav"  # 注意这里需要是wav格式
#     play_audio(audio_file)

# # from pydub import AudioSegment
 
# # def convert_mp3_to_wav(mp3_filepath, wav_filepath):
# #     """将 MP3 文件转换为 WAV 文件."""
# #     try:
# #         audio = AudioSegment.from_mp3(mp3_filepath)
# #         audio.export(wav_filepath, format="wav")
# #         print(f"Successfully converted {mp3_filepath} to {wav_filepath}")
# #     except Exception as e:
# #         print(f"Error converting {mp3_filepath} to WAV: {e}")
 
# # if __name__ == "__main__":
# #     mp3_file = "/home/myb/guide_dog/audio_file/start_xy.mp3"
# #     wav_file = "/home/myb/guide_dog/audio_file/start_xy.wav"  # 输出文件，确保你有写入权限
# #     convert_mp3_to_wav(mp3_file, wav_file)