import os
import shutil

from flywheel import run_flywheel


def delete_contents(directory: str):
    """
    Deletes all files and subdirectories within the given directory.

    Parameters:
        directory (str): The path to the directory whose contents should be deleted.

    Raises:
        FileNotFoundError: If the directory does not exist.
        PermissionError: If there are insufficient permissions to delete files.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory '{directory}' does not exist.")

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Delete directory and its contents
            else:
                os.remove(item_path)  # Delete file
        except Exception as e:
            print(f"Failed to delete {item_path}: {e}")


def clearDataFiles():
    delete_contents("./flywheel/data/")


def setup(reset_data):
    if reset_data:
        clearDataFiles()


def read_file(filename):
    with open(filename, "r") as file:
        return file.read()


def get_relevant_contexts(
    initial_document=None,
    initial_document_dir=None,
    reset_data=False,
    output_file_path=None,
):
    setup(reset_data)

    if not initial_document and not initial_document_dir:
        raise ValueError(
            "Either initial_document or initial_document_dir must be provided."
        )

    if initial_document and initial_document_dir:
        raise ValueError(
            "Only one of initial_document or initial_document_dir can be provided."
        )

    initial_context = initial_document or read_file(initial_document_dir)

    results = run_flywheel(initial_document=initial_context)

    if output_file_path:
        with open(output_file_path, "w") as output_file:
            output_file.write(results)
    else:
        return results


if __name__ == "__main__":
    get_relevant_contexts(
        initial_document = "Both Hathi Masala and Zoff Foods have their strengths, and the better choice depends on what you’re looking for in spices. Hathi Masala is a well-established brand with a strong reputation for its traditional spice blends. If you prefer time-tested flavors and a brand that has been around for years, this might be the better option for you. Zoff Foods, on the other hand, focuses on freshness and quality using cold grinding technology, which helps retain the natural oils and flavors of the spices. If you want something fresher and processed with modern techniques, Zoff might be a good pick. At the end of the day, both spice brands offer good quality, and it comes down to personal preference. If you want a deeper comparison, this blog breaks it down in detail: Hathi Masala vs Zoff Foods"
    )
