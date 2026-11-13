# Teaching with files and folders

Teach Sentinel accepts multiple files or a folder, up to 100 files per selection. Use **Choose folder** to preserve relative folder labels; these labels are metadata and never become server storage paths. Files receive individual missions and results. Retry failed submissions individually; check mission history before retrying an unconfirmed network submission.

Searchable sources include PDF text, PNG/JPEG text recognition, UTF-8 TXT/Markdown/CSV/JSON, and visible text from sampled MP4/MOV/WebM frames. Other file formats are preserved as stored sources. Stored sources do not create vectors or Learning Events and are not searchable in Recall. Scanned PDFs currently require a separate OCR step.

Image OCR uses local Tesseract English recognition. Video extraction samples at most 24 frames over videos up to two hours. It does not transcribe audio, extract embedded subtitle tracks, or understand every event in the recording. Each extracted frame carries its timestamp and sampling warnings.

The default upload ceiling is 1 GiB per file; an explicit existing `MAX_UPLOAD_BYTES` setting takes precedence. Images are additionally capped at 32 MiB and 40 million pixels; text files at 16 MiB input and 8 MiB extracted text. The interface reads actual server limits. PDF extraction has a separate 64 MiB text ceiling to accommodate large books. Local subprocesses have CPU, memory, output, and wall-time bounds. The backend Docker image installs Pillow, Tesseract, and FFmpeg; deployments must rebuild the image to enable these tools.

Accepted sources remain preserved when processing fails. A duplicate upload is detected by content hash. Resubmitting a stored-only source currently returns its existing record; it does not trigger reprocessing.

## Verification and local rollout

The November 12 rollout preserved the existing 76 catalog documents and eight teaching missions. The running API reports image OCR and video extraction available, audio transcription unavailable, and a 1 GiB server upload ceiling. The standard local startup script was run from a private release bundle under `outputs/media-upload-release`, referencing the installation's existing private environment and named volumes. The bundle retains the tested image; rebuilding the older checkout can replace it with that checkout's code.

Validation included real PNG and MP4 text extraction, local MiniLM embeddings, and indexing into an isolated in-memory Qdrant collection with a temporary SQLite catalog. No test sources were inserted into the live catalog. The frontend suite passed 90 tests and its production build; the final teaching UI checks passed 12 tests. Backend regression validation passed 2,019 tests across the full run and the eight migration tests rerun from their required backend directory; two optional tests were skipped. The final focused ingestion suite passed 75 tests with one optional skip. These checks validate ingestion behavior, not semantic accuracy of production answers.
