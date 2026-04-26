# Formal Letter Generator

## Description

Generate letters for different purposes under different identities.

The purpose is determined by the `Context` and the `Template` of the document.

The identity is provided by the `Sender` and its signature.

Documents are generated as PDF files.

## Setup

You need **Python 3.7** or higher.

Few packages are necessary:

```sh
pip install -r requirements.txt
```

`pdflatex` is required (and `LateX` packages) to build PDFs.

## Configuration

Sender:

Contact details of the sender and signature if any.

```yaml
full_name: "John DOE"               # required
phone_number: "(+1) 123456789"      # required
email_address: "john.doe@gmail.com" # required
signature_file: "signature.png"     # optional, replaced by fullname if not provided
```

Senders are defined as `.yaml` files and located in `./senders/`.

Context:

Definition of the context. `variables` are used for **Jinja2** substitutions in text.

```yaml
label: "Job application"     # optional
template: "cover-letter"     # required
sender: "joe"                # required
variables:                   # optional
  company: "OKAM Trade Ltd."
  position: "Vendor"
  recruiter: "Alicia WONG"
date: "1999-12-31"           # optional, defaulted to today's date
```

Contexts are defined as `.yaml` files and located in `./contexts/`.

Template:

Content of the document itself. All fields are required.
If mentioned, variables `%COMPANY%` and `%TITLE%` are substituted
respectively for `attention` and `subject` with values from the role.

```yaml
attention: "Hiring Manager at {{ company }}"
subject: "Application for {{ position }} position"
greeting: "Dear {{ recruiter }},"
content:
  - "I would like to sell stuff on your behalf."
  - "Please hire me."
  - "You can count on my loyalty and dedication."
closing: "Sincerely,"
```

Templates are defined as `.yaml` files and located in `./templates/`.

Overall, the configuration layout looks like this:

```
.
|-- contexts
|   `-- application-joe-okam.yaml
|-- senders
|   |-- joe.yaml
|   `-- signature.png
`-- templates
    `-- cover-letter.yaml
```

## Usage

You just need to run the script with no arguments:

```sh
python3 generator.py
```

All PDF files will be generated in the `output` folder:

```sh
ls output
```
