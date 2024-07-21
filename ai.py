import os
import sys
import json
import argparse
import datetime
import requests
import platform
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
import config # Edit the config.py file

console = Console()

DEBUG = False

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
    if OS:
        OS = OS.replace('"', '')
    return OS

def stream_api_response(chat_history, args):
    payload = {
        "messages": chat_history,
        "stream": True,
        "model": False
    }

    hist_output = ''
    
    if args.G:
        LLM = 'oai'
    elif args.O:
        LLM = 'ollama'
    else:
        LLM = config.DEFAULT_LLM

    # OpenAI
    if LLM == 'oai':
        payload['model'] = config.OAI_LLM
        headers = {"Authorization": "Bearer " + config.OAI_KEY}
        response = requests.post("https://api.openai.com/v1/chat/completions", stream=True, json=payload, headers=headers)
    # Ollama
    elif LLM == 'ollama':
        payload['model'] = config.OLLAMA_LLM
        response = requests.post(config.OLLAMA_URL + 'api/chat', stream=True, json=payload)
    else:
        print("Invalid LLM")
        exit()

    # Print time/LLM
    if not args.x:
        console.log('[bold black]' + payload['model'])

    response.raise_for_status()
    # Print output *without* markdown formatting
    if args.x:
        for line in response.iter_lines():
            if line:
                try:
                    if LLM == 'oai':
                        char = json.loads(line.decode("utf-8")[6:])['choices'][0]['delta']['content']
                    else:
                        char = json.loads(line.decode("utf-8"))['message']['content']
                    hist_output += char
                    print(char, end='')
                except json.JSONDecodeError:
                    pass
                except KeyError:
                    pass
        print()
    # Print output *with* markdown formatting
    else:
        with Live(console=console, refresh_per_second=8) as live:
            for line in response.iter_lines():
                if line:
                    try:
                        if LLM == 'oai':
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
    # Hi
    if not args.x:
        console.log('[bold black]done')

    return hist_output

def extract_command(output):
    command = []
    command_list = ['bash', 'sh']
    outputs = output.split('```')
    # Iterate through code blocks
    for snip in outputs:
        # Logic to determine language
        for lang in command_list:
            if snip[:len(lang)] == lang:
                command += [snip[len(lang)+1:][:-1]]
    return command

def extract_code(output):
    code = []
    code_list = ['python', 'java', 'javascript', 'cpp', 'c', 'ruby', 'html', 'css', 'php', 'sql', 'go', 'rust', 'perl', 'typescript', 'lua']
    outputs = output.split('```')
    # Iterate through code blocks
    for snip in outputs:
        # Logic to determine language
        for lang in code_list:
            if snip[:len(lang)] == lang:
                code += [snip[len(lang)+1:][:-1]]
    return code

def main():
    parser = argparse.ArgumentParser(description="AI Assistant using Ollama API")
    parser.add_argument("query", nargs="*", help="Query for the AI")

    # ARG LLM Provider
    parser.add_argument("-O", action="store_true", help="Use Ollama")
    parser.add_argument("-G", action="store_true", help="Use OpenAI (GPT)")

    # ARG Functions
    parser.add_argument("-E", action="store_true", help="Extract command(s) from last output")
    parser.add_argument("-C", action="store_true", help="Extract code from last output")

    # ARG Formatting
    parser.add_argument("-l", action="store_true", help="Print the last output")
    parser.add_argument("-x", action="store_true", help="Remove formatting from output")

    # ARG Engineering prompts
    parser.add_argument("--security-audit", action="store_true", help="Perform a security audit on the provided code")
    parser.add_argument("--extract-wisdom", action="store_true", help="Summarize and extract key insights")
    parser.add_argument("--explain-code", action="store_true", help="Explain the provided code")
    parser.add_argument("--optimize-code", action="store_true", help="Suggest optimizations")
    parser.add_argument("--find-bugs", action="store_true", help="Analyze code for potential issues")
    parser.add_argument("--document", action="store_true", help="Generate documentation for code")
    parser.add_argument("--architect", action="store_true", help="Propose architecture for the described problem")
    parser.add_argument("--refactor", action="store_true", help="Suggest refactoring strategys for the provided code")

    args = parser.parse_args()

    # Print previous response
    if args.l or args.E or args.C:
        # Open history file to print previous output from LLM
        with open('.aicli_last', 'r') as f:
            output = f.read()
            # Determine if output is wrapped in code wrappers
            if args.C:
                code = extract_code(output)
                for c in code:
                    print(c)
            elif args.E:
                code = extract_command(output)
                for c in code:
                    print(c)
            elif args.x:
                print(output)
            else:
                # Print output w/ markdown using rich library
                markdown = Markdown(output)
                console.print(markdown)
        exit()

    # Check if there's piped input
    if not sys.stdin.isatty():
        piped_input = sys.stdin.read().strip()
    else:
        piped_input = None

    # Construct the query
    if piped_input:
        query = f"<content>{piped_input}</content>\n\n" + " ".join(args.query)
    else:
        query = " ".join(args.query)

    # Create system prompt
    system_message = []

    # Add date & time to system prompt
    now = datetime.datetime.now()
    nowdate = now.strftime("%Y/%m/%d %H:%M")
    system_message += ["The current date and time is {0}.".format(nowdate)]

    # Add OS details to the prompt
    OS = get_os()
    if OS:
        system_message += ["The user operating system is {0}.".format(OS)]

    # Prompt AI to respond with markdown
    if not args.x:
        system_message += ["Your response should be in markdown format."]
    
    # Generic prompts to curate output
    if args.extract_wisdom:
        system_message += ["Your task is to extract wisdom, summarize, and provide key insights from the content. Do not leave out any important facts or details that may influence the understanding. Organizing information in bullet points is preffered."]
    elif args.explain_code:
        system_message += ["Your task is to explain the provided code in detail, breaking down its functionality and purpose. Do not explain the basic fundamentals or simple functions, such as printing."]
    elif args.optimize_code:
        system_message += ["Your task is to analyze the provided code and suggest optimizations for improved performance or readability. Repeat the code in full as provided, but with brief comments on the same line."]
    elif args.find_bugs:
        system_message += ["Your task is to carefully analyze the code for potential bugs, issues, or vulnerabilities."]
    elif args.document:
        system_message += ["Your task is to generate comprehensive documentation for the provided code, including function descriptions and usage examples."]
    elif args.architect:
        system_message += ["Your task is to propose a detailed software architecture for the described problem, considering scalability and maintainability."]
    elif args.refactor:
        system_message += ["Your task is to suggest a comprehensive refactoring strategy for the provided code, improving its structure and maintainability."]
    elif args.security_audit:
        system_message += ["Your task is to perform a thorough security audit on the provided code, identifying potential vulnerabilities and suggesting mitigations."]

    # Define chat history list
    chat_history = [
        {"role": "system", "content": ' '.join(system_message)},
        {"role": "user", "content": query}
    ]

    if DEBUG:
        print('[DEBUG] SYSTEM PROMPT:')
        for chat in chat_history:
            print('ROLE: {0:<8} CONTENT: {1}'.format(chat['role'], chat['content']))

    # Call the selected API
    output = stream_api_response(chat_history, args)
    # Write output to file in event -l is called for previous response
    with open('.aicli_last', 'w') as f:
        f.write(''.join(output))

if __name__ == "__main__":
    main()
