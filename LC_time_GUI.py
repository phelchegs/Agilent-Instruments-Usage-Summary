from datetime import datetime
from PyPDF2 import PdfReader
import tkinter as tk
from tkinter import messagebox
import re

#input time strings in the format "month/date/year h:min:sec AM/PM"
#compare str1 with str2.
def string_time_compare(str1, str2):
    FMT = "%m/%d/%Y %I:%M:%S %p"
    time1 = datetime.strptime(str1, FMT)
    time2 = datetime.strptime(str2, FMT)
    return time1 < time2

#input time strings in the format "month/date/year h:min:sec AM/PM"
#return the difference in hours, str2 must be later than str1 if the result is expected to be positive.
def string_time_diff(str1, str2):
    FMT = "%m/%d/%Y %I:%M:%S %p"
    tdelta = datetime.strptime(str2, FMT) - datetime.strptime(str1, FMT)
    return tdelta.total_seconds()/3600

#Since the logbook begins from very old date, there is no need to loop from the very beginning.
#Search the 1st page that has the date equal or later than the starting date. Input time strings in the format "month/date/year h:min:sec AM/PM"
#return the number of the 1st page that records dates equal or later than the starting date.
def start_page(reader, start_time):
    for i in range(len(reader.pages)):
        texts = reader.pages[i].extract_text()
        times = re.findall(r"\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", texts)
        if not string_time_compare(times[-2], start_time): #times[-2] because the last date of each page is the date when the pdf file is generated. It needs to be later than the start date.
            start_page = i
            break
    return start_page

#Sequence running time should be counted from "Sequence ....S started date" to "ECM data....... acquisition date". However, when the sequence name or data file name is long,
#the statement may begin on the next line and '>' is added at the end of the line above to show the two lines are connected.
def sequence_running_times(sptexts, start_time, stop_time):
    start_time_list = []
    stop_time_list = []
    start_text = ''
    completion_text = ''
    i = 0
    while i < len(sptexts):
        if sptexts[i].startswith('Sequence') and not string_time_compare(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", sptexts[i]).group(), start_time):
            search = re.search(r"(Sequence)\s+(.*?)\s+(\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)", sptexts[i])
            start_time = search.group(3)
            start_text = search.group(2)
            i += 1
            #reconnect the lines to located 'sequence.... started date'
            while not re.search(r"\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", sptexts[i]) and sptexts[i].startswith(' '):
                start_text += sptexts[i].strip()
                i += 1
            while sptexts[i].startswith('ECM') and string_time_compare(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", sptexts[i]).group(), stop_time):
                search1 = re.search(r"(ECM)\s+(.*?)\s+(\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)", sptexts[i])
                completion_text = search1.group(2)
                completion_time = search1.group(3)
                i += 1
            #reconnect the lines to located 'ECM.... acquisition date'
            while not re.search(r"\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", sptexts[i]) and sptexts[i].startswith(' '):
                completion_text += sptexts[i].strip()
                i += 1
            #remove '>' to connect the line to show the key words.
            start_text = start_text.replace('>', '')
            completion_text = completion_text.replace('>', '')
            if 'started' in start_text.lower() and 'acquisition' in completion_text.lower():
                start_time_list.append(start_time)
                stop_time_list.append(completion_time)
            start_text = ''
            completion_text = ''
        else:
            i += 1
    return start_time_list, stop_time_list

#calculate the used hours.
def total_times(log_path, start_time, end_time):
    reader = PdfReader(log_path)
    texts = []
    sequence_lengths = 0
    sp_number = start_page(reader, start_time = start_time)
    for i in range(sp_number, len(reader.pages)):
        texts += reader.pages[i].extract_text().split('\n')
    start_time_list, end_time_list = sequence_running_times(texts, start_time, end_time)
    for t in range(len(start_time_list)):
        sequence_lengths += string_time_diff(start_time_list[t], end_time_list[t])
    return sequence_lengths

#Make GUI.
root = tk.Tk()
root.geometry("740x440")
root.title('LC Used Time Calculator')
root.configure(bg = '#333333')

def calculate():
    try:
        messagebox.showinfo(title = 'Result in hours.', message = total_times(path_entry.get(), sd_entry.get(), ed_entry.get()))
    except FileNotFoundError:
        messagebox.showinfo(title = 'Logbook file path is not correct.', message = 'Please enter the correct absolute path of logbook with .pdf extension.')
    except ValueError:
        messagebox.showinfo(title = 'Date format is not correct.', message = 'Please enter the dates in the format of mm/dd/yyyy hh:mm:ss AM/PM.')
    except OSError:
        messagebox.showinfo(title = 'Logbook file path is not correct.', message = 'Please remove the quotation marks')


frame = tk.Frame(bg = '#333333')
label = tk.Label(frame, text = 'Calculate LC/GC used time, be patient!', font = ('Arial', 30), bg = '#333333', fg = '#FFFFFF')
path_label = tk.Label(frame, text = 'Absolute LC/GC logbook path', font = ('Arial', 16), bg = '#333333', fg = '#FFFFFF')
start_date_label = tk.Label(frame, text = 'Starting date (mm/dd/yyyy hh:mm:ss AM/PM)', font = ('Arial', 16), bg = '#333333', fg = '#FFFFFF')
end_date_label = tk.Label(frame, text = 'Ending date (mm/dd/yyyy hh:mm:ss AM/PM)', font = ('Arial', 16), bg = '#333333', fg = '#FFFFFF')
path_entry = tk.Entry(frame, font = ('Arial', 16))
sd_entry = tk.Entry(frame, font = ('Arial', 16))
ed_entry = tk.Entry(frame, font = ('Arial', 16))
button = tk.Button(frame, text = 'Calculate', font = ('Arial', 16), command = calculate)
label.grid(row = 0, column = 0, columnspan = 2,  sticky = 'news', pady = 40)
path_label.grid(row = 1, column = 0)
path_entry.grid(row = 1, column = 1, pady = 20)
start_date_label.grid(row = 2, column = 0)
sd_entry.grid(row = 2, column = 1, pady = 20)
end_date_label.grid(row = 3, column = 0)
ed_entry.grid(row = 3, column = 1, pady = 20)
button.grid(row = 4, column = 1, pady = 30)

frame.pack()

root.mainloop()