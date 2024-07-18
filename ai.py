import requests
import json
import sys
import os
import argparse
import datetime
import random
import subprocess
import platform
from rich.console import Console
from rich.markdown import Markdown

# Constants
OLLAMA_URL = 'http://localhost:11434/'  # Update this if your Ollama URL is different
DEFAULT_LLM = 'deepseek-coder-v2:16b'  #'llama3:70b'  # Update this to your default model

console = Console()

def stream_api_response(chat_history):
    url = OLLAMA_URL + 'api/chat'
    payload = {
        "model": DEFAULT_LLM,
        "messages": chat_history,
        "stream": True,
    }
    console.log('[bold black]' + DEFAULT_LLM)
    spinnerList = ['arc', 'dots12', 'growHorizontal']
    with console.status("[bold yellow] Thinking...", spinner=random.choice(spinnerList)) as status:
        with requests.post(url, stream=True, json=payload) as response:
            response.raise_for_status()
            hist_output = ''
            for line in response.iter_lines():
                if line:
                    char = json.loads(line.decode("utf-8"))['message']['content']
                    hist_output += char
            markdown = Markdown(hist_output)
            console.print(markdown)
            console.log("[bold black]Done")
    return hist_output


def main():
    parser = argparse.ArgumentParser(description="AI Assistant using Ollama API")
    parser.add_argument("query", nargs="*", help="Query for the AI")
    
    # Functional
    parser.add_argument("-l", action="store_true", help="Print the last LLM response")
    parser.add_argument("-e", action="store_true", help="Generate command to complete a task")

    # Basic prompts
    parser.add_argument("--extract-wisdom", action="store_true", help="Summarize and extract key insights")
    parser.add_argument("--explain-code", action="store_true", help="Explain the provided")
    parser.add_argument("--optimize-code", action="store_true", help="Suggest optimizations")
    parser.add_argument("--find-bugs", action="store_true", help="Analyze code for potential issues")
    parser.add_argument("--document", action="store_true", help="Generate documentation for code")
    
    # Advanced prompts
    parser.add_argument("--architect", action="store_true", help="Propose architecture for the described problem")
    parser.add_argument("--refactor", action="store_true", help="Suggest refactoring strategys for the provided code")
    parser.add_argument("--security-audit", action="store_true", help="Perform a security audit on the provided code")
    parser.add_argument("--design-patterns", action="store_true", help="Suggest applicable design patterns")

    args = parser.parse_args()

    # Check if there's piped input
    if not sys.stdin.isatty():
        piped_input = sys.stdin.read().strip()
    else:
        piped_input = None

    # Construct the query
    if piped_input:
        query = f"\n\nContent:\n{piped_input}\n\n\n" + " ".join(args.query)
    else:
        query = " ".join(args.query)

    # Prepare the chat history
    now = datetime.datetime.now()
    nowdate = now.strftime("%Y/%m/%d %H:%M")
    system_message = "The current time is {0}. ".format(nowdate)

    OS = False
    system = platform.system()
    if system == "Linux":
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
            os_info = dict(line.strip().split("=", 1) for line in lines if "=" in line)
            OS = "{0} {1}".format(os_info.get('NAME', 'Unknown'), os_info.get('VERSION', ''))
        except FileNotFoundError:
            pass
    elif system == "Windows":
        OS = "Windows {0}".format(platform.win32_ver()[0])
    elif system == "Darwin":
        OS = "macOS {0}".format(platform.mac_ver()[0])
    else:
        OS = system
    if OS:
        system_message += "The user operating system is {0}. ".format(OS.replace('"', ''))
    
    if args.extract_wisdom:
        system_message += "Your task is to extract wisdom, summarize, and provide key insights from the content. Do not leave out any important facts or details that may influence the understanding. Organizing information in bullet points is preffered. "
    elif args.explain_code:
        system_message += "Your task is to explain the provided code in detail, breaking down its functionality and purpose. Do not explain the basic fundamentals or simple functions, such as printing. "
    elif args.optimize_code:
        system_message += "Your task is to analyze the provided code and suggest optimizations for improved performance or readability. Repeat the code in full as provided, but with brief comments on the same line. "
    elif args.find_bugs:
        system_message += "Your task is to carefully analyze the code for potential bugs, issues, or vulnerabilities. "
    elif args.document:
        system_message += "Your task is to generate comprehensive documentation for the provided code, including function descriptions and usage examples. "
    elif args.architect:
        system_message += "Your task is to propose a detailed software architecture for the described problem, considering scalability and maintainability. "
    elif args.refactor:
        system_message += "Your task is to suggest a comprehensive refactoring strategy for the provided code, improving its structure and maintainability. "
    elif args.security_audit:
        system_message += "Your task is to perform a thorough security audit on the provided code, identifying potential vulnerabilities and suggesting mitigations. "
    elif args.design_patterns:
        system_message += "Your task is to suggest applicable design patterns for the given problem, explaining how they would be implemented and their benefits. "
    if not args.e:
        system_message += "Do not repeat the system message. Ensure your answers are well thought out and use the best technical practices when answering questions. "
        system_message += "If your response to the user includes code or code snippets, ensure the starting code wrapper ``` is followed with the name of the programming language. "
    else:
        system_message += """You are designed to act as a command line expert. Your primary function is to understand user descriptions of desired commands and output the exact Linux command that can be run on the terminal without any additional text or explanation.\nConstraints: You should strictly output Linux commands without any explanatory text, preambles, or follow-up messages. It must ensure the commands are syntactically correct and applicable to the described task.\nGuidelines: You should be capable of interpreting a wide range of descriptions related to file management, system administration, networking, and software management among other Linux command line tasks. It should focus on providing the most direct and efficient command solution to the user's request.\nClarification: You should be biased toward making a response based on the intended behavior, filling in any missing details. If the description is too vague or broad, it should opt for the most commonly used or straightforward command related to the request. Each seperate command should be on a new line.\nPersonalization: You maintain a neutral tone, focusing solely on the accuracy and applicability of the Linux commands provided. """

    chat_history = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]

    # Call the API
    if args.l:
        with open('.aicli_last', 'r') as f:
            output = f.read()
            markdown = Markdown(output)
            console.print(markdown)
    else:
        output = stream_api_response(chat_history)
        with open('.aicli_last', 'w') as f:
            f.write(''.join(output))
    if args.e:
        outputs = output.split('```')
        code = []
        if len(outputs) == 3:
            if '\n' in outputs[1]:
                code.append(outputs[1])
        elif len(outputs) == 5:
            if '\n' in outputs[1]:
                code.append(outputs[1])
            if '\n' in outputs[3]:
                code.append(outputs[3])
        else:
            code = output.split()
        if len(code) > 0 and len(code) < 3:
            color = '\033[38;5;88m'
            for c in code:
                choice = input("{0}[ (\033[31;0mE{0})xecute | (\033[31;0mD{0})escribe | (\033[31;0mC{0})ancel ]\033[31;239m:\033[31;0m ".format(color)).upper()
                if choice == 'E':
                    result = subprocess.run(c.split(), capture_output=True, text=True)

                    # Print the output and error (if any)
                    print("Output:", result.stdout)
                    if result.stderr:
                        print("Error:", result.stderr)
                elif choice == 'D':
                    chat_history = [
                        {"role": "system", "content": 'Your task is to explain the provided code in detail, breaking down its functionality and purpose. Do not explain the basic fundamentals or simple functions, such as printing. '},
                        {"role": "user", "content": '\n\n\n'.join(code)}
                    ]
                    stream_api_response(chat_history)
                    choice = input("{0}[ (\033[31;0mE{0})xecute | (\033[31;0mC{0})ancel ]\033[31;239m:\033[31;0m ".format(color)).upper()
                    if choice == 'E':
                        os.system(c)
                    else:
                        pass
                else:
                    pass

if __name__ == "__main__":
    main()
