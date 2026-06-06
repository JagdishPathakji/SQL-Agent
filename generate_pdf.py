import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count and draw running headers/footers.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4B5563"))
        
        # Cover page (page 1) should not have headers or footers
        if self._pageNumber == 1:
            self.restoreState()
            return

        # Running Header
        self.drawString(54, 750, "TCS NQT Preparation Question Bank")
        self.drawRightString(558, 750, "Quantitative, Logical, Verbal & Coding")
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Running Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidential - Prepared for Personal Examination Study")
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def build_pdf(filename="TCS_Question_Bank.pdf"):
    # Setup document geometry (Margins at 0.75 in / 54 pt, printable width = 504 pt)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles to fit the design system
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=30,
        leading=38,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=15,
        alignment=1 # Centered
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=30,
        alignment=1 # Centered
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=5,
        alignment=1
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=18,
        spaceAfter=12,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'QuestionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'QuestionBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=6
    )
    
    opt_style = ParagraphStyle(
        'OptionText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=3
    )
    
    ans_style = ParagraphStyle(
        'AnswerText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#16A34A"),
        spaceAfter=4
    )
    
    key_text_style = ParagraphStyle(
        'KeyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=10
    )

    story = []

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 150))
    story.append(Paragraph("TCS NQT PLACEMENT PREPARATION", title_style))
    story.append(Paragraph("Practice Question Bank & Answer Key", subtitle_style))
    
    # Visual accent bar
    bar_data = [['']]
    bar_table = Table(bar_data, colWidths=[200], rowHeights=[4])
    bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2563EB")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(bar_table)
    story.append(Spacer(1, 150))
    
    # Metadata
    story.append(Paragraph("SUBJECTS: QUANTITATIVE APTITUDE, LOGICAL REASONING, VERBAL ABILITY & CODING", meta_style))
    story.append(Paragraph("DATE GENERATED: JUNE 2026", meta_style))
    story.append(Paragraph("PREPARED BY: ANTIGRAVITY AI PARTNER", meta_style))
    story.append(PageBreak())

    # ==================== SECTIONS DATA ====================
    sections = [
        {
            "title": "1. Quantitative Aptitude (Slot 1)",
            "questions": [
                {
                    "num": 1,
                    "text": "What is the sum of LCM and HCF of 5/18, 35/9 and 15/63?",
                    "options": ["A. 1475/252", "B. 1475/126", "C. 625/252", "D. 625/126"],
                    "ans": "B. 1475/126"
                },
                {
                    "num": 2,
                    "text": "The reciprocal of a fraction is more than itself by 31/240. How much is the difference between the possible values of the fraction more than 2? (Note: Original text had typo '21/240' instead of '31/240')",
                    "options": ["A. 1/15", "B. 1/16", "C. 1/240", "D. 1/256"],
                    "ans": "C. 1/240"
                },
                {
                    "num": 3,
                    "text": "A person invested 2/3 of his capital at the rate of 6% and 1/5 at the rate of 10% and the remainder at the rate of 15%. If his actual income is Rs. 3,600, the capital will be: (Note: The options provided in the exam were incorrect, correct answer is Rs. 45,000)",
                    "options": ["A. Rs. 5,000", "B. Rs. 2,500", "C. Rs. 7,500", "D. Rs. 4,500"],
                    "ans": "Correct Answer: Rs. 45,000"
                },
                {
                    "num": 4,
                    "text": "If 8^(x+1) + 8^(1-x) = 20, then x = ?",
                    "options": ["A. 1/4, -1/4", "B. 1/2, -1/2", "C. 1/3, -1/3", "D. 1/5, -1/5"],
                    "ans": "C. 1/3, -1/3"
                },
                {
                    "num": 5,
                    "text": "At an academic institution, the break-up of holidays in 2016 was as under:\n- 52 weekends\n- 30 days of summer vacation which includes 4 weekends\n- Autumn and Winter Breaks of (10+10) days each inclusive of one weekend\n- 14 holidays on special occasions out of which one was a Saturday and one Sunday\nWhat was the percentage (correct up to two decimal places) of the number of holidays?",
                    "options": ["A. 45.90%", "B. 42.08%", "C. 42.19%", "D. 43.73%"],
                    "ans": "B. 42.08%"
                },
                {
                    "num": 6,
                    "text": "In a family of 10 adults and a few minors, the average consumption of flour is 12 kg. If the average consumption per adult and minor is 15 and 7 kg respectively, what is the number of minors?",
                    "options": ["A. 6", "B. 7", "C. 5", "D. 8"],
                    "ans": "A. 6"
                },
                {
                    "num": 7,
                    "text": "A person lends 35% of his sum of money at 12.5% per annum, 50% at 10% per annum and the rest at 18% per annum rate of interest. What would be the annual rate (in approx), if the interest is calculated on the whole sum?",
                    "options": ["A. 13%", "B. 14.5%", "C. 13.5%", "D. 13.75%"],
                    "ans": "C. 13.5%"
                },
                {
                    "num": 8,
                    "text": "The average weight of 6 people increases from 24 to 31.5 kg when one of them leaves the group and a new person joins in. If the weight of the person who joined is 60 kg, find the weight of the person who left the group?",
                    "options": ["A. 22.5 kg", "B. 37.5 kg", "C. 15 kg", "D. 30 kg"],
                    "ans": "C. 15 kg"
                },
                {
                    "num": 9,
                    "text": "There are three types of alloys A, B and C. The ratio of Copper, Tin and Nickel in A, B and C is 16:3:1, 15:3:2 and 14:5:1 respectively. If the amount of A, B, and C (10 kg, 15 kg and 50 kg) are mixed together, what is the final ratio of Copper, Tin and Nickel in the mixture?",
                    "options": ["A. 217 : 65 : 18", "B. 217 : 65 : 81", "C. 217 : 56 : 18", "D. 127 : 65 : 18"],
                    "ans": "A. 217 : 65 : 18"
                },
                {
                    "num": 10,
                    "text": "Rahul bought a watch (marked price Rs. 1,875) at a 24% discount. Rahul sold it to Rohit earning 28% profit. Rohit then set the marked price 25% higher than the cost price he paid. Mohit bought it from Rohit at a 15% discount. Mohit marked up the price 50% higher than his cost and sold it to Rahul at some discount. If Rahul had to pay Rs. 28.5 extra than the initial price he paid, what percent discount did Mohit sell the watch?",
                    "options": ["A. 35%", "B. 50%", "C. 45%", "D. 40%"],
                    "ans": "B. 50%"
                },
                {
                    "num": 11,
                    "text": "If a road of 210 km can be constructed by 540 workmen in 28 days, how many workmen are required to build a road of 150 km in 18 days?",
                    "options": ["A. 600", "B. 300", "C. 650", "D. 450"],
                    "ans": "A. 600"
                },
                {
                    "num": 12,
                    "text": "Two stations P and Q are 42 km apart. Rohit and Mohit start from P to Q at the speed of 6 km/h and 8 km/h, respectively. Mohit reaches Q first and returns to meet Rohit at R. Determine the distance between P and R in km.",
                    "options": ["A. 30 km", "B. 36 km", "C. 33 km", "D. 27 km"],
                    "ans": "B. 36 km"
                },
                {
                    "num": 13,
                    "text": "The railway platform at a certain station is 248m long. In how many seconds is it cleared by an Express train which is 127m long and travels at a speed of 150 km/h?",
                    "options": ["A. 9 seconds", "B. 12 seconds", "C. 8 seconds", "D. 10 seconds"],
                    "ans": "A. 9 seconds"
                },
                {
                    "num": 14,
                    "text": "Nookaraju and Bhavana have their salaries in the ratio 7:3. As Bhavana is skilled, she got an increment of Rs. 5,000. But Nookaraju's performance is not up to mark and he got a decrement of Rs. 1,000. If their present salaries are in the ratio of 1:1, then Nookaraju's present salary is:",
                    "options": ["A. Rs. 8,500", "B. Rs. 9,500", "C. Rs. 15,000", "D. Rs. 10,500"],
                    "ans": "B. Rs. 9,500"
                },
                {
                    "num": 15,
                    "text": "The perimeter of a regular hexagon with area of 21*sqrt(3) cm^2 is:",
                    "options": ["A. 12*sqrt(3)", "B. 6*sqrt(14)", "C. 9*sqrt(3)", "D. 7*sqrt(15)"],
                    "ans": "B. 6*sqrt(14)"
                },
                {
                    "num": 16,
                    "text": "If the first quartile Q1 = 28 and third quartile Q3 = 42, then the coefficient of quartile deviation is:",
                    "options": ["A. 1/5", "B. 1/3", "C. 1/4", "D. 1/2"],
                    "ans": "A. 1/5"
                },
                {
                    "num": 17,
                    "text": "A farmer purchased a Trolley and a Tractor for Rs. 8,00,000. He sold the Tractor at a profit of 30% and the Trolley at a loss of 10%. In this deal, he got an overall profit of 3%. What is the ratio of the cost price of tractor and trolley?",
                    "options": ["A. 54:31", "B. 27:13", "C. 13:27", "D. 13:54"],
                    "ans": "C. 13:27"
                },
                {
                    "num": 18,
                    "text": "The marked price of a marker is 5_5/9% higher than its cost price. A discount of 5_5/19% is given on its marked price. Find the difference between cost price and selling price.",
                    "options": ["No options provided"],
                    "ans": "0 (SP = CP)"
                }
            ]
        },
        {
            "title": "2. Verbal Ability (Slot 1)",
            "questions": [
                {
                    "num": 1,
                    "text": "Parts of the given sentence have been given as options. One of them contains a grammatical error. Select the option that has the error:\n'A university training enables a graduate seeing things as they are, and to disentangle a plethora of thoughts'",
                    "options": ["A. to disentangle a plethora of thoughts", "B. a graduate seeing things as they are", "C. to go right to the point", "D. A university training enables"],
                    "ans": "B. a graduate seeing things as they are"
                },
                {
                    "num": 2,
                    "text": "Identify the part of the sentence that has an error:\n'I like to sit at the window for hours and see children playing in the park'",
                    "options": ["A. I like to sit at", "B. The window for hours", "C. In the park", "D. And see children playing"],
                    "ans": "D. And see children playing"
                },
                {
                    "num": 3,
                    "text": "Identify the phrase which best replaces the wrong phrase in the sentence:\n'Explorers embody the finest spirit in human nature which is to seek new challenges, discover new worlds and create new frontiers and one such rare achievement of the indomitable spirit is the ascending of Mount Everest by Hillary and Tenzing.'",
                    "options": ["A. Finer spirits", "B. By the dominant", "C. To have sought", "D. The ascent"],
                    "ans": "D. The ascent"
                },
                {
                    "num": 4,
                    "text": "Select the most appropriate set of options to fill in the blanks:\n'Bill Gates dropped out from Harvard within a year, Then he formed Microsoft. Microsoft's (A) _______ is a computer on every desk and Microsoft software on every computer. Bill is a visionary and works very hard to (B) ______ his vision. His belief in high intelligence and hard work had put him where he is today. He does not believe in mere luck or God's grace, but just hard work and (C) ______. His beliefs are so powerful that they have helped him increase his wealth and establish his (D) _______ in the industry.'",
                    "options": [
                        "A. (A)Symbol (B) attain (C)investment (D) control",
                        "B. (A)target (B) progress(C)frankness (D) importance",
                        "C. (A)logo(B)believe (C)blessings (D) esteem",
                        "D. (A)vision (B) achieve (C)competitiveness (D) monopoly"
                    ],
                    "ans": "D. (A)vision (B) achieve (C)competitiveness (D) monopoly"
                },
                {
                    "num": 5,
                    "text": "Select the most appropriate set of options to fill in the blanks:\n'Mexico is home to more species of oak than any country in the world, though many of them are (1) ___ . In the case of the arroyo oak, as it is known, the species now faces a particularly (2)__ problem. Though plenty of trees aged more than 100 years can be found, locals (3)__ that in recent years there had been no seedlings that have sprouted from their acorns in sight. For some reason, the trees had (4)__ stopped reproducing.'",
                    "options": [
                        "A. 1-B (threatened), 2-B (troubling), 3-C (noticed), 4-D (simply)",
                        "B. 1-A, 2-B, 3-A, 4-D",
                        "C. 1-D, 2-A, 3-B, 4-C",
                        "D. 1-C, 2-D, 3-B, 4-B"
                    ],
                    "ans": "A. 1-B, 2-B, 3-C, 4-D"
                },
                {
                    "num": 6,
                    "text": "Choose the most appropriate set of idioms that would fit in the blanks:\n'Sadhguru, the famous mystic, made several attempts to improve the nation's rivers a few years back. The government of India (1) _______ some of his ideas he had incorporated in the union budget. However, his solutions were not received well in (2) __________. After bearing these criticisms he decided not to provide any more solutions but to focus on the problem itself. His strongest message? We cannot (3) _______ to the fact that soil is being rejected, whether it is concrete paving, denuding vegetation, use of chemicals etc. The soil is not being given the respect it deserves. He has now (4) ______ of the politicians, the bureaucrats and the technocrats to find and execute solutions...'",
                    "options": [
                        "A. 1. Reflected upon 2. certain quarters 3. Turn a blind eye 4. put the ball in the court",
                        "B. 1. Reflected upon 2. A chunk of 3. Turned the other way 4. Gave up on",
                        "C. 1. Reflected upon 2. A cross section 3. Turned the other way 4. Given up",
                        "D. 1. Thought aloud 2. Certain section 3. Turn a deaf ear 4. Taken a back seat"
                    ],
                    "ans": "A. 1. Reflected upon 2. certain quarters 3. Turn a blind eye 4. put the ball in the court"
                },
                {
                    "num": 7,
                    "text": "Choose the sentence in which the underlined idiom has been used appropriately:",
                    "options": [
                        "A. The way Sanya's obsessing over one doorknob when they're renovating the entire house makes one think that she can't see the wood in the trees.",
                        "B. Marcus is so focused on product details that he can't see the wood for the trees when it comes to the overall needs of the company.",
                        "C. The safety officer can't see the wood for the trees because she doesn't know which way to look.",
                        "D. Raman always argues on the silliest topics, it's like he can't see the tree for the woods."
                    ],
                    "ans": "B. Marcus is so focused on product details that he can't see the wood for the trees..."
                },
                {
                    "num": 8,
                    "text": "Four idioms are given below. Choose the sequence that would fill in the blanks and complete the text:\n'Instead of the big crowd we expected, people arrived in _____ at the musical night. Alpana Alam is a rising star and is usually able to _____. Even before the interval it was obvious that the event was ____. Despite all this, Alpana herself was ______.'\nIdioms: (1) A dead duck, (2) Bring the house down, (3) Full of beans, (4) dribs and drabs",
                    "options": ["A. 1234", "B. 4231", "C. 4213", "D. 1342"],
                    "ans": "C. 4213"
                },
                {
                    "num": 9,
                    "text": "Rearrange the jumbled sentences to form a coherent paragraph:\n(A) We need to listen and act upon what birds are telling us, as they disappear ever faster...\n(B) Birds truly are the canary in the coal mine - as indicators for the health of our planet...\n(C) Conservation efforts have been successful at rescuing individual species, but funding is needed...\n(D) Bird populations are affected by the damage caused by human activity, from habitat destruction...\n(E) Billions of birds have been lost in recent decades in North America and Europe alone...",
                    "options": ["Write in order"],
                    "ans": "BADEC"
                },
                {
                    "num": 10,
                    "text": "Choose the appropriate order for sentences S2 and S3:\nS1. Placebos are essential to the design of reliable clinical trials.\nS2. ______________\nS3. ______________\nS4. Red, Yellow and orange are associated with a stimulant effect, while blue and green are related to tranquilizing effect; says Dr. A. J. de Craen.\nSentences: (Q) Their once-surprising effect on participants has become the focus of many studies. (P) Such studies have found that even the color of pills made a difference in placebo results.",
                    "options": ["A. PS", "B. PQ", "C. QP", "D. QS"],
                    "ans": "C. QP"
                }
            ]
        },
        {
            "title": "3. Logical Reasoning (Slot 1)",
            "questions": [
                {
                    "num": 1,
                    "text": "Identify the letter-cluster that does not belong to the following series:\nCX, GT, EV, DW, HS, ZA, MN, UF",
                    "options": ["A. ZA", "B. UF", "C. HS", "D. MN"],
                    "ans": "C. HS"
                },
                {
                    "num": 2,
                    "text": "Select the different pair of letter-clusters:",
                    "options": [
                        "A. TMKOLFXOY : TOMKLFXOY",
                        "B. PVMSYGCXN : VSPMYCGNX",
                        "C. XDSWZOIVK : XWSDZIKOV",
                        "D. FCHVOTFGW : VHFCOFGTW"
                    ],
                    "ans": "A. TMKOLFXOY : TOMKLFXOY"
                },
                {
                    "num": 3,
                    "text": "Based on the code language: P&Q (son), P@Q (mother), P%Q (brother), P#Q (husband). How is K related to Q if 'K % G & T # V @ S @ N % Q'?",
                    "options": ["A. Father", "B. Father's brother", "C. Mother's brother", "D. Brother"],
                    "ans": "C. Mother's brother"
                },
                {
                    "num": 4,
                    "text": "Based on the company criteria for Senior Engineer: (a) age 22-35, (b) Graduate in EE with 60%, (c) Recruitment test 70%, (d) Rs. 45,000 deposit.\nApplication of Raini D'Souza: EE graduate with 70%, born 4 March 1982 (35 years on 8 March 2017), 76% in recruitment test. Deposit details are missing.",
                    "options": [
                        "A. Not to be selected",
                        "B. Data is incomplete",
                        "C. To be selected",
                        "D. Case referred to chairman"
                    ],
                    "ans": "B. Data is incomplete"
                },
                {
                    "num": 5,
                    "text": "Statement: Despite warnings, the student was caught exploding crackers secretly on the hostel campus during birthday celebrations.\nCourse of actions:\nI. All crackers should be taken away and they should be threatened.\nII. The students should be severely punished.",
                    "options": [
                        "A. Only I follows",
                        "B. Only II follows",
                        "C. Either I or II follows",
                        "D. Neither I nor II follows"
                    ],
                    "ans": "C. Either I or II follows"
                },
                {
                    "num": 6,
                    "text": "20 years ago Mohita was 22 years old, how old was she X years ago?",
                    "options": ["A. X - 42", "B. 42", "C. 42 - X", "D. 62 - X"],
                    "ans": "C. 42 - X"
                },
                {
                    "num": 7,
                    "text": "Question: Let p be males and q be females. What is the difference between p and q?\nStatement I: Vipraja has six daughters who have a brother. Vipraja is married to Shantanu.\nStatement II: Shantanu is father of six daughters. Kiran's mother Vipraja is married to Shantanu. Kiran is a male.",
                    "options": [
                        "A. Statement I alone is sufficient",
                        "B. Statement II alone is sufficient",
                        "C. Both together are necessary",
                        "D. Either alone is sufficient"
                    ],
                    "ans": "A. Statement I alone is sufficient"
                }
            ]
        },
        {
            "title": "4. Coding (Slot 1)",
            "questions": [
                {
                    "num": 1,
                    "text": "String Conversion Algorithm:\nConvert string A to B of equal length N using the following rule:\nChoose a subset X from A, find the alphabetically smallest element 's' in the subset, and replace all elements in the subset with 's'. Return the minimum moves required, or -1 if impossible.",
                    "options": [],
                    "ans": "Solved Code below",
                    "code": """def min_moves_to_convert(A, B):
    if len(A) != len(B):
        return -1
    if A == B:
        return 0
        
    n = len(A)
    for i in range(n):
        if A[i] < B[i]:
            return -1
            
    set_a = set(A)
    for char in B:
        if char not in set_a:
            return -1

    mismatches = {}
    for i in range(n):
        if A[i] != B[i]:
            mismatches.setdefault(B[i], []).append(i)
            
    moves = 0
    for char in sorted(mismatches.keys(), reverse=True):
        moves += 1
        
    return moves
"""
                },
                {
                    "num": 2,
                    "text": "Sports Board Permutation Cycles:\nN students in class stand in jersey order 1 to N. Boards point to location A[i]. After every beat of the drum, students move to index pointed by their board. Find the beats required to bring back all students to their original positions.",
                    "options": [],
                    "ans": "Solved Code below",
                    "code": """import math

def get_lcm(a, b):
    return (a * b) // math.gcd(a, b)

def find_drum_beats(N, board_alignment):
    adj_boards = [x - 1 for x in board_alignment]
    visited = [False] * N
    ans = 1
    
    for i in range(N):
        if not visited[i]:
            cycle_len = 0
            curr = i
            while not visited[curr]:
                visited[curr] = True
                curr = adj_boards[curr]
                cycle_len += 1
            ans = get_lcm(ans, cycle_len)
            
    return ans
"""
                }
            ]
        },
        {
            "title": "5. Advanced Quantitative Aptitude",
            "questions": [
                {
                    "num": 1,
                    "text": "If the equation (1 + L^2)x^2 + 2Lcx + (c^2 - a^2) = 0 has equal roots, then a^2(1 + L^2) = ?",
                    "options": ["A. c^2", "B. -2", "C. a^2", "D. -4"],
                    "ans": "A. c^2"
                },
                {
                    "num": 2,
                    "text": "A five-digit number is to be written using 1, 2, 3, 4 and 5 using each exactly once such that the number is divisible by 4. How many such numbers are there?",
                    "options": ["Write in integer"],
                    "ans": "24 (Note: NQT exam key specifies '6', correct mathematical solution is 24)"
                },
                {
                    "num": 3,
                    "text": "What is the value of x for the equation: 4 + 4*sqrt(x-1) = 2*sqrt(x+1)?",
                    "options": ["Write in integer"],
                    "ans": "1"
                },
                {
                    "num": 4,
                    "text": "Which of the following points lie in the region of inequations x >= 1, y >= 1 and x + y <= 6?",
                    "options": ["A. (4,2)", "B. (3,2)", "C. Both (2,5) and (4,2)", "D. (2,5)"],
                    "ans": "A and B"
                },
                {
                    "num": 5,
                    "text": "The equation (k+3)x^2 - 10(k+3)x + 15(k+9) = 0, k != -3, has equal roots, then k = ?",
                    "options": ["Write in integer"],
                    "ans": "6"
                },
                {
                    "num": 6,
                    "text": "Find the ratio of the average sale of all the branches for the years 2020 and 2021.",
                    "options": ["A. 80:81", "B. 66.5:81", "C. 88:76.5", "D. 76.5:82"],
                    "ans": "D. 76.5 : 82"
                },
                {
                    "num": 7,
                    "text": "A metallic solid cube of side length 4cm is melted and made into a hollow sphere of internal radius 3cm. What is the external radius of the sphere?",
                    "options": ["A. (24/pi + 27)^(1/3)", "B. (48/pi + 27)^(1/3)", "C. (24/pi + 9)^(1/3)", "D. (48/pi + 9)^(1/3)"],
                    "ans": "B. (48/pi + 27)^(1/3)"
                }
            ]
        },
        {
            "title": "6. Advanced Logical Reasoning",
            "questions": [
                {
                    "num": 1,
                    "text": "Screenplay requirements: average-sized, age 45-50, big body frame, grey head, blue eyes, fair skin, smiling face. The candidate who appeared is in her 30s, medium build, has black hair, big blue eyes, and fair complexion. Will the candidate be selected?",
                    "options": [],
                    "ans": "Not Selected"
                },
                {
                    "num": 2,
                    "text": "Rani gives 6 numbers to friends 1 to 6. Numbers relate to names: 1: Amabad, 2: Domabad, 3: Taimabad, 4: Chomabad, 5: Pemabad, 6: Chamabad. 1 likes Chamabad. 3 and 4 like Pemabad. 6 and 1 like Taimabad, Pemabad, Domabad. Which number likes Pemabad and Taimabad but not Chamabad?",
                    "options": [],
                    "ans": "6"
                },
                {
                    "num": 3,
                    "text": "Eight students 1 to 8 are seated around a circle facing the center. 5 is second to the right of 3 who is the third of the left of 2. 8 is third to the right of 6 who is not an immediate neighbor of 1. Who is the second to the right of 5?",
                    "options": [],
                    "ans": "1"
                },
                {
                    "num": 4,
                    "text": "In a certain code language JAVA is written as JVAA. How will MAWAA be written?",
                    "options": [],
                    "ans": "MWAAA"
                },
                {
                    "num": 5,
                    "text": "Who stood to the immediate left of R in a dance school row (B, L, P, R, D)?\nStatements:\nI. B stands at one of the extreme ends. L stood between B and P.\nII. Only one student stands between P and D. D is not to the right of L.",
                    "options": [
                        "A. Data in statement II alone sufficient",
                        "B. Neither sufficient",
                        "C. Data in statement I alone sufficient",
                        "D. Data in both statements together are sufficient"
                    ],
                    "ans": "D"
                },
                {
                    "num": 6,
                    "text": "In a code language, SUM is coded as NLVTTR and LATE is coded as FDUSZBMK. How will ROAST be coded?",
                    "options": ["A. SQPMBZTRUS", "B. UTBPSSRZNQ", "C. USTRBZPNSQ", "D. ZPNSQUSTRB"],
                    "ans": "C. USTRBZPNSQ"
                },
                {
                    "num": 7,
                    "text": "Statement: Each and every institute in India should be linked with an incubation centre.\nArguments:\nI. Students will be aware of start-ups and how it benefits society.\nII. Having more start-ups will help build the economy.",
                    "options": [
                        "A. Neither strong",
                        "B. Only II strong",
                        "C. Both strong",
                        "D. Only I strong"
                    ],
                    "ans": "D. Only I strong"
                },
                {
                    "num": 8,
                    "text": "Statement: Educational institutes at school level should encourage extra-curricular activities along with academic teaching.\nArguments:\nI. Sports is a good career option.\nII. Extra-curricular activities enhance learning abilities.\nIII. Extra-curricular activities help build a skill.",
                    "options": [
                        "A. Only I is strong",
                        "B. All I, II, III are strong",
                        "C. Only III is strong",
                        "D. Only II is strong"
                    ],
                    "ans": "D. Only II is strong"
                }
            ]
        },
        {
            "title": "7. 19th August - Slot 2 Quantitative Aptitude",
            "questions": [
                {
                    "num": 1,
                    "text": "What will be the remainder when the square of the LCM of 4, 6, 12, and 15 is divided by the square of HCF of 51, 119 and 323?",
                    "options": ["A. 130", "B. 136", "C. 132", "D. 134"],
                    "ans": "C. 132"
                },
                {
                    "num": 2,
                    "text": "The sum of the squares of two fractions is 1. One fraction is 21/29. The sum and product of the possible values of the other fraction are s and p respectively. What is the value of (s-p)?",
                    "options": ["A. 441/841", "B. 400/441", "C. 400/841", "D. 100/441"],
                    "ans": "C. 400/841"
                },
                {
                    "num": 3,
                    "text": "The average age of Ram and Mohan is 2 years more than the average age of Mohan and Jitesh. The average age of Jitesh and Ram is 12 years, which is 2 years less than the average age of Mohan and Jitesh. What is the age of Jitesh?",
                    "options": ["A. 12 years", "B. 8 years", "C. 10 years", "D. 14 years"],
                    "ans": "C. 10 years"
                },
                {
                    "num": 4,
                    "text": "The present ages of four persons are in the ratio 1:2:3:4. The average of their ages seven years ago was 28 years. What will be the average age (in years) of the youngest and the oldest among them, five years from now?",
                    "options": ["A. 32", "B. 36", "C. 35", "D. 40"],
                    "ans": "D. 40"
                },
                {
                    "num": 5,
                    "text": "A metallic cuboid length, breadth, and height increased by 10%, decreased by 8%, and increased by 5% respectively. What is the percentage change in volume?",
                    "options": ["A. Increases by 6.26%", "B. Increases by 1.20%", "C. Decreases by 1.20%", "D. Decreases by 6.26%"],
                    "ans": "A. Increases by 6.26%"
                },
                {
                    "num": 6,
                    "text": "A shopkeeper sold his 25%, 30% and 20% of the items at a profit of 10%, 20% and 30% respectively. The rest of the items are sold at cost price. What is the percentage of profit of all his sales?",
                    "options": ["A. 14.5%", "B. 12.5%", "C. 15.5%", "D. 13.5%"],
                    "ans": "A. 14.5%"
                },
                {
                    "num": 7,
                    "text": "What will be the compound interest earned on an amount of Rs. 16,800 in 1_3/4 years at the rate of 6.25% per annum?",
                    "options": ["A. 1050", "B. 2367", "C. 1887", "D. 9147"],
                    "ans": "C. 1887"
                },
                {
                    "num": 8,
                    "text": "Three containers A, B, and C are filled with milk. 1/4 of A is put into B. Now 1/3 of B is put into C. Again 5/11 of C is put into A. In the end, 1/4 of A is put into B again. Now the final amount of milk in each container is 6 liters. Find the initial quantity of milk in each container.",
                    "options": ["A. 4, 5, 9", "B. 3, 7, 8", "C. 3, 6, 9", "D. 4, 7, 7"],
                    "ans": "A. 4, 5, 9"
                },
                {
                    "num": 9,
                    "text": "Shyam purchases 20% extra quantity of milk than indicated and sells 20% less. He claims to sell at cost price. Ram wants to earn the same percentage of profit as Shyam without dishonesty, and sells milk at Rs. 39 per liter. What is the cost price of 1 liter of milk for Ram?",
                    "options": ["A. 26", "B. 23", "C. 21", "D. 28"],
                    "ans": "A. 26"
                },
                {
                    "num": 10,
                    "text": "Two persons are moving towards each other in opposite directions at 21 km/h and 17 km/h. The total distance between them is 19km. In how long will they meet?",
                    "options": ["A. 30 min", "B. 50 min", "C. 60 min", "D. 40 min"],
                    "ans": "A. 30 min"
                },
                {
                    "num": 11,
                    "text": "A cone and sphere have the same radius of 18cm. If the cone and the sphere have the same volume, then what is the height (in cm) of the cone?",
                    "options": ["A. 66", "B. 60", "C. 54", "D. 72"],
                    "ans": "D. 72 cm"
                },
                {
                    "num": 12,
                    "text": "If the quartile deviation of a series is 125, then the mean deviation of the series is:",
                    "options": ["A. 149", "B. 151", "C. 150", "D. 152"],
                    "ans": "100"
                },
                {
                    "num": 13,
                    "text": "The ratio of the numbers of boys and girls in a school is 5:9, and the total number of students is 224. If 64 girls left the school and some boys joined, the ratio becomes 6:5. Find the number of boys who joined.",
                    "options": ["A. 15", "B. 16", "C. 13", "D. 14"],
                    "ans": "B. 16"
                },
                {
                    "num": 14,
                    "text": "5 men and 4 women can earn Rs. 2,862 in 9 days, and 9 men and 12 women can earn Rs. 6,000 in 8 days. In how many days can 7 men and 9 women earn Rs. 11,991?",
                    "options": ["A. 21 days", "B. 19 days", "C. 20 days", "D. 17 days"],
                    "ans": "A. 21 days"
                },
                {
                    "num": 15,
                    "text": "Rhythm spends 16_2/3% of her monthly income on food, 5_5/19% on entertainment and 8_1/3% on travelling. She saves the leftover money, which is Rs. 15,900. Find her monthly income in Rs.",
                    "options": ["No options provided"],
                    "ans": "Rs. 22,800"
                },
                {
                    "num": 16,
                    "text": "A policeman saw a thief from a distance of 100 meters. He started chasing him at a speed of 4 m/s. On seeing the policeman, the thief started running at a speed of 2 m/s. Determine the distance run by the policeman to catch the thief.",
                    "options": ["A. 100 m", "B. 200 m", "C. 250 m", "D. 150 m"],
                    "ans": "B. 200 m"
                },
                {
                    "num": 17,
                    "text": "A person distributed 72% of the money he had between Ram and Raj in the ratio of 5:7. Ram and Raj deposited the amount received in a scheme offering 8% and 10% simple interest respectively, for 10 years. Find the amount left with the person if the sum of interests earned after 10 years is Rs. 6,600.",
                    "options": ["Write in integer"],
                    "ans": "Rs. 2,800"
                },
                {
                    "num": 18,
                    "text": "Study the table of percentage marks and answer: English (50), Math (100), Science (100), Hindi (50), Social Studies (75).\nStudent D percentages: English 72%, Math 72%, Science 67%, Hindi 74%, Social Studies 68%.\nWhat are the total marks obtained by D in all subjects?",
                    "options": ["Write in integer"],
                    "ans": "263"
                },
                {
                    "num": 19,
                    "text": "If simple interest is offered per year, maturity after 5 years is Rs. 2,340. Maturity after 2 years is Rs. 2,016. What is the original sum invested?",
                    "options": ["A. Rs. 1,750", "B. Rs. 1,800", "C. Rs. 1,600", "D. Rs. 2,000"],
                    "ans": "B. Rs. 1,800"
                }
            ]
        },
        {
            "title": "8. 19th August - Slot 2 Logical Section",
            "questions": [
                {
                    "num": 1,
                    "text": "Identify the letter cluster that does not belong to the series:\nBC, GH, LM, EF, JK, PQ, IJ, NO, ST",
                    "options": ["A. ST", "B. IJ", "C. PQ", "D. NO"],
                    "ans": "C. PQ"
                },
                {
                    "num": 2,
                    "text": "Select the option that shares the same relationship as: PLGTOXIV : HKOSUZCF",
                    "options": [
                        "A. BGSFXTEY : CHIKXZEG",
                        "B. EGWHUZKL : FIKOQADH",
                        "C. TGSHCZOK : ZTTQNLLI",
                        "D. TDHZNLPK : FINPSVAH"
                    ],
                    "ans": "D. TDHZNLPK : FINPSVAH"
                },
                {
                    "num": 3,
                    "text": "How many male and female members are there in the family?\nStatements:\nI. Mrudula has five daughters, who have two brothers. Mrudula is the wife of Rakesh.\nII. Rakesh is the father of five daughters. Rajeev and Alok's mother Mrudula is the wife of Rakesh. Rajeev and Alok are males.",
                    "options": [
                        "A. Statement I alone is sufficient while statement II alone is not sufficient",
                        "B. Either statement I alone or statement II alone is sufficient",
                        "C. Both statements together are not sufficient",
                        "D. Statement II alone is sufficient while statement I alone is not sufficient"
                    ],
                    "ans": "A. Statement I alone is sufficient while statement II alone is not sufficient"
                },
                {
                    "num": 4,
                    "text": "Based on code: M&N (wife), M@N (brother), M$N (father), M#N (mother), M+N (grandson).\nHow is P's father related to K if 'P+H&Q$N@J#K'?",
                    "options": ["A. Father's brother", "B. Brother", "C. Mother's brother", "D. Father"],
                    "ans": "C. Mother's brother"
                },
                {
                    "num": 5,
                    "text": "There are eight members in a family, four males and four females. Arunima is the wife of Charan. Charan has two sons Jay and Bidan. Taruni is the mother of Roshni. How is Roshni related to Charan?\nStatements:\nI. Somu is the nephew of Jay. Bidan is married to Dipti.\nII. Taruni is the sister-in-law of Dipti. Dipti is the wife of Bidan.\nIII. Roshni is the niece of Bidan. Bidan is the only sibling of Jay.",
                    "options": [
                        "A. All statement I, II and III together are necessary",
                        "B. Only statement III alone is sufficient",
                        "C. Statement I and II together are sufficient",
                        "D. Either I and II together or II and III together are sufficient"
                    ],
                    "ans": "B. Only statement III alone is sufficient"
                },
                {
                    "num": 6,
                    "text": "Code language: A$B (father), A%B (mother of A), A@B (brother), A*B (sister of A), A#B (wife), A/B (husband of A).\nWhich statement is NOT true?",
                    "options": [
                        "A. G @ H % J / K means 'G is the son of K'",
                        "B. T / V $ W # Z means 'T is the mother-in-law of Z'",
                        "C. P $ Q * R / S means 'S is the son-in-law of P'",
                        "D. C % D # E @ F means 'F is the uncle of C'"
                    ],
                    "ans": "D. C % D # E @ F means 'F is the uncle of C'"
                },
                {
                    "num": 7,
                    "text": "Identify the letter cluster that does not belong to the series:\nHUD, JOG, LKJ, NFM, PAP",
                    "options": ["Write Answer"],
                    "ans": "JOG"
                },
                {
                    "num": 8,
                    "text": "The sales price of a drilling machine was increased by 10% and then its price was again increased by 10%. What is the total increase in the initial price of the machine?",
                    "options": ["A. 22%", "B. 21%", "C. 24%", "D. 23%"],
                    "ans": "B. 21%"
                },
                {
                    "num": 9,
                    "text": "Each of the six students A, B, C, D, E, and F are reading two subjects, one compulsory and one optional. Sociology is read by E and F. English is F's compulsory subject, which is optional for C and E. Hindi and Geography are A's subjects but just reverse to those of D. Psychology is the optional subject of only one student. Geography is the optional subject of D while it is compulsory for three others. What is the compulsory subject of B?",
                    "options": ["Write Answer"],
                    "ans": "Geography"
                },
                {
                    "num": 10,
                    "text": "Sociology Assistant Professor selection criteria: PG Sociology 55%, UG Sociology Honors 55%, 10th and 12th 50% each, NET/JRF Sociology by Jan 2021, Age 25-40, Interview 60%.\nRahul Mehta PG 65%, UG Honors 59%, 10th 49%, 12th 60.83% (exception met since 10th + 12th = 55.45% >= 55%). NET in Social Work (instead of Sociology). Interview 67%. Born 21 Feb 1989 (32 years).\nWhat is his selection status?",
                    "options": [
                        "A. The candidate should not be selected",
                        "B. Inadequate information",
                        "C. The candidate should be selected",
                        "D. Candidate rejected based on class 10th criteria"
                    ],
                    "ans": "A. The candidate should not be selected"
                },
                {
                    "num": 11,
                    "text": "Statement: During a national emergency, even civilians can be deployed into the war field.\nAssumptions:\nI. It shows the interest of civilians to safeguard their nation.\nII. Due to insufficient military resources, the government has given an opportunity to their civilians.",
                    "options": [
                        "A. Only assumption I is implicit",
                        "B. Only assumption II is implicit",
                        "C. Neither assumption I nor II is implicit",
                        "D. Both assumptions I and II are implicit"
                    ],
                    "ans": "B. Only assumption II is implicit"
                },
                {
                    "num": 12,
                    "text": "Statement: Many social-media celebrities advertise about intra-day trading in their videos about how easily anyone can make money. But they don't show the negative aspect of it, i.e., about losing money.\nCourses of Action:\nI. The government should ban advertisement of intra-day trading.\nII. The government should make certain guidelines to advertise these kinds of apps.",
                    "options": [
                        "A. Only course of action II follows",
                        "B. Only course of action I follows",
                        "C. Both courses of action I and II follow",
                        "D. Neither course of action I nor II follows"
                    ],
                    "ans": "A. Only course of action II follows"
                },
                {
                    "num": 13,
                    "text": "MSc Bioinformatics criteria: Intermediate Science > 70%, BSc Zoology/Botany/Math/CS >= 65%, Entrance exam >= 75% and Interview >= 65%, Age 21-28.\nMr. Rakesh Ram (ST community): Intermediate Science 70%, Entrance 77%, Interview 74.67%, BSc Zoology 67% in 2019. Born 26.06.1994 (28 years).\nWhat is his status?",
                    "options": [
                        "A. Case referred to Director",
                        "B. Candidate is to be selected",
                        "C. Case referred to SC/ST cell",
                        "D. Candidate is to be rejected"
                    ],
                    "ans": "D. The candidate is to be rejected"
                },
                {
                    "num": 14,
                    "text": "In an institute, 90 students opted for English, 70 for Chemistry, 40 for Mathematics, 30 for Economics, 10 for both English and Chemistry, 5 for Economics and Math, 20 for English and Economics. How many students opted for English only?",
                    "options": ["Write in integer"],
                    "ans": "60"
                }
            ]
        },
        {
            "title": "9. 19th August - Slot 2 Verbal Section",
            "questions": [
                {
                    "num": 1,
                    "text": "Identify the error in the sentence:\n'I'm literally melting because it's the hottest month of June; it's 47 degrees out here'",
                    "options": ["A. Month of june", "B. I'm literally melting", "C. It's 47 degrees out here", "D. Because it's the hottest"],
                    "ans": "A. Month of june"
                },
                {
                    "num": 2,
                    "text": "Select the option that has the grammatical error:\n'Negotiations have reached such a state as management and union leaders are apprehensive that their differences can no longer be reconciled.'",
                    "options": ["A. can no longer be reconciled", "B. Negotiations have reached", "C. such a state as", "D. that their differences"],
                    "ans": "C. such a state as"
                },
                {
                    "num": 3,
                    "text": "Select the phrase that best replaces the INCORRECT phrase in the sentence:\n'The ability of the Sherpas to brave the vagaries of high altitudes has helped them to prosper and they have come along the way from being just porters to becoming mountaineers.'",
                    "options": ["A. Come a long way", "B. To be", "C. Capacity", "D. On higher altitudes"],
                    "ans": "A. Come a long way"
                },
                {
                    "num": 4,
                    "text": "Select the most appropriate options to fill in the blanks in the given passage:\n'The capacity of art (1)_____ a strong source of its contemporary appeal. We are conscious that, individually and collectively, we (2) ______; art can be valuable when it disrupts or astonishes us.'",
                    "options": [
                        "A. (1) to shock remains for same (2) grown complacent",
                        "B. (1) to shock remains for same (2) may grow complacent",
                        "C. (1) to shock remains for some (2) may grow complacent",
                        "D. (1) to shock remains for some (2) may grown complacent"
                    ],
                    "ans": "C. (1) to shock remains for some (2) may grow complacent"
                },
                {
                    "num": 5,
                    "text": "Select the most appropriate options to fill in the blanks:\n'We lit the candles, and (A) _________ in our hands and knees. We went about two hundred yards, and then the cave opened up. Tom soon (B) _____________ under a wall where there was a hole. We went along a narrow passage and got into a kind of room, all damp and sweaty and cold, and there we stopped. Tom said, \"Now, we'll start this (C)________ of robbers and call it Tom Sawyer's gang. Everybody that wants to join has got to take an oath, and write his name in blood.\" Everybody was (D) _______.'",
                    "options": [
                        "A. (A) glided, (B) dropped, (C) crew (D) pleased",
                        "B. (A) crawled, (B) ducked, (C) band (D) willing",
                        "C. (A) hauled, (B) crossed, (C) herd (D) opposing",
                        "D. (A) sailed, (B) dipped, (C) pack (D) obedient"
                    ],
                    "ans": "B. (A) crawled, (B) ducked, (C) band (D) willing"
                },
                {
                    "num": 6,
                    "text": "Select the most appropriate set of options to fill in the blanks (Partially truncated in NQT paper):\n'Babies and Young children are sponges that soak in practically everything in their environments. It's true!! Even during story time, their minds are at work, (1) ______ all the language they hear and lessons the characters learn. (2) ______ to your child - at any age - will boost their brain development, and your bond, and so much more. And all it takes is a few books, motivation and a (3) _______ time. Reading provides a wonderful opportunity for you and your child to (4)_____.'",
                    "options": [
                        "A. (1) absorbing, (2) Reading, (3) little, (4) bond",
                        "B. (1) ignoring, (2) Speaking, (3) lot, (4) argue"
                    ],
                    "ans": "A. (1) absorbing, (2) Reading, (3) little, (4) bond"
                }
            ]
        }
    ]

    # Process all sections for questions first
    for sec in sections:
        story.append(Paragraph(sec["title"], h1_style))
        story.append(Spacer(1, 8))
        
        for q in sec["questions"]:
            q_story = []
            
            # Question Header and Text
            q_head = f"Question {q['num']}"
            q_story.append(Paragraph(q_head, h2_style))
            q_story.append(Paragraph(q["text"], body_style))
            
            # Options (represented as lists or tables for clean alignment)
            if "options" in q and len(q["options"]) > 0:
                opt_data = []
                for opt in q["options"]:
                    opt_data.append([Paragraph(opt, opt_style)])
                
                opt_table = Table(opt_data, colWidths=[500])
                opt_table.setStyle(TableStyle([
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                ]))
                q_story.append(opt_table)
                
            story.append(KeepTogether(q_story))
            story.append(Spacer(1, 10))
            
        story.append(PageBreak())

    # ==================== ANSWER KEY SECTION ====================
    story.append(Paragraph("Answer Key", h1_style))
    story.append(Spacer(1, 12))
    
    # We will lay out the answers section by section
    for sec in sections:
        sec_story = []
        sec_story.append(Paragraph(f"<b>{sec['title']}</b>", h2_style))
        sec_story.append(Spacer(1, 6))
        
        # We can group MCQs into compact rows, and list codes separately
        ans_rows = []
        for q in sec["questions"]:
            # If it's a coding question with code, we render it below
            if "code" in q and q["code"]:
                # Print code answer separately
                sec_story.append(Paragraph(f"Question {q['num']} Solution:", key_text_style))
                sec_story.append(Preformatted(q["code"], code_style))
            else:
                ans_str = f"Q{q['num']}: {q['ans']}"
                ans_rows.append(Paragraph(ans_str, key_text_style))
        
        # Lay out multiple choice answers in a grid if there are any
        if len(ans_rows) > 0:
            grid_data = []
            row = []
            # Make a 3-column layout for answers to make it extremely clean and space-efficient
            for idx, cell in enumerate(ans_rows):
                row.append(cell)
                if len(row) == 3 or idx == len(ans_rows) - 1:
                    while len(row) < 3:
                        row.append(Paragraph("", key_text_style))
                    grid_data.append(row)
                    row = []
            
            ans_table = Table(grid_data, colWidths=[168, 168, 168])
            ans_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            sec_story.append(ans_table)
            
        story.append(KeepTogether(sec_story))
        story.append(Spacer(1, 15))

    # Build document using the two-pass NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
