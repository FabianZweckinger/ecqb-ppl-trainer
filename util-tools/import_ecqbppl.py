import os
from PyPDF2 import PdfReader
import json
from tqdm import tqdm
import fitz

# Make sure the spl-ecqb-ppl files are placed in /sourcefiles directory.

os.makedirs("../database/images", exist_ok=True)

files = {'ALW': '../sourcefiles/SPL-ECQB-PPL-10-ALW-ge.pdf',
         'HPL': '../sourcefiles/SPL-ECQB-PPL-20-HPL-ge.pdf',
         'MET': '../sourcefiles/SPL-ECQB-PPL-30-MET-ge.pdf',
         'COM': '../sourcefiles/SPL-ECQB-PPL-40-COM-ge.pdf',
         'PFA': '../sourcefiles/SPL-ECQB-PPL-51-PFA-ge.pdf',
         'OPR': '../sourcefiles/SPL-ECQB-PPL-60-OPR-ge.pdf',
         'FPP': '../sourcefiles/SPL-ECQB-PPL-70-FPP-ge.pdf',
         'AGK': '../sourcefiles/SPL-ECQB-PPL-80-AGK-ge.pdf',
         'NAV': '../sourcefiles/SPL-ECQB-PPL-90-NAV-ge.pdf', }

json_data = {'ALW': [], 'HPL': [], 'MET': [],
             'COM': [], 'PFA': [], 'OPR': [],
             'FPP': [], 'AGK': [], 'NAV': []}

for file in tqdm(files, desc="files"):
    topic = file

    reader = PdfReader(files[topic])

    doc = fitz.Document(files[topic])
    questions_buffer = {}
    page_index = 0
    image_index = 1

    for page in doc:

        if page_index > 1:
            lines = page.get_textpage().extractText().split("\n")

            result_question_nr = -1
            result_answers = ["", "", "", ""]
            result_true_answer = -1
            result_question = ""
            result_optional_image_path = ""

            # Temporal loop control variables
            expects_question = False
            answer_count = 0
            answer_count_reverse = 3

            for line in reversed(lines):
                if expects_question and answer_count % 4 == 0:

                    if line.strip().isnumeric():
                        answer_count_reverse = 3
                        expects_question = False
                        result_question_nr = int(line.strip())

                        if result_question.find("Please pay attention to annex") != -1:
                            new_result_question = ""
                            for qline in result_question.splitlines():
                                if not qline.startswith("Please pay attention to annex"):
                                    new_result_question += qline + "\n"
                                else:
                                    split_line = qline.split(" ")
                                    result_optional_image_path = split_line[4] + "" + split_line[5]
                            result_question = new_result_question

                        questions_buffer[result_question_nr] = {
                            'question': result_question, 'answers': result_answers,
                            'trueAnswer': result_true_answer, 'image': result_optional_image_path
                        }

                        result_question = ""
                        result_optional_image_path = ""

                    else:
                        if result_question != "":
                            result_question = line.strip() + "\n" + result_question
                        else:
                            result_question = line

                if line.startswith(("¨", "þ")):
                    expects_question = True

                    # Extract question from line string e.g. ¨A) Some answer   OR   þC) Other answer
                    # answer_count_reverse is used, because the page is read in reverse string from answer "D"
                    result_answers[answer_count_reverse] = line.split(')', 1)[1].strip()

                    if line.startswith("þ"):
                        result_true_answer = ord(line.split('þ')[1][0]) - ord('A')

                    answer_count_reverse -= 1
                    answer_count += 1

        # print(page.get_images())
        page_index += 1

        if page.get_textpage().extractText().startswith("Annexes"):
            for img in page.get_images():
                xref = img[0]
                image = doc.extract_image(xref)
                pix = fitz.Pixmap(doc, xref)
                pix.save("../database/images/" + topic + "annex" + str(image_index) + ".png")
                image_index += 1

        # Copy page_questions_buffer into json_data
    for key, value in sorted(questions_buffer.items()):
        print(value)
        json_data[topic].append(value)

# print(json_data)

with open('../database/questions.json', 'w') as f:
    json.dump(json_data, f)
