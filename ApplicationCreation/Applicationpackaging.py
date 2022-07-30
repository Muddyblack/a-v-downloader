#benötigt pyinstaller
import subprocess
import os, shutil
from shutil import copyfile
from time import sleep

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def read_file(input_path):
    f = open(input_path, "r")
    read_lines = f.readlines()
    read_lines = [r.replace("\\n",'\\\\n').replace("\\r",'\\\\r').replace('\n','') for r in read_lines] 
    f.close()

    return read_lines

def write_encrpyted_file(file_name):
    ddir_path = os.path.dirname(file_path)

    file_text = read_file(f"{ddir_path}\\{file_name}")

    with open(f"{file_path}\\{file_name}", 'w') as f: 
        f.write("from cryptography.fernet import Fernet\n"+
                "import base64\n\n"
                'code = b"""\n')

        for element in file_text:
            if element == "from Core import mainDownloader":
                pos = f.tell() #gives me current pointer
                pos =  pos - 2     #This will give above value, where second blank line resides
                f.seek(pos) 
            else:
                f.write(element+"\n")
        
        f.write('"""\n\n'+
                "key = Fernet.generate_key()\n"+
                "encryption_type = Fernet(key)\n"+
                "encrypted_message = encryption_type.encrypt(code)\n\n"+
                "decrypted_message = encryption_type.decrypt(encrypted_message)\n\n"+
                "exec(decrypted_message)")
        f.close()


file_path = os.path.dirname(os.path.realpath(__file__))

write_encrpyted_file("Core.py")


application_folder_dir = f"{file_path}\\AudioAndVideoDownloader"

does_applicationfolder_exist = os.path.isdir(application_folder_dir)

if os.path.isdir(application_folder_dir) == True:
    shutil.rmtree(application_folder_dir)
    os.mkdir(application_folder_dir)
else:
    os.mkdir(application_folder_dir)


subprocess.call(f"""python -m PyInstaller --clean  {file_path}\\Downloader.spec""", cwd=application_folder_dir)


copytree(f"{application_folder_dir}\\dist", application_folder_dir)


shutil.rmtree(f"{application_folder_dir}\\dist")
shutil.rmtree(f"{application_folder_dir}\\build")

copyfile(f"{os.path.dirname(file_path)}\\README.md", f"{application_folder_dir}\\README.md")


try:
    os.remove(file_path+"\\Core.py")
except:
    pass