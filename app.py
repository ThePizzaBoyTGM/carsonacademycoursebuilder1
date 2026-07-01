import http.server
import socketserver
import threading

def dummy_server():
    with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

# Start the dummy server in a background thread
threading.Thread(target=dummy_server, daemon=True).start()

# YOUR ACTUAL CODE CONTINUES HERE

import urllib.request
import urllib.error
import json
import threading
import time
import uuid
import re
import os
import sys

# Default Prompts
PROMPT_STRUCTURE = """[Course], for [Educational Level] students - Create a simple course structure guide with 6 to 12 units and 5 to 12 learning topics per unit (extra topics for content topics below). Follow these strict formatting rules: Units: Type "Unit #: Unit Name" for each unit. Topics: Start a line with a dash (-) for each topic under a unit. Use the format "Topic #.#: Topic Name (Title Case)". Content: Including topics for readings (language courses only, no reading otherwise). Make one exam for each unit (extra topic) where appropriate within the sequence. If the topic is something other than a normal topic (Reading, Exam, etc.), list it next to the topic name in brackets (Ex: Topic 1.3: Preterite Paragraph [Reading]) These topics are not included with the original 5 to 12 topic count. Make multiple parts for the reading if needed. No midterms or finals. Constraints: Do not include any extra text, bolding, italics, or special characters. Provide only the course structure. Structure: Format the units so that the skills required for the unit are at the beginning."""

PROMPT_SAMPLES = """Create 3 sample problems that progressively scale in difficulty based on all the skills and required knowledge of the topic above in the course [Course] for [Educational Level] students. Problem 1 must test basic intuition, visual/numerical understanding (like tables), or fundamental concepts. Problems 2 and 3 should escalate to medium and difficult applications. If practice problems are included, they must mimic the exact wording, difficulty, style, and skills. Don’t add any introductory or concluding text, just get straight into it. You may use skills from prerequisite courses. However, if a certain skill is not covered yet in the current course (in previous prompts), do not add it into the problems. No intro. or concluding marks, just get straight into the questions. If the course is a language or social science course, then add vocab in at the bottom."""

PROMPT_LEARNING = """Act as an expert instructor teaching [Course] to [Educational Level] students using the Feynman Technique: explain complex concepts using age-appropriate language, analogies, and a cohesive narrative flow with zero assumptions of prior knowledge.** **Analyze the provided text/problems to extract every mathematical operation, edge case, and conceptual step. Create parallel instructional content at the exact technical difficulty of the hardest source problem without referencing it directly. Do not skip logical or mathematical steps. Crucially, ensure each section feels like part of a connected journey. Use conversational transitions to explicitly link every new concept, formula, or procedural step back to the "main idea" or the overarching problem we are trying to solve, so the learner always understands why this specific step matters to the big picture.** **Constraints:** * **STEM:** Always build foundational intuition first. For math, explicitly demonstrate visual or numerical methods (like tables of values) before introducing formal algebraic notation, limit definitions, or advanced theorems like Squeeze Theorem. Prioritize procedural "how-to" steps over definitions, providing a repeatable, algorithmic set of instructions. Include 2–3 distinct ASCII diagrams across the responses to visually map procedures. * **Non-Math/Science:** Strictly prohibit mathematical formulas or variables; use qualitative analytical frameworks, rhetorical devices, or thematic theories instead. * **Output Restrictions:** Do not generate images, videos, or interactive quizzes. No filler, introductions, greetings, transitions, or concluding questions in your actual output. Start directly with the content. * **Mathematical Formatting (STEM Only):** Every variable in a formula must first be written entirely in words using LaTeX spoken-word equivalents: $$\text{word} = \text{word} + \text{word}$$ Provide the standard equation immediately below. Explicitly define every variable/constant upon its first appearance. **Deliver the content sequentially, one response at a time. Stop after each response and wait for the user to say "next" before proceeding. DO NOT COMBINE RESPONSES; KEEP THEM ALL SEPARATE. Ensure the steps provide enough detail to solve the toughest problem without external knowledge. No introductory or concluding remarks (e.g., "Awaiting next response" or "Here's the..."). For coding and other more hands-on topics: show the complete, actual code/concept implementation in each response, not just pseudocode or process, defining each concept or symbol used. Remember that you’re teaching to [Educational Level] students.** * **Response 1 (The Hook & Overview):** A strict 3–4 sentence paragraph overview of the fundamental concepts, vocabulary, and background. For STEM/Logic subjects, use a cohesive narrative flow linking steps to a "Main Problem". For Humanities/Language/Arts subjects, link concepts to a "Core Theme" or "Essential Question". Don’t put ---Finished--- on the last line in this response. * **Response 2 (The Mental Model):** Introduce the core analogy or 3-step logical framework. Explicitly state how this mental model acts as the key to solving the "Main Problem" established in Response 1. For STEM courses only, include the foundational Worded Formula and Standard Formula here. Don’t put ---Finished--- on the last line here. * **Responses 3 to X (The Toolbox - Required Skills & Knowledge):** Separate responses for each core skill, concept, or piece of knowledge required to understand the topic. Begin with the most basic, intuitive methods before scaling up to complex theorems. Focus purely on teaching the mechanics, formulas, syntax (for coding), and foundational logic using diagrams and isolated, bite-sized examples. Explicitly connect how mastering this specific skill equips the learner to solve the overarching "Main Problem." Do not solve the full sample problems here. Don’t put ---Finished--- on the last line here. * **Responses X+1 to Y (Applied Problem-Solving Walkthroughs):** Separate responses for each unique problem type provided in the source material. **You must begin each of these responses by exactly copying and pasting the full sample problem text at the very top.** Then, explicitly apply the skills from the "Toolbox" to solve it. Structure like an engaging textbook module: the copied sample problem, step-by-step logic, an ASCII diagram/table tracking the process, the complete execution of the problem (walking through it step-by-step, showing all code/math), and a 'Common Pitfalls' section detailing two incorrect approaches and their logical/syntax errors. Don’t put ---Finished--- on the last line. * **Final Response (Summary):** A rapid-fire, single-line-per-item bulleted summary of each formula, concept, step, or analysis, framing them as the tools we successfully used to conquer the main idea. If there is vocab included in the sample questions, include the definitions of every one in this response as well. The very last line must be exactly: ---Finished--- ONLY PUT THIS IN THE FINAL RESPONSE, NONE OF THE OTHERS."""

PROMPT_QUESTIONS = """Task: Create 24 multiple-choice practice problems mapping directly to the source problems. Maintain the exact same syntactic phrasing, question type, and difficulty. For STEM, swap out numbers and variables while keeping operations identical. For Humanities/Languages, alter the specific scenario, text snippet, or vocabulary word while testing the identical analytical skill or grammar rule. Questions cannot reference each other. Include all vocab. If there is vocab included, include every single one in the questions. Phase 1: Produce exactly the first 8 problems. STOP immediately and wait for the user to say "next". Phase 2: Produce the next 8 problems. Phase 3: Produce the remaining 8 problems. STOP. No introductory or concluding text. No conversational filler. Verify answers before writing. Delimiter Format: @#M@# [Premise/Scenario] @# [Choice 1] @# [Choice 2] @# [Choice 3] @# [Choice 4] @# [Letter Choice] @# [Logical Explanation]"""


class HeadlessCourseBuilder:
    def __init__(self):
        self.state = { 
            'apiKey': '', 
            'model': 'gemini-2.5-flash-preview-09-2025', 
            'courseTitle': '', 
            'courseLevel': 'High School', 
            'status': 'IDLE', 
            'queue': [], 
            'courseJSON': None, 
            'infiniteRetries': False, 
            'concurrent': True, 
            'concurrentCount': 1, 
            'resume_file': '', 
            'custom_structure_file': '',
            'custom_samples_file': ''
        }

    def log_message(self, msg, is_error=False):
        time_str = time.strftime("%H:%M:%S")
        prefix = "ERROR: " if is_error else ""
        print(f"[{time_str}] {prefix}{msg}")

    def fetch_gemini(self, contents, system_prompt=None):
        model = self.state['model'].lower()
        is_openai = "gpt" in model
        is_ollama = not is_openai and "gemini" not in model

        if is_openai:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {'Content-Type': 'application/json', 'Authorization': f"Bearer {self.state['apiKey']}"}
        elif is_ollama:
            url = "http://localhost:11434/v1/chat/completions"
            headers = {'Content-Type': 'application/json'}
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.state['model']}:generateContent?key={self.state['apiKey']}"
            headers = {'Content-Type': 'application/json'}

        if is_openai or is_ollama:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            for c in contents:
                role = "assistant" if c["role"] == "model" else c["role"]
                text = c["parts"][0]["text"]
                messages.append({"role": role, "content": text})
            payload = {"model": self.state['model'], "messages": messages}
        else:
            payload = {"contents": contents}
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        delays = [1, 2, 4, 8, 16]
        for i in range(5):
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = response.read().decode('utf-8')
                    res_json = json.loads(res_data)
                    if is_openai or is_ollama:
                        text = res_json.get('choices', [{}])[0].get('message', {}).get('content', '')
                        return {"candidates": [{"content": {"parts": [{"text": text}]}}]}
                    return res_json
            except urllib.error.HTTPError as e:
                err_text = e.read().decode('utf-8')
                if e.code == 429 and i < 4:
                    self.log_message(f"API busy (429), retrying in {delays[i]}s...")
                    time.sleep(delays[i])
                    continue
                raise Exception(f"API Error {e.code}: {err_text}")
            except Exception as e:
                if i < 4:
                    self.log_message(f"Network error, retrying in {delays[i]}s...")
                    time.sleep(delays[i])
                    continue
                raise e

    def run_multi_turn(self, initial_prompt, max_turns, break_on_finished=True):
        history = [{"role": "user", "parts": [{"text": initial_prompt}]}]
        full_text = ""

        for i in range(max_turns):
            if self.state['status'] not in ['RUNNING', 'PAUSED']:
                raise Exception("PAUSED")
            
            self.log_message(f"Executing multi-turn phase {i+1}...")
            response = self.fetch_gemini(history)
            
            try:
                text = response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            except IndexError:
                text = ""
                
            full_text += "\n\n" + text.strip()
            history.append({"role": "model", "parts": [{"text": text}]})

            if break_on_finished and ("---Finished---" in text or "Finished---" in text):
                break

            if break_on_finished:
                full_text += "\n\n---"
                
            if i == max_turns - 1:
                break

            history.append({"role": "user", "parts": [{"text": "next"}]})
            time.sleep(2)
            
        full_text = full_text.replace("---Finished---", "").replace("Finished---", "").strip()
        return full_text

    def get_topic(self, uid, tid):
        for u in self.state['courseJSON']['units']:
            if u['id'] == uid:
                for t in u['topics']:
                    if t['id'] == tid:
                        return t
        return None

    def task_build_structure(self, task): 
        if self.state.get('custom_structure_file') and os.path.exists(self.state['custom_structure_file']):
            with open(self.state['custom_structure_file'], 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            prompt = PROMPT_STRUCTURE.strip().replace('[Course]', self.state['courseTitle']).replace('[Educational Level]', self.state['courseLevel']) 
            response = self.fetch_gemini([{"role": "user", "parts": [{"text": prompt}]}]) 
            
            try: 
                text = response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '') 
            except IndexError: 
                raise Exception("Failed to get response text.") 
                
        lines = text.split('\n') 
        current_unit = None
        
        for line in lines:
            l = line.strip()
            l = re.sub(r'^[*#]+\s*', '', l)
            if not l: continue
            
            if l.lower().startswith('unit'):
                current_unit = {
                    'id': str(uuid.uuid4()),
                    'title': l,
                    'config_isOptional': False,
                    'config_gradingModel': 'standard',
                    'topics': []
                }
                self.state['courseJSON']['units'].append(current_unit)
            elif (l.startswith('-') or re.match(r'^\d+\.', l) or l.lower().startswith('topic')) and current_unit:
                title = re.sub(r'^[-*]\s*', '', l)
                title = re.sub(r'^\d+\.\s*', '', title)
                title = re.sub(r'^topic\s*\d+\.\d+[:.-]?\s*', '', title, flags=re.IGNORECASE).strip()
                
                is_assignment = False
                is_exam = False
                
                tag_match = re.search(r'\[(.*?)\]$', title)
                if tag_match:
                    if tag_match.group(1).lower() == 'exam':
                        is_exam = True
                    else:
                        is_assignment = True
                    title = re.sub(r'\s*\[.*?\]$', '', title).strip()
                    
                current_unit['topics'].append({
                    'id': str(uuid.uuid4()),
                    'title': title,
                    '_isAssignmentTask': is_assignment,
                    '_isExamTask': is_exam,
                    'learningContent': "",
                    'rawSamples': "",
                    'questions': [],
                    'assignments': [],
                    'config_baseStreak': 5, 'config_quizQuestions': 10, 'config_timeLimit': 0,
                    'config_streakIncrement': 1, 'config_quizOnly': False, 'config_disablePractice': False,
                    'config_disableQuiz': False, 'config_isOptional': False, 'config_randomizeQuestions': True,
                    'config_isGraded': False, 'config_useUniversalPercentage': True, 'config_passingPercentage': 70,
                    'config_isTest': is_exam, 'config_testSourceMode': "unit" if is_exam else "manual",
                    'config_testQuestionsPerTopic': 3 if is_exam else 2, 'config_isFlashcard': False
                })

        if not self.state['courseJSON']['units']:
            raise Exception("Failed to parse units from response.")
            
        for u in self.state['courseJSON']['units']:
            for t in u['topics']:
                if not t['_isExamTask']:
                    self.state['queue'].append({
                        'id': str(uuid.uuid4()), 'type': 'GEN_SAMPLES',
                        'title': f"Generate Samples: {t['title']}",
                        'unitId': u['id'], 'topicId': t['id'], 'status': 'PENDING'
                    })
                    
        self.log_message(f"Parsed {len(self.state['courseJSON']['units'])} units. Structure and sample tasks queued.")

    def task_gen_samples(self, task): 
        topic = self.get_topic(task['unitId'], task['topicId']) 
        
        text = ""
        if self.state.get('custom_samples_file') and os.path.exists(self.state['custom_samples_file']):
            with open(self.state['custom_samples_file'], 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(rf'---\s*{re.escape(topic["title"])}\s*---(.*?)(?=---|$)', content, re.DOTALL | re.IGNORECASE)
                if match:
                    text = match.group(1).strip()

        if not text:
            base_prompt = PROMPT_SAMPLES.strip().replace('[Course]', self.state['courseTitle']).replace('[Educational Level]', self.state['courseLevel']) 
            
            struct_text = "Course Structure:\n" 
            current_unit_title = "" 
            for u in self.state['courseJSON']['units']: 
                struct_text += f"{u['title']}\n" 
                if u['id'] == task['unitId']: 
                    current_unit_title = u['title'] 
                for t in u['topics']: 
                    struct_text += f"* {t['title']}\n" 
                struct_text += "\n" 

            prompt = f"{struct_text.strip()}\n--- Current Unit: {current_unit_title} ---\n--- Current Topic (To Generate): {topic['title']} - Generate based on what you would expect a beginner to know after learning this topic for the first time - {base_prompt}" 
            
            response = self.fetch_gemini([{"role": "user", "parts": [{"text": prompt}]}]) 
            try: 
                text = response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '') 
            except IndexError: 
                text = "" 
                
        if not text.strip(): 
            raise Exception("API returned an empty response. Possible safety block.") 
            
        topic['rawSamples'] = text 

        self.state['queue'].append({ 
            'id': str(uuid.uuid4()), 'type': 'GEN_LEARNING',
            'title': f"Build Learning Content: {topic['title']}",
            'unitId': task['unitId'], 'topicId': task['topicId'], 'status': 'PENDING'
        })
        self.state['queue'].append({
            'id': str(uuid.uuid4()), 'type': 'GEN_QUESTIONS',
            'title': f"Build Practice Assignments: {topic['title']}",
            'unitId': task['unitId'], 'topicId': task['topicId'], 'status': 'PENDING'
        })

    def task_gen_learning(self, task):
        topic = self.get_topic(task['unitId'], task['topicId'])
        base_prompt = PROMPT_LEARNING.strip()
        base_prompt = base_prompt.replace('[Topic]', topic['title']).replace('[Educational Level]', self.state['courseLevel']).replace('[Course]', self.state['courseTitle'])
        
        prior_knowledge = "Prior Knowledge (Topics Already Covered):\n"
        found_current = False
        for u in self.state['courseJSON']['units']:
            if found_current: break
            unit_header_added = False
            for t in u['topics']:
                if t['id'] == task['topicId']:
                    found_current = True
                    break
                if not unit_header_added:
                    prior_knowledge += f"{u['title']}\n"
                    unit_header_added = True
                prior_knowledge += f" - {t['title']}\n"
                
        if prior_knowledge == "Prior Knowledge (Topics Already Covered):\n":
            prior_knowledge += "None (This is the first topic).\n"
        
        prompt = f"{base_prompt}\n\n{prior_knowledge}\nTopic: {topic['title']}\n\n=== SOURCE PRACTICE PROBLEMS ===\n{topic['rawSamples']}"
        full_markdown = self.run_multi_turn(prompt, 10, True)
        topic['learningContent'] = full_markdown

    def task_gen_questions(self, task):
        topic = self.get_topic(task['unitId'], task['topicId'])
        base_prompt = PROMPT_QUESTIONS.strip()
        prompt = f"{base_prompt}\n\nTopic: {topic['title']}\n\n=== SOURCE LOGIC TO MIMIC ===\n{topic['rawSamples']}"
        
        raw_output = self.run_multi_turn(prompt, 3, False)
        
        generated_questions = []
        blocks = raw_output.split('@#M@#')
        for block in blocks:
            if not block.strip(): continue
            parts = [s.strip() for s in re.split(r'\s*@#+\s*', block)]
            if len(parts) >= 6:
                correct_letter = parts[5].upper()
                correct_letter = re.sub(r'[^A-D]', '', correct_letter)
                if not correct_letter: correct_letter = 'A'
                else: correct_letter = correct_letter[0]

                generated_questions.append({
                    'Type': 'M',
                    'Question': parts[0],
                    'A': parts[1] if len(parts) > 1 else '',
                    'B': parts[2] if len(parts) > 2 else '',
                    'C': parts[3] if len(parts) > 3 else '',
                    'D': parts[4] if len(parts) > 4 else '',
                    'Correct': correct_letter,
                    'Explanation': parts[6] if len(parts) > 6 else ''
                })

        if topic.get('_isAssignmentTask'):
            topic['assignments'].append({
                'id': str(uuid.uuid4()),
                'title': f"{topic['title']} - Assessment",
                'required': True,
                'items': generated_questions
            })
        else:
            topic['questions'].extend(generated_questions)

    def process_queue(self):
        runners = {
            'BUILD_STRUCTURE': self.task_build_structure,
            'GEN_SAMPLES': self.task_gen_samples,
            'GEN_LEARNING': self.task_gen_learning,
            'GEN_QUESTIONS': self.task_gen_questions
        }
        
        active_threads = []

        def worker(task):
            try:
                runners[task['type']](task)
                task['status'] = 'DONE'
                task['desc'] = 'Completed.'
                self.log_message(f"Task Complete: {task['title']}")
                self.export_progress()
            except Exception as e:
                    self.log_message(f"Task Failed [{task['title']}]: {str(e)}", True)
                    retries = task.get('retries', 0)
                    if self.state.get('infiniteRetries', False) or retries < 3:
                        attempt_str = str(retries + 1) if self.state.get('infiniteRetries', False) else f"{retries + 1}/3"
                        self.log_message(f"Restarting [{task['title']}] (Attempt {attempt_str})...")
                        task['retries'] = retries + 1
                        task['status'] = 'PENDING'
                        task['desc'] = f'Retrying (Attempt {attempt_str})...'
                        time.sleep(2)
                    else:
                        task['status'] = 'ERROR'
                        task['desc'] = f"Failed after 3 retries: {str(e)}"

        while self.state['status'] in ['RUNNING', 'PAUSED']:
            active_threads = [t for t in active_threads if t.is_alive()]
            max_workers = self.state['concurrentCount'] if self.state['concurrent'] else 1
            
            if self.state['status'] == 'RUNNING' and len(active_threads) < max_workers:
                task_index = next((i for i, t in enumerate(self.state['queue']) if t['status'] == 'PENDING'), -1)
                
                if task_index != -1:
                    task = self.state['queue'][task_index]
                    task['status'] = 'RUNNING'
                    task['desc'] = 'Processing API requests...'
                    self.log_message(f"Starting Task: {task['title']}")
                    t = threading.Thread(target=worker, args=(task,), daemon=True)
                    t.start()
                    active_threads.append(t)
                    time.sleep(1.5)
                    continue

            if len(active_threads) == 0:
                if self.state['status'] == 'PAUSED':
                    break
                all_done = all(t['status'] == 'DONE' for t in self.state['queue'])
                if all_done and len(self.state['queue']) > 0:
                    self.state['status'] = 'DONE'
                    self.log_message("All tasks completed successfully. Course is ready for export.")
                elif any(t['status'] == 'ERROR' for t in self.state['queue']):
                    self.state['status'] = 'PAUSED'
                    self.log_message("Queue halted due to errors. Exporting current progress...", True)
                    self.export_progress()
                else:
                    self.state['status'] = 'IDLE'
                break
                
            time.sleep(1)

    def start_build(self):
        if not self.state['courseJSON']:
            self.state['courseJSON'] = {
                'id': str(uuid.uuid4()),
                'title': self.state['courseTitle'],
                'description': f"Auto-generated course for {self.state['courseLevel']} level.",
                'units': [],
                'config_enableGrades': True,
                'config_universalPassingPercentage': 70,
                'config_enableRetakes': True,
                'config_maxRetakes': 3,
                'config_enableRollingDueDates': False,
                'config_paceMode': "normal",
                'config_enablePracticeMarathon': True,
                'config_adaptiveMarathon': True,
                'config_enableQuickMaster': True,
                'config_learnSections': False,
                'config_editAccountLocked': False
            }
            
            self.state['queue'].append({
                'id': str(uuid.uuid4()), 'type': 'BUILD_STRUCTURE',
                'title': 'Architect Course Structure',
                'status': 'PENDING'
            })

        self.state['status'] = 'RUNNING'
        self.log_message("Starting Build Process...")
        self.process_queue()

    def export_course_json(self):
        if not self.state['courseJSON']:
            self.log_message("No course built yet to export.", True)
            return
            
        export_data = json.loads(json.dumps(self.state['courseJSON']))
        
        for u in export_data.get('units', []):
            for t in u.get('topics', []):
                t.pop('rawSamples', None)
                t.pop('_isAssignmentTask', None)
                t.pop('_isExamTask', None)

        filename = f"{export_data['title'].replace(' ', '_').lower()}_autobuild.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        self.log_message(f"Course JSON Exported to {filepath}")

    def export_samples(self):
        if not self.state['courseJSON']:
            self.log_message("No course built yet to export.", True)
            return

        filename = f"{self.state['courseJSON']['title'].replace(' ', '_').lower()}_samples.txt"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for u in self.state['courseJSON']['units']:
                f.write(f"=== {u['title']} ===\n")
                for t in u['topics']:
                    f.write(f"\n--- {t['title']} ---\n")
                    f.write(t.get('rawSamples', 'No samples generated.'))
                    f.write("\n\n")
        self.log_message(f"Samples Exported to {filepath}")

    def export_progress(self):
        progress_data = {
            'courseJSON': self.state['courseJSON'],
            'queue': self.state['queue'],
            'courseTitle': self.state['courseTitle'],
            'courseLevel': self.state['courseLevel']
        }
        
        filepath = os.path.join(os.getcwd(), "course_progress_backup.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)
        self.log_message(f"Progress backup exported to {filepath}")

    def import_progress(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            self.state['courseJSON'] = progress_data.get('courseJSON')
            self.state['queue'] = progress_data.get('queue', [])
            self.state['courseTitle'] = progress_data.get('courseTitle', '')
            self.state['courseLevel'] = progress_data.get('courseLevel', '')
            
            self.state['status'] = 'PAUSED'
            self.log_message(f"Progress imported from {filepath}. Ready to resume build.")
        except Exception as e:
            self.log_message(f"Import Error: {str(e)}", True)

    def run(self):
        if self.state['status'] == 'IDLE':
            self.start_build()
        elif self.state['status'] in ['PAUSED', 'ERROR']:
            self.state['status'] = 'RUNNING'
            self.log_message("Resuming Build Process...")
            self.process_queue()

        if self.state['status'] == 'DONE':
            self.export_course_json()
            self.export_samples()

    def interactive_menu(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=== Carson Academy - Course Builder ===")
            print(f"1. Set API Key         : {'[SET]' if self.state['apiKey'] else '[UNSET]'}")
            print(f"2. Set Course Title    : {self.state['courseTitle'] if self.state['courseTitle'] else '[UNSET]'}")
            print(f"3. Set Education Level : {self.state['courseLevel']}")
            print(f"4. Set Model           : {self.state['model']}")
            print(f"5. Concurrent Sections : {self.state['concurrentCount']}")
            print(f"6. Toggle Infinite Retries : {self.state.get('infiniteRetries', False)}")
            print(f"7. Resume from File    : {self.state['resume_file'] if self.state['resume_file'] else '[NONE]'}") 
            print(f"8. Custom Structure File: {self.state.get('custom_structure_file', '[NONE]')}")
            print(f"9. Custom Samples File : {self.state.get('custom_samples_file', '[NONE]')}")
            build_status = "" if self.state['status'] == 'IDLE' else f" [IN PROGRESS: {self.state['status']}]" 
            print(f"10. START / RESUME BUILD{build_status}")
            print(f"11. Exit")
            print("==============================================") 
            print("Shortcuts available at any time: (e)xport, (i)mport, (s)tart from section, (p)ause, (r)esume") 
            
            choice = input("Select an option (1-11) or type e/i/s/p/r: ").strip().lower()
            
            if choice == '1':
                self.state['apiKey'] = input("Enter API Key: ").strip()
            elif choice == '2':
                self.state['courseTitle'] = input("Enter Course Title: ").strip()
            elif choice == '3':
                self.state['courseLevel'] = input("Enter Education Level (e.g., High School): ").strip()
            elif choice == '4':
                self.state['model'] = input("Enter Model: ").strip()
            elif choice == '5':
                try:
                    count = int(input("Enter Concurrent Sections (1-10): ").strip())
                    self.state['concurrentCount'] = count
                    self.state['concurrent'] = count > 1
                except ValueError:
                    pass
            elif choice == '6':
                self.state['infiniteRetries'] = not self.state.get('infiniteRetries', False)
            elif choice == '7': 
                self.state['resume_file'] = input("Enter path to resume file: ").strip() 
                if self.state['resume_file']: 
                    self.import_progress(self.state['resume_file']) 
                    input("Press Enter to continue...") 
            elif choice == '8':
                self.state['custom_structure_file'] = input("Enter path to custom structure text file: ").strip()
            elif choice == '9':
                self.state['custom_samples_file'] = input("Enter path to custom master samples text file: ").strip()
            elif choice == 'e': 
                self.export_progress()
                input("Press Enter to continue...")
            elif choice == 'i':
                filepath = input("Enter path to import: ").strip()
                if filepath:
                    self.import_progress(filepath)
                input("Press Enter to continue...")
            elif choice == 's':
                if not self.state['queue']:
                    print("Queue is empty. Build structure first.")
                else:
                    for idx, t in enumerate(self.state['queue']):
                        print(f"[{idx}] {t['status']} - {t['title']}")
                    try:
                        start_idx = int(input("\nEnter the number of the section to start from: ").strip())
                        for i in range(len(self.state['queue'])):
                            if i < start_idx:
                                if self.state['queue'][i]['status'] in ['PENDING', 'ERROR', 'RUNNING']:
                                    self.state['queue'][i]['status'] = 'DONE'
                                    self.state['queue'][i]['desc'] = 'Skipped.'
                            else:
                                self.state['queue'][i]['status'] = 'PENDING'
                                self.state['queue'][i]['desc'] = 'Pending execution...'
                        self.state['status'] = 'PAUSED'
                        self.log_message(f"Reset queue to start from task #{start_idx}.")
                    except ValueError:
                        print("Invalid input.")
                input("Press Enter to continue...")
            elif choice == 'p':
                if self.state['status'] == 'RUNNING':
                    self.state['status'] = 'PAUSED'
                    self.log_message("Build paused by user. Active tasks will complete.")
                else:
                    print("Build is not currently running.")
                input("Press Enter to continue...")
            elif choice == 'r':
                if self.state['status'] in ['PAUSED', 'ERROR']:
                    self.log_message("Resuming build in background...")
                    threading.Thread(target=self.run, daemon=True).start()
                else:
                    print("Build is already running or cannot be resumed.")
                input("Press Enter to continue...")
            elif choice == '10':
                if not self.state['apiKey']: 
                    print("Error: API Key is required.")
                    input("Press Enter to continue...")
                    continue
                if not self.state['courseTitle'] and not self.state['courseJSON']:
                    print("Error: Course Title is required.")
                    input("Press Enter to continue...")
                    continue
                print("\nStarting build... (Type e/i/s/p/r and press Enter at any time to execute shortcuts)")
                
                build_thread = threading.Thread(target=self.run, daemon=True)
                build_thread.start()
                
                while build_thread.is_alive() or self.state['status'] == 'PAUSED':
                    try:
                        cmd = input().strip().lower()
                        if cmd == 'e':
                            self.export_progress()
                        elif cmd == 'i':
                            filepath = input("Enter path to import: ").strip()
                            if filepath:
                                self.import_progress(filepath)
                        elif cmd == 's':
                            if not self.state['queue']:
                                print("Queue is empty.")
                            else:
                                for idx, t in enumerate(self.state['queue']):
                                    print(f"[{idx}] {t['status']} - {t['title']}")
                                try:
                                    start_idx = int(input("\nEnter the number of the section to start from: ").strip())
                                    for idx_q in range(len(self.state['queue'])):
                                        if idx_q < start_idx:
                                            if self.state['queue'][idx_q]['status'] in ['PENDING', 'ERROR', 'RUNNING']:
                                                self.state['queue'][idx_q]['status'] = 'DONE'
                                                self.state['queue'][idx_q]['desc'] = 'Skipped.'
                                        else:
                                            self.state['queue'][idx_q]['status'] = 'PENDING'
                                            self.state['queue'][idx_q]['desc'] = 'Pending execution...'
                                    self.state['status'] = 'PAUSED'
                                    self.log_message(f"Reset queue to start from task #{start_idx}.")
                                    self.state['status'] = 'RUNNING'
                                    build_thread = threading.Thread(target=self.process_queue, daemon=True)
                                    build_thread.start()
                                except ValueError:
                                    print("Invalid input.")
                        elif cmd == 'p':
                            if self.state['status'] == 'RUNNING':
                                self.state['status'] = 'PAUSED'
                                self.log_message("Build paused by user. Active tasks will complete.")
                            else:
                                print("Build is not currently running.")
                        elif cmd == 'r':
                            if self.state['status'] in ['PAUSED', 'ERROR']:
                                self.log_message("Resuming build...")
                                build_thread = threading.Thread(target=self.run, daemon=True)
                                build_thread.start()
                            else:
                                print("Build is already running or cannot be resumed.")
                        elif cmd == '':
                            if not build_thread.is_alive() and self.state['status'] != 'PAUSED':
                                break
                    except EOFError:
                        break
                        
                if not build_thread.is_alive() and self.state['status'] != 'PAUSED': 
                    input("\nPress Enter to return to menu...") 
            elif choice == '11':
                print("Exiting...") 
                sys.exit(0) 


if __name__ == "__main__":
    app = HeadlessCourseBuilder()
    app.interactive_menu()
