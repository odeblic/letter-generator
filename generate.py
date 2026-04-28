import argparse
import csv
import datetime
import glob
import jinja2
import os
import shutil
import subprocess
import yaml
from dataclasses import dataclass
from pathlib import Path


def render(template: str, variables: dict[str, str]) -> str:
    return jinja2.Template(template, undefined=jinja2.StrictUndefined).render(variables)


@dataclass
class Sender:
    full_name: str
    phone_number: str
    email_address: str
    signature_file: str | None = None

    @classmethod
    def read_yaml(cls, file: Path) -> 'Sender':
        with open(file, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)


@dataclass
class Context:
    label: str
    template: str
    sender: str
    variables: list[str]
    date: datetime.date | None = None

    @classmethod
    def read_yaml(cls, file: Path) -> 'Context':
        with open(file, 'r') as f:
            data = yaml.safe_load(f)
        if 'label' not in data:
            data['label'] = data['template']
        if 'variables' not in data:
            data['variables'] = []
        if 'date' in data:
            data['date'] = datetime.datetime.strptime(data['date'], "%Y-%m-%d").date()
        return cls(**data)


@dataclass
class Template:
    attention: str
    subject: str
    greeting: str
    content: list[str]
    closing: str

    @classmethod
    def read_yaml(cls, file: Path) -> 'Template':
        with open(file, 'r') as f:
            data = yaml.safe_load(f)
        for line in data['content']:
            if len(line) == 0:
                raise ValueError('Empty lines are not allowed')
        return cls(**data)

    def __write_contact(self, full_name: str, phone_number: str, email_address: str) -> None:
        with open('contact.tex', 'w') as f:
            f.write(f'{full_name}\n')
            f.write('\\newline\n')
            f.write(f'{phone_number}\n')
            f.write('\\newline\n')
            f.write(f'\\uline{{{email_address}}}\n')
            f.write('\\newline\n')

    def __write_date(self, date: datetime.date | None = None) -> None:
        with open('date.tex', 'w') as f:
            if date is None:
                date = datetime.datetime.now()
            text = date.strftime("%d. %B %Y")
            f.write(f'\hfill {text}\n')
            f.write('\\newline\n')

    def __write_attention(self, variables: dict[str, str]) -> None:
        with open('attention.tex', 'w') as f:
            text = render(self.attention, variables)
            f.write(f'\\uline{{\\textbf{{Attention:}}}}\n')
            f.write(f'{text}\n')
            f.write('\\newline\n')

    def __write_subject(self, variables: dict[str, str]) -> None:
        with open('subject.tex', 'w') as f:
            text = render(self.subject, variables)
            f.write(f'\\uline{{\\textbf{{Subject:}}}}\n')
            f.write(f'{text}\n')
            f.write('\\newline\n')

    def __write_greeting(self, variables: dict[str, str]) -> None:
        with open('greeting.tex', 'w') as f:
            greeting = variables.get('greeting', self.greeting)
            for line in greeting.split('\n'):
                text = render(line, variables)
                f.write(f'{text}\n')
                f.write('\\newline\n')

    def __write_content(self, variables: dict[str, str]) -> None:
        with open('content.tex', 'w') as f:
            for line in self.content:
                text = render(line, variables)
                f.write(f'{text}\n')
                f.write('\\newline\n\n')

    def __write_closing(self, variables: dict[str, str]) -> None:
        with open('closing.tex', 'w') as f:
            text = render(self.closing, variables)
            f.write(f'{text}\n')
            f.write('\\newline\n')

    def __write_signature(self, signature_file: str | None, full_name: str) -> None:
        with open('signature.tex', 'w') as f:
            if signature_file is not None:
                f.write('\\hspace{8cm}\n')
                f.write(f'\\includegraphics[scale=0.2]{{senders/{signature_file}}}\n')
            else:
                f.write('\\hspace{8cm}\n')
                f.write(f'{full_name}\n')

    # TODO: use a dedicated folder for LateX
    def write_latex(self, context: Context, sender: Sender, date: datetime.date | None = None) -> None:
        self.__write_contact(sender.full_name, sender.phone_number, sender.email_address)
        self.__write_date(date or context.date)
        self.__write_attention(context.variables)
        self.__write_subject(context.variables)
        self.__write_greeting(context.variables)
        self.__write_content(context.variables)
        self.__write_closing(context.variables)
        self.__write_signature(sender.signature_file, sender.full_name)


def build_pdf(label: str) -> None:
    folder = Path('output')
    folder.mkdir(exist_ok=True)
    try:
        with open(f'output/pdflatex-{label}.log', 'w') as log_file:
            command = ["pdflatex", f'-output-directory={folder.name}', f'-jobname={label}', "document.tex"]
            subprocess.run(command, check=True, stdout=log_file, stderr=subprocess.STDOUT)
        print('\033[32mCover letter generated with success\033[0m')
    except subprocess.CalledProcessError as e:
        print('\033[31mCover letter failed to be generated\033[0m')
        print(f'\033[31mError: {e}.\033[0m')


def cleanup(label: str) -> None:
    folder = Path('output')
    os.remove(folder / f'pdflatex-{label}.log')
    os.remove(folder / f'{label}.log')
    os.remove(folder / f'{label}.aux')
    os.remove(folder / f'{label}.out')
    os.remove('date.tex')
    os.remove('greeting.tex')
    os.remove('attention.tex')
    os.remove('subject.tex')
    os.remove('closing.tex')
    os.remove('contact.tex')
    os.remove('content.tex')
    os.remove('signature.tex')


# unused
def move_documents() -> None:
    folder = Path('documents')
    folder.mkdir(exist_ok=True)
    for pdf_file in glob.glob('output/*.pdf'):
        source_file = Path(pdf_file)
        destination_file = folder / source_file.name
        print(f'Getting document \033[35m{destination_file.name}\033[0m')
        shutil.move(source_file, destination_file)


# TODO: normalize the CTX generation from CVS
def make_context() -> None:
    folder = Path('contexts')
    folder.mkdir(exist_ok=True)
    source_file = 'roles.csv'
    print(f'Generating all contexts from \033[33m{source_file}\033[0m')
    with open(source_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for index, row in enumerate(reader):
            company = row['COMPANY']
            position = row['POSITION']
            template = row['TEMPLATE']
            if template.startswith('hr-'):
                prefix = 'Cover letter for the HR officer at'
            elif template.startswith('it'):
                prefix = 'Cover letter for the IT team at'
            else:
                prefix = 'Cover letter for'
            label = f'{prefix} {company} - Olivier de BLIC - {position}'
            context = {
                'label': label,
                'template': 'cover-letter-' + template,
                'sender': 'odeblic',
                'variables': {
                    'company': company,
                    'position': position,
                }
            }
            print(f'Creating context \033[33m{label}\033[0m')
            filename = folder / f'letter_{index + 1}.yaml'
            with open(filename, 'w') as f:
                yaml.dump(context, f, default_flow_style=False)


def main() -> None:
    if args.generate:
        make_context()
    default_sender = None
    if args.sender is not None:
        sender_file = f'senders/{args.sender}.yaml'
        print(f'Looking at file \033[34m{sender_file}\033[0m')
        default_sender = Sender.read_yaml(sender_file)
        print(f'Defaulting the sender to \033[33m{default_sender.full_name}\033[0m')
    for context_file in glob.glob('contexts/*.yaml'):
        print('-' * 60)
        try:
            print(f'Looking at file \033[34m{context_file}\033[0m')
            context = Context.read_yaml(context_file)
            print(f'Processing context \033[35m{context.label}\033[0m')
            template_file = f'templates/{context.template}.yaml'
            print(f'Looking at file \033[34m{template_file}\033[0m')
            template = Template.read_yaml(template_file)
            if default_sender is None:
                sender_file = f'senders/{context.sender}.yaml'
                print(f'Looking at file \033[34m{sender_file}\033[0m')
                sender = Sender.read_yaml(sender_file)
                print(f'Using sender \033[35m{sender.full_name}\033[0m')
            else:
                sender = default_sender
        except (ValueError, TypeError) as e:
            print(f'\033[31mError: {e}\033[0m')
            continue
        try:
            template.write_latex(context, sender, args.date)
        except jinja2.exceptions.UndefinedError as e:
            print(f'\033[31mError at variable substitution: {e}\033[0m')
            continue
        build_pdf(context.label)
        if not args.nocleanup:
            cleanup(context.label)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple string parser")
    parser.add_argument("--generate", action='store_true', help="Generate context files")
    parser.add_argument("--context", help="Only process this context")
    parser.add_argument("--sender", help="Force the sender")
    parser.add_argument("--date", type=datetime.date.fromisoformat, help="Force the date (YYYY-MM-DD)")
    parser.add_argument("--nocleanup", action='store_true', help="Do not cleanup")
    args = parser.parse_args()
    main()
