import shutil
from tabulate import tabulate
import win32api
import os,operator,sys
import time
import hashlib
import magic

f=True
gigabyte=1073741824
megabyte=1048576
kilobyte=1024

def binarySearch(files_and_sizes,threshold):
    left=0
    right=len(files_and_sizes)-1
    index=-1
    while left<=right:
        mid=left+(right-left)//2
        if files_and_sizes[mid][1]>=threshold:
            index=mid
            right=mid-1
        else:
            left=mid+1
    return index

def bytesFormat(num):
    if num >= gigabyte:
        num = num // gigabyte
        num = str(num)+" GB"
    elif num >= megabyte:
        num = num // megabyte
        num = str(num)+" MB"
    elif num >= kilobyte:
        num = num // kilobyte
        num = str(num)+" KB"
    else:
        num = str(num)+" bytes"
    return num

def storageStats():
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
    drive_list=[]
    head=["Drive","Total","Used","Free"]
    for drive in drives:
        total, used, free = shutil.disk_usage(drive)
        drive_list.append([drive[0], bytesFormat(total), bytesFormat(used), bytesFormat(free)])
    print(tabulate(drive_list, headers=head, tablefmt="grid"))
    print()

def fileTypeBreakdown(directory):
    if not os.path.exists(directory):
        print("!!! Incorrect Path !!!")
        return
    else:
        fileTypes=dict()
        totalUsedSize = 0
        mime = magic.Magic(mime=True)
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size=os.stat(file_path).st_size
                totalUsedSize+=file_size
                try:
                    file_type=mime.from_file(file_path).split("/")[0]
                    if file_type not in fileTypes:
                        fileTypes[file_type] = [1,file_size]
                    else:
                        fileTypes[file_type][0]+=1
                        fileTypes[file_type][1]+=file_size
                except PermissionError:
                    pass
        totalUsedSize = bytesFormat(totalUsedSize)
        newlist = list()
        for key in fileTypes:
            newlist.append([key, fileTypes[key][0], bytesFormat(fileTypes[key][1])])
        head=["Type","Count","Size"]
        print(f"File Type Breakdown for {directory}")
        print(f"with Total Used Size = {totalUsedSize}")
        print(tabulate(newlist, headers=head, tablefmt="grid"))
        print()

def duplicateFiles(directory):
    if not os.path.exists(directory):
        print("!!! Incorrect Path !!!")
        return
    else:
        unique_files = dict()
        duplicate_files = dict()
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    Hash_file = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                    if Hash_file not in unique_files:
                        unique_files[Hash_file] = file_path
                    else:
                        if Hash_file not in duplicate_files:
                            duplicate_files[Hash_file] = [[unique_files[Hash_file]],[file_path]]
                        else:
                            duplicate_files[Hash_file].append([file_path])
                except PermissionError:
                    pass
        if len(duplicate_files) == 0:
            print(f"No duplicates found in {directory}")
            print()
            return
        c = 0
        for key in duplicate_files:
            c+=1
            print(tabulate(duplicate_files[key],headers=[f"Conflict No. {c}"],tablefmt="grid",showindex="always"))
            listOfIndices = input("Space-separated indices of files to delete [\"all\" to delete all, enter to skip]- ")
            if listOfIndices!="":
                if listOfIndices.lower()=="all":
                    listOfIndices = range(len(duplicate_files[key]))
                else:
                    listOfIndices = listOfIndices.split(" ")
                for entry in listOfIndices:
                    os.remove(duplicate_files[key][int(entry)][0])
                    print(f"Deleting {duplicate_files[key][int(entry)][0]}")
                print()

def largeFiles(directory, threshold):
    if not os.path.exists(directory):
        print("!!! Incorrect Path !!!")
        return
    else:
        threshold=int(threshold)
        all_files = [os.path.join(root, file) for root, dirs, files in os.walk(directory) for file in files]
        files_and_sizes = [[path, os.path.getsize(path)] for path in all_files]
        files_and_sizes = sorted(files_and_sizes, key = operator.itemgetter(1))
        large_files=[]
        index=binarySearch(files_and_sizes,threshold)
        if index!=-1:
            large_files=files_and_sizes[index:]
        else:
            print(f"No large files found in {directory}")
            print()
            return
        for file in large_files:
            file[1] = bytesFormat(file[1])
        head=["Path","Size"]
        print(tabulate(large_files,headers=head,tablefmt="grid",showindex="always"))
        listOfIndices = input("Space-separated indices of files to delete [\"all\" to delete all, enter to skip]- ")
        if listOfIndices!="":
                if listOfIndices.lower()=="all":
                    listOfIndices = range(len(large_files))
                else:
                    listOfIndices = listOfIndices.split(" ")
                for entry in listOfIndices:
                    os.remove(large_files[entry[0]])
                    print(f"Deleting {large_files[int(entry)][0]}")
                print()

def scanSpecific(directory, userInput):
    if not os.path.exists(directory):
        print("!!! Incorrect Path !!!")
        return
    else:
        types = ["video", "audio", "application", "image", "text", "others"]
        userInput = list(map(int, userInput.split(" ")))
        scanList = list()
        for idx in userInput:
            scanList.append(types[idx-1])
        fileTypes=dict()
        mime = magic.Magic(mime=True)
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size=os.stat(file_path).st_size
                try:
                    file_type=mime.from_file(file_path).split("/")[0]
                    if file_type not in types[:-1]:
                        file_type = "others"
                    if file_type not in fileTypes:
                        fileTypes[file_type] = [[[file_path,bytesFormat(file_size)]],1,file_size]
                    else:
                        fileTypes[file_type][0].append([file_path,bytesFormat(file_size)])
                        fileTypes[file_type][1]+=1
                        fileTypes[file_type][2]+=file_size
                except PermissionError:
                    pass
        results = list()
        for i in scanList:
            if i not in fileTypes:
                print(f"No files of type {i} found in {directory}")
            else:
                print(tabulate(fileTypes[i][0],headers=[f"Type-{i}", "Size"],showindex="always",tablefmt="grid"))
                print(f"Total size of type {i} = {bytesFormat(fileTypes[i][2])} with {fileTypes[i][1]} items")
                listOfIndices = input("Space-separated indices of files to delete [\"all\" to delete all, enter to skip]- ")
                if listOfIndices!="":
                    if listOfIndices.lower()=="all":
                        listOfIndices = range(len(fileTypes[i][0]))
                    else:
                        listOfIndices = listOfIndices.split(" ")
                    for entry in listOfIndices:
                        os.remove(fileTypes[i][0][int(entry)][0])
                        print(f"Deleting {fileTypes[i][0][int(entry)][0]}")
                    print()
            print()

def deleteFolder(directory):
    if not os.path.exists(directory):
        print("!!! Incorrect Path !!!")
        return
    else:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            try:
                shutil.rmtree(filepath)
                print(f"Deleting entire folder {filepath}")
            except OSError:
                os.remove(filepath)
                print(F"Deleting file {filepath}")
            except PermissionError:
                pass
        print()

while f:
    print("------------------------------")
    print("----------BRUHMOMENT----------")
    print("\nSelect an operation:")
    print("1. Storage Statistics for All Drives")
    print("2. Space Utilization for Chosen Directory")
    print("3. Duplicate File Management")
    print("4. Large File Management")
    print("5. Scan Specific File Type in Chosen Directory")
    print("6. Delete a folder")
    choice = input("\nEnter your choice [enter to skip]- ")
    match choice:
        case "1":
            start_time = time.time()
            storageStats()
            print("--- %s seconds ---" % (time.time() - start_time))
        case "2":
            start_time = time.time()
            directory = input("Enter path to check [current path]- ") or os.getcwd()
            fileTypeBreakdown(directory)
            print("--- %s seconds ---" % (time.time() - start_time))
        case "3":
            start_time = time.time()
            directory = input("Enter path to check for duplicates [current path]- ") or os.getcwd()
            duplicateFiles(directory)
            print("--- %s seconds ---" % (time.time() - start_time))
        case "4": 
            start_time = time.time()
            directory = input("Enter path to check for large files [current path]- ") or os.getcwd()
            threshold = input("Enter threshold (in bytes) for large file consideration [1 GB]- ") or gigabyte
            largeFiles(directory, threshold)
            print("--- %s seconds ---" % (time.time() - start_time))
        case "5":
            start_time = time.time()
            directory = input("Enter path to scan [current path]- ") or os.getcwd()
            print("1.video, 2.audio, 3.application(includes documents) 4.image 5.text 6.others\n")
            userInput = input("Enter space-separated indices of types to scan [all]- ") or "1 2 3 4 5 6"
            scanSpecific(directory, userInput)
            print("--- %s seconds ---" % (time.time() - start_time))
        case "6":
            start_time = time.time()
            directory = input("Enter path to check for large files [current path]- ") or os.getcwd()
            deleteFolder(directory)
            print("--- %s seconds ---" % (time.time() - start_time))
        case _:
            x = input("\nDo you want to continue? (Y/N) [Y]- ") or "Y"
            x = x.upper()
            if x == "Y":
                f = True
            else:
                f = False