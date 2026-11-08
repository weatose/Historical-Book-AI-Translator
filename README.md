# Historical Book AI Translator

### Preserving the past, making knowledge accessible, and building a foundation for the future.

**An open-source, AI-assisted historical book transcription and translation pipeline powered by Python, AMD Lemonade, and vision-language models.**

**Project Status:** Working Prototype | Active Development  
**Initial Language:** Latin → English  
**First Historical Source:** *De Magnete* (1600), William Gilbert  
**Local AI Backend:** AMD Lemonade  
**Development Platform:** Windows 10 / Python 3.11

---

## 📖 Project Overview

Throughout history, countless books have been written by people who were attempting to understand the world with the knowledge and tools available to them.

Many of these works contain scientific observations, philosophical arguments, mathematical theories, medical ideas, cultural beliefs, and historical perspectives that are rarely encountered today.

Unfortunately, a large portion of this material remains difficult to access.

Some books have never received modern translations. Others exist only as scanned pages containing centuries-old typography, damaged lettering, unfamiliar languages, or printing conventions that modern optical character recognition software struggles to interpret.

**Historical Book AI Translator is my attempt to help change that.**

The project uses artificial intelligence to examine scanned historical documents, transcribe their original text, and translate that material into modern languages while preserving the original wording for comparison.

My objective is not simply to generate readable translations. I want to develop a reproducible, expandable system that can help preserve historical knowledge and make it easier for anyone to explore.

I believe there is tremendous value in understanding not only what earlier generations discovered, but how they reasoned, what they believed, and how they interpreted the world around them.

Even when their conclusions were incorrect, their thought processes remain an important part of human intellectual history.

Sometimes learning how people understood the world hundreds of years ago can change how we understand our own.

That is the foundation of this project.

---

## 🎯 Project Goals

The primary goals of Historical Book AI Translator are:

1. **Preserve historical literature** by creating accessible digital transcriptions of old books and documents.

2. **Translate historical languages** into modern languages without unnecessarily changing the original author's meaning.

3. **Maintain access to original source material** so readers and researchers can compare AI-generated text with the historical document.

4. **Improve transcription accuracy** through additional AI-assisted correction and verification passes.

5. **Make historical knowledge more accessible** to independent researchers, students, historians, developers, and anyone curious about the past.

6. **Support local AI processing** to reduce dependence on expensive hosted services and make the technology more accessible.

7. **Build an expandable open-source foundation** that can eventually support additional languages, historical collections, research tools, and interactive educational applications.

The long-term goal is to create a system that can be adapted to many historical documents rather than developing a translator limited to one particular book.

---

## 📚 The First Book: *De Magnete* (1600)

The first book selected for this project is *De Magnete*, published in 1600 by the English physician and natural philosopher William Gilbert.

This work is an important contribution to the early scientific study of magnetism and electricity.

Gilbert investigated magnetic behavior through observation, experimentation, and comparisons with earlier explanations of natural phenomena.

What makes the book particularly interesting to me is the way it demonstrates a historical transition in scientific thinking.

Earlier explanations of magnetism frequently involved astrology, mystical properties, planetary influences, and other beliefs that were widely discussed before modern scientific explanations became established.

Gilbert examined and challenged many of these claims while developing his own experimental approach.

Reading the original text provides an opportunity to experience scientific reasoning from a time when many of the concepts we now consider fundamental had not yet been established.

**This is exactly the kind of historical material I want to help preserve.**

The initial workflow uses scanned pages from the Latin edition, processes the original page images, and produces English translations alongside the Latin transcription.

### Why start with Latin?

Latin was widely used in European scholarship for centuries.

Important works in astronomy, mathematics, natural philosophy, medicine, theology, and other fields were published in Latin.

By beginning with Latin, this project can establish a workflow that may eventually be adapted to a much larger collection of historical scientific and philosophical literature.

---

## ⚙️ How the System Works

The application uses a multi-stage Python pipeline to process historical book pages.

### Stage 1 — Document Processing

A scanned PDF is loaded into the application.

Individual pages are rendered into images using PyMuPDF.

The rendering resolution can be configured to balance image clarity, memory consumption, and processing speed.

Historical typography presents unique challenges, so the quality of the source image is particularly important.

### Stage 2 — AI Transcription

A vision-language model examines the rendered page image and attempts to reproduce the original Latin text.

The transcription instructions emphasize preserving:

- Original wording and spelling
- Historical punctuation
- Paragraph structure
- Unusual or unfamiliar terminology
- Uncertain or unreadable passages

The objective is to recover the text as faithfully as possible rather than rewriting it into modern Latin.

### Stage 3 — Translation

The transcribed Latin is passed to an AI language model for translation into English.

The translation process aims to preserve the author's intended meaning while producing readable modern English.

Historical scientific terminology requires special attention because some words were used differently from their modern equivalents.

Translations should not silently replace historical concepts with modern scientific interpretations.

### Stage 4 — Correction and Comparison

The project includes an additional correction workflow designed to improve transcription reliability.

This process can independently examine the original page, compare readings, and produce revised Latin and English outputs.

Differences between versions can be retained for review.

This is especially useful when processing historical printing, where individual characters may be misread or confused.

AI-assisted correction is not equivalent to human verification, and additional review remains necessary.

### Stage 5 — Output Generation

Processed text is saved into structured output files.

The pipeline supports side-by-side Markdown output, allowing the Latin transcription and English translation to be examined together.

Separate page files help preserve progress and make it easier to revisit individual sections without restarting an entire book.

---

## 🛠️ Current Features

The working prototype includes:

- PDF page rendering
- AI-assisted image transcription
- Latin-to-English translation
- Local and hosted AI backend configuration
- OpenAI-compatible API integration
- Sequential page processing
- Configurable cooldown intervals
- Automatic retry handling
- Individual page output files
- Markdown output generation
- Additional transcription correction workflow
- Logging and error reporting
- Resume-friendly processing through saved page results

These features were developed with practical hardware limitations in mind.

Instead of attempting to process an entire historical book at once, the application processes manageable groups of pages and saves the results as work progresses.

This approach reduces the risk of losing completed work and makes long-running historical preservation projects more manageable.

---

## 🍋 AMD Lemonade Integration

A major objective of this project is to demonstrate that useful historical document processing can be performed with locally hosted AI models.

AMD Lemonade provides a way to run compatible AI models locally through an OpenAI-compatible API.

The Python pipeline can communicate with the Lemonade server without requiring a separate cloud inference service.

For the initial local demonstration, I used:

**Model:** Qwen2.5-VL-7B-Instruct-GGUF  
**Backend:** AMD Lemonade  
**API:** Local OpenAI-compatible endpoint  
**Tasks:** Historical page transcription and Latin-to-English translation

The application also supports AMD Token Lab as an optional hosted backend for development and comparison.

Switching between backends is handled through the project configuration.

### Why local AI matters

Local inference offers several potential benefits:

- Reduced dependence on hosted AI services
- No cloud inference charges for locally processed requests
- Greater control over model selection and processing
- The ability to work with documents without transmitting them to a hosted inference provider
- More opportunities for independent developers to experiment with AI applications

Local processing is particularly interesting for historical preservation because large collections may require thousands of individual page-processing operations.

Reducing the ongoing cost of those operations could make projects like this more accessible.

---

## 💻 Development Hardware

This project is currently being developed on an older consumer computer.

| Component | Hardware |
|---|---|
| Operating System | Windows 10 Pro |
| Processor | Intel Core i7-6700 |
| Memory | 16 GB RAM |
| Graphics Card | NVIDIA GeForce RTX 2060 SUPER |
| Video Memory | 8 GB VRAM |
| Python | 3.11 |
| Local AI Platform | AMD Lemonade |

This is not a modern dedicated AI workstation.

The limited memory and VRAM place practical restrictions on which models can be loaded, how much context can be allocated, and how quickly documents can be processed.

These limitations have directly influenced the design of the application.

### Developing with limited resources

Rather than abandoning the project because of hardware constraints, I have focused on making the workflow more manageable.

Some of the approaches include:

- Processing pages sequentially
- Introducing configurable delays between requests
- Saving completed work before moving to the next page
- Retrying temporary failures
- Monitoring memory and GPU usage
- Testing small page ranges before attempting larger batches
- Adjusting model context settings to accommodate scanned document requests

This has been a significant learning experience.

Working with older hardware has forced me to pay attention to resource consumption, error handling, and practical reliability.

I believe those lessons can be useful to other developers working with limited equipment.

**The goal is not to demonstrate the most powerful computer. It is to demonstrate what can be accomplished with the resources already available.**

---

## 📊 Local AI Test Results

**Test Date:** November 7, 2026  
**AI Platform:** AMD Lemonade  
**Model:** Qwen2.5-VL-7B-Instruct-GGUF  
**Source:** *De Magnete* (1600)  
**Test Pages:** 60–61

The following results were recorded during a successful local processing test.

| Page | Processing Time | Result |
|---|---|---|
| Page 60 | 90 seconds | Completed |
| Page 61 | 101 seconds | Completed |

**Total elapsed time:** Approximately 3 minutes and 21 seconds, including the configured cooldown interval.

Both pages completed successfully on their first attempts during the final test.

### Technical challenges encountered

Initial testing produced an HTTP 400 error because the scanned page request exceeded the model's configured context size.

The request required approximately 4,062 tokens, while the available context was only 2,560 tokens.

After adjusting the model's context configuration and restarting the test, the application successfully processed both pages.

This was an important milestone because it confirmed that the Python pipeline could communicate with Lemonade and complete the transcription and translation workflow using local inference.

### What these results demonstrate

The test demonstrates:

- Successful communication with the local Lemonade API
- Working integration with a locally hosted vision-language model
- Successful processing of scanned historical pages
- Sequential execution with configurable cooldowns
- Completion of the requested two-page test
- No hosted inference credits required for the local run

These results do not establish transcription accuracy or translation quality. Those require separate evaluation against verified historical text.

Future testing will focus on measuring accuracy, performance, and reliability across larger collections and different AI models.

---

## 🚀 Installation and Setup

### Requirements

- Windows or another operating system capable of running the required software
- Python 3.11 or a compatible version
- AMD Lemonade for local inference
- A compatible vision-language model
- A scanned historical PDF document

Install the project's Python dependencies:

```bash
python -m pip install -r requirements.txt
```

### Step 1 — Prepare the Project

Download or clone this repository.

Place a legally usable historical PDF in the project directory.

The default filename is:

```text
book.pdf
```

### Step 2 — Configure the AI Backend

Open the configuration file:

```text
config.toml
```

For local processing, set:

```toml
active = "lemonade"
```

Configure the Lemonade API endpoint and model identifiers to match your installation.

For example:

```toml
[backends.lemonade]
base_url = "http://127.0.0.1:13305/api/v1"
api_key = "lemonade"
vision_model = "Qwen2.5-VL-7B-Instruct-GGUF"
text_model = "Qwen2.5-VL-7B-Instruct-GGUF"
requests_per_minute = 0
```

The address above is an example from the development environment. The actual local server address may differ between installations.

The local `api_key` value is a client placeholder and is not a cloud API credential.

### Step 3 — Start AMD Lemonade

Launch AMD Lemonade and make sure the local server is running.

Load a compatible vision-language model.

Confirm that the model is available through the local API.

The model must support image input for scanned page transcription.

### Step 4 — Run a Small Test

Open a command prompt in the project directory.

For example:

```cmd
python auto_loader.py --start 60 --end 61 --wait 10
```

This requests processing of pages 60 and 61 with a 10-second cooldown between pages.

Page numbering refers to the PDF pages used by the application, which may not match the printed page numbers inside a historical book.

### Step 5 — Review the Results

After processing, examine the generated files in the configured output directory.

The application produces page-level text outputs and assembled Markdown files for reviewing the Latin transcription and English translation.

Compare the results against the original scanned document.

**Important:** Historical text generated by AI should always be reviewed before being treated as an accurate scholarly transcription or translation.

---

## 🔍 Historical Accuracy and Responsible Use

Historical preservation requires more than producing readable text.

AI models can introduce errors when interpreting damaged documents, unusual typography, unfamiliar terminology, or ambiguous passages.

A transcription may appear convincing while containing incorrect words.

A translation may sound natural while changing the meaning of the original author.

For this reason, the project is designed around preserving the relationship between the original source and the generated output.

The following principles guide development:

**Source preservation:** Original historical documents remain the primary evidence.

**Transparency:** AI-generated text should be identified as machine-produced until independently verified.

**Historical context:** Authors should be understood within the intellectual and cultural environment of their own time.

**Correction and review:** Uncertain passages should be revisited rather than silently treated as accurate.

**Reproducibility:** Processing methods, model configurations, and results should be documented wherever practical.

The purpose of this project is to improve access to historical knowledge, not to replace professional historical scholarship.

---

## 🌍 Future Language Expansion

Although the initial project focuses on Latin-to-English translation, the underlying approach is intended to be adaptable.

Potential future language support includes:

- Ancient Greek
- Medieval Latin
- Early Modern English
- French
- German
- Italian
- Spanish
- Other historical languages supported by suitable AI models

Different languages and historical writing systems will require additional testing and potentially specialized models.

The objective is to make the processing pipeline flexible enough to support different source and target languages without rebuilding the entire application.

---

## 🧠 Long-Term Vision: Understanding Historical Perspectives

The translator is only the beginning of a much larger idea.

One of the things I find most fascinating about history is that the people who lived hundreds or thousands of years ago were not fundamentally different from us in their capacity to observe, question, imagine, and reason.

They were working with different information, different experiences, and different explanations of the world.

I want to explore what becomes possible when we preserve those historical perspectives and make them accessible through modern technology.

In the future, verified historical texts could help support AI research systems designed to explore the intellectual world of specific periods.

For example, a historically grounded AI simulation could attempt to answer questions using only the information that would have been available before a particular date.

This could allow users to explore questions such as:

- How might a natural philosopher in 1600 explain magnetism?
- How would an ancient scholar interpret modern technology?
- What scientific ideas were considered reasonable before later discoveries?
- How did historical beliefs about mythical creatures, astronomy, medicine, and the natural world develop?
- How did new evidence change the way people understood reality?

Such systems would be educational reconstructions, not literal recreations of historical individuals.

They would require carefully dated sources, historical verification, controls against anachronisms, and clear separation between documented beliefs and speculative simulations.

Eventually, these systems could be connected to interactive environments, games, or virtual reality experiences.

Imagine exploring a historically reconstructed environment while discussing natural philosophy with a simulated scholar whose responses are grounded in texts from that period.

Or placing different historical perspectives into a shared simulation and observing how their explanations differ.

There are countless possibilities for education, research, and experimentation.

**Before any of that becomes possible, however, the historical source material needs to be collected, transcribed, translated, and verified.**

That is why this project begins with the books themselves.

---

## 🗺️ Development Roadmap

### Phase 1 — Working Translation Pipeline

- [x] PDF page rendering
- [x] AI-assisted transcription
- [x] Latin-to-English translation
- [x] AMD Token Lab integration
- [x] AMD Lemonade local API integration
- [x] Sequential page processing
- [x] Configurable cooldown intervals
- [x] Retry and logging functionality
- [x] Markdown output generation
- [x] Initial local AI processing tests

### Phase 2 — Accuracy and Reliability

- [ ] Expand transcription correction testing
- [ ] Compare multiple AI models
- [ ] Evaluate transcription accuracy against verified reference text
- [ ] Improve handling of damaged or unusual historical typography
- [ ] Add clearer uncertainty reporting
- [ ] Expand automated error detection
- [ ] Improve performance on limited hardware

### Phase 3 — Historical Collection Support

- [ ] Support additional historical languages
- [ ] Add structured document metadata
- [ ] Improve source and edition tracking
- [ ] Support larger document collections
- [ ] Develop searchable historical text datasets
- [ ] Improve reproducibility and dataset documentation

### Phase 4 — Historical AI Research

- [ ] Explore period-constrained historical AI systems
- [ ] Develop methods for controlling historical knowledge cutoffs
- [ ] Build source-grounded historical question-answering experiments
- [ ] Investigate historical perspective simulations
- [ ] Explore educational and interactive applications

These phases represent development goals rather than completed features or guaranteed release dates.

---

## 🤝 Open Source and Community Contributions

I intend for this project to remain open and useful to others.

Historical knowledge belongs in the hands of people who want to learn from it.

Contributions, testing, bug reports, documentation improvements, and suggestions are welcome.

Areas where community assistance could be especially valuable include:

- Historical language expertise
- Transcription verification
- Translation quality evaluation
- AI model benchmarking
- Performance optimization
- Document processing improvements
- Historical source identification
- Documentation and accessibility

Even small improvements can make a meaningful difference when processing large collections of historical material.

---

## 📜 Licensing and Historical Source Rights

The project's original software code is intended to be distributed under the MIT License.

Historical documents, scanned editions, AI models, and third-party materials may be subject to separate copyright, licensing, or access restrictions.

The historical age of a work does not automatically establish that every modern scan, transcription, or edition can be redistributed without restrictions.

Users are responsible for ensuring that they have the appropriate rights to process and distribute their source materials.

AI-generated transcriptions and translations should be reviewed for accuracy before publication or scholarly use.

---

## ❤️ A Personal Note

I started this project because I genuinely love learning about how people throughout history understood the world.

There is something incredible about opening a book written hundreds of years ago and reading the thoughts of someone who was trying to solve problems with the knowledge available to them.

Sometimes their explanations seem strange by modern standards. Sometimes their observations are surprisingly insightful.

Either way, there is something worth learning.

I am developing this project independently, using the computer and resources I currently have available.

My hardware is old, and some tasks take significantly longer than they would on a modern AI workstation. I have had to work through memory limitations, model configuration issues, failed requests, and repeated testing.

But the system is working, and I intend to keep improving it.

Access to newer AI hardware would allow me to run larger models, process documents more efficiently, and spend more time improving the quality of the results.

Regardless of the equipment available, I want to continue building this project because I believe the underlying idea is worth pursuing.

If this work eventually helps even one person discover something new, explore a historical perspective they had never considered, or develop a greater appreciation for the knowledge left behind by earlier generations, then I consider that meaningful progress.

**The past contains an extraordinary amount of knowledge. We have the technology to make more of it accessible. I want to help make that happen.**

---

## Project Information

**Project:** Historical Book AI Translator  
**Developer:** weatose  
**Repository:** https://github.com/weatose/Historical-Book-AI-Translator  
**Initial Source:** William Gilbert, *De Magnete* (1600)  
**Technology:** Python, AMD Lemonade, vision-language AI models  
**Status:** Active development

*Preserving historical knowledge, one page at a time.*
