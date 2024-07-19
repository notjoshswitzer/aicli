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
from rich.live import Live
from rich.panel import Panel

import config # Edit the config.py file

console = Console()

def get_os():
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
    return OS

def stream_api_response(chat_history, args):
    payload = {
        "messages": chat_history,
        "stream": True,
        "model": False
    }

    hist_output = ''
    
    if args.G:
        payload['model'] = config.OAI_LLM
        headers = {"Authorization": "Bearer " + config.OAI_KEY}
        response = requests.post("https://api.openai.com/v1/chat/completions", stream=True, json=payload, headers=headers)
    else:
        payload['model'] = config.OLLAMA_LLM
        response = requests.post(config.OLLAMA_URL + 'api/chat', stream=True, json=payload)

    if not args.x:
        console.log('[bold black]' + payload['model'])

    response.raise_for_status()
    if args.x:
        for line in response.iter_lines():
            if line:
                try:
                    if args.G:
                        char = json.loads(line.decode("utf-8")[6:])['choices'][0]['delta']['content']
                    else:
                        char = json.loads(line.decode("utf-8"))['message']['content']
                    hist_output += char
                    print(char, end='')
                except json.JSONDecodeError:
                    pass
                except KeyError:
                    pass
    else:
        with Live(console=console, refresh_per_second=4) as live:
            for line in response.iter_lines():
                if line:
                    try:
                        if args.G:
                            char = json.loads(line.decode("utf-8")[6:])['choices'][0]['delta']['content']
                        else:
                            char = json.loads(line.decode("utf-8"))['message']['content']
                        hist_output += char
                        markdown = Markdown(hist_output)
                        live.update(Panel(markdown))
                    except json.JSONDecodeError:
                        pass
                    except KeyError:
                        pass

    if not args.x:
        console.log('[bold black]done')

    return hist_output


def main():
    parser = argparse.ArgumentParser(description="AI Assistant using Ollama API")
    parser.add_argument("query", nargs="*", help="Query for the AI")
    
    parser.add_argument("-G", action="store_true", help="Use OpenAI (GPT)")
    # Functional
    parser.add_argument("-l", action="store_true", help="Print the last output")
    parser.add_argument("-x", action="store_true", help="Remove formatting from output")

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

    args = parser.parse_args()
    # Check if there's piped input
    if not sys.stdin.isatty():
        piped_input = sys.stdin.read().strip()
    else:
        piped_input = None

    # Construct the query
    if piped_input:
        query = f"\n\nContent:\n{piped_input}\n\n\n\n" + " ".join(args.query)
    else:
        query = " ".join(args.query)
    if piped_input and len(query) == 0:
        query = "Give a breif description of the provided content. "

    # Prepare the chat history
    now = datetime.datetime.now()
    nowdate = now.strftime("%Y/%m/%d %H:%M")
    system_message = "The current time is {0}. ".format(nowdate)

    # Add user OS information to the prompt
    OS = get_os()
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

    chat_history = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]

    # Print previous response
    if args.l:
        with open('.aicli_last', 'r') as f:
            output = f.read()
            if args.x:
                print(output)
            else:
                markdown = Markdown(output)
                console.print(markdown)
    # Call the Ollama API
    else:
        output = stream_api_response(chat_history, args)
        with open('.aicli_last', 'w') as f:
            f.write(''.join(output))

    if args.x:
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
        color = '\033[38;5;88m'
        if len(code) > 0 and len(code) < 3:
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
                    stream_api_response(chat_history, args)
                    choice = input("{0}[ (\033[31;0mE{0})xecute | (\033[31;0mC{0})ancel ]\033[31;239m:\033[31;0m ".format(color)).upper()
                    if choice == 'E':
                        os.system(c)
                    else:
                        pass
                else:
                    pass

if __name__ == "__main__":
    main()
