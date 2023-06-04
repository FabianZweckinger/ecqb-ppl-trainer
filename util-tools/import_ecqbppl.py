from PyPDF2 import PdfReader
import re
import json

# Make sure the spl-ecqb-ppl files are placed in sourcefiles.

files = {'ALW': '../sourcefiles/SPL-ECQB-PPL-10-ALW-ge.pdf',
         'HPL': '../sourcefiles/SPL-ECQB-PPL-20-HPL-ge.pdf',
         'MET': '../sourcefiles/SPL-ECQB-PPL-30-MET-ge.pdf',
         'COM': '../sourcefiles/SPL-ECQB-PPL-40-COM-ge.pdf',
         'PFA': '../sourcefiles/SPL-ECQB-PPL-50-PFA-ge.pdf',
         'OPR': '../sourcefiles/SPL-ECQB-PPL-60-OPR-ge.pdf',
         'FPP': '../sourcefiles/SPL-ECQB-PPL-70-FPP-ge.pdf',
         'AGK': '../sourcefiles/SPL-ECQB-PPL-80-AGK-ge.pdf',
         'NAV': '../sourcefiles/SPL-ECQB-PPL-90-NAV-ge.pdf', }

json_data = {'questions': {'ALW': [], 'HPL': [], 'MET': [],
                           'COM': [], 'PFA': [], 'OPR': [],
                           'FPP': [], 'AGK': [], 'NAV': []}}

for file in files:
    topic = file

    reader = PdfReader(files['ALW'])

    for page in reader.pages:

        text = page.extract_text()

        questions = text.split('Pts.: 1,00')

        for s in questions[1:]:
            s = s.strip()  # Cut away spaces

            s = s.split(' ', 1)[1]

            t = re.split('[¨þ]', s)  # Regex

            question = t[0]

            answers = [t[1].split(')')[1].strip(),
                       t[2].split(')')[1].strip(),
                       t[3].split(')')[1].strip(),
                       t[4].split('   ')[0].split(')')[1].strip()]

            true_answer = ord(s.split('þ')[1][0]) - ord('A')

            json_data['questions'][topic].append({'question': question,
                                                  'answers': answers,
                                                  'true_answer': true_answer,
                                                  })

print(json_data)

with open('../database/questions.json', 'w') as f:
    json.dump(json_data, f)
