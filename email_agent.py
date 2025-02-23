import subprocess
import sys
import imaplib
import email
from datetime import datetime, timedelta
from email.header import decode_header
import getpass
from typing import List, Dict, Optional
from collections import defaultdict
import re

# First, install required packages if not present
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
required_packages = ['nltk', 'scikit-learn']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        install_package(package)

# Now import the required packages
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class EmailAgent:
    def __init__(self):
        self.mail = None
        self.logged_in = False
        self.email_cache = {}  # Cache for processed emails
        
        # Download NLTK data with error handling
        self.download_nltk_data()
        
        # Initialize NLP components
        try:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"Warning: Could not initialize NLP components. Error: {e}")
            self.lemmatizer = None
            self.stop_words = set()

    def download_nltk_data(self):
        """Download required NLTK data with robust error handling."""
        import ssl
        import nltk
        
        # Create unverified HTTPS context
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # List of required NLTK resources
        resources = [
            ('punkt', 'tokenizers/punkt'),
            ('stopwords', 'corpora/stopwords'),
            ('wordnet', 'corpora/wordnet'),
            ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger')
        ]

        # Download each resource
        for resource, path in resources:
            try:
                try:
                    nltk.data.find(path)
                except LookupError:
                    print(f"Downloading {resource}...")
                    nltk.download(resource, quiet=True)
            except Exception as e:
                print(f"Error downloading {resource}: {e}")
                print(f"Attempting alternative download method for {resource}...")
                try:
                    nltk.download(resource, download_dir='./nltk_data')
                    nltk.data.path.append('./nltk_data')
                except Exception as e2:
                    print(f"Failed to download {resource}. Error: {e2}")

    def login(self):
        """Logs into the email account using IMAP."""
        try:
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
            
            try:
                username = input("Enter your email: ").strip()
                password = getpass.getpass("Enter your app password: ").strip()
                
                if not username or not password:
                    raise ValueError("Email and password cannot be empty")
                
            except EOFError:
                print("\nInput interrupted. Please run the program in a terminal that supports input.")
                self.logged_in = False
                return
            except KeyboardInterrupt:
                print("\nLogin cancelled by user.")
                self.logged_in = False
                return
            
            try:
                self.mail.login(username, password)
                self.mail.select('inbox')
                self.logged_in = True
                print("Successfully logged in.")
            except imaplib.IMAP4.error as e:
                print(f"Login failed: Invalid credentials or IMAP access not enabled. Error: {e}")
                self.logged_in = False
            
        except Exception as e:
            print(f"Login failed: {e}")
            self.logged_in = False

    def decode_email_subject(self, subject):
        """Properly decode email subject."""
        if subject is None:
            return ""
        
        decoded_chunks = []
        for chunk, encoding in decode_header(subject):
            if isinstance(chunk, bytes):
                try:
                    decoded_chunks.append(chunk.decode(encoding or 'utf-8', errors='replace'))
                except:
                    decoded_chunks.append(chunk.decode('utf-8', errors='replace'))
            else:
                decoded_chunks.append(chunk)
        return ' '.join(decoded_chunks)

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better analysis."""
        if not self.lemmatizer:
            return text.lower()
            
        try:
            # Convert to lowercase and tokenize
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and lemmatize
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                     if token.isalnum() and token not in self.stop_words]
            
            return ' '.join(tokens)
        except Exception as e:
            print(f"Warning: Text preprocessing failed. Using basic processing. Error: {e}")
            return text.lower()

    def extract_key_information(self, text: str) -> Dict:
        """Extract key information from email text."""
        # Extract dates
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{2,4}'
        dates = re.findall(date_pattern, text)
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        # Extract potential action items
        action_patterns = [
            r'please\s+[^.!?]*[.!?]',
            r'required\s+[^.!?]*[.!?]',
            r'deadline[^.!?]*[.!?]',
            r'due\s+[^.!?]*[.!?]'
        ]
        action_items = []
        for pattern in action_patterns:
            action_items.extend(re.findall(pattern, text.lower()))
        
        return {
            "dates": dates,
            "urls": urls,
            "action_items": action_items
        }

    def summarize_email(self, email_text: str) -> str:
        """Generate a meaningful summary of the email content."""
        if not email_text:
            return "Unable to generate summary: No content provided."
            
        try:
            # Split into sentences with error handling
            try:
                sentences = sent_tokenize(email_text)
            except Exception as e:
                print(f"Warning: Sentence tokenization failed. Using basic splitting. Error: {e}")
                sentences = [s.strip() for s in email_text.split('.') if s.strip()]
                
            if not sentences:
                return "Unable to generate summary: Could not process content."
            
            # Preprocess sentences
            preprocessed_sentences = []
            for sent in sentences:
                try:
                    preprocessed = self.preprocess_text(sent)
                    if preprocessed:
                        preprocessed_sentences.append(preprocessed)
                except Exception as e:
                    print(f"Warning: Preprocessing failed for sentence. Error: {e}")
                    continue
                    
            if not preprocessed_sentences:
                return "Basic summary:\n" + email_text[:200] + "..."
            
            # Calculate sentence importance using TF-IDF
            try:
                sentence_vectors = self.vectorizer.fit_transform(preprocessed_sentences)
                sentence_scores = sentence_vectors.sum(axis=1).A1
            except Exception as e:
                print(f"Warning: TF-IDF calculation failed. Using basic selection. Error: {e}")
                return "Basic summary:\n" + sentences[0] + "\n..." + sentences[-1]
            
            # Select top sentences
            num_sentences = min(3, len(sentences))
            top_indices = sentence_scores.argsort()[-num_sentences:][::-1]
            
            # Extract key information
            key_info = self.extract_key_information(email_text)
            
            # Build summary
            summary = "Summary:\n"
            summary += "\nKey Points:\n"
            for idx in sorted(top_indices):
                if idx < len(sentences):
                    summary += f"- {sentences[idx].strip()}\n"
            
            if key_info['dates']:
                summary += "\nRelevant Dates:\n"
                for date in key_info['dates']:
                    summary += f"- {date}\n"
            
            if key_info['action_items']:
                summary += "\nAction Items:\n"
                for item in key_info['action_items']:
                    summary += f"- {item.capitalize()}\n"
            
            if key_info['urls']:
                summary += "\nRelevant Links:\n"
                for url in key_info['urls'][:3]:
                    summary += f"- {url}\n"
            
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate detailed summary. Basic content:\n" + email_text[:200] + "..."

    def get_emails_by_date(self, days_ago: int = 0) -> List[str]:
        """Fetches emails from specified number of days ago until now."""
        if not self.logged_in:
            return []

        try:
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%d-%b-%Y")
            status, messages = self.mail.search(None, f'SINCE "{date}"')
            if status != 'OK':
                return []
            
            return messages[0].split()
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def get_email_details(self, email_id) -> Optional[Dict]:
        """Fetches and processes details of a specific email."""
        # Check cache first
        if email_id in self.email_cache:
            return self.email_cache[email_id]
        
        try:
            status, msg_data = self.mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                return None
            
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject = self.decode_email_subject(email_message["Subject"])
            sender = email_message["From"]
            date = email_message["Date"]
            
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode()
                            break
                        except:
                            continue
            else:
                try:
                    body = email_message.get_payload(decode=True).decode()
                except:
                    body = "Unable to decode email body"
            
            # Process and categorize email
            categories = self.categorize_email(subject, body)
            summary = self.summarize_email(body)
            
            email_details = {
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "categories": categories,
                "summary": summary,
                "id": email_id
            }
            
            # Cache the processed email
            self.email_cache[email_id] = email_details
            
            return email_details
        except Exception as e:
            print(f"Error fetching email details: {e}")
            return None

    def categorize_email(self, subject: str, body: str) -> List[str]:
        """Categorize email based on content."""
        categories = []
        text = (subject + " " + body).lower()
        
        # Job-related emails
        job_keywords = [
            'job', 'career', 'position', 'opportunity', 'hiring', 'recruitment', 
            'interview', 'application', 'role', 'vacancy', 'resume', 'cv', 
            'employment', 'offer', 'recruit', 'apply', 'opening'
        ]
        if any(keyword in text for keyword in job_keywords):
            categories.append('job')

        # Course/Education related
        edu_keywords = [
            'course', 'training', 'workshop', 'webinar', 'education', 
            'learning', 'certification', 'degree', 'study', 'lecture', 
            'seminar', 'tutorial', 'class', 'program', 'online course'
        ]
        if any(keyword in text for keyword in edu_keywords):
            categories.append('education')

        return categories

    def close(self):
        """Closes the IMAP connection."""
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass

    def find_similar_emails(self, email_id: str) -> List[Dict]:
        """Find emails similar to the given email."""
        try:
            target_email = self.get_email_details(email_id)
            if not target_email:
                return []

            # Get recent emails for comparison
            recent_email_ids = self.get_emails_by_date(30)  # Look back 30 days
            similar_emails = []

            target_text = self.preprocess_text(target_email['subject'] + ' ' + target_email['body'])

            for other_id in recent_email_ids:
                if other_id == email_id:
                    continue

                other_email = self.get_email_details(other_id)
                if not other_email:
                    continue

                other_text = self.preprocess_text(other_email['subject'] + ' ' + other_email['body'])

                # Calculate similarity using TF-IDF and cosine similarity
                try:
                    tfidf_matrix = self.vectorizer.fit_transform([target_text, other_text])
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

                    if similarity > 0.3:  # Threshold for similarity
                        similar_emails.append(other_email)
                except Exception as e:
                    print(f"Warning: Similarity calculation failed for email. Error: {e}")

            return sorted(similar_emails, key=lambda x: x['date'], reverse=True)
        except Exception as e:
            print(f"Error finding similar emails: {e}")
            return []