import customtkinter
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import json,uuid,base64
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from threading import Thread
from queue import Queue
from enum import Enum,auto
from datetime import datetime

#pyinstaller gui.py --onefile --windowed --name "Chem App Question Maker"

class TicketPurpose(Enum):
    MAKE_QUESTION = auto()
    
class Ticket:
    def __init__(self, ticket_type:TicketPurpose, ticket_value):
        self.ticket_type = ticket_type
        self.ticket_value = ticket_value

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.active_asyncs = []
        self.queue_tickets = Queue()
        self.bind("<<CheckQueue>>", self.check_queue)

        self.bind_all("<Button-1>", lambda event: event.widget.focus_set())

        # ==========================
        #         GUI SETUP
        # ==========================
        # configure window
        self.title("Chem App Question Maker")
        self.geometry(f"{1200}x{780}")

        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((0), weight=1)
        self.grid_rowconfigure((1), weight=0)

        self.statusbar = customtkinter.CTkProgressBar(self)
        self.statusbar.grid(row=1, column=0, padx=(0, 0), pady=(0, 0), sticky="ew")

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.tabview.add("Question Maker")
        self.tabview.add("Log")
        main_tab = self.tabview.tab("Question Maker")
        log_tab = self.tabview.tab("Log")

        main_tab.grid_columnconfigure(0, weight=1)
        main_tab.grid_rowconfigure(5, weight=0) 
        main_tab.grid_rowconfigure((1,2), weight=0)
        log_tab.grid_columnconfigure(0, weight=1)
        log_tab.grid_rowconfigure(0, weight=1)

        # ------- Main Tab -------
        main_row_index = 0

        self.question_type_label = customtkinter.CTkLabel(main_tab, text="Question Type", font=customtkinter.CTkFont(size=20, weight="bold"), anchor="center")
        self.question_type_label.grid(row=main_row_index, column=0, padx=20, pady=(5, 0), sticky="ew")
        main_row_index += 1
        self.question_type_label.update()
        self.question_selector_menu = customtkinter.CTkOptionMenu(main_tab, command=self.selected_question_type,values=["MCQ","Drop-down","Fill in the Blank"], width=300, dynamic_resizing=False)
        self.question_selector_menu.grid(row=main_row_index, column=0, padx=20, pady=(5, 5))
        main_row_index += 1

        self.question_details_frame_1 = customtkinter.CTkFrame(master=main_tab)
        self.question_details_frame_1.grid(row=main_row_index,column=0, padx=20, pady=(10, 0))
        self.question_details_frame_1.columnconfigure((0,1,2,3), weight=0)
        self.question_details_frame_1.rowconfigure((0,1,2,3), weight=0)
        self.question_details_frame_1.update()
        main_row_index += 1

        validateCmd = (self.register(self.validate_number))
        self.question_chapter_label = customtkinter.CTkLabel(self.question_details_frame_1, text="Chapter: ")
        self.question_chapter_label.grid(row=0, column=0, padx=(20,0), sticky="w")
        self.question_chapter_entry = customtkinter.CTkEntry(self.question_details_frame_1, placeholder_text='1', validate='all', validatecommand=(validateCmd, '%P'))
        self.question_chapter_entry.grid(row=0, column=1, padx=(5,20), sticky="ew")

        self.question_number_label = customtkinter.CTkLabel(self.question_details_frame_1, text="Question Number: ")
        self.question_number_label.grid(row=0, column=2, padx=(20,0), sticky="w")
        self.question_number_entry = customtkinter.CTkEntry(self.question_details_frame_1, placeholder_text='1', validate='all', validatecommand=(validateCmd, '%P'))
        self.question_number_entry.grid(row=0, column=3, padx=(5,20), sticky="ew")

        self.question_details_frame_2 = customtkinter.CTkFrame(master=main_tab)
        self.question_details_frame_2.grid(row=main_row_index,column=0, padx=20, pady=(10, 0))
        self.question_details_frame_2.columnconfigure((0,1,2,3), weight=0)
        self.question_details_frame_2.rowconfigure((0,1,2,3), weight=0)
        self.question_details_frame_2.update()
        main_row_index += 1

        self.question_title_label = customtkinter.CTkLabel(self.question_details_frame_2, text="Question Title: ")
        self.question_title_label.grid(row=0, column=0, padx=(20,0), sticky="w")
        self.question_title_entry = customtkinter.CTkEntry(self.question_details_frame_2, placeholder_text='Identify Organic Product', width=300)
        self.question_title_entry.grid(row=0, column=1, padx=(5,20), sticky="ew")

        self.question_difficulty_label = customtkinter.CTkLabel(self.question_details_frame_2, text="Difficulty: ")
        self.question_difficulty_label.grid(row=0, column=2, padx=(20,0), sticky="w")
        self.question_difficulty_menu = customtkinter.CTkOptionMenu(self.question_details_frame_2, command=self.selected_question_difficulty,values=["Easy","Medium","Hard"], width=100, dynamic_resizing=False)
        self.question_difficulty_menu.grid(row=0, column=3, padx=(5,20))

        self.question_desc_label = customtkinter.CTkLabel(main_tab, text="Question Description")
        self.question_desc_label.grid(row=main_row_index, column=0, padx=20, sticky="w")
        main_row_index += 1
        self.question_desc_entry = customtkinter.CTkEntry(main_tab, placeholder_text='What is the result of the follwing reaction?')
        self.question_desc_entry.grid(row=main_row_index, column=0, padx=20, pady=(3, 5), sticky="ew")
        main_row_index += 1

        self.question_upload_frame = customtkinter.CTkFrame(master=main_tab)
        self.question_upload_frame.grid(row=main_row_index,column=0, padx=20, pady=(10, 0))
        self.question_upload_frame.columnconfigure(1, weight=1)
        self.question_upload_frame.columnconfigure((0,1,2,3), weight=1)
        self.question_upload_frame.update()
        main_row_index += 1

        self.question_upload_label = customtkinter.CTkLabel(self.question_upload_frame, text="Selected File: ")
        self.question_upload_label.grid(row=0, column=0, padx=(20,0), sticky="w")
        self.question_upload_button = customtkinter.CTkButton(self.question_upload_frame, text="Select Question File", font=customtkinter.CTkFont(size=14, weight="bold"), command=self.get_question_file)
        self.question_upload_button.grid(row=0, column=2, padx=(20,0))

        self.question_answers_frame = customtkinter.CTkScrollableFrame(master=main_tab, label_text="Answers", label_font=customtkinter.CTkFont(size=16, weight="bold"))
        self.question_answers_frame.grid(row=main_row_index,column=0, padx=20, pady=(10, 0), sticky="nsew")
        self.question_answers_frame.columnconfigure((0), weight=1)
        self.question_answers_frame.update()
        main_row_index += 1

        self.new_answer_frame = customtkinter.CTkFrame(master=main_tab)
        self.new_answer_frame.grid(row=main_row_index,column=0, padx=20, pady=(10, 0))
        self.new_answer_frame.columnconfigure(1, weight=1)
        self.new_answer_frame.columnconfigure((0,1,2,3), weight=1)
        self.new_answer_frame.update()
        main_row_index += 1

        self.new_answer_label = customtkinter.CTkLabel(self.new_answer_frame, text="New Answer: ")
        self.new_answer_label.grid(row=0, column=0, padx=(20,0), sticky="w")
        self.new_answer_entry = customtkinter.CTkEntry(self.new_answer_frame, placeholder_text='2,4-dimethylbenzene',width=250)
        self.new_answer_entry.grid(row=0, column=1, padx=(5,20), sticky="ew")
        self.new_answer_button = customtkinter.CTkButton(self.new_answer_frame, text="Add Answer", font=customtkinter.CTkFont(size=14, weight="bold"), command=self.add_answer)
        self.new_answer_button.grid(row=0, column=2, padx=(0,0))
        #self.new_answer_upload_button = customtkinter.CTkButton(self.new_answer_frame, text="Add Answer With File", font=customtkinter.CTkFont(size=14, weight="bold"), command=self.add_answer_with_file)
        #self.new_answer_upload_button.grid(row=0, column=3, padx=(20,0))

        self.question_feedback_label = customtkinter.CTkLabel(main_tab, text="Question Feedback")
        self.question_feedback_label.grid(row=main_row_index, column=0, padx=20, pady=(10, 0), sticky="w")
        main_row_index += 1
        self.question_feedback_entry = customtkinter.CTkEntry(main_tab, placeholder_text='The correct answer is 1,3-dimethylbenzene')
        self.question_feedback_entry.grid(row=main_row_index, column=0, padx=20, pady=(3, 5), sticky="ew")
        main_row_index += 1

        self.feedback_upload_frame = customtkinter.CTkFrame(master=main_tab)
        self.feedback_upload_frame.grid(row=main_row_index,column=0, padx=20, pady=(10, 0))
        self.feedback_upload_frame.columnconfigure(1, weight=1)
        self.feedback_upload_frame.columnconfigure((0,1,2,3), weight=1)
        self.feedback_upload_frame.update()
        main_row_index += 1

        self.feedback_upload_label = customtkinter.CTkLabel(self.feedback_upload_frame, text="Selected File: ")
        self.feedback_upload_label.grid(row=0, column=0, padx=(20,0), sticky="w")
        self.feedback_upload_button = customtkinter.CTkButton(self.feedback_upload_frame, text="Select Feedback File", font=customtkinter.CTkFont(size=14, weight="bold"), command=self.get_feedback_file)
        self.feedback_upload_button.grid(row=0, column=2, padx=(20,0))
        
        self.export_button = customtkinter.CTkButton(main_tab, text="Export Question", font=customtkinter.CTkFont(size=28, weight="bold"), command=self.export_question)
        self.export_button.grid(row=main_row_index, column=0, padx=20, pady=10)
        main_row_index += 1



        # ------- Log Tab -------
        self.log_textbox = customtkinter.CTkTextbox(master=log_tab, width=250, wrap="word")
        self.log_textbox.grid(row=0, column=0, padx=(20, 0), pady=(0, 0), sticky="nsew")
        self.log_textbox.configure(state="disabled")
        self.log(f"Launching Question Maker")

        # set default values
        self.question_selector_menu.set("MCQ")
        self.question_difficulty_menu.set("Easy")
        self.statusbar.set(1)
        self.question_type = "MCQ"
        self.question_difficulty = "Easy"
        self.question_number = 1
        self.question_chapter = 1
        self.correct_answer = -1
        self.answers = []
        self.question_file = ""
        self.answer_files = []
        self.feedback_file = ""


    # ==============================================================
    #                         GUI EVENTS
    # ==============================================================

    def export_question(self):
        if not TicketPurpose.MAKE_QUESTION in self.active_asyncs:
            Thread(target=self.export_question_async,daemon=True).start()
        else:
            self.log("Already Exporting Question")

    def selected_question_type(self, question_type: str):
        self.question_type = question_type
        for answer in self.answers:
            if question_type == "Fill in the Blank":
                answer.select()
                answer.configure(state="disabled")
            else:
                answer.configure(state="normal")
                answer.deselect()
    
    def selected_question_difficulty(self, question_difficulty: str):
        self.question_difficulty = question_difficulty

    def add_answer(self):
        checkbox = customtkinter.CTkCheckBox(self.question_answers_frame, text=self.new_answer_entry.get())
        checkbox.grid(row = len(self.answers),padx=20,pady=10)
        if self.question_type == "Fill in the Blank":
                checkbox.select()
                checkbox.configure(state="disabled")
        self.answers.append(checkbox)
        self.answer_files.append("")

    def add_answer_with_file(self):
        answer_file = self.select_file()
        checkbox = customtkinter.CTkCheckBox(self.question_answers_frame, text=self.new_answer_entry.get()+" (With File)")
        checkbox.grid(row = len(self.answers),padx=20,pady=10)
        if self.question_type == "Fill in the Blank":
                checkbox.select()
                checkbox.configure(state="disabled")
        self.answers.append(checkbox)
        self.answer_files.append(answer_file)

    def get_question_file(self):
        self.question_file = self.select_file()
        self.question_upload_label.configure(text=f"Selected File: {self.question_file}")

    def get_feedback_file(self):
        self.feedback_file = self.select_file()
        self.feedback_upload_label.configure(text=f"Selected File: {self.feedback_file}")


    # ==============================================================
    #                          ASYNC CALLS
    # ==============================================================

    def add_active_async(self, ticket_type: TicketPurpose):
        self.active_asyncs.append(ticket_type)
        self.statusbar.configure(mode="indeterminate")
        self.statusbar.start()

    def export_question_async(self):
        self.log("Exporting Question")
        self.add_active_async(TicketPurpose.MAKE_QUESTION)
        Path("./export").mkdir(parents=True, exist_ok=True)
        correct_answers = []
        answers = []
        for answer in self.answers:
            if answer.get() == 1:
                correct_answers.append(self.answers.index(answer))
            answers.append(answer.cget("text"))
        
        if self.question_chapter_entry.get().isdigit():
            self.question_chapter = int(self.question_chapter_entry.get())
        else:
            self.question_chapter = 1

        if self.question_number_entry.get().isdigit():
            self.question_number = int(self.question_number_entry.get())
        
        question_base64 = ""
        if self.question_file is not None and self.question_file:
            data = open(self.question_file, "r").read()
            data_byte = data.encode("utf-8")
            question_base64 = base64.b64encode(data_byte).decode('utf-8')
        feedback_base64 = ""
        if self.feedback_file is not None and self.feedback_file:
            data = open(self.question_file, "r").read()
            data_byte = data.encode("utf-8")
            feedback_base64 = base64.b64encode(data_byte).decode('utf-8')

        question = {
            "id": str(uuid.uuid4()),
            "type": self.question_type,
            "chapter": self.question_chapter,
            "question": self.question_number,
            "title": self.question_title_entry.get(),
            "difficulty": self.question_difficulty,
            "description": self.question_desc_entry.get(),
            "options": answers,
            "correctAnswers": correct_answers,
            "feedback": self.question_feedback_entry.get(),
            "questionMolFile": question_base64,
            "feedbackMolFile": feedback_base64
        }

        name = f"question_{self.question_chapter}-{self.question_number}"

        with open(f"./export/{name}.json",'w') as file:
            file.write(json.dumps(question, indent=4))

        self.generate_ticket_event(Ticket(TicketPurpose.MAKE_QUESTION,question))

    # ==============================================================
    #                       QUEUE PROCESSOR
    # ==============================================================

    def check_queue(self, event):
        ticket: Ticket
        ticket = self.queue_tickets.get()

        if ticket.ticket_type == TicketPurpose.MAKE_QUESTION:
            self.question_number += 1
            self.question_number_entry.delete("0","end")
            self.question_number_entry.insert("0",str(self.question_number))
            for answer in self.answers:
                answer.destroy()
            self.answers.clear()
            self.answer_files.clear()
            self.question_file = ""
            self.feedback_file = ""
            self.question_upload_label.configure(text=f"Selected File: ")
            self.feedback_upload_label.configure(text=f"Selected File: ")

        
        self.active_asyncs.remove(ticket.ticket_type)
        if not self.active_asyncs:
            self.statusbar.configure(mode="determinate")
            self.statusbar.set(1)
            self.statusbar.stop()

    # ==============================================================
    #                      UTILITY FUNCTIONS
    # ==============================================================

    def generate_ticket_event(self, ticket):
        self.queue_tickets.put(ticket)
        self.event_generate("<<CheckQueue>>")

    def log(self, message):
        self.log_textbox.configure(state="normal")
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        self.log_textbox.insert("end",timestamp + " " + message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.update()

    def validate_number(self, P):
        if str.isdigit(P) or P == "":
            return True
        else:
            return False
    
    def select_file(self):
        filetypes = (
            ('Mol Files', '*.mol'),
            ('All files', '*.*')
        )

        selected_file = fd.askopenfilename(
            title='Open a file',
            initialdir='./',
            filetypes=filetypes)

        # showinfo(
        #     title='Selected File',
        #     message=selected_file
        # )
        return selected_file

def main():
    customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    app = App()
    app.mainloop()

if __name__ == "__main__":
    app = App()
    app.mainloop()