from PyPDF2 import PdfReader
import re
import json

# Make sure the spl-ecqb-ppl files are placed in /sourcefiles directory.

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

for file in files:
    topic = file

    reader = PdfReader(files[topic])

    for page in reader.pages[2:]:
        text = page.extract_text()

        if not text.startswith("Annexes"):
            if topic == 'ALW':
                new_text = ""
                for i in range(text.count('Pts.: 1,00  ')):
                    new_text = new_text + text.split('Pts.: 1,00  ')[i + 1].split('   ')[0] + '   '
                text = new_text
            else:
                text = text[20:]

            text = text.split(" ", 1)[1].strip()

            for q in re.split("\s{3}(\d+) ", text):
                if len(q) > 3:
                    q = q.strip()  # Cut away spaces

                    t = re.split('[¨þ]', q)  # Regex

                    question = t[0]

                    answers = [t[1].split(')', 1)[1].strip(),
                               t[2].split(')', 1)[1].strip(),
                               t[3].split(')', 1)[1].strip(),
                               t[4].split('   ')[0].split(')', 1)[1].strip()]

                    true_answer = ord(q.split('þ')[1][0]) - ord('A')

                    json_data[topic].append({'question': question,
                                             'answers': answers,
                                             'true_answer': true_answer,
                                             })

print(json_data)

with open('../database/questions.json', 'w') as f:
    json.dump(json_data, f)
