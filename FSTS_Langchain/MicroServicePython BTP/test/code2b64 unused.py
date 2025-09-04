import os
import base64

def main():
    # Define the main folder path (relative)
    main_folder = "code_files"
    subfolder = input("Enter the subfolder name inside 'code_files': ").strip()
    code_folder_path = os.path.join(main_folder, subfolder)
    if not os.path.exists(code_folder_path):
        os.makedirs(code_folder_path)
        # Create a dummy file for demonstration if the folder is empty
        with open(os.path.join(code_folder_path, 'sample_code.txt'), 'w') as f:
            f.write("REPORT Z_SAMPLE_REPORT.") # Add some dummy code

    code_input = ""
    for filename in os.listdir(code_folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(code_folder_path, filename), 'r') as f:
                code_input += f.read() + "\n\n"

    print(code_input)

    # Get output file name from user
    # file_name = input("Enter the output .b64 file name (without extension): ").strip()
    file_name = subfolder
    if not file_name:
        print("No file name provided. Exiting.")
        return
    if not file_name.endswith('.b64'):
        file_name += '.b64'

    # Encode code_input to Base64
    encoded = base64.b64encode(code_input.encode('utf-8')).decode('utf-8')

    # Ensure code_files_b64 directory exists
    b64_dir = 'code_files_b64'
    os.makedirs(b64_dir, exist_ok=True)
    out_path = os.path.join(b64_dir, file_name)

    # Save encoded content
    with open(out_path, 'w') as f:
        f.write(encoded)
    print(f"Base64-encoded code saved to {out_path}")

if __name__ == "__main__":
    main()
