# !pip install ultralytics ncnn

import os
from ultralytics import YOLO

def export_to_ncnn():
    model_paths = [
        "/kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolov8_best.pt",
        "/kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolov9_best.pt",
        "//kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolov10_best.pt",
        "/kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolov11_best.pt",
        "/kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolov12_best.pt",
        "/kaggle/input/models/irfanqs/model-sawit/tensorflow2/default/1/yolo26_best.pt"
    ]
    
    # Resolusi gambar yang akan digunakan (Raspberry Pi biasanya lebih cepat di 320x320)
    image_size = 320 

    for path in model_paths:
        if not os.path.exists(path):
            print(f"[SKIP] Model tidak ditemukan: {path}")
            continue
            
        print("="*50)
        print(f"Mengekspor: {path} ke NCNN (imgsz={image_size})")
        print("="*50)
        
        try:
            # Pindahkan file .pt ke temporary directory yang writeable (/kaggle/working)
            import shutil
            output_dir = "/kaggle/working"
            base_name = os.path.basename(path)
            local_path = os.path.join(output_dir, base_name)
            
            # Copy file agar tidak ada di folder read-only saat melakukan export
            print(f"Menyalin {path} ke {local_path}...")
            shutil.copy2(path, local_path)
            
            # Load model PyTorch dari lokasi yang writeable
            model = YOLO(local_path)
            
            # Export ke format ncnn
            output = model.export(format="ncnn", imgsz=image_size, optimize=False)
            print(f"[BERHASIL] Tersimpan di: {output}")
            
            # (Opsional) Hapus file .pt lokal agar tidak memenuhi memori working directory
            if os.path.exists(local_path):
                os.remove(local_path)
            
        except Exception as e:
            print(f"[GAGAL] Error saat mengekspor {path}: {e}")

if __name__ == "__main__":
    export_to_ncnn()