import re
from collections import Counter

class SimpleSummarizer:
    """
    A simple extractive summarizer that selects the most relevant sentences
    based on keyword frequency.
    """
    
    def __init__(self):
        # Common stop words to ignore (simple list)
        self.stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'of', 'to', 'in', 'that', 'it', 'this', 'for', 'with', 'as', 'by',
            'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do',
            'does', 'did', 'not', 'so', 'can', 'could', 'should', 'would',
            'will', 'may', 'might', 'must', 'my', 'your', 'his', 'her', 'its',
            'our', 'their', 'I', 'you', 'he', 'she', 'we', 'they', 'me', 'him',
            'us', 'them', 'video', 'watch', 'subscribe', 'channel', 'like'
        }

    def _preprocess(self, text):
        """Clean and split text into sentences."""
        # Split by typical sentence terminators
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _score_sentences(self, sentences):
        """Score sentences based on word frequency."""
        words = []
        for s in sentences:
            # Tokenize and simplistic clean
            w_list = re.findall(r'\w+', s.lower())
            words.extend([w for w in w_list if w not in self.stop_words and len(w) > 2])
            
        word_freq = Counter(words)
        
        sentence_scores = {}
        for s in sentences:
            score = 0
            s_words = re.findall(r'\w+', s.lower())
            for w in s_words:
                if w in word_freq:
                    score += word_freq[w]
            
            # Normalize by length to avoid favoring long sentences too much
            if len(s_words) > 0:
                sentence_scores[s] = score / len(s_words)
            else:
                sentence_scores[s] = 0
                
        return sentence_scores

    def summarize(self, text, num_sentences=3):
        """
        Generate a summary from the text.
        """
        if not text:
            return ""
            
        sentences = self._preprocess(text)
        if not sentences:
            return text[:200] + "..."
            
        scores = self._score_sentences(sentences)
        
        # Get top N sentences by score
        top_sentences = sorted(scores, key=scores.get, reverse=True)[:num_sentences]
        
        # Sort them back by their original order in the text to maintain flow
        # (This is tricky since we lost index, effectively we just return them joined)
        # To maintain order, let's filter the original list
        
        summary = [s for s in sentences if s in top_sentences]
        
        return "\n".join(summary)

    def extract_text_from_srt(self, srt_path):
        """
        Extract plain text from an SRT file.
        """
        text_lines = []
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            is_time = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.isdigit():
                    continue
                if '-->' in line:
                    continue
                text_lines.append(line)
            
            return " ".join(text_lines)
        except Exception as e:
            return ""
