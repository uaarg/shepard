from src.modules.imaging.camera import GazeboCamera
import os


cam = GazeboCamera()

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new


cam.capture_to(f"tmp/log/{ft_num}/gazebocamera.png")
