from PIL import Image
from pathlib import *
from datetime import *
from rich.logging import RichHandler
import json
import pillow_heif
import logging
import locale
import shutil
import sys

def _handle_logging() -> None:
    """
    Loads logging settings and handlers for terminal formatting and saving the log onto a file.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_formatter = RichHandler()
    log_file_dump = logging.FileHandler(f"{datetime.today().strftime('%d-%m-%Y %H:%M')} log.txt")

    logger.addHandler(log_formatter)
    logger.addHandler(log_file_dump)

def _load_config() -> dict:
    """
    Loads basic configuration of the script from dependencies and settings file.
    :return:
    """
    pillow_heif.register_heif_opener()
    _handle_logging()

    try:
        with open("settings.json") as settings_file:
            config = json.load(settings_file)

        accepted_formats: list = config["accepted_formats"]
        locale.setlocale(locale.LC_TIME, config["locale"])

        logging.info("Loaded configuration from 'settings.json'")
        return {"accepted_formats":accepted_formats}
    
    except FileNotFoundError as e:
        logging.error(f"Cannot fetch 'settings.json. Exception:{e}")
        sys.exit()

def load_folder(folder_path: str) -> Path:
    """Loads the specified folder to perform sorting operations. Checks if
    the folder exists and returns a Path object with the folder itself."""
    try:
        photos_folder: Path = Path(folder_path)
        if photos_folder.is_dir():
            logging.info(f"Loaded '{photos_folder}' directory.")
            return photos_folder
        else:
            raise NotADirectoryError(f"The directory '{photos_folder}' does not exist.")
    except NotADirectoryError as e:
        logging.error(e)
        sys.exit("Closing program. ")


def set_output_folder(folder_path: str) -> Path:
    """
    Sets the output folder for the copied and sorted photos. Checks if the folder already exists
    and asks for permission to use it anyway. If it does not exist it will create it.
    :param folder_path:
    :return:
    """
    try:
        output_folder: Path = Path(folder_path)
        if output_folder.is_dir():
            logging.info(f"'{output_folder}' already exists, dou you want to use it anyway? (y/n) ")

            # Output folder permission to use/create
            choice: str = input().lower()
            if len(choice) == 1 and choice == "y":
                logging.info(f"Set output folder to '{output_folder}'")
                return output_folder
            elif len(choice) == 1 and choice == "n":
                logging.info("Closing program. Set another output folder path.")
                sys.exit()
            else:
                logging.error(f"{choice} is an invalid input. Exiting program.")
                sys.exit()

        else:
            output_folder.mkdir()
            logging.info(f"Created '{output_folder}' and set it as output folder.")
            return output_folder
    except NotADirectoryError as e:
        logging.error(e)
        sys.exit()

def is_format_supported(file, accepted_formats) -> bool:
    """
    Checks if the file extension of the current selected file is supported by the script.
    :param file:
    :param accepted_formats:
    :return:
    """
    item: Path = Path(file)
    try:
        if item.suffix.upper() in accepted_formats:
            return True
        else:
            raise ValueError(f"{item.suffix} is not a supported file format.")
    except ValueError as ve:
        logging.warning(f"{ve} {item} will be ignored from sorting.")

def get_date_from_metadata(img_file: Image) -> str:
    """
    Extract the date of capture from EXIF metadata and converts it a datetime object to perform
    sorting based by month and year.
    :param img_file:
    :return:
    """
    raw_data = img_file.getexif()
    try:
        if raw_data == {}:
            raise KeyError(f"'{img_file.filename}' has empty metadata. It will be ignored from sorting.")
        elif 306 not in raw_data:
            raise KeyError(f"'{img_file}' has no date metadata. It will be ignored from sorting.")

        # 306 is the key for date of capture in the EXIF metadata
        raw_date: list = raw_data[306].split(" ")[0].split(":")
        for idx, n in enumerate(raw_date):
            raw_date[idx] = int(raw_date[idx])

        date_of_capture: datetime = datetime(raw_date[0], raw_date[1], raw_date[2])
        return date_of_capture.strftime("%B %Y").title()
    except KeyError as ke:
        logging.warning(ke)


def sort(img_file: Path, date_of_capture: str, output_folder: Path) -> None:
    """
    Sorts the photos in the input folder by month and year of capture. Checks if there is an output
    folder set in memory. Creates a new folder for every month and year extracted from EXIF metadata,
    if it does already exist it just copies the photo in the correct folder.
    :param img_file:
    :param date_of_capture:
    :param output_folder:
    :return:
    """
    if output_folder:
        pass
    else:
        logging.error(f"Missing output folder path: '{output_folder}'")
        sys.exit()

    # If a photo has no date of capture it means its metadata are missing, it will be skipped as warned
    # in the extract_date_from_metadata function.
    if date_of_capture:
        dest_folder = Path(output_folder, date_of_capture)
        if dest_folder.is_dir():
            try:
                shutil.copy2(str(img_file), str(dest_folder))
            except Exception as e:
                logging.error(e)
            else:
                logging.info(f"Moved '{img_file}' to '{dest_folder}'")
        else:
            dest_folder.mkdir()
            logging.info(f"Created '{dest_folder}' folder.")
            shutil.copy2(str(img_file), str(dest_folder))

def main() -> None:
    """Program entry point."""

    config: dict = _load_config()
    supported_ext: list = config["accepted_formats"]

    photo_folder = load_folder(r"photos")
    destination_folder = set_output_folder("output")

    for photo_file in photo_folder.iterdir():
        if is_format_supported(photo_file, supported_ext):
            with Image.open(photo_file) as img:
                date_of_capture = get_date_from_metadata(img)
            sort(photo_file, date_of_capture, destination_folder)


if __name__ == "__main__":
    main()
