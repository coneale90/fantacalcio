# rename all fine from Voti_Fantacalcio_Stagione_2025_26_Giornata_{x} to voti_2025_giornata_x
import os

folder = './'
for filename in os.listdir(folder):
    if filename.startswith("Voti_Fantacalcio_Stagione_"):
        new_filename = filename.replace("Voti_Fantacalcio_Stagione_2024_25_Giornata_", "voti_2024_giornata_")
        os.rename(os.path.join(folder, filename), os.path.join(folder, new_filename))

